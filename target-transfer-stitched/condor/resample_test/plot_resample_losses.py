#!/usr/bin/env python3
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
COMBINED = BASE / "combined"
PLOTS = BASE / "plots"


def load_rows(path):
    rows = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "z_mm": float(row["z_mm"]),
                    "total": int(row["total"]),
                    "pi+": int(row["pi+"]),
                    "mu+": int(row["mu+"]),
                }
            )
    return rows


def plot_counts(rows):
    fig, ax = plt.subplots(figsize=(9.5, 5.8), dpi=170)
    z_m = [row["z_mm"] / 1000.0 for row in rows]
    for key, color, marker in [
        ("total", "#1f2937", "o"),
        ("pi+", "#2563eb", "s"),
        ("mu+", "#dc2626", "^"),
    ]:
        ax.plot(z_m, [row[key] for row in rows], marker=marker, linewidth=2, markersize=4.5, label=key, color=color)
    ax.set_yscale("log")
    ax.set_xlabel("z [m]")
    ax.set_ylabel("Tracks within r < 200 mm")
    ax.set_title("Resampled pi+ transport: survival vs z")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS / "resample_survival_counts_vs_z.png")
    plt.close(fig)


def plot_fraction(rows):
    fig, ax = plt.subplots(figsize=(9.5, 5.8), dpi=170)
    z_m = [row["z_mm"] / 1000.0 for row in rows]
    input_pi = rows[0]["pi+"] if rows else 1
    for key, color, marker in [
        ("total", "#1f2937", "o"),
        ("pi+", "#2563eb", "s"),
        ("mu+", "#dc2626", "^"),
    ]:
        values = [row[key] / input_pi if input_pi else 0.0 for row in rows]
        ax.plot(z_m, values, marker=marker, linewidth=2, markersize=4.5, label=key, color=color)
    ax.set_yscale("log")
    ax.set_xlabel("z [m]")
    ax.set_ylabel("Fraction of input pi+ sample")
    ax.set_title("Resampled pi+ transport: fractional survival vs z")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS / "resample_survival_fraction_vs_z.png")
    plt.close(fig)


def main():
    PLOTS.mkdir(exist_ok=True)
    rows = load_rows(COMBINED / "score_summary.csv")
    plot_counts(rows)
    plot_fraction(rows)
    print(PLOTS / "resample_survival_counts_vs_z.png")
    print(PLOTS / "resample_survival_fraction_vs_z.png")


if __name__ == "__main__":
    main()
