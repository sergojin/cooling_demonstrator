#!/usr/bin/env python3
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path


P_MIN_MEV = 190.0
P_MAX_MEV = 210.0
PLANES = [
    ("after_horn", "score_z02000.txt", 2000),
    ("before_chicane", "score_z11000.txt", 11000),
    ("after_chicane", "score_z20500.txt", 20500),
    ("after_final_focusing", "score_z23300.txt", 23300),
]


def iter_tracks(path: Path):
    if not path.exists():
        return
    with path.open() as handle:
        for line in handle:
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
            pdgid = int(float(parts[7]))
            p = math.sqrt(px * px + py * py + pz * pz)
            yield x, y, px, py, pz, p, pdgid


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: summarize_nominal_job.py run_dir job_id n_events")
    run_dir = Path(sys.argv[1])
    job_id = int(sys.argv[2])
    n_events = int(sys.argv[3])

    rows = []
    for plane, filename, z_mm in PLANES:
        counts = Counter()
        for *_, p, pdgid in iter_tracks(run_dir / filename):
            if pdgid == -13:
                counts["mu_all"] += 1
                if P_MIN_MEV <= p <= P_MAX_MEV:
                    counts["mu_p190_210"] += 1
            elif pdgid == 211:
                counts["pi_all"] += 1
                if P_MIN_MEV <= p <= P_MAX_MEV:
                    counts["pi_p190_210"] += 1
        rows.append((plane, z_mm, counts))

    summary = run_dir / "plane_summary.txt"
    with summary.open("w") as out:
        out.write(f"job_id {job_id}\n")
        out.write(f"n_events {n_events}\n")
        out.write(f"momentum_window_MeVc {P_MIN_MEV:g} {P_MAX_MEV:g}\n")
        for plane, z_mm, counts in rows:
            out.write(f"{plane} z_mm {z_mm}\n")
            out.write(f"{plane}_mu+_all {counts['mu_all']}\n")
            out.write(f"{plane}_mu+_p190_210 {counts['mu_p190_210']}\n")
            out.write(f"{plane}_pi+_all {counts['pi_all']}\n")
            out.write(f"{plane}_pi+_p190_210 {counts['pi_p190_210']}\n")

    csv_path = run_dir / "plane_summary.csv"
    with csv_path.open("w") as out:
        out.write("job_id,n_events,plane,z_mm,mu+_all,mu+_p190_210,pi+_all,pi+_p190_210\n")
        for plane, z_mm, counts in rows:
            out.write(
                f"{job_id},{n_events},{plane},{z_mm},"
                f"{counts['mu_all']},{counts['mu_p190_210']},"
                f"{counts['pi_all']},{counts['pi_p190_210']}\n"
            )

    print(summary)
    print(csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
