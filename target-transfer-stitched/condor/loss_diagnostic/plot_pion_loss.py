#!/usr/bin/env python3
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
ALL = BASE / "loss_all.summary.csv"
R200 = BASE / "loss_r200.summary.csv"
OUT = BASE / "pion_loss_vs_z.png"


def read_counts(path):
    rows = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            z = float(row["z_m"])
            # Keep the regular 0.5 m scoring planes; loss_all also includes
            # extra planes where tracks cross curved chicane coordinates.
            if abs((z * 2) - round(z * 2)) > 1e-6:
                continue
            rows.append((z, int(row.get("pi+", 0)), int(row.get("mu+", 0)), int(row["total"])))
    return rows


def main():
    all_rows = read_counts(ALL)
    r200_rows = read_counts(R200)

    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=160)
    ax.plot([z for z, pi, _, _ in all_rows], [pi for _, pi, _, _ in all_rows],
            marker="o", lw=1.8, label="pi+ all live")
    ax.plot([z for z, pi, _, _ in r200_rows], [pi for _, pi, _, _ in r200_rows],
            marker="s", lw=1.8, label="pi+ r < 200 mm")

    elements = [
        (11.55, "ch_q1"),
        (12.55, "ch_q2"),
        (13.8, "bend 1"),
        (15.55, "ch_q3"),
        (16.55, "ch_q4"),
        (17.55, "ch_q5"),
        (19.3, "bend 2"),
        (20.55, "ch_q6"),
        (21.55, "ch_q7"),
        (22.55, "ch_q8"),
    ]
    for z, label in elements:
        ax.axvline(z, color="#555", lw=0.9, alpha=0.35)
        ax.text(z, ax.get_ylim()[1] * 0.96, label, rotation=90,
                va="top", ha="right", fontsize=8, color="#333")

    ax.set_xlabel("z [m]")
    ax.set_ylabel("pi+ count per 1000 protons")
    ax.set_title("Pion survival through decay channel and chicane")
    ax.set_yscale("symlog", linthresh=1)
    ax.grid(True, which="both", axis="y", alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
