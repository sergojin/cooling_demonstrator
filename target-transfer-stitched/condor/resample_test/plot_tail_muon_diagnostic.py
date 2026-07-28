#!/usr/bin/env python3
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
RUN = BASE / "dense_tail_100k"
PLOTS = BASE / "plots"


def load(path):
    rows = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            n = int(row["n_mu_180_220"])
            if n == 0:
                continue
            rows.append(
                {
                    "z_m": float(row["z_mm"]) / 1000.0,
                    "n": n,
                    "r_p10": float(row["r_p10"]) if row["r_p10"] else None,
                    "r_med": float(row["r_med"]) if row["r_med"] else None,
                    "r_p90": float(row["r_p90"]) if row["r_p90"] else None,
                    "x_med": float(row["x_med"]) if row["x_med"] else None,
                    "xp_med": float(row["xp_med"]) if row["xp_med"] else None,
                }
            )
    return rows


def main():
    PLOTS.mkdir(exist_ok=True)
    rows = load(RUN / "tail_muons_180_220_summary.csv")
    z = [row["z_m"] for row in rows]

    fig, (ax_n, ax_r, ax_x) = plt.subplots(3, 1, figsize=(9.5, 8.2), dpi=170, sharex=True)
    ax_n.plot(z, [row["n"] for row in rows], marker="o", color="#dc2626", linewidth=2)
    ax_n.set_yscale("log")
    ax_n.set_ylabel("mu+ count")
    ax_n.grid(True, which="both", linewidth=0.4, alpha=0.35)

    ax_r.plot(z, [row["r_med"] for row in rows], marker="o", label="median r", color="#2563eb", linewidth=2)
    ax_r.plot(z, [row["r_p90"] for row in rows], marker="s", label="90% r", color="#7c3aed", linewidth=2)
    ax_r.axhline(200, color="#111827", linestyle="--", linewidth=1.2, label="200 mm aperture")
    ax_r.set_ylabel("r [mm]")
    ax_r.grid(True, linewidth=0.4, alpha=0.35)
    ax_r.legend(loc="lower left")

    ax_x.plot(z, [row["x_med"] for row in rows], marker="o", label="median x", color="#059669", linewidth=2)
    ax_x.plot(z, [1000 * row["xp_med"] for row in rows], marker="s", label="median xp x1000", color="#f97316", linewidth=2)
    ax_x.set_xlabel("z [m]")
    ax_x.set_ylabel("x [mm], xp x1000")
    ax_x.grid(True, linewidth=0.4, alpha=0.35)
    ax_x.legend(loc="lower left")

    fig.suptitle("Tail diagnostic for 180-220 MeV/c mu+")
    fig.tight_layout()
    fig.savefig(PLOTS / "tail_muons_180_220_diagnostic.png")
    print(PLOTS / "tail_muons_180_220_diagnostic.png")


if __name__ == "__main__":
    main()
