#!/usr/bin/env python3
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
INPUT = BASE / "loss_all.txt"
OUT = BASE / "pion_momentum_z2000.png"


def read_piplus_z2000():
    momenta = []
    with INPUT.open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 12:
                continue
            iptyp = int(parts[2])
            z = float(parts[8])
            if iptyp != 3 or abs(z - 2.0) > 1e-6:
                continue
            px, py, pz = map(float, parts[9:12])
            momenta.append(math.sqrt(px * px + py * py + pz * pz))
    return momenta


def main():
    momenta = read_piplus_z2000()
    if not momenta:
        raise SystemExit("no pi+ entries found at z=2000 mm")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), dpi=160)

    axes[0].hist(momenta, bins=80, color="#4c78a8", edgecolor="#263238", alpha=0.85)
    axes[0].axvspan(0.18, 0.22, color="#f58518", alpha=0.25, label="180-220 MeV/c")
    axes[0].axvline(0.2, color="#d62728", lw=1.4, ls="--", label="200 MeV/c")
    axes[0].set_xlabel("pi+ momentum [GeV/c]")
    axes[0].set_ylabel("count per 1000 protons")
    axes[0].set_title("pi+ at z = 2000 mm")
    axes[0].grid(True, axis="y", alpha=0.3)
    axes[0].legend(frameon=False)

    axes[1].hist(momenta, bins=[i / 1000 for i in range(0, 1001, 10)],
                 color="#59a14f", edgecolor="#263238", alpha=0.85)
    axes[1].axvspan(0.18, 0.22, color="#f58518", alpha=0.25)
    axes[1].axvline(0.2, color="#d62728", lw=1.4, ls="--")
    axes[1].set_xlim(0, 1.0)
    axes[1].set_xlabel("pi+ momentum [GeV/c]")
    axes[1].set_ylabel("count per 1000 protons")
    axes[1].set_title("Low-momentum zoom")
    axes[1].grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT)

    in_150_250 = sum(0.150 <= p <= 0.250 for p in momenta)
    in_180_220 = sum(0.180 <= p <= 0.220 for p in momenta)
    in_190_210 = sum(0.190 <= p <= 0.210 for p in momenta)
    momenta.sort()
    print(OUT)
    print(f"n_pi_plus={len(momenta)}")
    print(f"p_min={momenta[0]:.6g}")
    print(f"p_median={momenta[len(momenta)//2]:.6g}")
    print(f"p_max={momenta[-1]:.6g}")
    print(f"n_150_250_MeVc={in_150_250}")
    print(f"n_180_220_MeVc={in_180_220}")
    print(f"n_190_210_MeVc={in_190_210}")


if __name__ == "__main__":
    main()
