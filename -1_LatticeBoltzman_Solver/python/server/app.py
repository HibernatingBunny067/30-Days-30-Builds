"""
Partially written by AI (Claude)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from pathlib import Path

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from matplotlib import colormaps

from solver.lbm import PRESETS, WindTunnel

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
TARGET_FPS = 30
log = logging.getLogger("uvicorn.error")
active_sessions = 0

# mode -> (matplotlib colormap, symmetric around zero?)
MODES = {
    "vorticity": ("RdBu_r", True),
    "speed": ("inferno", False),
    "pressure": ("coolwarm", True),
}

app = FastAPI(title="LB Wind Tunnel")


def make_lut(cmap_name: str) -> list[int]:
    rgb = colormaps[cmap_name](np.linspace(0, 1, 256))[:, :3]
    return (rgb * 255).round().astype(np.uint8).ravel().tolist()


def clamp(value, lo, hi, cast=float):
    return max(lo, min(hi, cast(value)))


class Session:
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.sim = WindTunnel()
        self.sim.load_preset("cylinder")
        self.mode = "vorticity"
        self.steps_per_frame = 10
        self.paused = False
        self.commands: deque[dict] = deque()
        self.scale = None  # running colour-scale, adapts to the flow
        self.needs_config = True

    # ---------------------------------------------------------------- I/O

    async def run(self) -> None:
        receiver = asyncio.create_task(self.receive())
        sim_loop = asyncio.create_task(self.loop())
        done, pending = await asyncio.wait({receiver, sim_loop}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            exc = task.exception()
            if exc and not isinstance(exc, WebSocketDisconnect):
                raise exc

    async def receive(self) -> None:
        while True:
            text = await self.ws.receive_text()
            try:
                msg = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(msg, dict):
                self.commands.append(msg)

    async def send_config(self) -> None:
        cmap, _ = MODES[self.mode]
        await self.ws.send_text(json.dumps({
            "type": "config",
            "nx": self.sim.nx,
            "ny": self.sim.ny,
            "mode": self.mode,
            "modes": list(MODES),
            "presets": list(PRESETS),
            "lut": make_lut(cmap),
            "u0": self.sim.u0,
            "viscosity": self.sim.viscosity,
            "steps_per_frame": self.steps_per_frame,
            "paused": self.paused,
        }))

    # ---------------------------------------------------------- simulation

    def apply_commands(self) -> None:
        while self.commands:
            msg = self.commands.popleft()
            kind = msg.get("type")
            try:
                if kind == "draw":
                    self.sim.paint(
                        clamp(msg["x"], -50, self.sim.nx + 50),
                        clamp(msg["y"], -50, self.sim.ny + 50),
                        clamp(msg.get("r", 3), 0.5, 30),
                        solid=not msg.get("erase", False),
                    )
                elif kind == "set":
                    if "u0" in msg:
                        self.sim.u0 = clamp(msg["u0"], 0.01, 0.2)
                    if "viscosity" in msg:
                        self.sim.viscosity = clamp(msg["viscosity"], 0.003, 0.2)
                    if "steps_per_frame" in msg:
                        self.steps_per_frame = clamp(msg["steps_per_frame"], 1, 60, int)
                    if msg.get("mode") in MODES and msg["mode"] != self.mode:
                        self.mode = msg["mode"]
                        self.scale = None
                        self.needs_config = True
                elif kind == "preset" and msg.get("name") in PRESETS:
                    self.sim.load_preset(msg["name"])
                    self.scale = None
                elif kind == "reset":
                    self.sim.reset()
                    self.scale = None
                elif kind == "pause":
                    self.paused = bool(msg.get("paused", not self.paused))
            except (KeyError, TypeError, ValueError):
                continue  # ignore malformed input

    def advance_and_render(self, steps: int) -> tuple[bytes, bool]:
        """Runs in a worker thread so the event loop stays responsive."""
        sim = self.sim
        if steps:
            sim.step(steps)
            if not sim.is_finite():
                sim.reset()
                self.scale = None
                return self.render(), False
        return self.render(), True

    def render(self) -> bytes:
        sim = self.sim
        field = getattr(sim, self.mode)()
        _, symmetric = MODES[self.mode]
        fluid = field[~sim.obstacle]
        # Robust colour range (99th percentile), smoothed so it doesn't flicker.
        if symmetric:
            target = float(np.percentile(np.abs(fluid), 99)) if fluid.size else 1.0
        else:
            target = float(np.percentile(fluid, 99.5)) if fluid.size else 1.0
        target = max(target, 1e-6)
        self.scale = target if self.scale is None else 0.9 * self.scale + 0.1 * target
        lo, hi = (-self.scale, self.scale) if symmetric else (0.0, self.scale)

        out = np.empty((sim.ny, sim.nx, 2), np.uint8)
        out[..., 0] = np.clip((field - lo) * (255.0 / (hi - lo)), 0, 255)
        out[..., 1] = sim.obstacle * np.uint8(255)
        return out.tobytes()

    async def loop(self) -> None:
        frame_time = 1.0 / TARGET_FPS
        window_start, window_steps, window_frames = time.perf_counter(), 0, 0
        while True:
            start = time.perf_counter()
            self.apply_commands()
            if self.needs_config:
                self.needs_config = False
                await self.send_config()

            steps = 0 if self.paused else self.steps_per_frame
            frame, stable = await asyncio.to_thread(self.advance_and_render, steps)
            if not stable:
                await self.ws.send_text(json.dumps({
                    "type": "notice",
                    "text": "Flow went unstable and was reset. Raise viscosity or lower inlet speed.",
                }))
            await self.ws.send_bytes(frame)
            window_steps += steps
            window_frames += 1

            now = time.perf_counter()
            if now - window_start >= 1.0:
                elapsed = now - window_start
                await self.ws.send_text(json.dumps({
                    "type": "stats",
                    "steps_per_sec": round(window_steps / elapsed),
                    "fps": round(window_frames / elapsed, 1),
                    "mlups": round(window_steps * self.sim.nx * self.sim.ny / elapsed / 1e6, 2),
                    "reynolds": round(self.sim.reynolds()),
                    "step": self.sim.steps,
                }))
                window_start, window_steps, window_frames = now, 0, 0

            await asyncio.sleep(max(0.0, frame_time - (time.perf_counter() - start)))


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    global active_sessions
    await ws.accept()
    active_sessions += 1
    log.info("session started (%d active)", active_sessions)
    try:
        await Session(ws).run()
    except WebSocketDisconnect:
        pass
    finally:
        active_sessions -= 1
        log.info("session ended (%d active)", active_sessions)


# Registered last so /ws takes precedence over the static catch-all.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
