#!/usr/bin/env python3
"""Train a small surrogate model and propose chicane group-scale points."""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from pathlib import Path


LOCAL_PACKAGE_DIR = Path(__file__).resolve().parent / "python_packages"
if LOCAL_PACKAGE_DIR.exists():
    sys.path.insert(0, str(LOCAL_PACKAGE_DIR))

FEATURES = ("G12_scale", "G345_scale", "G678_scale", "G345_z_shift_mm", "G678_z_shift_mm")


def parse_scale(value: str) -> tuple[float, ...]:
    return tuple(float(part) for part in str(value).strip().split("_"))


def feature_row(row: dict[str, str]) -> tuple[float, ...]:
    group = row.get("group_name", "").strip()
    scale_text = row.get("scale", "").strip()

    g12 = 1.0
    g345 = 1.0
    g678 = 1.0
    g345_z = 0.0
    g678_z = 0.0

    if group == "nominal" or not scale_text:
        return g12, g345, g678, g345_z, g678_z

    scales = parse_scale(scale_text)
    scale = scales[0]

    if group == "G12":
        g12 = scale
    elif group == "G345":
        g345 = scale
    elif group == "G678":
        g678 = scale
    elif group == "GALL":
        g12 = g345 = g678 = scale
    elif group == "G12_G678":
        if len(scales) != 2:
            raise ValueError(f"G12_G678 scale should be '<g12>_<g678>': {scale_text}")
        g12, g678 = scales
    elif group == "G12_G345_G678":
        if len(scales) != 3:
            raise ValueError(f"G12_G345_G678 scale should be '<g12>_<g345>_<g678>': {scale_text}")
        g12, g345, g678 = scales
    elif group == "G12_G345_G678_Z345_Z678":
        if len(scales) != 5:
            raise ValueError(
                "G12_G345_G678_Z345_Z678 scale should be "
                "'<g12>_<g345>_<g678>_<g345_z>_<g678_z>': "
                f"{scale_text}"
            )
        g12, g345, g678, g345_z, g678_z = scales
    elif group == "DQF_DQD_G12_G345_G678":
        if len(scales) != 5:
            raise ValueError(
                "DQF_DQD_G12_G345_G678 scale should be "
                "'<decay_qf>_<decay_qd>_<g12>_<g345>_<g678>': "
                f"{scale_text}"
            )
        _, _, g12, g345, g678 = scales
    else:
        raise ValueError(f"unknown group_name '{group}'")

    return g12, g345, g678, g345_z, g678_z


