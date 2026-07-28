#!/usr/bin/env python3
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
JOBS = BASE / "jobs"
COMBINED = BASE / "combined"
PLOTS = BASE / "plots"
N_EVENTS_PER_JOB = 100000
N_JOBS = 100


def parse_final_muons():
    muons = []
    final_counts = Counter()
    completed_jobs = []
    job_muon_counts = {}

    candidates = {}
    for root in [BASE / "rescue", BASE, JOBS]:
        for job_dir in root.glob("job_*"):
            job_id = int(job_dir.name.split("_")[-1])
            candidates.setdefault(job_id, []).append(job_dir)

    def score(job_dir):
        if (job_dir / "stitched_output.txt").exists():
            return 3
        if (job_dir / "final_muons.csv").exists() and (job_dir / "job_summary.txt").exists():
            return 2
        if (job_dir / "job_summary.txt").exists():
            return 1
        return 0

    for job_id in sorted(candidates):
        usable = sorted(candidates[job_id], key=score, reverse=True)
        if not usable or score(usable[0]) == 0:
            continue
        job_dir = usable[0]
        completed_jobs.append(job_id)
        job_muon_counts[job_id] = 0

        output = job_dir / "stitched_output.txt"
        if output.exists():
            seen_muons = []
            with output.open() as f:
                for line in f:
                    if not line.strip() or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) < 16:
                        continue
                    iptyp = int(parts[2])
                    event = int(parts[0])
                    z = float(parts[8])
                    if abs(z - 23.3) > 1e-6:
                        continue

                    final_counts[iptyp] += 1
                    if iptyp in (2, -2):
                        px, py, pz = map(float, parts[9:12])
                        momentum = math.sqrt(px * px + py * py + pz * pz)
                        seen_muons.append(
                            {
                                "job_id": job_id,
                                "global_event": job_id * N_EVENTS_PER_JOB + event - 1,
                                "event": event,
                                "charge": 1 if iptyp == 2 else -1,
                                "px_GeVc": px,
                                "py_GeVc": py,
                                "pz_GeVc": pz,
                                "p_GeVc": momentum,
                            }
                        )
            muons.extend(seen_muons)
            job_muon_counts[job_id] = len(seen_muons)
            continue

        summary = job_dir / "job_summary.txt"
        if summary.exists():
            with summary.open() as f:
                for line in f:
                    parts = line.split()
                    if len(parts) != 2:
                        continue
                    key, value = parts
                    if key == "final_mu+":
                        final_counts[2] += int(value)
                    elif key == "final_mu-":
                        final_counts[-2] += int(value)
                    elif key == "final_muons":
                        job_muon_counts[job_id] = int(value)

        muon_csv = job_dir / "final_muons.csv"
        if muon_csv.exists():
            with muon_csv.open() as f:
                reader = csv.DictReader(f)
                seen = 0
                for row in reader:
                    event = int(row["event"])
                    iptyp = int(row["iptyp"])
                    muons.append(
                        {
                            "job_id": job_id,
                            "global_event": job_id * N_EVENTS_PER_JOB + event - 1,
                            "event": event,
                            "charge": 1 if iptyp == 2 else -1,
                            "px_GeVc": float(row["px_GeVc"]),
                            "py_GeVc": float(row["py_GeVc"]),
                            "pz_GeVc": float(row["pz_GeVc"]),
                            "p_GeVc": float(row["p_GeVc"]),
                        }
                    )
                    seen += 1
                job_muon_counts[job_id] = seen

    return completed_jobs, final_counts, muons, job_muon_counts


