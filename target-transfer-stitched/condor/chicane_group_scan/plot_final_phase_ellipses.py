#!/usr/bin/env python3
"""Plot final-plane mu+ x-x' and y-y' with fitted 2 mm rad ellipses."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


BASE = Path(__file__).resolve().parent
P_MIN_MEV = 190.0
P_MAX_MEV = 210.0
ELLIPSE_EPS_MM_RAD = 2.0


def iter_score_files(cluster: str):
    patterns = [f"{cluster}_point_*/score_z23300.txt", f"jobs/{cluster}_point_*/score_z23300.txt"]
    seen = set()
    for pattern in patterns:
        for path in sorted(BASE.glob(pattern)):
            if path in seen:
                continue
            seen.add(path)
            yield path


def load_muons(cluster: str) -> np.ndarray:
    rows = []
    for path in iter_score_files(cluster):
        with path.open() as handle:
            for line in handle:
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 8 or int(float(parts[7])) != -13:
                    continue
                x = float(parts[0])
                y = float(parts[1])
                px = float(parts[3])
                py = float(parts[4])
                pz = float(parts[5])
                if pz == 0.0:
                    continue
                p = math.sqrt(px * px + py * py + pz * pz)
                if P_MIN_MEV <= p <= P_MAX_MEV:
                    rows.append((x, px / pz, y, py / pz, p))
    return np.asarray(rows, dtype=float)


def fit_twiss(u_mm: np.ndarray, up_rad: np.ndarray) -> dict[str, float | np.ndarray]:
    data = np.column_stack((u_mm, up_rad))
    mean = data.mean(axis=0)
    centered = data - mean
    cov = np.cov(centered, rowvar=False, ddof=0)
    eps = math.sqrt(float(np.linalg.det(cov)))
    beta = cov[0, 0] / eps
    alpha = -cov[0, 1] / eps
    gamma = cov[1, 1] / eps
    action = gamma * centered[:, 0] ** 2 + 2.0 * alpha * centered[:, 0] * centered[:, 1] + beta * centered[:, 1] ** 2
    return {
        "mean": mean,
        "eps": eps,
        "beta": beta,
        "alpha": alpha,
        "gamma": gamma,
        "action": action,
    }


def ellipse_points(twiss: dict[str, float | np.ndarray], eps_mm_rad: float, n: int = 360):
    phi = np.linspace(0.0, 2.0 * math.pi, n)
    beta = float(twiss["beta"])
    alpha = float(twiss["alpha"])
    mean_u, mean_up = np.asarray(twiss["mean"], dtype=float)
    amp_u = math.sqrt(beta * eps_mm_rad)
    amp_up = math.sqrt(eps_mm_rad / beta)
    u = mean_u + amp_u * np.cos(phi)
    up = mean_up - amp_up * (alpha * np.cos(phi) + np.sin(phi))
    return u, up


def plot_plane(axis, u, up, p, twiss, name):
    inside = np.asarray(twiss["action"]) <= ELLIPSE_EPS_MM_RAD
    u_cm = u / 10.0
    axis.scatter(u_cm[~inside], up[~inside], c=p[~inside], cmap="viridis", s=5, alpha=0.22, linewidths=0)
    axis.scatter(u_cm[inside], up[inside], c=p[inside], cmap="viridis", s=8, alpha=0.70, linewidths=0)
    eu, eup = ellipse_points(twiss, ELLIPSE_EPS_MM_RAD)
    axis.plot(eu / 10.0, eup, color="black", linewidth=1.8, label="2 mm rad ellipse")
    axis.axhline(0.0, color="0.2", linewidth=0.6, alpha=0.35)
    axis.axvline(0.0, color="0.2", linewidth=0.6, alpha=0.35)
    axis.set_xlabel(f"{name} [cm]")
    axis.set_ylabel(f"{name}' [rad]")
    axis.set_xlim(-30.0, 30.0)
    axis.set_ylim(-0.3, 0.3)
    axis.grid(True, linewidth=0.35, alpha=0.35)
    axis.legend(loc="upper right", frameon=True, fontsize=8)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cluster", help="Condor cluster id, e.g. 3763181")
    parser.add_argument("--label", default="", help="plot title label")
    parser.add_argument("--output", type=Path, help="output PNG path")
    args = parser.parse_args()

    rows = load_muons(args.cluster)
    if len(rows) < 2:
        raise SystemExit(f"not enough final mu+ in {P_MIN_MEV:g}-{P_MAX_MEV:g} MeV/c for cluster {args.cluster}")

    x, xp, y, yp, p = rows.T
    xt = fit_twiss(x, xp)
    yt = fit_twiss(y, yp)
    accepted = (np.asarray(xt["action"]) <= ELLIPSE_EPS_MM_RAD) & (np.asarray(yt["action"]) <= ELLIPSE_EPS_MM_RAD)

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.2), dpi=170, constrained_layout=True)
    plot_plane(axes[0], x, xp, p, xt, "x")
    plot_plane(axes[1], y, yp, p, yt, "y")
    label = f" - {args.label}" if args.label else ""
    fig.suptitle(
        f"Final mu+ phase space{label}: {len(rows)} in 190-210 MeV/c, "
        f"{int(accepted.sum())} inside both ellipses"
    )

    output = args.output or BASE / "plots" / f"final_phase_ellipses_{args.cluster}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    print(output)
    print(f"p_window_muplus {len(rows)}")
    print(f"accepted_both_ellipses {int(accepted.sum())}")
    print(f"x_eps_rms_mm_rad {float(xt['eps']):.9g}")
    print(f"y_eps_rms_mm_rad {float(yt['eps']):.9g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
