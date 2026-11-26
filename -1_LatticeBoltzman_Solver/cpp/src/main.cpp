// Headless LBM wind tunnel: runs the simulation and writes vorticity frames.
//
//   ./build/lbm [--nx 400] [--ny 100] [--steps 4000] [--every 100]
//               [--u0 0.1] [--nu 0.02] [--out output]
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <string>

#include "image.hpp"
#include "simulation.hpp"

int main(int argc, char** argv) {
  int nx = 400, ny = 100, steps = 4000, every = 100;
  float u0 = 0.1f, nu = 0.02f;
  std::string outDir = "output";

  for (int i = 1; i + 1 < argc; i += 2) {
    std::string key = argv[i];
    const char* v = argv[i + 1];
    if (key == "--nx") nx = std::atoi(v);
    else if (key == "--ny") ny = std::atoi(v);
    else if (key == "--steps") steps = std::atoi(v);
    else if (key == "--every") every = std::atoi(v);
    else if (key == "--u0") u0 = std::strtof(v, nullptr);
    else if (key == "--nu") nu = std::strtof(v, nullptr);
    else if (key == "--out") outDir = v;
    else { std::fprintf(stderr, "unknown option %s\n", argv[i]); return 1; }
  }

  std::filesystem::create_directories(outDir);
  Simulation sim(nx, ny, u0, nu);
  // Same cylinder as the Python preset (offset one cell to trigger shedding).
  sim.addCylinder(nx / 5.0f, ny / 2.0f + 1, ny / 10.0f);

  std::printf("grid %dx%d  u0=%.3f  nu=%.4f  omega=%.3f  Re=%.0f\n", nx, ny, u0, nu, sim.omega(),
              u0 * (ny / 5.0f) / nu);

  auto start = std::chrono::steady_clock::now();
  for (int s = 1; s <= steps; ++s) {
    sim.step();
    if (s % every == 0 || s == steps) {
      if (!sim.isFinite()) {
        std::fprintf(stderr, "step %d: simulation blew up (NaN/inf). Raise --nu or lower --u0.\n", s);
        return 2;
      }
      sim.computeMacroscopic();
      char name[64];
      std::snprintf(name, sizeof name, "/frame_%05d.ppm", s);
      writePPM(outDir + name, sim.vorticity(), sim.obstacle(), nx, ny, /*symmetric=*/true);
    }
  }
  double secs = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
  std::printf("%d steps in %.2f s  (%.0f steps/s, %.1f MLUPS)\n", steps, secs, steps / secs,
              double(steps) * nx * ny / secs / 1e6);
  std::printf("frames in %s/\n", outDir.c_str());
  return 0;
}
