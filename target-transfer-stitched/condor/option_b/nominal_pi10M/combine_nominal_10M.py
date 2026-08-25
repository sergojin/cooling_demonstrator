#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from pathlib import Path


BASE = Path(__file__).resolve().parent
COMBINED = BASE / "combined"
P_MIN_MEV = 190.0
P_MAX_MEV = 210.0
ELLIPSE_EPS_MM_RAD = 2.0
PLANES = [
    "after_horn",
    "before_chicane",
    "after_chicane",
    "after_final_focusing",
]


def iter_final_window_muons():
    for path in sorted(BASE.glob("job_*/score_z23300.txt")):
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
                if P_MIN_MEV <= p <= P_MAX_MEV:
                    yield (x, px / pz, y, py / pz, p)


def fit_twiss(rows, coord_index, slope_index):
    if len(rows) < 2:
        return None
    mean_u = sum(row[coord_index] for row in rows) / len(rows)
    mean_up = sum(row[slope_index] for row in rows) / len(rows)
    centered = [(row[coord_index] - mean_u, row[slope_index] - mean_up) for row in rows]
    suu = sum(u * u for u, _ in centered) / len(centered)
    suup = sum(u * up for u, up in centered) / len(centered)
    supup = sum(up * up for _, up in centered) / len(centered)
    det = suu * supup - suup * suup
    if det <= 0.0:
        return None
    eps = math.sqrt(det)
    return {
        "mean_u": mean_u,
        "mean_up": mean_up,
        "eps": eps,
        "beta": suu / eps,
        "alpha": -suup / eps,
        "gamma": supup / eps,
    }


def phase_action(row, twiss, coord_index, slope_index):
    u = row[coord_index] - twiss["mean_u"]
    up = row[slope_index] - twiss["mean_up"]
    return twiss["gamma"] * u * u + 2.0 * twiss["alpha"] * u * up + twiss["beta"] * up * up


def main() -> int:
    COMBINED.mkdir(exist_ok=True)
    totals = {
        plane: {"z_mm": 0, "mu+_all": 0, "mu+_p190_210": 0, "pi+_all": 0, "pi+_p190_210": 0}
        for plane in PLANES
    }
    job_rows = []

    for path in sorted(BASE.glob("job_*/plane_summary.csv")):
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                job_rows.append(row)
                plane = row["plane"]
                totals[plane]["z_mm"] = int(row["z_mm"])
                for field in ("mu+_all", "mu+_p190_210", "pi+_all", "pi+_p190_210"):
                    totals[plane][field] += int(row[field])

    final_window_muons = list(iter_final_window_muons())
    x_twiss = fit_twiss(final_window_muons, 0, 1)
    y_twiss = fit_twiss(final_window_muons, 2, 3)
    if x_twiss and y_twiss:
        ellipse_count = sum(
            1
            for row in final_window_muons
            if phase_action(row, x_twiss, 0, 1) <= ELLIPSE_EPS_MM_RAD
            and phase_action(row, y_twiss, 2, 3) <= ELLIPSE_EPS_MM_RAD
        )
    else:
        ellipse_count = 0

    combined_csv = COMBINED / "plane_summary.csv"
    with combined_csv.open("w") as out:
        out.write("plane,z_mm,mu+_all,mu+_p190_210,pi+_all,pi+_p190_210\n")
        for plane in PLANES:
            row = totals[plane]
            out.write(
                f"{plane},{row['z_mm']},{row['mu+_all']},{row['mu+_p190_210']},"
                f"{row['pi+_all']},{row['pi+_p190_210']}\n"
            )

    summary = COMBINED / "summary.txt"
    with summary.open("w") as out:
        out.write(f"completed_jobs {len({row['job_id'] for row in job_rows})}\n")
        out.write("events_per_job 1000000\n")
        out.write(f"total_events {len({row['job_id'] for row in job_rows}) * 1000000}\n")
        out.write(f"momentum_window_MeVc {P_MIN_MEV:g} {P_MAX_MEV:g}\n")
        for plane in PLANES:
            row = totals[plane]
            out.write(f"{plane} z_mm {row['z_mm']}\n")
            out.write(f"{plane}_mu+_all {row['mu+_all']}\n")
            out.write(f"{plane}_mu+_p190_210 {row['mu+_p190_210']}\n")
            out.write(f"{plane}_pi+_all {row['pi+_all']}\n")
            out.write(f"{plane}_pi+_p190_210 {row['pi+_p190_210']}\n")
        out.write(f"final_mu+_p190_210_xxp_yyp_eps_lt_2mmrad {ellipse_count}\n")
        if x_twiss and y_twiss:
            out.write(f"final_x_eps_rms_mm_rad {x_twiss['eps']:.9g}\n")
            out.write(f"final_x_beta_mm {x_twiss['beta']:.9g}\n")
            out.write(f"final_x_alpha {x_twiss['alpha']:.9g}\n")
            out.write(f"final_y_eps_rms_mm_rad {y_twiss['eps']:.9g}\n")
            out.write(f"final_y_beta_mm {y_twiss['beta']:.9g}\n")
            out.write(f"final_y_alpha {y_twiss['alpha']:.9g}\n")

    print(summary)
    print(combined_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
