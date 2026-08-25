#!/usr/bin/env python3
"""Plot 2D slices of the chicane surrogate model."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-codex")

SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_PACKAGE_DIR = SCRIPT_DIR / "python_packages"
if LOCAL_PACKAGE_DIR.exists():
    sys.path.insert(0, str(LOCAL_PACKAGE_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from propose_chicane_points import FEATURES, dedupe_rows, fit_predict, read_rows


FEATURE_ALIAS = {
    "G12": "G12_scale",
    "G345": "G345_scale",
    "G678": "G678_scale",
    "G345Z": "G345_z_shift_mm",
    "G678Z": "G678_z_shift_mm",
}

def feature_ranges(values: list[tuple[float, ...]]) -> dict[str, tuple[float, float]]:
    defaults = {
        "G12_scale": (0.75, 1.10),
        "G345_scale": (0.85, 1.15),
        "G678_scale": (0.90, 1.25),
        "G345_z_shift_mm": (-200.0, 200.0),
        "G678_z_shift_mm": (-400.0, 400.0),
    }
    output = {}
    for index, name in enumerate(FEATURES):
        lo = min(v[index] for v in values)
        hi = max(v[index] for v in values)
        dlo, dhi = defaults[name]
        margin = max(0.03, 0.15 * (hi - lo))
        output[name] = (min(dlo, lo - margin), max(dhi, hi + margin))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="+", type=Path, help="summary CSVs to train on")
    parser.add_argument("--target", default="phase_ellipse_yield_per_track")
    parser.add_argument("--model", choices=("auto", "extra_trees", "rbf"), default="auto")
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--grid", type=int, default=80)
    parser.add_argument("--pair", default="G12,G678", help="Feature pair, e.g. G12,G678 or G345Z,G678Z")
    parser.add_argument("--fixed-g12", type=float, default=1.0)
    parser.add_argument("--fixed-g345", type=float, default=1.0)
    parser.add_argument("--fixed-g678", type=float, default=1.0)
    parser.add_argument("--fixed-g345-z", type=float, default=0.0)
    parser.add_argument("--fixed-g678-z", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=SCRIPT_DIR / "surrogate_g12_g678.png")
    args = parser.parse_args()

    rows = read_rows(args.csv, args.target)
    data = dedupe_rows(rows)
    if len(data) < 5:
        raise SystemExit(f"need at least 5 distinct training points, found {len(data)}")

    train_x = [row["x"] for row in data]
    train_y = [float(row["y"]) for row in data]
    ranges = feature_ranges(train_x)

    pair_short = args.pair.split(",")
    if len(pair_short) != 2:
        raise SystemExit("--pair must contain exactly two comma-separated feature aliases")
    try:
        pair = tuple(FEATURE_ALIAS[name] for name in pair_short)
    except KeyError as exc:
        aliases = ", ".join(sorted(FEATURE_ALIAS))
        raise SystemExit(f"unknown feature alias {exc}; valid aliases: {aliases}") from exc
    fixed = {
        "G12_scale": args.fixed_g12,
        "G345_scale": args.fixed_g345,
        "G678_scale": args.fixed_g678,
        "G345_z_shift_mm": args.fixed_g345_z,
        "G678_z_shift_mm": args.fixed_g678_z,
    }

    x_name, y_name = pair
    x_values = np.linspace(*ranges[x_name], args.grid)
    y_values = np.linspace(*ranges[y_name], args.grid)
    candidates = []
    for y_value in y_values:
        for x_value in x_values:
            point = dict(fixed)
            point[x_name] = float(x_value)
            point[y_name] = float(y_value)
            candidates.append(tuple(point[name] for name in FEATURES))

    model_name = "rbf_ensemble" if args.model == "rbf" else args.model
    model_used, mean, std = fit_predict(model_name, train_x, train_y, candidates, args.seed)
    z_mean = np.array(mean).reshape(len(y_values), len(x_values))
    z_std = np.array(std).reshape(len(y_values), len(x_values))

    train_array = np.array(train_x)
    target_array = np.array(train_y)
    x_index = FEATURES.index(x_name)
    y_index = FEATURES.index(y_name)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    panels = (
        (axes[0], z_mean, f"Predicted {args.target}"),
        (axes[1], z_std, "Tree-to-tree model spread"),
    )
    for axis, z_values, title in panels:
        image = axis.imshow(
            z_values,
            origin="lower",
            extent=(x_values[0], x_values[-1], y_values[0], y_values[-1]),
            aspect="auto",
            cmap="viridis",
        )
        axis.scatter(
            train_array[:, x_index],
            train_array[:, y_index],
            c=target_array,
            cmap="magma",
            s=42,
            edgecolor="white",
            linewidth=0.7,
            label="simulated",
        )
        axis.set_xlabel(x_name)
        axis.set_ylabel(y_name)
        axis.set_title(title)
        fig.colorbar(image, ax=axis)
        axis.legend(loc="best", frameon=True)

    fixed_text = ", ".join(
        f"{name}={value:.3g}" for name, value in fixed.items() if name not in pair
    )
    fig.suptitle(f"Chicane surrogate slice ({model_used}); fixed {fixed_text}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    print(f"training_points={len(data)} target={args.target} model={model_used}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
