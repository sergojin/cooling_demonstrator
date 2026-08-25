#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import shutil
from pathlib import Path

import run_dispersion_scan as coarse


BASE = Path(__file__).resolve().parent
RUNS = BASE / "runs_refine_negative_outer"
OUTER_SCALES = tuple(round(-0.8 + 0.1 * i, 10) for i in range(7))
CENTER_SCALES = tuple(round(1.15 + 0.05 * i, 10) for i in range(7))


def main() -> int:
    if RUNS.exists():
        shutil.rmtree(RUNS)
    RUNS.mkdir(parents=True)

    rows = []
    for outer_scale in OUTER_SCALES:
        for center_scale in CENTER_SCALES:
            outer_label = f"{outer_scale:+.2f}".replace("+", "p").replace("-", "m")
            center_label = f"{center_scale:.2f}".replace(".", "p")
            run_dir = RUNS / f"outer_{outer_label}_center_{center_label}"
            run_dir.mkdir()
            coarse.write_beam(run_dir / "beam.tmp")
            coarse.write_config(run_dir / "resample_downstream.g4bl", outer_scale, center_scale)
            coarse.run_g4bl(run_dir)

            row = {
                "outer_scale": f"{outer_scale:.2f}",
                "center_scale": f"{center_scale:.2f}",
                "q3_q5_gradient_T_per_m": f"{coarse.Q3_NOMINAL * outer_scale:.9g}",
                "q4_gradient_T_per_m": f"{coarse.Q4_NOMINAL * center_scale:.9g}",
            }
            for plane, filename in coarse.SCORE_PLANES.items():
                tracks = coarse.read_plane(run_dir / filename)
                d_mm, dp, n_tracks = coarse.fit_dispersion(tracks)
                row[f"{plane}_tracks"] = str(n_tracks)
                row[f"{plane}_D_mm"] = f"{d_mm:.9g}" if not math.isnan(d_mm) else "nan"
                row[f"{plane}_Dp_rad"] = f"{dp:.9g}" if not math.isnan(dp) else "nan"
                row[f"{plane}_objective_mm"] = f"{coarse.objective(d_mm, dp):.9g}"
            rows.append(row)

    fields = [
        "outer_scale",
        "center_scale",
        "q3_q5_gradient_T_per_m",
        "q4_gradient_T_per_m",
        "after_chicane_tracks",
        "after_chicane_D_mm",
        "after_chicane_Dp_rad",
        "after_chicane_objective_mm",
        "final_tracks",
        "final_D_mm",
        "final_Dp_rad",
        "final_objective_mm",
    ]
    summary_csv = BASE / "dispersion_refine_negative_outer_summary.csv"
    with summary_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    ranked = sorted(rows, key=lambda row: float(row["final_objective_mm"]))
    best_txt = BASE / "best_refine_negative_outer_objective.txt"
    with best_txt.open("w") as out:
        out.write("Negative-outer refined points ranked by final objective sqrt(D^2 + (1000 D')^2)\n")
        out.write("D is in mm, D' is in rad per delta.\n\n")
        for row in ranked[:20]:
            out.write(
                "outer={outer_scale} center={center_scale} "
                "q3=q5={q3_q5_gradient_T_per_m} q4={q4_gradient_T_per_m} "
                "after_D={after_chicane_D_mm} after_Dp={after_chicane_Dp_rad} "
                "final_D={final_D_mm} final_Dp={final_Dp_rad} "
                "final_obj={final_objective_mm}\n".format(**row)
            )

    print(summary_csv)
    print(best_txt)
    print(best_txt.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
