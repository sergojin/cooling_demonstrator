#!/usr/bin/env python3
import argparse
import csv
import math
import random
from pathlib import Path


PDGID = {"pi+": 211, "mu+": -13}


def parse_args():
    parser = argparse.ArgumentParser(description="Sample pi+ rows in 0-400 MeV/c into a G4BL beam file.")
    parser.add_argument("source_csv", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--p-min-mev", type=float, default=0.0)
    parser.add_argument("--p-max-mev", type=float, default=400.0)
    return parser.parse_args()


def load_rows(path, p_min_mev, p_max_mev):
    rows = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["particle"] != "pi+":
                continue
            px = float(row["px_GeVc"]) * 1000.0
            py = float(row["py_GeVc"]) * 1000.0
            pz = float(row["pz_GeVc"]) * 1000.0
            p = math.sqrt(px * px + py * py + pz * pz)
            if p_min_mev <= p <= p_max_mev:
                rows.append(row)
    if not rows:
        raise SystemExit(f"no pi+ rows selected from {path}")
    return rows


def main():
    args = parse_args()
    rng = random.Random(args.seed)
    rows = load_rows(args.source_csv, args.p_min_mev, args.p_max_mev)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w") as out:
        out.write("#BLTrackFile ResampledZ2000PiP0_400\n")
        out.write("#x y z Px Py Pz t PDGid EventID TrackID ParentID Weight\n")
        out.write("#mm mm mm MeV/c MeV/c MeV/c ns - - - - -\n")
        for event_id in range(1, args.n + 1):
            row = rng.choice(rows)
            x_mm = float(row["x_mm"])
            y_mm = float(row["y_mm"])
            z_mm = float(row["z_mm"])
            px = float(row["px_GeVc"]) * 1000.0
            py = float(row["py_GeVc"]) * 1000.0
            pz = float(row["pz_GeVc"]) * 1000.0
            out.write(
                f"{x_mm:.9g} {y_mm:.9g} {z_mm:.9g} "
                f"{px:.9g} {py:.9g} {pz:.9g} "
                f"0 {PDGID['pi+']} {event_id} 1 0 1.0000\n"
            )

    print(f"selected_pi+_p0_400_rows={len(rows)}")
    print(f"sampled_events={args.n}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
