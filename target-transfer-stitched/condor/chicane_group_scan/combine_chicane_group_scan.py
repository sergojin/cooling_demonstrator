#!/usr/bin/env python3
import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
COMBINED = BASE / "combined"


FIELDS = [
    "point_id",
    "group_name",
    "scale",
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
    "smooth_score",
    "smooth_score_per_track",
]


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


def coerce(row):
    out = {}
    for field in FIELDS:
        value = row.get(field, "0")
        if field in ("group_name",):
            out[field] = value
        elif field == "scale" or field.startswith("smooth"):
            out[field] = float(value)
        else:
            out[field] = int(value)
    out["hard_yield_per_track"] = (
        out["p_190_210_MeVc_r_le_20mm"] / out["n_events"] if out["n_events"] else 0.0
    )
    return out


def main():
    rows = []
    candidates = (
        list(BASE.glob("point_*"))
        + list(BASE.glob("*_point_*"))
        + list((BASE / "jobs").glob("point_*"))
        + list((BASE / "jobs").glob("*_point_*"))
    )
    for job_dir in sorted(candidates):
        summary = read_pairs(job_dir / "job_summary.txt")
        if summary:
            rows.append(coerce(summary))

    rows.sort(key=lambda row: (-row["smooth_score_per_track"], -row["p_190_210_MeVc_r_le_20mm"], row["point_id"]))
    COMBINED.mkdir(exist_ok=True)
    out = COMBINED / "chicane_group_scan_summary.csv"
    fieldnames = FIELDS + ["hard_yield_per_track"]
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"completed_points={len(rows)}")
    if rows:
        best = rows[0]
        print(
            "best="
            f"point {best['point_id']} "
            f"group={best['group_name']} "
            f"scale={best['scale']:.4g} "
            f"accepted={best['p_190_210_MeVc_r_le_20mm']} "
            f"smooth_per_track={best['smooth_score_per_track']:.8g}"
        )
    print(f"summary={out}")


if __name__ == "__main__":
    main()
