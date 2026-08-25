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
P_MIN_MEV = 190
P_MAX_MEV = 210
R_MAX_MM = 20


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
                    "x": float(parts[0]),
                    "y": float(parts[1]),
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
        r = math.sqrt(track["x"] ** 2 + track["y"] ** 2)
        accepted = P_MIN_MEV <= p <= P_MAX_MEV and r <= R_MAX_MM
        muons.append({**track, "p": p, "r": r, "accepted": accepted})

    csv_path = COMBINED / "final_muon_momentum.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["accepted", "p", "r", "x", "y", "px", "py", "pz", "pdgid", "source"],
        )
        writer.writeheader()
        writer.writerows(muons)

    accepted_muons = [row for row in muons if row["accepted"]]
    summary_path = COMBINED / "final_momentum_summary.txt"
    with summary_path.open("w") as f:
        f.write(f"score_files {len(score_paths)}\n")
        f.write(f"muon_momentum_window_MeVc {P_MIN_MEV} {P_MAX_MEV}\n")
        f.write(f"muon_transverse_acceptance_mm {R_MAX_MM}\n")
        f.write(f"final_mu+ {len(accepted_muons)}\n")
        f.write(f"final_mu+_uncut {len(muons)}\n")
        for pdgid, count in sorted(species.items()):
            f.write(f"final_{pdgid} {count}\n")
        if muons:
            ps = sorted(row["p"] for row in muons)
            f.write(f"p_min_MeVc {ps[0]:.6g}\n")
            f.write(f"p_median_MeVc {ps[len(ps)//2]:.6g}\n")
            f.write(f"p_mean_MeVc {sum(ps)/len(ps):.6g}\n")
            f.write(f"p_max_MeVc {ps[-1]:.6g}\n")
            f.write(f"p_190_210_MeVc {sum(P_MIN_MEV <= p <= P_MAX_MEV for p in ps)}\n")
            f.write(f"r_le_20mm {sum(row['r'] <= R_MAX_MM for row in muons)}\n")
            f.write(f"p_190_210_MeVc_r_le_20mm {len(accepted_muons)}\n")

    fig, ax = plt.subplots(figsize=(8.8, 5.4), dpi=170)
    ax.hist([row["p"] for row in muons], bins=60, range=(0, 500), histtype="stepfilled", color="#2563eb", alpha=0.78)
    ax.axvspan(P_MIN_MEV, P_MAX_MEV, color="#dc2626", alpha=0.16, label=f"{P_MIN_MEV}-{P_MAX_MEV} MeV/c")
    ax.axvline(200, color="#dc2626", linewidth=1.5, label="200 MeV/c")
    ax.set_xlabel("Final mu+ momentum [MeV/c]")
    ax.set_ylabel("Muons")
    ax.set_title("Final-plane mu+ momentum, z = 23.3 m")
    ax.grid(True, linewidth=0.4, alpha=0.35)
    ax.legend()
    fig.tight_layout()
    plot_path = PLOTS / "final_muon_momentum_z23300.png"
    fig.savefig(plot_path)

    fig, ax = plt.subplots(figsize=(8.8, 5.4), dpi=170)
    bins = range(0, 501, 10)
    ax.hist(
        [row["p"] for row in muons],
        bins=bins,
        histtype="stepfilled",
        color="#93c5fd",
        alpha=0.5,
        label=f"all final mu+ (N={len(muons)})",
    )
    ax.hist(
        [row["p"] for row in muons if row["r"] <= R_MAX_MM],
        bins=bins,
        histtype="step",
        linewidth=2.0,
        color="#f97316",
        label=f"r <= {R_MAX_MM} mm (N={sum(row['r'] <= R_MAX_MM for row in muons)})",
    )
    ax.axvspan(P_MIN_MEV, P_MAX_MEV, color="#dc2626", alpha=0.16, label=f"{P_MIN_MEV}-{P_MAX_MEV} MeV/c")
    ax.axvline(200, color="#dc2626", linewidth=1.5)
    ax.set_xlabel("Final mu+ momentum [MeV/c]")
    ax.set_ylabel("Muons")
    ax.set_title("Final-plane mu+ momentum with transverse acceptance")
    ax.grid(True, linewidth=0.4, alpha=0.35)
    ax.legend()
    fig.tight_layout()
    accepted_plot_path = PLOTS / "final_muon_momentum_acceptance_z23300.png"
    fig.savefig(accepted_plot_path)

    fig, ax = plt.subplots(figsize=(8.8, 5.4), dpi=170)
    ax.scatter(
        [row["p"] for row in muons],
        [row["r"] for row in muons],
        s=9,
        alpha=0.35,
        color="#2563eb",
        edgecolors="none",
        label=f"all final mu+ (N={len(muons)})",
    )
    rect = plt.Rectangle(
        (P_MIN_MEV, 0),
        P_MAX_MEV - P_MIN_MEV,
        R_MAX_MM,
        fill=False,
        edgecolor="#dc2626",
        linewidth=2.0,
        label=f"accepted (N={len(accepted_muons)})",
    )
    ax.add_patch(rect)
    ax.set_xlim(80, 510)
    ax.set_ylim(0, 210)
    ax.set_xlabel("Final mu+ momentum [MeV/c]")
    ax.set_ylabel("Transverse radius r [mm]")
    ax.set_title("Final-plane mu+ momentum vs transverse radius")
    ax.grid(True, linewidth=0.4, alpha=0.35)
    ax.legend()
    fig.tight_layout()
    scatter_plot_path = PLOTS / "final_muon_momentum_radius_scatter_z23300.png"
    fig.savefig(scatter_plot_path)
    print(plot_path)
    print(accepted_plot_path)
    print(scatter_plot_path)
    print(summary_path)


if __name__ == "__main__":
    main()
