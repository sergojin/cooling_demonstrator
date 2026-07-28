#!/usr/bin/env python3
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "source_z2000_pi_mu.csv"
PLOTS = BASE / "plots"
COMBINED = BASE / "combined"


def load_pions():
    rows = []
    with SOURCE.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["particle"] != "pi+":
                continue
            rows.append(
                (
                    float(row["x_mm"]),
                    float(row["xp_rad"]),
                    float(row["y_mm"]),
                    float(row["yp_rad"]),
                    float(row["p_GeVc"]) * 1000.0,
                )
            )
    return np.asarray(rows, dtype=float)


def fit_twiss(u_mm, up_rad):
    data = np.column_stack((u_mm, up_rad))
    mean = data.mean(axis=0)
    centered = data - mean
    cov = np.cov(centered, rowvar=False, ddof=0)
    eps = math.sqrt(np.linalg.det(cov))
    beta = cov[0, 0] / eps
    alpha = -cov[0, 1] / eps
    gamma = cov[1, 1] / eps
    action = gamma * centered[:, 0] ** 2 + 2.0 * alpha * centered[:, 0] * centered[:, 1] + beta * centered[:, 1] ** 2
    return {
        "mean": mean,
        "cov": cov,
        "eps": eps,
        "beta": beta,
        "alpha": alpha,
        "gamma": gamma,
        "action": action,
    }


def ellipse_points(twiss, eps_mm_rad, n=360):
    phi = np.linspace(0.0, 2.0 * math.pi, n)
    beta = twiss["beta"]
    alpha = twiss["alpha"]
    mean_u, mean_up = twiss["mean"]
    amp_u = math.sqrt(beta * eps_mm_rad)
    amp_up = math.sqrt(eps_mm_rad / beta)
    u = mean_u + amp_u * np.cos(phi)
    up = mean_up - amp_up * (alpha * np.cos(phi) + np.sin(phi))
    return u, up


def plot_plane(ax, u, up, p, twiss, plane_name, sample_idx):
    sc = ax.scatter(
        u[sample_idx],
        1000.0 * up[sample_idx],
        c=p[sample_idx],
        s=3,
        cmap="viridis",
        alpha=0.18,
        linewidths=0,
    )
    eu, eup = ellipse_points(twiss, 2.0)
    ax.plot(eu, 1000.0 * eup, color="#111827", linewidth=1.7, label="2 mm rad ellipse")

    ax.axhline(0.0, color="black", linewidth=0.7, alpha=0.35)
    ax.axvline(0.0, color="black", linewidth=0.7, alpha=0.35)
    ax.grid(True, linewidth=0.35, alpha=0.35)
    ax.set_xlabel(f"{plane_name} [mm]")
    ax.set_ylabel(f"{plane_name}p [mrad]")
    ax.set_xlim(-120.0, 120.0)
    ax.set_ylim(-260.0, 260.0)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), fontsize=8, frameon=False)
    return sc


def main():
    PLOTS.mkdir(exist_ok=True)
    COMBINED.mkdir(exist_ok=True)

    rows = load_pions()
    x, xp, y, yp, p = rows.T
    xt = fit_twiss(x, xp)
    yt = fit_twiss(y, yp)

    rng = np.random.default_rng(12345)
    nsample = min(75000, len(rows))
    sample_idx = rng.choice(len(rows), size=nsample, replace=False)

    fig, axs = plt.subplots(1, 2, figsize=(12.0, 5.4), dpi=170)
    plot_plane(axs[0], x, xp, p, xt, "x", sample_idx)
    plot_plane(axs[1], y, yp, p, yt, "y", sample_idx)
    fig.suptitle(f"Horn/source pi+ phase-space ellipses at z = 2000 mm, N = {len(rows)}", y=0.99)
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.12, top=0.82, wspace=0.24)
    output = PLOTS / "horn_pion_emittance_ellipses_z2000.png"
    fig.savefig(output)

    summary = COMBINED / "horn_pion_emittance_summary.txt"
    with summary.open("w") as f:
        f.write(f"N_pi+ {len(rows)}\n")
        for name, tw in [("x", xt), ("y", yt)]:
            f.write(f"{name}_mean_mm {tw['mean'][0]:.6g}\n")
            f.write(f"{name}p_mean_rad {tw['mean'][1]:.6g}\n")
            f.write(f"{name}_eps_rms_mm_rad {tw['eps']:.6g}\n")
            f.write(f"{name}_beta_mm {tw['beta']:.6g}\n")
            f.write(f"{name}_alpha {tw['alpha']:.6g}\n")
            f.write(f"{name}_gamma_1_per_mm {tw['gamma']:.6g}\n")
            f.write(f"{name}_fraction_eps_lt_2mmrad {np.mean(tw['action'] < 2.0):.6g}\n")
        f.write(f"both_planes_fraction_eps_lt_2mmrad {np.mean((xt['action'] < 2.0) & (yt['action'] < 2.0)):.6g}\n")
        f.write(f"momentum_mean_MeVc {np.mean(p):.6g}\n")
        f.write(f"momentum_median_MeVc {np.median(p):.6g}\n")

    print(output)
    print(summary)


if __name__ == "__main__":
    main()
