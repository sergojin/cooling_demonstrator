#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import re
import shutil
import subprocess
from pathlib import Path


BASE = Path(__file__).resolve().parent
OPTION_B = BASE.parent
TEMPLATE = OPTION_B / "nominal_pi10M" / "inputs" / "resample_downstream.g4bl"
RUNS = BASE / "runs"
P0_MEV = 200.0
MOMENTA_MEV = (190.0, 200.0, 210.0)
PDG_MUP = -13
Q3_NOMINAL = -0.784936358
Q4_NOMINAL = 1.59657119
Q5_NOMINAL = -0.784936358
SCALES = tuple(round(0.2 + 0.1 * i, 10) for i in range(13))
SCORE_PLANES = {
    "after_chicane": "score_z20500.txt",
    "final": "score_z23300.txt",
}


def write_beam(path: Path) -> None:
    with path.open("w") as out:
        out.write("#BLTrackFile DispersionProbe\n")
        out.write("#x y z Px Py Pz t PDGid EventID TrackID ParentID Weight\n")
        out.write("#mm mm mm MeV/c MeV/c MeV/c ns - - - - -\n")
        for event_id, pz in enumerate(MOMENTA_MEV, start=1):
            out.write(f"0 0 11000 0 0 {pz:.9g} 0 {PDG_MUP} {event_id} 1 0 1\n")


def write_config(path: Path, outer_scale: float, center_scale: float) -> None:
    text = TEMPLATE.read_text()
    text = re.sub(r"^reference particle=.*$", "reference particle=mu+ beamZ=11000 referenceMomentum=200", text, flags=re.MULTILINE)
    text = re.sub(r"^beam ascii file=.*$", "beam ascii file=beam.tmp beamZ=11000 lastEvent=$last_event", text, flags=re.MULTILINE)
    text = re.sub(
        r"^param ch_q3_gradient=.*$",
        f"param ch_q3_gradient={Q3_NOMINAL * outer_scale:.9g}",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^param ch_q4_gradient=.*$",
        f"param ch_q4_gradient={Q4_NOMINAL * center_scale:.9g}",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^param ch_q5_gradient=.*$",
        f"param ch_q5_gradient={Q5_NOMINAL * outer_scale:.9g}",
        text,
        flags=re.MULTILINE,
    )
    path.write_text(text)


def run_g4bl(run_dir: Path) -> None:
    cmd = (
        "export SPACK_USER_CACHE_PATH=${SPACK_USER_CACHE_PATH:-/tmp/spack-cache-${USER}} && "
        "mkdir -p ${SPACK_USER_CACHE_PATH} && "
        "source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh && "
        "spack load g4beamline && "
        "g4bl resample_downstream.g4bl last_event=3 viewer=none > g4bl.stdout 2> g4bl.stderr"
    )
    subprocess.run(cmd, cwd=run_dir, shell=True, executable="/bin/bash", check=True)


def read_plane(path: Path) -> dict[int, tuple[float, float]]:
    tracks = {}
    if not path.exists():
        return tracks
    with path.open() as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 10:
                continue
            x = float(parts[0])
            px = float(parts[3])
            pz = float(parts[5])
            event_id = int(float(parts[8]))
            if pz != 0.0:
                tracks[event_id] = (x, px / pz)
    return tracks


def fit_dispersion(tracks: dict[int, tuple[float, float]]) -> tuple[float, float, int]:
    points = []
    for event_id, p in enumerate(MOMENTA_MEV, start=1):
        if event_id not in tracks:
            continue
        delta = (p - P0_MEV) / P0_MEV
        x, xp = tracks[event_id]
        points.append((delta, x, xp))
    if len(points) < 2:
        return math.nan, math.nan, len(points)
    mean_delta = sum(point[0] for point in points) / len(points)
    var_delta = sum((point[0] - mean_delta) ** 2 for point in points)
    if var_delta == 0.0:
        return math.nan, math.nan, len(points)
    mean_x = sum(point[1] for point in points) / len(points)
    mean_xp = sum(point[2] for point in points) / len(points)
    d_mm = sum((delta - mean_delta) * (x - mean_x) for delta, x, _ in points) / var_delta
    dp = sum((delta - mean_delta) * (xp - mean_xp) for delta, _, xp in points) / var_delta
    return d_mm, dp, len(points)


def objective(d_mm: float, dp: float) -> float:
    if math.isnan(d_mm) or math.isnan(dp):
        return math.inf
    return math.sqrt(d_mm * d_mm + (1000.0 * dp) ** 2)


def main() -> int:
    if RUNS.exists():
        shutil.rmtree(RUNS)
    RUNS.mkdir(parents=True)

    rows = []
    for outer_scale in SCALES:
        for center_scale in SCALES:
            run_dir = RUNS / f"outer_{outer_scale:.1f}_center_{center_scale:.1f}"
            run_dir.mkdir()
            write_beam(run_dir / "beam.tmp")
            write_config(run_dir / "resample_downstream.g4bl", outer_scale, center_scale)
            run_g4bl(run_dir)

            row = {
                "outer_scale": f"{outer_scale:.1f}",
                "center_scale": f"{center_scale:.1f}",
                "q3_q5_gradient_T_per_m": f"{Q3_NOMINAL * outer_scale:.9g}",
                "q4_gradient_T_per_m": f"{Q4_NOMINAL * center_scale:.9g}",
            }
            for plane, filename in SCORE_PLANES.items():
                tracks = read_plane(run_dir / filename)
                d_mm, dp, n_tracks = fit_dispersion(tracks)
                row[f"{plane}_tracks"] = str(n_tracks)
                row[f"{plane}_D_mm"] = f"{d_mm:.9g}" if not math.isnan(d_mm) else "nan"
                row[f"{plane}_Dp_rad"] = f"{dp:.9g}" if not math.isnan(dp) else "nan"
                row[f"{plane}_objective_mm"] = f"{objective(d_mm, dp):.9g}"
            rows.append(row)

    summary_csv = BASE / "dispersion_scan_summary.csv"
    fields = [
        "outer_scale",
        "center_scale",
        "q3_q5_gradient_T_per_m",
        "q4_gradient_T_per_m",
        "after_chicane_tracks",
        "after_chicane_D_mm",
        "after_chicane_Dp_rad",
        "after_chicane_objective_mm",
        "final_tracks",
        "final_D_mm",
        "final_Dp_rad",
        "final_objective_mm",
    ]
    with summary_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    ranked = sorted(rows, key=lambda row: float(row["final_objective_mm"]))
    best_txt = BASE / "best_by_final_objective.txt"
    with best_txt.open("w") as out:
        out.write("Best points ranked by final objective sqrt(D^2 + (1000 D')^2)\n")
        out.write("D is in mm, D' is in rad per delta.\n\n")
        for row in ranked[:15]:
            out.write(
                "outer={outer_scale} center={center_scale} "
                "q3=q5={q3_q5_gradient_T_per_m} q4={q4_gradient_T_per_m} "
                "after_D={after_chicane_D_mm} after_Dp={after_chicane_Dp_rad} "
                "final_D={final_D_mm} final_Dp={final_Dp_rad} "
                "final_obj={final_objective_mm}\n".format(**row)
            )

    print(summary_csv)
    print(best_txt)
    print(best_txt.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
