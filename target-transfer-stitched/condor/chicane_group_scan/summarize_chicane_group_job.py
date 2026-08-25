#!/usr/bin/env python3
import math
import sys
from collections import Counter
from pathlib import Path


P_MIN_MEV = 190.0
P_MAX_MEV = 210.0
R_CUT_MM = 20.0
PHASE_ELLIPSE_EPS_MM_RAD = 2.0
LOOSE_R_CUTS_MM = (50.0, 75.0, 100.0)


def iter_tracks(path):
    if not path.exists():
        return
    with path.open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 8:
                continue
            x = float(parts[0])
            y = float(parts[1])
            px = float(parts[3])
            py = float(parts[4])
            pz = float(parts[5])
            pdgid = int(parts[7])
            p = math.sqrt(px * px + py * py + pz * pz)
            r = math.sqrt(x * x + y * y)
            xp = px / pz if pz else float("inf")
            yp = py / pz if pz else float("inf")
            yield x, y, xp, yp, p, r, pdgid


def fit_phase_ellipse(rows, coord_index, slope_index):
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


def particle_name(pdgid):
    if pdgid == 211:
        return "pi+"
    if pdgid == -13:
        return "mu+"
    return str(pdgid)


def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: summarize_chicane_group_job.py run_dir point_id group scale n_events")
    run_dir = Path(sys.argv[1])
    point_id = int(sys.argv[2])
    group_name = sys.argv[3]
    scale = sys.argv[4]
    n_events = int(sys.argv[5])

    species = Counter()
    muons = []
    for x, y, xp, yp, p, r, pdgid in iter_tracks(run_dir / "score_z23300.txt"):
        species[particle_name(pdgid)] += 1
        if pdgid == -13:
            muons.append((x, y, xp, yp, p, r))

    p_window = [row for row in muons if P_MIN_MEV <= row[4] <= P_MAX_MEV]
    accepted = [row for row in p_window if row[5] <= R_CUT_MM]
    x_twiss = fit_phase_ellipse(p_window, 0, 2)
    y_twiss = fit_phase_ellipse(p_window, 1, 3)
    if x_twiss and y_twiss:
        phase_accepted = [
            row
            for row in p_window
            if phase_action(row, x_twiss, 0, 2) <= PHASE_ELLIPSE_EPS_MM_RAD
            and phase_action(row, y_twiss, 1, 3) <= PHASE_ELLIPSE_EPS_MM_RAD
        ]
    else:
        phase_accepted = []
    smooth_score = sum(
        math.exp(-((p - 200.0) / 10.0) ** 2) * math.exp(-(r / R_CUT_MM) ** 2)
        for _, _, _, _, p, r in muons
    )

    summary = run_dir / "job_summary.txt"
    with summary.open("w") as f:
        f.write(f"point_id {point_id}\n")
        f.write(f"group_name {group_name}\n")
        f.write(f"scale {scale}\n")
        f.write(f"n_events {n_events}\n")
        f.write(f"final_tracks {sum(species.values())}\n")
        for particle, count in sorted(species.items()):
            f.write(f"final_{particle} {count}\n")
        f.write(f"final_mu+_uncut {len(muons)}\n")
        f.write(f"p_190_210_MeVc {len(p_window)}\n")
        for r_cut in LOOSE_R_CUTS_MM:
            f.write(f"r_le_{int(r_cut)}mm {sum(row[5] <= r_cut for row in muons)}\n")
            f.write(f"p_190_210_MeVc_r_le_{int(r_cut)}mm {sum(row[5] <= r_cut for row in p_window)}\n")
        f.write(f"r_le_20mm {sum(row[5] <= R_CUT_MM for row in muons)}\n")
        f.write(f"p_190_210_MeVc_r_le_20mm {len(accepted)}\n")
        f.write(f"p_190_210_MeVc_xxp_yyp_eps_lt_2mmrad {len(phase_accepted)}\n")
        f.write(
            "phase_ellipse_yield_per_track "
            f"{len(phase_accepted) / n_events if n_events else 0.0:.9g}\n"
        )
        if x_twiss and y_twiss:
            f.write(f"x_eps_rms_mm_rad {x_twiss['eps']:.9g}\n")
            f.write(f"x_beta_mm {x_twiss['beta']:.9g}\n")
            f.write(f"x_alpha {x_twiss['alpha']:.9g}\n")
            f.write(f"y_eps_rms_mm_rad {y_twiss['eps']:.9g}\n")
            f.write(f"y_beta_mm {y_twiss['beta']:.9g}\n")
            f.write(f"y_alpha {y_twiss['alpha']:.9g}\n")
        f.write(f"smooth_score {smooth_score:.9g}\n")
        f.write(f"smooth_score_per_track {smooth_score / n_events if n_events else 0.0:.9g}\n")

    scan_point = run_dir / "scan_point.txt"
    with scan_point.open("w") as f:
        f.write(f"point_id {point_id}\n")
        f.write(f"group_name {group_name}\n")
        f.write(f"scale {scale}\n")
        f.write(f"n_events {n_events}\n")

    print(summary)


if __name__ == "__main__":
    main()
