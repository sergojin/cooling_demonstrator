#!/usr/bin/env python3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
TRACE = BASE / "trace_event_2865.txt"
OUT = BASE / "pion_decay_to_final_muon.png"


def read_trace(path):
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
                raise RuntimeError("trace header not found")
            rows.append(dict(zip(header, line.split())))
    return rows


def track(rows, event_id, track_id, pdgid):
    selected = [
        row for row in rows
        if int(float(row["EventID"])) == event_id
        and int(float(row["TrackID"])) == track_id
        and int(float(row["PDGid"])) == pdgid
    ]
    selected.sort(key=lambda row: float(row["PathLength"]))
    return selected


def arrays(rows):
    z = [float(row["z"]) / 1000.0 for row in rows]
    x = [float(row["x"]) / 1000.0 for row in rows]
    y = [float(row["y"]) / 1000.0 for row in rows]
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

    for z in [2.65, 3.55, 4.45, 5.75, 6.65, 7.55, 8.85, 9.75, 10.65,
              11.55, 12.55, 15.55, 16.55, 17.55, 20.55, 21.55, 22.55]:
        ax.axvline(z, color="#777", lw=0.35, alpha=0.2)


def main():
    rows = read_trace(TRACE)
    pion = track(rows, event_id=2865, track_id=1059, pdgid=211)
    muon = track(rows, event_id=2865, track_id=1060, pdgid=-13)
    if not pion or not muon:
        raise RuntimeError("required pion/muon tracks were not found")

    zp, xp, yp = arrays(pion)
    zm, xm, ym = arrays(muon)
    decay_z = zm[0]
    decay_x = xm[0]
    decay_y = ym[0]

    fig, (ax_x, ax_y) = plt.subplots(2, 1, figsize=(14, 8), dpi=160, sharex=True)

    for ax in (ax_x, ax_y):
        draw_lattice(ax)
        ax.grid(True, alpha=0.25)

    ax_x.plot(zp, xp, color="#6f42c1", lw=2.0, label="pi+ parent")
    ax_x.plot(zm, xm, color="#0f766e", lw=2.0, label="mu+ daughter")
    ax_x.scatter([decay_z], [decay_x], s=45, color="#111", zorder=5, label="decay")

    ax_y.plot(zp, yp, color="#6f42c1", lw=2.0)
    ax_y.plot(zm, ym, color="#0f766e", lw=2.0)
    ax_y.scatter([decay_z], [decay_y], s=45, color="#111", zorder=5)

    ax_x.set_ylabel("x [m]")
    ax_y.set_ylabel("y [m]")
    ax_y.set_xlabel("z [m]")
    ax_x.set_title("pi+ decay to mu+ reaching the final scoring plane")
    ax_x.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
