#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path


BASE = Path(__file__).resolve().parent
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
            if pdgid in PDG_NAMES:
                counts[PDG_NAMES[pdgid]] += 1
    return counts


def main() -> int:
    summary_path = BASE / "plane_multiplicity_summary.txt"
    csv_path = BASE / "plane_multiplicity_summary.csv"
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
        for row in rows:
            out.write(f"{row['plane']} z_mm {row['z_mm']}\n")
            out.write(f"{row['plane']}_pi+ {row['pi+']}\n")
            out.write(f"{row['plane']}_mu+ {row['mu+']}\n")
            out.write(f"{row['plane']}_total_pi_mu {row['total_pi_mu']}\n")

    with csv_path.open("w") as out:
        out.write("plane,z_mm,pi+,mu+,total_pi_mu\n")
        for row in rows:
            out.write(f"{row['plane']},{row['z_mm']},{row['pi+']},{row['mu+']},{row['total_pi_mu']}\n")

    print(summary_path)
    print(csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
