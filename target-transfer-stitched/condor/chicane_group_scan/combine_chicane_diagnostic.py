#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
COMBINED = BASE / "combined"


def main():
    cluster = sys.argv[1] if len(sys.argv) > 1 else None
    if cluster:
        dirs = sorted(BASE.glob(f"{cluster}_diag_*")) + sorted((BASE / "jobs").glob(f"{cluster}_diag_*"))
    else:
        dirs = sorted(BASE.glob("*_diag_*")) + sorted((BASE / "jobs").glob("*_diag_*"))

    plane_rows = []
    track_rows = []
    for run_dir in dirs:
        plane_csv = run_dir / "diagnostic_plane_summary.csv"
        track_csv = run_dir / "diagnostic_tracks_p190_210_muplus.csv"
        if plane_csv.exists():
            with plane_csv.open(newline="") as f:
                plane_rows.extend(csv.DictReader(f))
        if track_csv.exists():
            with track_csv.open(newline="") as f:
                track_rows.extend(csv.DictReader(f))

    COMBINED.mkdir(exist_ok=True)
    suffix = f"_{cluster}" if cluster else ""
    plane_out = COMBINED / f"chicane_diagnostic_plane_summary{suffix}.csv"
    track_out = COMBINED / f"chicane_diagnostic_tracks_p190_210_muplus{suffix}.csv"

    if plane_rows:
        with plane_out.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=plane_rows[0].keys())
            writer.writeheader()
            writer.writerows(plane_rows)
    if track_rows:
        with track_out.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=track_rows[0].keys())
            writer.writeheader()
            writer.writerows(track_rows)

    print(f"diagnostic_dirs={len(dirs)}")
    print(f"plane_rows={len(plane_rows)}")
    print(f"track_rows={len(track_rows)}")
    print(f"plane_summary={plane_out}")
    print(f"tracks={track_out}")


if __name__ == "__main__":
    main()
