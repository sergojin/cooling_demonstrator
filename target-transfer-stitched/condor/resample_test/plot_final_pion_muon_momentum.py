#!/usr/bin/env python3
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
PLOTS = BASE / "plots"


def load_momenta():
    momenta = {"mu+": [], "pi+": []}
    for path in sorted(BASE.glob("finalmom_job_*/score_z23300.txt")):
        with path.open() as f:
            for line in f:
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 8:
                    continue
                pdgid = int(parts[7])
                if pdgid not in (-13, 211):
                    continue
                px, py, pz = map(float, parts[3:6])
                p = math.sqrt(px * px + py * py + pz * pz)
                momenta["mu+" if pdgid == -13 else "pi+"].append(p)
    return momenta


def main():
    PLOTS.mkdir(exist_ok=True)
    momenta = load_momenta()

    fig, ax = plt.subplots(figsize=(9.2, 5.7), dpi=170)
    bins = range(0, 551, 10)
    ax.hist(
        momenta["pi+"],
        bins=bins,
        histtype="step",
        linewidth=2.0,
        color="#2563eb",
        label=f"pi+ (N={len(momenta['pi+'])})",
    )
    ax.hist(
        momenta["mu+"],
        bins=bins,
        histtype="step",
        linewidth=2.0,
        color="#dc2626",
        label=f"mu+ (N={len(momenta['mu+'])})",
    )
    ax.axvspan(190, 210, color="#111827", alpha=0.12, label="190-210 MeV/c")
    ax.set_xlabel("Momentum at z = 23.3 m [MeV/c]")
    ax.set_ylabel("Tracks")
    ax.set_title("Final-plane momentum before analysis cuts")
    ax.grid(True, linewidth=0.4, alpha=0.35)
    ax.legend()
    fig.tight_layout()
    output = PLOTS / "final_pion_muon_momentum_uncut_z23300.png"
    fig.savefig(output)
    print(output)

    fig, ax = plt.subplots(figsize=(9.2, 5.7), dpi=170)
    ax.hist(momenta["pi+"], bins=bins, histtype="step", linewidth=2.0, color="#2563eb", label=f"pi+ (N={len(momenta['pi+'])})")
    ax.hist(momenta["mu+"], bins=bins, histtype="step", linewidth=2.0, color="#dc2626", label=f"mu+ (N={len(momenta['mu+'])})")
    ax.axvspan(190, 210, color="#111827", alpha=0.12, label="190-210 MeV/c")
    ax.set_yscale("log")
    ax.set_xlabel("Momentum at z = 23.3 m [MeV/c]")
    ax.set_ylabel("Tracks")
    ax.set_title("Final-plane momentum before analysis cuts")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.35)
    ax.legend()
    fig.tight_layout()
    output_log = PLOTS / "final_pion_muon_momentum_uncut_z23300_log.png"
    fig.savefig(output_log)
    print(output_log)


if __name__ == "__main__":
    main()
