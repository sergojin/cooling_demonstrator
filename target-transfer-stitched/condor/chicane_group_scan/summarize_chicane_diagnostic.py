#!/usr/bin/env python3
import csv
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path


P_MIN_MEV = 190.0
P_MAX_MEV = 210.0
R_CUT_MM = 20.0


def iter_tracks(path):
    with path.open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 12:
                continue
            x = float(parts[0])
            y = float(parts[1])
            z = float(parts[2])
            px = float(parts[3])
            py = float(parts[4])
            pz = float(parts[5])
            pdgid = int(parts[7])
            event_id = int(parts[8])
            p = math.sqrt(px * px + py * py + pz * pz)
            r = math.sqrt(x * x + y * y)
            xp_mrad = 1000.0 * px / pz if pz else 0.0
            yp_mrad = 1000.0 * py / pz if pz else 0.0
            yield {
                "x_mm": x,
                "y_mm": y,
                "z_mm": z,
                "px_MeVc": px,
                "py_MeVc": py,
                "pz_MeVc": pz,
                "p_MeVc": p,
                "r_mm": r,
                "xp_mrad": xp_mrad,
                "yp_mrad": yp_mrad,
                "pdgid": pdgid,
                "event_id": event_id,
            }


def mean(values):
    return sum(values) / len(values) if values else 0.0


def rms(values):
    if not values:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))


def percentile(values, fraction):
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return ordered[index]


def main():
    if len(sys.argv) != 7:
        raise SystemExit(
            "usage: summarize_chicane_diagnostic.py run_dir point_id config g12_scale g678_scale n_events"
        )
    run_dir = Path(sys.argv[1])
    point_id = int(sys.argv[2])
    config = sys.argv[3]
    g12_scale = sys.argv[4]
    g678_scale = sys.argv[5]
    n_events = int(sys.argv[6])

    selected_by_plane = defaultdict(list)
    species_by_plane = defaultdict(Counter)
    p_window_counts = Counter()
    accepted_counts = Counter()

    for path in sorted(run_dir.glob("score_z*.txt")):
        z_mm = int(path.stem.replace("score_z", ""))
        for track in iter_tracks(path):
            species_by_plane[z_mm][track["pdgid"]] += 1
            if track["pdgid"] != -13:
                continue
            if P_MIN_MEV <= track["p_MeVc"] <= P_MAX_MEV:
                selected_by_plane[z_mm].append(track)
                p_window_counts[z_mm] += 1
                if track["r_mm"] <= R_CUT_MM:
                    accepted_counts[z_mm] += 1

    tracks_csv = run_dir / "diagnostic_tracks_p190_210_muplus.csv"
    with tracks_csv.open("w", newline="") as f:
        fieldnames = [
            "point_id",
            "config",
            "g12_scale",
            "g678_scale",
            "z_mm",
            "event_id",
            "x_mm",
            "y_mm",
            "r_mm",
            "px_MeVc",
            "py_MeVc",
            "pz_MeVc",
            "p_MeVc",
            "xp_mrad",
            "yp_mrad",
            "accepted_r20",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for z_mm in sorted(selected_by_plane):
            for track in selected_by_plane[z_mm]:
                writer.writerow(
                    {
                        "point_id": point_id,
                        "config": config,
                        "g12_scale": g12_scale,
                        "g678_scale": g678_scale,
                        "z_mm": z_mm,
                        "event_id": track["event_id"],
                        "x_mm": f"{track['x_mm']:.9g}",
                        "y_mm": f"{track['y_mm']:.9g}",
                        "r_mm": f"{track['r_mm']:.9g}",
                        "px_MeVc": f"{track['px_MeVc']:.9g}",
                        "py_MeVc": f"{track['py_MeVc']:.9g}",
                        "pz_MeVc": f"{track['pz_MeVc']:.9g}",
                        "p_MeVc": f"{track['p_MeVc']:.9g}",
                        "xp_mrad": f"{track['xp_mrad']:.9g}",
                        "yp_mrad": f"{track['yp_mrad']:.9g}",
                        "accepted_r20": int(track["r_mm"] <= R_CUT_MM),
                    }
                )

    plane_csv = run_dir / "diagnostic_plane_summary.csv"
    with plane_csv.open("w", newline="") as f:
        fieldnames = [
            "point_id",
            "config",
            "g12_scale",
            "g678_scale",
            "z_mm",
            "total_tracks",
            "final_pi+",
            "final_mu+",
            "mu_p190_210",
            "mu_p190_210_r20",
            "mean_x_mm",
            "mean_y_mm",
            "mean_r_mm",
            "r_rms_mm",
            "r_p50_mm",
            "r_p90_mm",
            "r_p95_mm",
            "mean_xp_mrad",
            "mean_yp_mrad",
            "xp_rms_mrad",
            "yp_rms_mrad",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for z_mm in sorted(species_by_plane):
            rows = selected_by_plane[z_mm]
            rs = [row["r_mm"] for row in rows]
            xs = [row["x_mm"] for row in rows]
            ys = [row["y_mm"] for row in rows]
            xps = [row["xp_mrad"] for row in rows]
            yps = [row["yp_mrad"] for row in rows]
            species = species_by_plane[z_mm]
            writer.writerow(
                {
                    "point_id": point_id,
                    "config": config,
                    "g12_scale": g12_scale,
                    "g678_scale": g678_scale,
                    "z_mm": z_mm,
                    "total_tracks": sum(species.values()),
                    "final_pi+": species.get(211, 0),
                    "final_mu+": species.get(-13, 0),
                    "mu_p190_210": p_window_counts[z_mm],
                    "mu_p190_210_r20": accepted_counts[z_mm],
                    "mean_x_mm": f"{mean(xs):.9g}",
                    "mean_y_mm": f"{mean(ys):.9g}",
                    "mean_r_mm": f"{mean(rs):.9g}",
                    "r_rms_mm": f"{rms(rs):.9g}",
                    "r_p50_mm": f"{percentile(rs, 0.50):.9g}",
                    "r_p90_mm": f"{percentile(rs, 0.90):.9g}",
                    "r_p95_mm": f"{percentile(rs, 0.95):.9g}",
                    "mean_xp_mrad": f"{mean(xps):.9g}",
                    "mean_yp_mrad": f"{mean(yps):.9g}",
                    "xp_rms_mrad": f"{rms(xps):.9g}",
                    "yp_rms_mrad": f"{rms(yps):.9g}",
                }
            )

    summary = run_dir / "diagnostic_summary.txt"
    final_z = 23300
    with summary.open("w") as f:
        f.write(f"point_id {point_id}\n")
        f.write(f"config {config}\n")
        f.write(f"g12_scale {g12_scale}\n")
        f.write(f"g678_scale {g678_scale}\n")
        f.write(f"n_events {n_events}\n")
        f.write(f"final_mu_p190_210 {p_window_counts[final_z]}\n")
        f.write(f"final_mu_p190_210_r20 {accepted_counts[final_z]}\n")
        f.write(f"tracks_csv {tracks_csv.name}\n")
        f.write(f"plane_csv {plane_csv.name}\n")

    print(summary)


if __name__ == "__main__":
    main()
