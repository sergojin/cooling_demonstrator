#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
FINAL = BASE / "score_z23300.txt"
P_MIN_MEV = 190.0
P_MAX_MEV = 210.0
ELLIPSE_EPS_MM_RAD = 2.0


def load_rows() -> list[tuple[float, float, float, float, float]]:
    rows = []
    with FINAL.open() as handle:
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
    return rows


def fit_twiss(rows: list[tuple[float, float, float, float, float]], coord_index: int, slope_index: int):
    mean_u = sum(row[coord_index] for row in rows) / len(rows)
    mean_up = sum(row[slope_index] for row in rows) / len(rows)
    centered = [(row[coord_index] - mean_u, row[slope_index] - mean_up) for row in rows]
    suu = sum(u * u for u, _ in centered) / len(centered)
    suup = sum(u * up for u, up in centered) / len(centered)
    supup = sum(up * up for _, up in centered) / len(centered)
    det = suu * supup - suup * suup
    eps = math.sqrt(det)
    return {
        "mean_u": mean_u,
        "mean_up": mean_up,
        "eps": eps,
        "beta": suu / eps,
        "alpha": -suup / eps,
        "gamma": supup / eps,
    }


def phase_action(row, twiss, coord_index: int, slope_index: int) -> float:
    u = row[coord_index] - twiss["mean_u"]
    up = row[slope_index] - twiss["mean_up"]
    return twiss["gamma"] * u * u + 2.0 * twiss["alpha"] * u * up + twiss["beta"] * up * up


def ellipse_points(twiss, eps: float):
    xs = []
    xps = []
    beta = twiss["beta"]
    alpha = twiss["alpha"]
    for i in range(361):
        psi = 2.0 * math.pi * i / 360.0
        u = math.sqrt(eps * beta) * math.cos(psi)
        up = -math.sqrt(eps / beta) * (alpha * math.cos(psi) + math.sin(psi))
        xs.append((twiss["mean_u"] + u) / 1000.0)
        xps.append(twiss["mean_up"] + up)
    return xs, xps


def main() -> int:
    rows = load_rows()
    if len(rows) < 2:
        raise SystemExit(f"not enough final-plane mu+ in {P_MIN_MEV:g}-{P_MAX_MEV:g} MeV/c")

    x_twiss = fit_twiss(rows, 0, 1)
    y_twiss = fit_twiss(rows, 2, 3)
    accepted = sum(
        1
        for row in rows
        if phase_action(row, x_twiss, 0, 1) <= ELLIPSE_EPS_MM_RAD
        and phase_action(row, y_twiss, 2, 3) <= ELLIPSE_EPS_MM_RAD
    )

    plots = BASE / "plots"
    plots.mkdir(exist_ok=True)
    output = plots / "final_muon_phase_space_p190_210_with_2mmrad_ellipses.png"

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), constrained_layout=True)
    fig.suptitle(
        "Final-plane mu+ phase space, 190-210 MeV/c "
        f"(N={len(rows)}, inside both ellipses={accepted})"
    )

    panels = [
        (axes[0], 0, 1, x_twiss, "x [m]", "x' = px/pz [rad]"),
        (axes[1], 2, 3, y_twiss, "y [m]", "y' = py/pz [rad]"),
    ]
    p_values = [row[4] for row in rows]
    for axis, coord_index, slope_index, twiss, xlabel, ylabel in panels:
        scatter = axis.scatter(
            [row[coord_index] / 1000.0 for row in rows],
            [row[slope_index] for row in rows],
            c=p_values,
            cmap="viridis",
            s=12,
            alpha=0.72,
            linewidths=0,
        )
        ex, exp = ellipse_points(twiss, ELLIPSE_EPS_MM_RAD)
        axis.plot(ex, exp, color="crimson", linewidth=2.0, label="2 mm rad ellipse")
        axis.axhline(0.0, color="0.25", linewidth=0.7, alpha=0.35)
        axis.axvline(0.0, color="0.25", linewidth=0.7, alpha=0.35)
        axis.set_xlabel(xlabel)
        axis.set_ylabel(ylabel)
        axis.set_xlim(-0.2, 0.2)
        axis.set_ylim(-0.15, 0.15)
        axis.grid(True, linewidth=0.4, alpha=0.35)
        axis.legend(loc="upper right", frameon=False)
        axis.figure.colorbar(scatter, ax=axis, label="p [MeV/c]")

    fig.savefig(output, dpi=170)

    summary = output.with_suffix(".txt")
    summary.write_text(
        "\n".join(
            [
                f"run_dir {BASE}",
                f"selection final-plane mu+ with {P_MIN_MEV:g} <= p <= {P_MAX_MEV:g} MeV/c",
                f"axis_x_or_y_m -0.2 0.2",
                f"axis_xp_or_yp_rad -0.15 0.15",
                f"final_mu+_p190_210 {len(rows)}",
                f"final_mu+_p190_210_xxp_yyp_eps_lt_2mmrad {accepted}",
                f"final_x_eps_rms_mm_rad {x_twiss['eps']:.9g}",
                f"final_x_beta_mm {x_twiss['beta']:.9g}",
                f"final_x_alpha {x_twiss['alpha']:.9g}",
                f"final_y_eps_rms_mm_rad {y_twiss['eps']:.9g}",
                f"final_y_beta_mm {y_twiss['beta']:.9g}",
                f"final_y_alpha {y_twiss['alpha']:.9g}",
                f"plot {output}",
            ]
        )
        + "\n"
    )

    print(output)
    print(summary)
    print(f"final_mu+_p190_210 {len(rows)}")
    print(f"final_mu+_p190_210_xxp_yyp_eps_lt_2mmrad {accepted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
