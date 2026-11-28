import csv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

here = Path(__file__).parent

S_ut, S_y = 630.0, 530.0 #MPa
n = 2.0
T = 63.66 #N-m

k_a = 4.51 * S_ut**-0.265
k_c, k_d, k_e = 1.0, 1.0, 0.814
Se_dash = 0.5 * S_ut

def k_b(d):
    return 1.24 * d**-0.107

def q(r, torsion=False):
    s = S_ut / 6.894757
    if torsion:
        sqrt_a = 0.190 - 2.51e-3*s + 1.35e-5*s**2 - 2.67e-8*s**3
    else:
        sqrt_a = 0.246 - 3.08e-3*s + 1.51e-5*s**2 - 2.67e-8*s**3
    return 1 / (1 + sqrt_a / np.sqrt(r/25.4))

shoulder = (2.7, 2.2)
keyseat = (2.14, 3.0)

sections = [
    ("collar fillet",        42.5, 38, 1.5,  shoulder, 34.5, 0.0),
    ("gear keyseat",         55.0, 38, 0.76, keyseat,  44.7, T),
    ("shoulder 36-30",      132.0, 30, 1.0,  shoulder, 64.0, T),
    ("step at B 30-28",     148.0, 28, 1.0,  shoulder, 59.2, T),
    ("pulley keyseat",      197.5, 25, 0.5,  keyseat,  11.9, T),
]

## FATIGUE AND YIELD

rows = []
for name, x, d, r, (Kt, Kts), M, Tq in sections:
    Kf = 1 + q(r)*(Kt - 1)
    Kfs = 1 + q(r, True)*(Kts - 1)
    Se = k_a * k_b(d) * k_c * k_d * k_e * Se_dash

    Ma, Tm = M*1000, Tq*1000 #N-mm
    n_f = 1 / (16/(np.pi*d**3) * (2*Kf*Ma/Se + np.sqrt(3)*Kfs*Tm/S_ut))
    sig = np.sqrt((32*Kf*Ma/(np.pi*d**3))**2 + 3*(16*Kfs*Tm/(np.pi*d**3))**2)
    n_y = S_y / sig
    d_min = (16*n/np.pi * (2*Kf*Ma/Se + np.sqrt(3)*Kfs*Tm/S_ut))**(1/3)

    rows.append([name, x, d, M, round(Tq, 1), round(Kf, 2), round(Kfs, 2),
                 round(Se, 1), round(n_f, 2), round(n_y, 2), round(d_min, 1)])

print(f"k_a = {k_a:.3f}, Se' = {Se_dash:.0f} MPa\n")
print(f"{'section':18s}{'x':>7s}{'d':>5s}{'M':>7s}{'T':>7s}{'Kf':>6s}{'Kfs':>6s}{'Se':>7s}{'n_f':>7s}{'n_y':>7s}{'d_min':>7s}")
for row in rows:
    print(f"{row[0]:18s}{row[1]:7.1f}{row[2]:5.0f}{row[3]:7.1f}{row[4]:7.1f}{row[5]:6.2f}{row[6]:6.2f}{row[7]:7.1f}{row[8]:7.2f}{row[9]:7.2f}{row[10]:7.1f}")

worst = min(rows, key=lambda row: row[8])
print(f"\nlowest n_f = {worst[8]} at {worst[0]} (x = {worst[1]} mm)")

## CHECKING

for row in rows:
    assert row[8] >= n and row[9] >= n, f"{row[0]} fails"
print("all sections pass")

## SAVING

header = ["section", "x_mm", "d_mm", "M_Nm", "T_Nm", "Kf", "Kfs", "Se_MPa", "n_f", "n_y", "d_min_mm"]
with open(here / "results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)

cols = [0, 1, 2, 3, 4, 5, 6, 8, 9, 10]
labels = ["Section", "x (mm)", "d (mm)", "M (N·m)", "T (N·m)", "Kf", "Kfs", "n_f", "n_y", "d_min (mm)"]
fig, ax = plt.subplots(figsize=(11, 2.8))
ax.axis("off")
tbl = ax.table(cellText=[[row[c] for c in cols] for row in rows], colLabels=labels, loc="center", cellLoc="center")
tbl.auto_set_font_size(False)
tbl.set_fontsize(11)
tbl.scale(1, 1.6)
for j in range(len(cols)):
    tbl[0, j].set_facecolor("#dddddd")
    tbl[rows.index(worst) + 1, j].set_facecolor("#ffd9a0")
ax.set_title("DE-Goodman, AISI 1045 CD, 99% reliability (lowest n_f highlighted)")
fig.tight_layout()
fig.savefig(here / "figures" / "01_sf_table.png", dpi=200)
