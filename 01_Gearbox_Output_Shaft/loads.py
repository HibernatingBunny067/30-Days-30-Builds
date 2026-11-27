import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

out = Path(__file__).parent / "figures" / "01_diagrams.png"

phi = np.deg2rad(20) #radians
N1,N2 = 1440,450 #RPM
P = 3000.0 #Watts
d_gear = 160 #mm
D_pulley = 200.0 #mm
ratio = 5.0

x_A, x_gear, x_B, x_pulley = 0.0, 55.0, 140.0, 210.0 #mm
x_start, x_end = -8.0, 222.5 #mm

omega = 2*np.pi*N2/60 #rad/s
T = 1000*P/omega #N-mm
Wt = T/(d_gear/2) 
Wr = Wt* np.tan(phi)
dF = T/(D_pulley/2)
F2 = dF/(ratio-1)
F1 = ratio*F2
F_belt = F1 + F2


print(f"""
T = {T/1000:.2f} N-m, Wt = {Wt:.1f} N, Wr = {Wr:.1f} N, F1 = {F1:.1f} N, F2 = {F2:.1f} N 
""")

loads_z = [[x_gear,-Wt]]
loads_y =[[x_gear,Wr],[x_pulley,-F_belt]]

def reactions(loads):
    sum_F = sum(F for _, F in loads)
    sum_M_a = sum(F*(x-x_A) for x, F in loads)
    R_B = -sum_M_a / (x_B-x_A)
    R_A = -sum_F - R_B
    return R_A, R_B

R_Az, R_Bz = reactions(loads_z)
R_Ay, R_By = reactions(loads_y)

print(f"xz: R_A = {R_Az:.1f} N, R_B = {R_Bz:.1f} N")
print(f"xy: R_A = {R_Ay:.1f} N, R_B = {R_By:.1f} N")

x = np.linspace(x_start, x_end, 2001)

def shear_moment(point_loads):
    V = np.zeros_like(x)
    M = np.zeros_like(x)
    for xi, F in point_loads:
        left = x > xi                       
        V += F * left
        M += F * (x - xi) * left
    return V, M

V_z, M_z = shear_moment(loads_z + [(x_A, R_Az), (x_B, R_Bz)])
V_y, M_y = shear_moment(loads_y + [(x_A, R_Ay), (x_B, R_By)])

M_res = np.hypot(M_y, M_z)                                      
T_x   = np.where((x >= x_gear) & (x <= x_pulley), T, 0.0)


## CHECKING THE CALCULATIONS

for name, loads, RA, RB in [("xz", loads_z, R_Az, R_Bz), ("xy", loads_y, R_Ay, R_By)]:
    assert abs(sum(F for _, F in loads) + RA + RB) < 1e-6, f"{name}: forces don't balance"

assert abs(M_res[-1]) < 1e-6, "moment should be zero at the free end"
M_at_B = np.interp(x_B, x, M_res)
assert np.isclose(M_at_B, F_belt * (x_pulley - x_B), rtol=1e-3), "M at B should equal belt pull × overhang"
print("checks passed")

## PLOTTING and TABLING

sections = [(42.5, "collar fillet"), (55, "gear keyseat"), (132, "shoulder"),
            (148, "step at bearing B"), (197.5, "pulley step / keyseat")]
print(f"\n{'section':24s}{'x (mm)':>8s}{'M (N·m)':>10s}{'T (N·m)':>10s}")
for xs, name in sections:
    Ms = np.interp(xs, x, M_res) / 1000
    Ts = T / 1000 if x_gear <= xs <= x_pulley else 0.0
    print(f"{name:24s}{xs:8.1f}{Ms:10.1f}{Ts:10.1f}")

fig, ax = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
ax[0].plot(x, V_y, label="V_xy"); ax[0].plot(x, V_z, label="V_xz"); ax[0].set_ylabel("Shear (N)")
ax[1].plot(x, M_y/1000, label="M_xy"); ax[1].plot(x, M_z/1000, label="M_xz"); ax[1].set_ylabel("Moment (N·m)")
ax[2].plot(x, M_res/1000, color="k"); ax[2].set_ylabel("Resultant M (N·m)")
i = np.argmax(M_res); ax[2].annotate(f"max {M_res[i]/1000:.1f} N·m at x = {x[i]:.0f} mm", (x[i], M_res[i]/1000))
ax[3].plot(x, T_x/1000, color="tab:purple"); ax[3].set_ylabel("Torque (N·m)"); ax[3].set_xlabel("x (mm)")
for a in ax:
    a.axhline(0, color="grey", lw=0.6)
    for xs in (x_A, x_gear, x_B, x_pulley):
        a.axvline(xs, color="grey", lw=0.5, ls=":")
    if a.get_legend_handles_labels()[0]:
        a.legend()
fig.tight_layout()
fig.savefig(out, dpi=200)
plt.show()