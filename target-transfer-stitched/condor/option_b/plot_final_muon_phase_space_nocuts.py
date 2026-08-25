#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_final_muons(base: Path) -> list[tuple[float, float, float, float, float]]:
    rows = []
    for path in sorted(base.glob("job_*/score_z23300.txt")):
        with path.open() as handle:
            for line in handle:
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 8 or int(float(parts[7])) != -13:
                    continue
                x = float(parts[0])
                y = float(parts[1])
                px = float(parts[3])
                py = float(parts[4])
                pz = float(parts[5])
                if pz == 0.0:
                    continue
                p = math.sqrt(px * px + py * py + pz * pz)
                rows.append((x, px / pz, y, py / pz, p))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot final-plane mu+ x-x' and y-y' before momentum and ellipse cuts.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--label", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    rows = load_final_muons(run_dir)
    output = args.output or run_dir / "plots" / "final_muon_phase_space_nocuts_z23300.png"
    output.parent.mkdir(exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), constrained_layout=True)
    title_label = f" - {args.label}" if args.label else ""
    fig.suptitle(f"Final-plane mu+ phase space before cuts{title_label}, N = {len(rows)}")

    panels = [
        (axes[0], 0, 1, "x [m]", "x' = px/pz [rad]"),
        (axes[1], 2, 3, "y [m]", "y' = py/pz [rad]"),
    ]
    if rows:
        p_values = [row[4] for row in rows]
        for axis, u_index, up_index, xlabel, ylabel in panels:
            scatter = axis.scatter(
                [row[u_index] / 1000.0 for row in rows],
                [row[up_index] for row in rows],
                c=p_values,
                cmap="viridis",
                s=8,
                alpha=0.55,
                linewidths=0,
            )
            axis.figure.colorbar(scatter, ax=axis, label="p [MeV/c]")
            axis.axhline(0.0, color="0.25", linewidth=0.7, alpha=0.35)
            axis.axvline(0.0, color="0.25", linewidth=0.7, alpha=0.35)
            axis.set_xlabel(xlabel)
            axis.set_ylabel(ylabel)
            axis.set_xlim(-0.2, 0.2)
            axis.set_ylim(-0.15, 0.15)
            axis.grid(True, linewidth=0.4, alpha=0.35)
    else:
        for axis, _, _, xlabel, ylabel in panels:
            axis.text(0.5, 0.5, "No final-plane mu+", ha="center", va="center", transform=axis.transAxes)
            axis.set_xlabel(xlabel)
            axis.set_ylabel(ylabel)
            axis.set_xlim(-0.2, 0.2)
            axis.set_ylim(-0.15, 0.15)
            axis.grid(True, linewidth=0.4, alpha=0.35)

    fig.savefig(output, dpi=160)

    summary = output.with_suffix(".txt")
    with summary.open("w") as out:
        out.write(f"run_dir {run_dir}\n")
        out.write("selection PDGid==-13 only; no momentum cut; no ellipse cut\n")
        out.write(f"final_mu+_nocuts {len(rows)}\n")
        if rows:
            p_values = [row[4] for row in rows]
            out.write(f"p_min_MeVc {min(p_values):.9g}\n")
            out.write(f"p_max_MeVc {max(p_values):.9g}\n")
        out.write(f"plot {output}\n")

    print(output)
    print(summary)
    print(f"final_mu+_nocuts {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
