#!/usr/bin/env python3
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
COMBINED = BASE / "combined"
PLOTS = BASE / "plots"


def iter_tracks(paths):
    for path in paths:
        with path.open() as f:
            for line in f:
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 8:
                    continue
                yield {
                    "px": float(parts[3]),
                    "py": float(parts[4]),
                    "pz": float(parts[5]),
                    "pdgid": int(parts[7]),
                    "source": str(path.parent.name),
                }


def main():
    COMBINED.mkdir(exist_ok=True)
    PLOTS.mkdir(exist_ok=True)
    score_paths = sorted(BASE.glob("finalmom_job_*/score_z23300.txt"))
    muons = []
    species = {}
    for track in iter_tracks(score_paths):
        species[track["pdgid"]] = species.get(track["pdgid"], 0) + 1
        if track["pdgid"] != -13:
            continue
        p = math.sqrt(track["px"] ** 2 + track["py"] ** 2 + track["pz"] ** 2)
        muons.append({**track, "p": p})

    csv_path = COMBINED / "final_muon_momentum.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["p", "px", "py", "pz", "pdgid", "source"])
        writer.writeheader()
        writer.writerows(muons)

    summary_path = COMBINED / "final_momentum_summary.txt"
    with summary_path.open("w") as f:
        f.write(f"score_files {len(score_paths)}\n")
        f.write(f"final_mu+ {len(muons)}\n")
        for pdgid, count in sorted(species.items()):
            f.write(f"final_{pdgid} {count}\n")
        if muons:
            ps = sorted(row["p"] for row in muons)
            f.write(f"p_min_MeVc {ps[0]:.6g}\n")
            f.write(f"p_median_MeVc {ps[len(ps)//2]:.6g}\n")
            f.write(f"p_mean_MeVc {sum(ps)/len(ps):.6g}\n")
            f.write(f"p_max_MeVc {ps[-1]:.6g}\n")
            f.write(f"p_180_220_MeVc {sum(180 <= p <= 220 for p in ps)}\n")

    fig, ax = plt.subplots(figsize=(8.8, 5.4), dpi=170)
    ax.hist([row["p"] for row in muons], bins=60, range=(0, 500), histtype="stepfilled", color="#2563eb", alpha=0.78)
    ax.axvspan(180, 220, color="#dc2626", alpha=0.16, label="180-220 MeV/c")
    ax.axvline(200, color="#dc2626", linewidth=1.5, label="200 MeV/c")
    ax.set_xlabel("Final mu+ momentum [MeV/c]")
    ax.set_ylabel("Muons")
    ax.set_title("Final-plane mu+ momentum, z = 23.3 m")
    ax.grid(True, linewidth=0.4, alpha=0.35)
    ax.legend()
    fig.tight_layout()
    plot_path = PLOTS / "final_muon_momentum_z23300.png"
    fig.savefig(plot_path)
    print(plot_path)
    print(summary_path)


if __name__ == "__main__":
    main()
