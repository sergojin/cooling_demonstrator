#!/usr/bin/env python3
from __future__ import annotations

import math
from collections import Counter
from pathlib import Path


BASE = Path(__file__).resolve().parent
P_MIN_MEV = 190.0
P_MAX_MEV = 210.0
PLANES = [
    ("after_horn", "score_z02000.txt", 2000),
    ("before_chicane", "score_z11000.txt", 11000),
    ("after_chicane", "score_z20500.txt", 20500),
    ("after_final_focusing", "score_z23300.txt", 23300),
]
PDG_NAMES = {
    211: "pi+",
    -13: "mu+",
}


def count_particles(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not path.exists():
        return counts

    with path.open() as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 8:
                continue
            pdgid = int(float(parts[7]))
            if pdgid not in PDG_NAMES:
                continue
            px = float(parts[3])
            py = float(parts[4])
            pz = float(parts[5])
            p = math.sqrt(px * px + py * py + pz * pz)
            if P_MIN_MEV <= p <= P_MAX_MEV:
                counts[PDG_NAMES[pdgid]] += 1
    return counts


def main() -> int:
    summary_path = BASE / "plane_multiplicity_p190_210_summary.txt"
    csv_path = BASE / "plane_multiplicity_p190_210_summary.csv"
    rows = []

    for label, filename, z_mm in PLANES:
        counts = count_particles(BASE / filename)
        rows.append(
            {
                "plane": label,
                "z_mm": z_mm,
                "pi+": counts["pi+"],
                "mu+": counts["mu+"],
                "total_pi_mu": counts["pi+"] + counts["mu+"],
            }
        )

    with summary_path.open("w") as out:
        out.write(f"momentum_window_MeVc {P_MIN_MEV:g} {P_MAX_MEV:g}\n")
        for row in rows:
            out.write(f"{row['plane']} z_mm {row['z_mm']}\n")
            out.write(f"{row['plane']}_pi+_p190_210 {row['pi+']}\n")
            out.write(f"{row['plane']}_mu+_p190_210 {row['mu+']}\n")
            out.write(f"{row['plane']}_total_pi_mu_p190_210 {row['total_pi_mu']}\n")

    with csv_path.open("w") as out:
        out.write("plane,z_mm,pi+_p190_210,mu+_p190_210,total_pi_mu_p190_210\n")
        for row in rows:
            out.write(f"{row['plane']},{row['z_mm']},{row['pi+']},{row['mu+']},{row['total_pi_mu']}\n")

    print(summary_path)
    print(csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
