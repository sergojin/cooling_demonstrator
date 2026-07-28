#!/usr/bin/env python3
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


BASE = Path(__file__).resolve().parent
PLOTS = BASE / "plots"
SOURCE = BASE / "source_z2000_pi_mu.csv"

M_PI = 139.57039
M_MU = 105.6583745
E_MU_STAR = (M_PI * M_PI + M_MU * M_MU) / (2 * M_PI)
P_MU_STAR = math.sqrt(E_MU_STAR * E_MU_STAR - M_MU * M_MU)


def load_pions():
    pions = []
    with SOURCE.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["particle"] == "pi+":
                pions.append(float(row["p_GeVc"]) * 1000.0)
    return np.array(pions)


def sample_decay_muons(pions, samples_per_pion=3, seed=12345):
    rng = np.random.default_rng(seed)
    sample = rng.choice(pions, size=min(len(pions), 250000), replace=False)
    ppi = np.repeat(sample, samples_per_pion)
    costh = rng.uniform(-1.0, 1.0, size=ppi.size)
    epi = np.sqrt(ppi * ppi + M_PI * M_PI)
    gamma = epi / M_PI
    beta = ppi / epi
    emu = gamma * (E_MU_STAR + beta * P_MU_STAR * costh)
    return np.sqrt(np.maximum(0.0, emu * emu - M_MU * M_MU))


def main():
    PLOTS.mkdir(exist_ok=True)
    pions = load_pions()
    muons = sample_decay_muons(pions)

    fig, ax = plt.subplots(figsize=(9.4, 5.8), dpi=170)
    bins = np.linspace(0, 3000, 121)
    ax.hist(pions, bins=bins, histtype="step", linewidth=2.0, color="#2563eb", label=f"pi+ at z=2 m (N={len(pions)})")
    ax.hist(muons, bins=bins, histtype="step", linewidth=2.0, color="#dc2626", label="ideal decay mu+ estimate")
    ax.axvspan(190, 210, color="#111827", alpha=0.12, label="190-210 MeV/c")
    ax.set_yscale("log")
    ax.set_xlabel("Momentum [MeV/c]")
    ax.set_ylabel("Tracks / sampled decays")
    ax.set_title("Horn-exit pion momentum and ideal daughter-muon spectrum")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.35)
    ax.legend()
    fig.tight_layout()
    output = PLOTS / "horn_pion_decay_muon_momentum.png"
    fig.savefig(output)
    print(output)


if __name__ == "__main__":
    main()