def read_rows(paths: list[Path], target: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in paths:
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or target not in reader.fieldnames:
                print(f"warning: skipping {path}; missing target column '{target}'", file=sys.stderr)
                continue
            for raw in reader:
                try:
                    y = float(raw[target])
                    n_events = float(raw.get("n_events", "nan"))
                    x = feature_row(raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"could not parse row in {path}: {raw}") from exc
                if not math.isfinite(y):
                    continue
                rows.append(
                    {
                        "path": str(path),
                        "group_name": raw.get("group_name", ""),
                        "scale": raw.get("scale", ""),
                        "x": x,
                        "y": y,
                        "n_events": n_events,
                    }
                )
    return rows


def dedupe_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Merge repeated settings with an n_events-weighted target average."""
    merged: dict[tuple[float, ...], dict[str, object]] = {}
    for row in rows:
        x = tuple(row["x"])  # type: ignore[arg-type]
        weight = row["n_events"]
        if not isinstance(weight, float) or not math.isfinite(weight) or weight <= 0:
            weight = 1.0
        if x not in merged:
            merged[x] = {"x": x, "weight": 0.0, "weighted_y": 0.0, "sources": []}
        merged[x]["weight"] = float(merged[x]["weight"]) + weight
        merged[x]["weighted_y"] = float(merged[x]["weighted_y"]) + weight * float(row["y"])
        merged[x]["sources"].append(row)  # type: ignore[union-attr]

    output = []
    for x, item in merged.items():
        weight = float(item["weight"])
        output.append({"x": x, "y": float(item["weighted_y"]) / weight, "weight": weight})
    return output


def candidate_points(
    n: int,
    ranges: dict[str, tuple[float, float]],
    fixed: dict[str, float],
    seed: int,
) -> list[tuple[float, ...]]:
    rng = random.Random(seed)
    points = []
    for _ in range(n):
        values = []
        for name in FEATURES:
            if name in fixed:
                values.append(fixed[name])
            else:
                lo, hi = ranges[name]
                values.append(rng.uniform(lo, hi))
        points.append(tuple(values))  # type: ignore[arg-type]
    return points


def min_distance(point: tuple[float, ...], tried: list[tuple[float, ...]]) -> float:
    return min(math.dist(point, old) for old in tried) if tried else float("inf")


def fit_predict_extra_trees(
    train_x: list[tuple[float, ...]],
    train_y: list[float],
    candidates: list[tuple[float, ...]],
    seed: int,
) -> tuple[list[float], list[float]]:
    try:
        import numpy as np
        from sklearn.ensemble import ExtraTreesRegressor
    except ImportError as exc:
        raise SystemExit(
            "This script needs scikit-learn and numpy. Try running it in an environment "
            "with sklearn available, or install scikit-learn."
        ) from exc

    model = ExtraTreesRegressor(
        n_estimators=500,
        random_state=seed,
        min_samples_leaf=1,
        bootstrap=True,
        max_features=1.0,
    )
    x_array = np.array(train_x, dtype=float)
    y_array = np.array(train_y, dtype=float)
    cand_array = np.array(candidates, dtype=float)
    model.fit(x_array, y_array)

    tree_predictions = np.array([tree.predict(cand_array) for tree in model.estimators_])
    mean = tree_predictions.mean(axis=0)
    std = tree_predictions.std(axis=0)
    return mean.tolist(), std.tolist()


def fit_predict_rbf_ensemble(
    train_x: list[tuple[float, ...]],
    train_y: list[float],
    candidates: list[tuple[float, ...]],
    seed: int,
    n_models: int = 101,
) -> tuple[list[float], list[float]]:
    """No-dependency surrogate fallback using bootstrap RBF kernel smoothers."""
    rng = random.Random(seed)
    predictions = [[] for _ in candidates]
    global_mean = sum(train_y) / len(train_y)

    for _ in range(n_models):
        length_scale = rng.uniform(0.06, 0.22)
        sample_indices = [rng.randrange(len(train_x)) for _ in train_x]
        sampled_x = [train_x[index] for index in sample_indices]
        sampled_y = [train_y[index] for index in sample_indices]

        for candidate_index, point in enumerate(candidates):
            weighted_sum = 0.0
            total_weight = 0.0
            for x, y in zip(sampled_x, sampled_y):
                distance = math.dist(point, x)
                weight = math.exp(-0.5 * (distance / length_scale) ** 2)
                weighted_sum += weight * y
                total_weight += weight
            if total_weight <= 1e-12:
                predictions[candidate_index].append(global_mean)
            else:
                predictions[candidate_index].append(weighted_sum / total_weight)

    mean = []
    std = []
    for values in predictions:
        mu = sum(values) / len(values)
        variance = sum((value - mu) ** 2 for value in values) / len(values)
        mean.append(mu)
        std.append(math.sqrt(variance))
    return mean, std


def fit_predict(
    model_name: str,
    train_x: list[tuple[float, ...]],
    train_y: list[float],
    candidates: list[tuple[float, ...]],
    seed: int,
) -> tuple[str, list[float], list[float]]:
    if model_name in ("auto", "extra_trees"):
        try:
            mean, std = fit_predict_extra_trees(train_x, train_y, candidates, seed)
            return "extra_trees", mean, std
        except SystemExit:
            if model_name == "extra_trees":
                raise
    mean, std = fit_predict_rbf_ensemble(train_x, train_y, candidates, seed)
    return "rbf_ensemble", mean, std


def write_combo_points(
    path: Path,
    proposals: list[dict[str, float]],
    point_id_start: int,
    n_events: int,
) -> None:
    with path.open("w") as handle:
        for index, proposal in enumerate(proposals):
            handle.write(
                f"{point_id_start + index} G12_G678 "
                f"{proposal['G12_scale']:.3f} {proposal['G678_scale']:.3f} {n_events}\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="+", type=Path, help="summary CSVs to train on")
    parser.add_argument("--target", default="phase_ellipse_yield_per_track")
    parser.add_argument("--n-candidates", type=int, default=50000)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--model", choices=("auto", "extra_trees", "rbf"), default="auto")
    parser.add_argument("--kappa", type=float, default=0.5, help="score = mean + kappa*std")
    parser.add_argument("--min-distance", type=float, default=0.025)
    parser.add_argument("--proposal-min-distance", type=float, default=0.04)
    parser.add_argument("--g12-range", nargs=2, type=float, default=(0.80, 1.10))
    parser.add_argument("--g345-range", nargs=2, type=float, default=(0.85, 1.15))
    parser.add_argument("--g678-range", nargs=2, type=float, default=(1.00, 1.25))
    parser.add_argument("--g345-z-range", nargs=2, type=float, default=(-200.0, 200.0))
    parser.add_argument("--g678-z-range", nargs=2, type=float, default=(-400.0, 400.0))
    parser.add_argument("--fix-g12", type=float)
    parser.add_argument("--fix-g345", type=float)
    parser.add_argument("--fix-g678", type=float)
    parser.add_argument("--fix-g345-z", type=float)
    parser.add_argument("--fix-g678-z", type=float)
    parser.add_argument("--write-combo-points", type=Path)
    parser.add_argument("--point-id-start", type=int, default=14000)
    parser.add_argument("--n-events", type=int, default=1000000)
    args = parser.parse_args()

    rows = read_rows(args.csv, args.target)
    data = dedupe_rows(rows)
    if len(data) < 5:
        raise SystemExit(f"need at least 5 distinct training points, found {len(data)}")

    train_x = [row["x"] for row in data]  # type: ignore[list-item]
    train_y = [float(row["y"]) for row in data]

    ranges = {
        "G12_scale": tuple(args.g12_range),
        "G345_scale": tuple(args.g345_range),
        "G678_scale": tuple(args.g678_range),
        "G345_z_shift_mm": tuple(args.g345_z_range),
        "G678_z_shift_mm": tuple(args.g678_z_range),
    }
    fixed = {}
    for name, value in (
        ("G12_scale", args.fix_g12),
        ("G345_scale", args.fix_g345),
        ("G678_scale", args.fix_g678),
        ("G345_z_shift_mm", args.fix_g345_z),
        ("G678_z_shift_mm", args.fix_g678_z),
    ):
        if value is not None:
            fixed[name] = value

    candidates = candidate_points(args.n_candidates, ranges, fixed, args.seed)
    model_name = "rbf_ensemble" if args.model == "rbf" else args.model
    model_used, mean, std = fit_predict(model_name, train_x, train_y, candidates, args.seed)

    ranked = []
    for point, pred, sigma in zip(candidates, mean, std):
        distance = min_distance(point, train_x)
        if distance < args.min_distance:
            continue
        ranked_row = {name: point[index] for index, name in enumerate(FEATURES)}
        ranked_row.update(
            {
                "predicted_target": pred,
                "model_std": sigma,
                "acquisition": pred + args.kappa * sigma,
                "distance_to_tried": distance,
            }
        )
        ranked.append(ranked_row)
    ranked.sort(key=lambda row: row["acquisition"], reverse=True)
    proposals = []
    for row in ranked:
        point = tuple(row[name] for name in FEATURES)
        chosen = [
            tuple(old[name] for name in FEATURES)
            for old in proposals
        ]
        if not chosen or min_distance(point, chosen) >= args.proposal_min_distance:
            proposals.append(row)
        if len(proposals) >= args.top:
            break

    print(f"training_csvs={len(args.csv)}")
    print(f"training_points={len(data)} target={args.target} model={model_used}")
    print(",".join(["rank", *FEATURES, "predicted_target", "model_std", "acquisition", "distance_to_tried"]))
    for index, row in enumerate(proposals, start=1):
        print(
            f"{index},"
            + ",".join(f"{row[name]:.4f}" for name in FEATURES)
            + ","
            f"{row['predicted_target']:.8g},{row['model_std']:.8g},"
            f"{row['acquisition']:.8g},{row['distance_to_tried']:.4f}"
        )

    if args.write_combo_points:
        bad = [row for row in proposals if abs(row["G345_scale"] - 1.0) > 1e-12]
        if bad:
            raise SystemExit("--write-combo-points requires --fix-g345 1.0")
        if args.fix_g345_z != 0.0 or args.fix_g678_z != 0.0:
            raise SystemExit(
                "--write-combo-points requires --fix-g345-z 0 --fix-g678-z 0; "
                "the point format cannot encode position shifts"
            )
        write_combo_points(args.write_combo_points, proposals, args.point_id_start, args.n_events)
        print(f"wrote_combo_points={args.write_combo_points}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
