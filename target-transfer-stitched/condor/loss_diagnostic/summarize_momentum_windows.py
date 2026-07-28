#!/usr/bin/env python3
import csv
import math
import sys
from collections import Counter, defaultdict
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

WINDOWS = [
    ("p150_250", 0.150, 0.250),
    ("p180_220", 0.180, 0.220),
    ("p190_210", 0.190, 0.210),
]


def read_rows(path):
    rows = []
    with Path(path).open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 16:
                continue
            iptyp = int(parts[2])
            x = float(parts[6])
            y = float(parts[7])
            z = round(float(parts[8]), 6)
            px, py, pz = map(float, parts[9:12])
            p = math.sqrt(px * px + py * py + pz * pz)
            rows.append((z, iptyp, p, math.hypot(x, y)))
    return rows


def main():
    if len(sys.argv) != 2:
        print("usage: summarize_momentum_windows.py loss_all.txt", file=sys.stderr)
        return 2

    rows = read_rows(sys.argv[1])
    z_values = sorted({row[0] for row in rows})
    species = [3, 2, -3, -2, 5, 4, -4, 1, -1]

    totals = Counter()
    window_counts = defaultdict(Counter)
    accepted_counts = defaultdict(Counter)
    for z, iptyp, p, r in rows:
        totals[(z, iptyp)] += 1
        for name, pmin, pmax in WINDOWS:
            if pmin <= p <= pmax:
                window_counts[(z, name)][iptyp] += 1
                if r < 200:
                    accepted_counts[(z, name)][iptyp] += 1

    out = Path(sys.argv[1]).with_suffix(".momentum_windows.csv")
    with out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["z_m", "window", "acceptance", *[NAMES.get(ip, str(ip)) for ip in species]])
        for z in z_values:
            writer.writerow([z, "all_p", "all_r", *[totals[(z, ip)] for ip in species]])
            for name, _, _ in WINDOWS:
                writer.writerow([z, name, "all_r", *[window_counts[(z, name)][ip] for ip in species]])
                writer.writerow([z, name, "r_lt_200mm", *[accepted_counts[(z, name)][ip] for ip in species]])
    print(out)


if __name__ == "__main__":
    raise SystemExit(main())
