#!/usr/bin/env python3
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
COMBINED = BASE / "combined"
PLOTS = BASE / "plots"


def read_pairs(path):
    data = {}
    if not path.exists():
        return data
    with path.open() as f:
        for line in f:
            parts = line.split()
            if len(parts) == 2:
                data[parts[0]] = parts[1]
    return data


def main():
    rows = []
    candidates = list(BASE.glob("point_*")) + list((BASE / "jobs").glob("point_*"))
    for job_dir in sorted(candidates):
        point = read_pairs(job_dir / "scan_point.txt")
        summary = read_pairs(job_dir / "job_summary.txt")
        if not point or not summary:
            continue
        n_events = int(summary.get("n_events", point["n_events"]))
        final_muons = int(summary.get("final_muons", "0"))
        rows.append(
            {
                "point_id": int(point["point_id"]),
                "qf_gradient_T_per_m": float(point["qf_gradient"]),
                "qd_gradient_T_per_m": float(point["qd_gradient"]),
                "n_events": n_events,
                "final_muons": final_muons,
                "yield_per_proton": final_muons / n_events if n_events else 0.0,
            }
        )

    rows.sort(key=lambda row: (-row["yield_per_proton"], row["point_id"]))
    COMBINED.mkdir(exist_ok=True)
    out = COMBINED / "quad_gradient_scan_summary.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "point_id",
                "qf_gradient_T_per_m",
                "qd_gradient_T_per_m",
                "n_events",
                "final_muons",
                "yield_per_proton",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"completed_points={len(rows)}")
    if rows:
        best = rows[0]
        print(
            "best="
            f"point {best['point_id']} "
            f"QF={best['qf_gradient_T_per_m']} "
            f"QD={best['qd_gradient_T_per_m']} "
            f"muons={best['final_muons']} "
            f"yield={best['yield_per_proton']:.8g}"
        )
    print(f"summary={out}")

    PLOTS.mkdir(exist_ok=True)
    if rows:
        make_plots(rows)


def make_plots(rows):
    by_point = sorted(rows, key=lambda row: row["point_id"])

    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=160)
    labels = [f"{row['qf_gradient_T_per_m']:.3g}, {row['qd_gradient_T_per_m']:.3g}" for row in by_point]
    yields = [row["yield_per_proton"] for row in by_point]
    bars = ax.bar(range(len(by_point)), yields, color="#4c78a8", edgecolor="#263238")
    best_index = max(range(len(by_point)), key=lambda index: yields[index])
    bars[best_index].set_color("#59a14f")
    ax.set_xticks(range(len(by_point)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_xlabel("QF gradient, QD gradient [T/m]")
    ax.set_ylabel("Final-plane muon yield / proton")
    ax.set_title("QF/QD scan yield")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTS / "quad_gradient_scan_yield_by_point.png")
    plt.close(fig)

    qf_values = sorted({row["qf_gradient_T_per_m"] for row in rows})
    qd_values = sorted({row["qd_gradient_T_per_m"] for row in rows})
    yield_map = [
        [
            next(
                (
                    row["yield_per_proton"]
                    for row in rows
                    if row["qf_gradient_T_per_m"] == qf and row["qd_gradient_T_per_m"] == qd
                ),
                0.0,
            )
            for qf in qf_values
        ]
        for qd in qd_values
    ]

    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=160)
    image = ax.imshow(yield_map, origin="lower", aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(qf_values)))
    ax.set_xticklabels([f"{value:.3g}" for value in qf_values])
    ax.set_yticks(range(len(qd_values)))
    ax.set_yticklabels([f"{value:.3g}" for value in qd_values])
    ax.set_xlabel("QF gradient [T/m]")
    ax.set_ylabel("QD gradient [T/m]")
    ax.set_title("Final-plane muon yield / proton")
    fig.colorbar(image, ax=ax, label="muons / proton")
    for y_index, qd in enumerate(qd_values):
        for x_index, qf in enumerate(qf_values):
            value = yield_map[y_index][x_index]
            ax.text(x_index, y_index, f"{value:.2g}", ha="center", va="center", color="white")
    fig.tight_layout()
    fig.savefig(PLOTS / "quad_gradient_scan_yield_heatmap.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
