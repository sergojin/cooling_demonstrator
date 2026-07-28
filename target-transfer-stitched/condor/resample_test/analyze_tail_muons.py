#!/usr/bin/env python3
import math
import statistics
import sys
from pathlib import Path


def quantiles(values):
    if not values:
        return "", "", ""
    values = sorted(values)
    return (
        values[int(0.1 * (len(values) - 1))],
        statistics.median(values),
        values[int(0.9 * (len(values) - 1))],
    )


def rows(path):
    with path.open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 8 or int(parts[7]) != -13:
                continue
            x, y = map(float, parts[0:2])
            px, py, pz = map(float, parts[3:6])
            p = math.sqrt(px * px + py * py + pz * pz)
            if not 180 <= p <= 220:
                continue
            yield {
                "x": x,
                "y": y,
                "r": math.sqrt(x * x + y * y),
                "xp": px / pz if pz else 0.0,
                "yp": py / pz if pz else 0.0,
                "p": p,
            }


def fmt(value):
    return "" if value == "" else f"{value:.4g}"


def main():
    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    print("z_mm,n_mu_180_220,p_med,r_p10,r_med,r_p90,x_med,y_med,xp_med,yp_med")
    for path in sorted(run_dir.glob("tail_z*.txt")):
        z = int(path.stem.replace("tail_z", ""))
        selected = list(rows(path))
        if not selected:
            print(f"{z},0,,,,,,,,")
            continue
        r10, r50, r90 = quantiles([row["r"] for row in selected])
        print(
            f"{z},{len(selected)},{statistics.median(row['p'] for row in selected):.4g},"
            f"{fmt(r10)},{fmt(r50)},{fmt(r90)},"
            f"{statistics.median(row['x'] for row in selected):.4g},"
            f"{statistics.median(row['y'] for row in selected):.4g},"
            f"{statistics.median(row['xp'] for row in selected):.4g},"
            f"{statistics.median(row['yp'] for row in selected):.4g}"
        )


if __name__ == "__main__":
    main()
