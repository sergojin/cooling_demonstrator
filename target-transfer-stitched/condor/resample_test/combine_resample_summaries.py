#!/usr/bin/env python3
from collections import Counter
import argparse
import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent


def read_summary(path):
    rows = {}
    with path.open() as f:
        for line in f:
            parts = line.split()
            if len(parts) != 2:
                continue
            rows[parts[0]] = int(parts[1])
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-glob", default="transfer_job_*")
    args = parser.parse_args()

    counts = Counter()
    plane_counts = Counter()
    completed = 0
    job_dirs = list(BASE.glob(args.job_glob))
    for job_dir in sorted(job_dirs):
        summary = job_dir / "resample_summary.txt"
        if not summary.exists():
            continue
        completed += 1
        counts.update(read_summary(summary))
        score_summary = job_dir / "score_summary.csv"
        if score_summary.exists():
            with score_summary.open(newline="") as f:
                for row in csv.DictReader(f):
                    z_mm = row["z_mm"]
                    for key in ("total", "pi+", "mu+"):
                        plane_counts[(z_mm, key)] += int(row[key])

    combined = BASE / "combined"
    combined.mkdir(exist_ok=True)
    output = combined / "resample_summary.txt"
    with output.open("w") as f:
        f.write(f"completed_jobs {completed}\n")
        for key, value in sorted(counts.items()):
            f.write(f"{key} {value}\n")

    plane_output = combined / "score_summary.csv"
    z_values = sorted({z_mm for z_mm, _ in plane_counts}, key=int)
    with plane_output.open("w") as f:
        f.write("z_mm,total,pi+,mu+\n")
        for z_mm in z_values:
            f.write(
                f"{z_mm},{plane_counts[(z_mm, 'total')]},"
                f"{plane_counts[(z_mm, 'pi+')]},{plane_counts[(z_mm, 'mu+')]}\n"
            )
    print(output)


if __name__ == "__main__":
    main()
