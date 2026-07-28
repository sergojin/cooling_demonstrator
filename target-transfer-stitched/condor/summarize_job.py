#!/usr/bin/env python3
import csv
import math
import sys
from collections import Counter
from pathlib import Path


NAMES = {
    5: "p",
    4: "K+",
    -4: "K-",
    3: "pi+",
    -3: "pi-",
    2: "mu+",
    -2: "mu-",
    1: "e+",
    -1: "e-",
}


def main() -> int:
    if len(sys.argv) != 5:
        print("usage: summarize_job.py stitched_output.txt job_summary.txt job_id n_events", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    summary_path = Path(sys.argv[2])
    job_id = int(sys.argv[3])
    n_events = int(sys.argv[4])

    counts = Counter()
    final_muons = []

    with input_path.open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 16:
                continue

            iptyp = int(parts[2])
            z = float(parts[8])
            if abs(z - 23.3) > 1e-6:
                continue

            counts[iptyp] += 1

            if iptyp in (2, -2):
                event = int(parts[0])
                px, py, pz = map(float, parts[9:12])
                momentum = math.sqrt(px * px + py * py + pz * pz)
                final_muons.append((job_id, event, iptyp, px, py, pz, momentum))

    with summary_path.open("w") as f:
        f.write(f"job_id {job_id}\n")
        f.write(f"n_events {n_events}\n")
        f.write(f"final_supported_tracks {sum(counts.values())}\n")
        for iptyp, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            f.write(f"final_{NAMES.get(iptyp, iptyp)} {count}\n")
        f.write(f"final_muons {len(final_muons)}\n")

    muon_csv = summary_path.with_name("final_muons.csv")
    with muon_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["job_id", "event", "iptyp", "px_GeVc", "py_GeVc", "pz_GeVc", "p_GeVc"])
        writer.writerows(final_muons)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