def write_tables(completed_jobs, final_counts, muons, job_muon_counts):
    COMBINED.mkdir(exist_ok=True)

    muon_csv = COMBINED / "final_muons.csv"
    with muon_csv.open("w", newline="") as f:
        fieldnames = ["job_id", "global_event", "event", "charge", "px_GeVc", "py_GeVc", "pz_GeVc", "p_GeVc"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(muons)

    multiplicity = Counter(muon["global_event"] for muon in muons)
    total_events = len(completed_jobs) * N_EVENTS_PER_JOB
    multiplicity_counts = Counter(multiplicity.values())
    multiplicity_counts[0] = total_events - len(multiplicity)

    mult_csv = COMBINED / "final_muon_multiplicity.csv"
    with mult_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["muons_per_event", "events"])
        for n_muons in sorted(multiplicity_counts):
            writer.writerow([n_muons, multiplicity_counts[n_muons]])

    yield_csv = COMBINED / "final_muon_yields_by_job.csv"
    with yield_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["job_id", "n_events", "final_muons", "yield_per_proton"])
        for job_id in sorted(completed_jobs):
            count = job_muon_counts.get(job_id, 0)
            writer.writerow([job_id, N_EVENTS_PER_JOB, count, count / N_EVENTS_PER_JOB])

    summary = COMBINED / "summary.txt"
    with summary.open("w") as f:
        f.write(f"completed_jobs {len(completed_jobs)}\n")
        f.write(f"job_ids {' '.join(map(str, completed_jobs))}\n")
        f.write(f"events_per_job {N_EVENTS_PER_JOB}\n")
        f.write(f"total_events {total_events}\n")
        f.write(f"final_supported_tracks {sum(final_counts.values())}\n")
        for iptyp, count in sorted(final_counts.items(), key=lambda item: (-item[1], item[0])):
            f.write(f"final_iptyp_{iptyp} {count}\n")
        f.write(f"final_muons {len(muons)}\n")
        f.write(f"final_muon_yield_per_proton {len(muons) / total_events if total_events else 0:.8g}\n")

    return multiplicity_counts


def make_plots(muons, multiplicity_counts, job_muon_counts):
    PLOTS.mkdir(exist_ok=True)

    max_mult = max(multiplicity_counts) if multiplicity_counts else 0
    xs = list(range(max_mult + 1))
    ys = [multiplicity_counts.get(x, 0) for x in xs]

    fig, ax = plt.subplots(figsize=(7, 5), dpi=160)
    ax.bar(xs, ys, color="#4c78a8", edgecolor="#263238")
    ax.set_xlabel("Final-plane muons per proton event")
    ax.set_ylabel("Events")
    ax.set_title("Final scoring plane muon multiplicity")
    ax.set_yscale("log")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTS / "final_muon_multiplicity.png")

    xs = sorted(job_muon_counts)
    ys = [job_muon_counts[x] / N_EVENTS_PER_JOB for x in xs]
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=160)
    ax.bar(xs, ys, color="#59a14f", edgecolor="#263238")
    ax.axhline(sum(job_muon_counts.values()) / (len(xs) * N_EVENTS_PER_JOB), color="#222", lw=1.2, ls="--", label="mean")
    ax.set_xlabel("Job ID")
    ax.set_ylabel("Final-plane muon yield / proton")
    ax.set_title("Final scoring plane muon yield by job")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(PLOTS / "final_muon_yield_by_job.png")

    mu_plus = [m["p_GeVc"] for m in muons if m["charge"] > 0]
    mu_minus = [m["p_GeVc"] for m in muons if m["charge"] < 0]
    all_p = mu_plus + mu_minus

    fig, ax = plt.subplots(figsize=(8, 5), dpi=160)
    if all_p:
        max_p = max(all_p)
        bin_width = 0.05
        bins = [i * bin_width for i in range(int(math.ceil(max_p / bin_width)) + 2)]
        ax.hist(mu_plus, bins=bins, histtype="stepfilled", alpha=0.65, color="#2f80ed", label=f"mu+ ({len(mu_plus)})")
        ax.hist(mu_minus, bins=bins, histtype="stepfilled", alpha=0.65, color="#d1495b", label=f"mu- ({len(mu_minus)})")
    ax.set_xlabel("Total momentum p [GeV/c]")
    ax.set_ylabel("Counts")
    ax.set_title("Final scoring plane muon momentum spectrum")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(PLOTS / "final_muon_momentum_spectrum.png")


def main():
    completed_jobs, final_counts, muons, job_muon_counts = parse_final_muons()
    multiplicity_counts = write_tables(completed_jobs, final_counts, muons, job_muon_counts)
    make_plots(muons, multiplicity_counts, job_muon_counts)
    print(f"completed_jobs={len(completed_jobs)}")
    print(f"final_muons={len(muons)}")
    print(f"summary={COMBINED / 'summary.txt'}")
    print(f"plots={PLOTS}")


if __name__ == "__main__":
    main()
