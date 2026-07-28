#!/usr/bin/env python3
import sys
from collections import Counter
from pathlib import Path


def count_particles(path):
    counts = Counter()
    if not path.exists():
        return counts
    with path.open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 8:
                continue
            pdgid = int(parts[7])
            if pdgid == 211:
                counts["pi+"] += 1
            elif pdgid == -13:
                counts["mu+"] += 1
            else:
                counts[str(pdgid)] += 1
    return counts


def main():
    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    input_counts = count_particles(run_dir / "beam.tmp")
    plane_counts = []
    for path in sorted(run_dir.glob("score_z*.txt")):
        z_mm = int(path.stem.replace("score_z", ""))
        plane_counts.append((z_mm, path, count_particles(path)))

    final_counts = Counter()
    for z_mm, _, counts in plane_counts:
        if z_mm == 23300:
            final_counts = counts
            break

    summary = run_dir / "resample_summary.txt"
    with summary.open("w") as f:
        f.write(f"input_tracks {sum(input_counts.values())}\n")
        for particle, count in sorted(input_counts.items()):
            f.write(f"input_{particle} {count}\n")
        f.write(f"final_tracks {sum(final_counts.values())}\n")
        for particle, count in sorted(final_counts.items()):
            f.write(f"final_{particle} {count}\n")

    planes_csv = run_dir / "score_summary.csv"
    with planes_csv.open("w") as f:
        f.write("z_mm,total,pi+,mu+\n")
        for z_mm, _, counts in plane_counts:
            f.write(
                f"{z_mm},{sum(counts.values())},"
                f"{counts.get('pi+', 0)},{counts.get('mu+', 0)}\n"
            )
    print(summary)


if __name__ == "__main__":
    main()
