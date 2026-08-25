#!/usr/bin/env python3
from __future__ import annotations

import csv
import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "source_z2000_pi_mu.csv"
OUT_DIR = BASE / "plots"
N_JOBS = 10
N_EVENTS_PER_JOB = 1_000_000
SEED_BASE = 3_400_000


def load_pion_momenta_mevc(path: Path) -> list[float]:
    momenta = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["particle"] == "pi+":
                momenta.append(float(row["p_GeVc"]) * 1000.0)
    if not momenta:
        raise SystemExit(f"no pi+ rows found in {path}")
    return momenta


def sample_momenta(source_momenta: list[float]) -> list[float]:
    sampled = []
    for job_id in range(N_JOBS):
        rng = random.Random(SEED_BASE + job_id * 1009)
        sampled.extend(rng.choice(source_momenta) for _ in range(N_EVENTS_PER_JOB))
    return sampled


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    source_momenta = load_pion_momenta_mevc(SOURCE)
    sampled = sample_momenta(source_momenta)

    n_total = len(sampled)
    n_0_400 = sum(0.0 <= p <= 400.0 for p in sampled)
    n_190_210 = sum(190.0 <= p <= 210.0 for p in sampled)

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), constrained_layout=True)

    axes[0].hist(sampled, bins=160, range=(0.0, 2000.0), histtype="stepfilled", color="#3b73b9", alpha=0.78)
    axes[0].axvspan(190.0, 210.0, color="#c23b22", alpha=0.22, label="190-210 MeV/c")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("pion momentum p [MeV/c]")
    axes[0].set_ylabel("resampled pi+ count")
    axes[0].set_title("Option B resampled pi+ momentum, 10M samples")
    axes[0].legend(frameon=False)

    axes[1].hist(sampled, bins=160, range=(0.0, 400.0), histtype="stepfilled", color="#4f8f69", alpha=0.82)
    axes[1].axvspan(190.0, 210.0, color="#c23b22", alpha=0.25, label="190-210 MeV/c")
    axes[1].set_xlabel("pion momentum p [MeV/c]")
    axes[1].set_ylabel("resampled pi+ count")
    axes[1].set_title("Zoom: 0-400 MeV/c")
    axes[1].legend(frameon=False)

    plot_path = OUT_DIR / "resampled_pion_momentum_10M.png"
    fig.savefig(plot_path, dpi=160)

    summary_path = OUT_DIR / "resampled_pion_momentum_10M.txt"
    with summary_path.open("w") as out:
        out.write(f"source_pi+ {len(source_momenta)}\n")
        out.write(f"resampled_pi+ {n_total}\n")
        out.write(f"resampled_pi+_p0_400_MeVc {n_0_400}\n")
        out.write(f"resampled_pi+_p190_210_MeVc {n_190_210}\n")
        out.write(f"fraction_p0_400 {n_0_400 / n_total:.9g}\n")
        out.write(f"fraction_p190_210 {n_190_210 / n_total:.9g}\n")
        out.write(f"plot {plot_path}\n")

    print(plot_path)
    print(summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
