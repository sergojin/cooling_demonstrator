#!/usr/bin/env python3
import csv
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


def summarize(path):
    counts = Counter()
    with Path(path).open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 16:
                continue
            z_m = round(float(parts[8]), 6)
            iptyp = int(parts[2])
            counts[(z_m, iptyp)] += 1
    return counts


def main():
    if len(sys.argv) < 2:
        print("usage: summarize_loss.py loss_all.txt [loss_r200.txt ...]", file=sys.stderr)
        return 2

    for filename in sys.argv[1:]:
        counts = summarize(filename)
        out = Path(filename).with_suffix(".summary.csv")
        z_values = sorted({z for z, _ in counts})
        species = sorted({iptyp for _, iptyp in counts}, key=lambda ip: (NAMES.get(ip, str(ip)), ip))
        with out.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["z_m", "total", *[NAMES.get(ip, str(ip)) for ip in species]])
            for z in z_values:
                row_counts = [counts[(z, ip)] for ip in species]
                writer.writerow([z, sum(row_counts), *row_counts])
        print(out)


if __name__ == "__main__":
    raise SystemExit(main())
