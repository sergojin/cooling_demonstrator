#!/usr/bin/env python3
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
PLOTS = BASE / "plots"


def load_muons():
    rows = []
    for path in sorted(BASE.glob("finalmom_job_*/score_z23300.txt")):
        with path.open() as f:
            for line in f:
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 8 or int(parts[7]) != -13:
                    continue
                x, y = float(parts[0]), float(parts[1])
                px, py, pz = map(float, parts[3:6])
                p = math.sqrt(px * px + py * py + pz * pz)
                xp = px / pz if pz else 0.0
                yp = py / pz if pz else 0.0
                rows.append((x, y, px, py, pz, p, xp, yp))
    return rows


def main():
    PLOTS.mkdir(exist_ok=True)
    rows = load_muons()
    p = [r[5] for r in rows]
    x = [r[0] for r in rows]
    y = [r[1] for r in rows]
    px = [r[2] for r in rows]
    xp = [1000.0 * r[6] for r in rows]

    fig, axs = plt.subplots(2, 2, figsize=(11.5, 8.5), dpi=170)

    ax = axs[0, 0]
    ax.hist(p, bins=70, range=(0, 520), color="#2563eb", alpha=0.75)
    ax.axvspan(180, 220, color="#dc2626", alpha=0.16)
    ax.axvline(200, color="#dc2626", linewidth=1.4)
    ax.set_xlabel("p [MeV/c]")
    ax.set_ylabel("mu+")
    ax.set_title("Final mu+ momentum")

    ax = axs[0, 1]
    sc = ax.scatter(p, x, c=p, s=6, cmap="viridis", alpha=0.55, linewidths=0)
    ax.axvspan(180, 220, color="#dc2626", alpha=0.12)
    ax.set_xlabel("p [MeV/c]")
    ax.set_ylabel("x [mm]")
    ax.set_title("Momentum vs horizontal position")
    fig.colorbar(sc, ax=ax, label="p [MeV/c]")

    ax = axs[1, 0]
    ax.scatter(p, px, c=p, s=6, cmap="viridis", alpha=0.55, linewidths=0)
    ax.axvspan(180, 220, color="#dc2626", alpha=0.12)
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.4)
    ax.set_xlabel("p [MeV/c]")
    ax.set_ylabel("px [MeV/c]")
    ax.set_title("Momentum vs horizontal momentum")

    ax = axs[1, 1]
    ax.scatter(x, xp, c=p, s=6, cmap="viridis", alpha=0.55, linewidths=0)
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.4)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("xp = px/pz [mrad]")
    ax.set_title("Final horizontal phase space")

    for ax in axs.flat:
        ax.grid(True, linewidth=0.35, alpha=0.35)

    fig.suptitle(f"Final-plane mu+ phase space, z = 23.3 m, N = {len(rows)}", y=0.995)
    fig.tight_layout()
    output = PLOTS / "final_muon_phase_space_z23300.png"
    fig.savefig(output)
    print(output)

    # A second plot with explicit low/high momentum populations makes the two
    # branches easier to inspect without relying on a color scale.
    low = [r for r in rows if 180 <= r[5] <= 220]
    high = [r for r in rows if r[5] >= 300]
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=170)
    for selected, label, color in [(low, "180-220 MeV/c", "#2563eb"), (high, ">=300 MeV/c", "#dc2626")]:
        axs[0].scatter([r[0] for r in selected], [1000.0 * r[6] for r in selected], s=7, alpha=0.55, label=label, color=color, linewidths=0)
        axs[1].scatter([r[0] for r in selected], [r[1] for r in selected], s=7, alpha=0.55, label=label, color=color, linewidths=0)
    axs[0].set_xlabel("x [mm]")
    axs[0].set_ylabel("xp [mrad]")
    axs[0].set_title("Horizontal phase-space branches")
    axs[1].set_xlabel("x [mm]")
    axs[1].set_ylabel("y [mm]")
    axs[1].set_title("Final transverse positions")
    for ax in axs:
        ax.grid(True, linewidth=0.35, alpha=0.35)
        ax.legend()
    fig.tight_layout()
    output2 = PLOTS / "final_muon_branch_overlay_z23300.png"
    fig.savefig(output2)
    print(output2)


if __name__ == "__main__":
    main()
