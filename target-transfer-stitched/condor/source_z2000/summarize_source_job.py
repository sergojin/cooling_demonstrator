#!/usr/bin/env python3
import math
import sys
from collections import Counter
from pathlib import Path


NAMES = {
    3: "pi+",
    2: "mu+",
}


def main():
    if len(sys.argv) != 5:
        print("usage: summarize_source_job.py source_z2000.txt source_summary.txt job_id n_events", file=sys.stderr)
        return 2

    source_path = Path(sys.argv[1])
    summary_path = Path(sys.argv[2])
    job_id = int(sys.argv[3])
    n_events = int(sys.argv[4])

    counts = Counter()
    p_by_type = {2: [], 3: []}
    with source_path.open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 16:
                continue
            iptyp = int(parts[2])
            counts[iptyp] += 1
            px, py, pz = map(float, parts[9:12])
            p_by_type.setdefault(iptyp, []).append(math.sqrt(px * px + py * py + pz * pz))

    with summary_path.open("w") as f:
        f.write(f"job_id {job_id}\n")
        f.write(f"n_events {n_events}\n")
        f.write(f"source_tracks {sum(counts.values())}\n")
        for iptyp, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            name = NAMES.get(iptyp, str(iptyp))
            f.write(f"source_{name} {count}\n")
            momenta = sorted(p_by_type.get(iptyp, []))
            if momenta:
                f.write(f"source_{name}_p_min {momenta[0]:.8g}\n")
                f.write(f"source_{name}_p_median {momenta[len(momenta)//2]:.8g}\n")
                f.write(f"source_{name}_p_max {momenta[-1]:.8g}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
