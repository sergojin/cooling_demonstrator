#!/usr/bin/env python3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


BASE = Path(__file__).resolve().parent
FINAL = BASE / "final_true_muons.txt"
TRACE = BASE / "trace_all_final_muon_events.txt"
OUT = BASE / "all_pion_decays_to_final_muons.png"


def read_track_file(path):
    header = None
    rows = []
    with path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            if line.startswith("#"):
                if line.startswith("#x "):
                    header = line.lstrip("#").split()
                continue
            if header is None:
                raise RuntimeError(f"header not found in {path}")
            rows.append(dict(zip(header, line.split())))
    return rows


def as_int(row, name):
    return int(float(row[name]))


def as_float(row, name):
    return float(row[name])


def group_tracks(rows):
    grouped = {}
    for row in rows:
        key = (as_int(row, "EventID"), as_int(row, "TrackID"), as_int(row, "PDGid"))
        grouped.setdefault(key, []).append(row)
    for values in grouped.values():
        values.sort(key=lambda row: as_float(row, "PathLength"))
    return grouped


def arrays(rows):
    z = [as_float(row, "z") / 1000.0 for row in rows]
    x = [as_float(row, "x") / 1000.0 for row in rows]
    y = [as_float(row, "y") / 1000.0 for row in rows]
    return z, x, y


def draw_lattice(ax):
    bands = [
        (0.0, 2.0, "#fff1d6", "target + horn"),
        (2.0, 11.3, "#e9f4ff", "decay channel"),
        (11.3, 23.3, "#edf8ed", "chicane / transfer"),
    ]
    for z0, z1, color, label in bands:
        ax.axvspan(z0, z1, color=color, alpha=0.9, zorder=0)
        ax.text((z0 + z1) / 2, 0.97, label, transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=9)

    for z, label in [(2.0, "score"), (11.3, "decay end"), (23.3, "final score")]:
        ax.axvline(z, color="#444", ls="--", lw=0.8, alpha=0.65)
        ax.text(z, 0.04, label, transform=ax.get_xaxis_transform(),
                rotation=90, ha="right", va="bottom", fontsize=8, color="#444")


def main():
    final_muons = read_track_file(FINAL)
    trace_rows = read_track_file(TRACE)
    tracks = group_tracks(trace_rows)

    chains = []
    missing_parents = []
    for mu in final_muons:
        event_id = as_int(mu, "EventID")
        mu_track_id = as_int(mu, "TrackID")
        mu_pdgid = as_int(mu, "PDGid")
        parent_id = as_int(mu, "ParentID")

        mu_key = (event_id, mu_track_id, mu_pdgid)
        mu_rows = tracks.get(mu_key, [])

        pion_rows = None
        for pion_pdgid in (211, -211):
            candidate = tracks.get((event_id, parent_id, pion_pdgid), [])
            if candidate:
                pion_rows = candidate
                break

        if mu_rows and pion_rows:
            chains.append((mu, pion_rows, mu_rows))
        else:
            missing_parents.append((event_id, mu_track_id, parent_id))

    fig, (ax_x, ax_y) = plt.subplots(2, 1, figsize=(15, 8.5), dpi=160, sharex=True)
    for ax in (ax_x, ax_y):
        draw_lattice(ax)
        ax.grid(True, alpha=0.25)

    colors = plt.cm.tab20.colors
    for index, (mu, pion_rows, mu_rows) in enumerate(chains):
        color = colors[index % len(colors)]
        zp, xp, yp = arrays(pion_rows)
        zm, xm, ym = arrays(mu_rows)

        ax_x.plot(zp, xp, color=color, lw=1.2, alpha=0.75, ls="--")
        ax_y.plot(zp, yp, color=color, lw=1.2, alpha=0.75, ls="--")
        ax_x.plot(zm, xm, color=color, lw=1.6, alpha=0.95)
        ax_y.plot(zm, ym, color=color, lw=1.6, alpha=0.95)
        ax_x.scatter([zm[0]], [xm[0]], s=14, color=color, edgecolor="black", linewidth=0.25, zorder=5)
        ax_y.scatter([zm[0]], [ym[0]], s=14, color=color, edgecolor="black", linewidth=0.25, zorder=5)

    ax_x.set_ylabel("x [m]")
    ax_y.set_ylabel("y [m]")
    ax_y.set_xlabel("z [m]")
    ax_x.set_title(f"{len(chains)} pion decays with daughter muons reaching the final scoring plane")

    legend = [
        Line2D([0], [0], color="black", lw=1.2, ls="--", label="pion parent"),
        Line2D([0], [0], color="black", lw=1.6, label="muon daughter"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="black",
               markersize=5, label="decay point"),
    ]
    ax_x.legend(handles=legend, loc="upper right")

    if missing_parents:
        ax_y.text(
            0.01, 0.02,
            f"{len(missing_parents)} final muon(s) had no traced pion parent",
            transform=ax_y.transAxes,
            fontsize=8,
            color="#555",
            ha="left",
            va="bottom",
        )

    fig.tight_layout()
    fig.savefig(OUT)
    print(OUT)
    print(f"chains={len(chains)} missing_parent={len(missing_parents)}")


if __name__ == "__main__":
    main()
