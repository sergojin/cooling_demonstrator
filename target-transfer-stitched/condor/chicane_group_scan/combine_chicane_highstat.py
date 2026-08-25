#!/usr/bin/env python3
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path


BASE = Path(__file__).resolve().parent
COMBINED = BASE / "combined"
P_MIN_MEV = 190.0
P_MAX_MEV = 210.0
PHASE_ELLIPSE_EPS_MM_RAD = 2.0


SUM_FIELDS = [
    "n_events",
    "final_mu+_uncut",
    "p_190_210_MeVc",
    "r_le_20mm",
    "p_190_210_MeVc_r_le_20mm",
    "r_le_50mm",
    "p_190_210_MeVc_r_le_50mm",
    "r_le_75mm",
    "p_190_210_MeVc_r_le_75mm",
    "r_le_100mm",
    "p_190_210_MeVc_r_le_100mm",
    "p_190_210_MeVc_xxp_yyp_eps_lt_2mmrad",
]


def read_pairs(path):
    data = {}
    with path.open() as f:
        for line in f:
            parts = line.split()
            if len(parts) == 2:
                data[parts[0]] = parts[1]
    return data


def iter_summaries(cluster=None):
    patterns = []
    if cluster:
        patterns.extend([f"{cluster}_point_*/job_summary.txt", f"jobs/{cluster}_point_*/job_summary.txt"])
    else:
        patterns.extend(["*_point_*/job_summary.txt", "jobs/*_point_*/job_summary.txt"])
    seen = set()
    for pattern in patterns:
        for path in BASE.glob(pattern):
            if path in seen:
                continue
            seen.add(path)
            data = read_pairs(path)
            point_id = int(data.get("point_id", "-1"))
            if point_id >= 1000:
                yield path, data


def iter_momentum_window_muons(score_path):
    if not score_path.exists():
        return
    with score_path.open() as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 8:
                continue
            pdgid = int(float(parts[7]))
            if pdgid != -13:
                continue
            x = float(parts[0])
            y = float(parts[1])
            px = float(parts[3])
            py = float(parts[4])
            pz = float(parts[5])
            p = math.sqrt(px * px + py * py + pz * pz)
            if not (P_MIN_MEV <= p <= P_MAX_MEV):
                continue
            if pz == 0.0:
                continue
            yield (x, y, px / pz, py / pz)


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


def main():
    cluster = sys.argv[1] if len(sys.argv) > 1 else None
    groups = defaultdict(lambda: {"chunks": 0, "smooth_score": 0.0})
    phase_rows = defaultdict(list)
    for summary_path, data in iter_summaries(cluster):
        key = (data["group_name"], data["scale"])
        row = groups[key]
        row["group_name"] = data["group_name"]
        row["scale"] = data["scale"]
        row["chunks"] += 1
        row["smooth_score"] += float(data.get("smooth_score", "0"))
        for field in SUM_FIELDS:
            row[field] = row.get(field, 0) + int(data.get(field, "0"))
        score_path = summary_path.parent / "score_z23300.txt"
        phase_rows[key].extend(iter_momentum_window_muons(score_path))

    rows = []
    for key, row in groups.items():
        n_events = row.get("n_events", 0)
        p_window_rows = phase_rows[key]
        x_twiss = fit_phase_ellipse(p_window_rows, 0, 2)
        y_twiss = fit_phase_ellipse(p_window_rows, 1, 3)
        if x_twiss and y_twiss:
            phase_accepted = sum(
                phase_action(track, x_twiss, 0, 2) <= PHASE_ELLIPSE_EPS_MM_RAD
                and phase_action(track, y_twiss, 1, 3) <= PHASE_ELLIPSE_EPS_MM_RAD
                for track in p_window_rows
            )
            row["x_eps_rms_mm_rad"] = x_twiss["eps"]
            row["x_beta_mm"] = x_twiss["beta"]
            row["x_alpha"] = x_twiss["alpha"]
            row["y_eps_rms_mm_rad"] = y_twiss["eps"]
            row["y_beta_mm"] = y_twiss["beta"]
            row["y_alpha"] = y_twiss["alpha"]
        else:
            phase_accepted = 0
            row["x_eps_rms_mm_rad"] = 0.0
            row["x_beta_mm"] = 0.0
            row["x_alpha"] = 0.0
            row["y_eps_rms_mm_rad"] = 0.0
            row["y_beta_mm"] = 0.0
            row["y_alpha"] = 0.0
        row["p_190_210_MeVc_xxp_yyp_eps_lt_2mmrad"] = phase_accepted
        row["phase_ellipse_yield_per_track"] = phase_accepted / n_events if n_events else 0.0
        row["hard_yield_per_track"] = row["p_190_210_MeVc_r_le_20mm"] / n_events if n_events else 0.0
        row["smooth_score_per_track"] = row["smooth_score"] / n_events if n_events else 0.0
        rows.append(row)
    rows.sort(
        key=lambda row: (
            -row["p_190_210_MeVc_xxp_yyp_eps_lt_2mmrad"],
            -row["smooth_score_per_track"],
        )
    )

    COMBINED.mkdir(exist_ok=True)
    suffix = f"_{cluster}" if cluster else ""
    out = COMBINED / f"chicane_highstat_summary{suffix}.csv"
    fieldnames = [
        "group_name",
        "scale",
        "chunks",
        *SUM_FIELDS,
        "smooth_score",
        "smooth_score_per_track",
        "hard_yield_per_track",
        "phase_ellipse_yield_per_track",
        "x_eps_rms_mm_rad",
        "x_beta_mm",
        "x_alpha",
        "y_eps_rms_mm_rad",
        "y_beta_mm",
        "y_alpha",
    ]
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"configs={len(rows)}")
    for row in rows:
        print(
            f"{row['group_name']} scale={row['scale']} "
            f"chunks={row['chunks']} n={row['n_events']} "
            f"r20_accepted={row['p_190_210_MeVc_r_le_20mm']} "
            f"phase_accepted={row['p_190_210_MeVc_xxp_yyp_eps_lt_2mmrad']} "
            f"phase_yield={row['phase_ellipse_yield_per_track']:.8g} "
            f"smooth={row['smooth_score_per_track']:.8g}"
        )
    print(f"summary={out}")


if __name__ == "__main__":
    main()
