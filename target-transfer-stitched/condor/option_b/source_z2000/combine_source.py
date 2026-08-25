#!/usr/bin/env python3
import csv
import math
from collections import Counter
from pathlib import Path


BASE = Path(__file__).resolve().parent
COMBINED = BASE / "combined"
N_EVENTS_PER_JOB = 100000


def rows_from_source(job_id, path):
    with path.open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 16:
                continue
            event = int(parts[0])
            iptyp = int(parts[2])
            x_m = float(parts[6])
            y_m = float(parts[7])
            z_m = float(parts[8])
            px, py, pz = map(float, parts[9:12])
            p = math.sqrt(px * px + py * py + pz * pz)
            yield {
                "job_id": job_id,
                "global_event": job_id * N_EVENTS_PER_JOB + event - 1,
                "event": event,
                "iptyp": iptyp,
                "particle": "pi+" if iptyp == 3 else "mu+" if iptyp == 2 else str(iptyp),
                "x_mm": x_m * 1000,
                "y_mm": y_m * 1000,
                "z_mm": z_m * 1000,
                "px_GeVc": px,
                "py_GeVc": py,
                "pz_GeVc": pz,
                "p_GeVc": p,
                "xp_rad": px / pz if pz else 0.0,
                "yp_rad": py / pz if pz else 0.0,
            }


def source_candidates():
    job_ids = set()
    for pattern in ("job_*", "rescue_job_*"):
        for job_dir in BASE.glob(pattern):
            try:
                job_ids.add(int(job_dir.name.split("_")[-1]))
            except ValueError:
                continue

    for job_id in sorted(job_ids):
        candidates = [BASE / f"rescue_job_{job_id}", BASE / f"job_{job_id}"]
        for job_dir in candidates:
            source_path = job_dir / "source_z2000.txt"
            if source_path.exists() and source_path.stat().st_size > 0:
                yield job_id, job_dir, source_path
                break


def main():
    COMBINED.mkdir(exist_ok=True)
    summary_rows = []
    counts = Counter()
    selected_rows = []
    output_csv = COMBINED / "source_z2000_pi_mu.csv"
    with output_csv.open("w", newline="") as f:
        fieldnames = [
            "job_id",
            "global_event",
            "event",
            "iptyp",
            "particle",
            "x_mm",
            "y_mm",
            "z_mm",
            "px_GeVc",
            "py_GeVc",
            "pz_GeVc",
            "p_GeVc",
            "xp_rad",
            "yp_rad",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for job_id, job_dir, source_path in source_candidates():
            n_rows = 0
            for row in rows_from_source(job_id, source_path):
                counts[row["particle"]] += 1
                n_rows += 1
                writer.writerow(row)
            summary_rows.append((job_id, n_rows))
            selected_rows.append((job_id, job_dir.name, n_rows, source_path))

    summary = COMBINED / "summary.txt"
    total_events = len(summary_rows) * N_EVENTS_PER_JOB
    with summary.open("w") as f:
        f.write(f"completed_jobs {len(summary_rows)}\n")
        f.write(f"events_per_job {N_EVENTS_PER_JOB}\n")
        f.write(f"total_events {total_events}\n")
        for particle, count in sorted(counts.items()):
            f.write(f"source_{particle} {count}\n")
            f.write(f"source_{particle}_per_proton {count / total_events if total_events else 0:.8g}\n")
        f.write(f"source_tracks {sum(counts.values())}\n")
        f.write("selected_sources\n")
        for job_id, job_name, n_rows, source_path in selected_rows:
            f.write(f"selected_job_{job_id} {job_name} {n_rows} {source_path.relative_to(BASE)}\n")

    print(f"completed_jobs={len(summary_rows)}")
    print(f"source_tracks={sum(counts.values())}")
    print(f"summary={summary}")
    print(f"csv={output_csv}")


if __name__ == "__main__":
    main()
