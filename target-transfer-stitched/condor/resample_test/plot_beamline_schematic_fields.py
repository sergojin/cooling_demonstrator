#!/usr/bin/env python3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


BASE = Path(__file__).resolve().parent
PLOTS = BASE / "plots"
COMBINED = BASE / "combined"


def mm_to_m(z_mm):
    return z_mm / 1000.0


def add_radial_box(ax, z0_mm, z1_mm, radius_mm, color, label, text, text_y=330.0, text_x_offset=0.0, alpha=0.55):
    z0 = mm_to_m(z0_mm)
    width = mm_to_m(z1_mm - z0_mm)
    rect = Rectangle(
        (z0, -radius_mm),
        width,
        2.0 * radius_mm,
        facecolor=color,
        edgecolor="black",
        linewidth=0.8,
        alpha=alpha,
    )
    ax.add_patch(rect)
    cx = z0 + width / 2
    ax.text(cx, 0.0, label, ha="center", va="center", fontsize=7.5, color="black")
    if text:
        ax.annotate(
            text,
            xy=(cx, radius_mm),
            xytext=(cx + text_x_offset, text_y),
            ha="center",
            va="bottom",
            fontsize=7,
            arrowprops=dict(arrowstyle="-", linewidth=0.5, color="0.35"),
        )


def add_radius_lines(ax, z0_mm, z1_mm, radius_mm, color="0.25", linewidth=0.8, linestyle="--"):
    z0 = mm_to_m(z0_mm)
    z1 = mm_to_m(z1_mm)
    ax.hlines([radius_mm, -radius_mm], z0, z1, color=color, linewidth=linewidth, linestyle=linestyle)


def main():
    PLOTS.mkdir(exist_ok=True)
    COMBINED.mkdir(exist_ok=True)

    elements = []

    # Target/capture stage.
    elements.append(("horn", 0.0, 2000.0, "Horn", "I = 220 kA\nBphi = 44/r_mm T", "horn"))
    elements.append(("score", 2000.0, 2000.0, "z=2.0 m", "source plane", "plane"))

    # Decay-channel triplets, centers from the active G4BL input. Quads are 0.5 m long.
    decay = [
        (2650.0, "QF1", "+0.973 T/m"),
        (3550.0, "QD", "-1.85 T/m"),
        (4450.0, "QF2", "+0.973 T/m"),
        (5750.0, "QF1", "+0.973 T/m"),
        (6650.0, "QD", "-1.85 T/m"),
        (7550.0, "QF2", "+0.973 T/m"),
        (8850.0, "QF1", "+0.973 T/m"),
        (9750.0, "QD", "-1.85 T/m"),
        (10650.0, "QF2", "+0.973 T/m"),
    ]
    for i, (zc, name, field) in enumerate(decay, start=1):
        triplet = (i - 1) // 3 + 1
        elements.append(("quad", zc - 250.0, zc + 250.0, f"{name}.{triplet}", field, "decay_quad"))

    # Chicane: quads are 0.5 m long. Sector bends are drawn as their 1 m arc length along z.
    chicane_quads = [
        (11550.0, "CQ1", "+0.874 T/m"),
        (12550.0, "CQ2", "-0.701 T/m"),
        (15550.0, "CQ3", "-0.785 T/m"),
        (16550.0, "CQ4", "+1.60 T/m"),
        (17550.0, "CQ5", "-0.785 T/m"),
        (20550.0, "CQ6", "+1.18 T/m"),
        (21550.0, "CQ7", "-1.12 T/m"),
        (22550.0, "CQ8", "+0.300 T/m"),
    ]
    for zc, name, field in chicane_quads:
        elements.append(("quad", zc - 250.0, zc + 250.0, name, field, "chicane_quad"))

    elements.append(("bend", 13300.0, 14300.0, "B1", "By = +0.396 T\nangle = -34 deg", "bend1"))
    elements.append(("bend", 18800.0, 19800.0, "B2", "By = -0.396 T\nangle = +34 deg", "bend2"))
    elements.append(("score", 23300.0, 23300.0, "z=23.3 m", "final plane", "plane"))

    colors = {
        "horn": "#f6c85f",
        "decay_quad": "#82c7e6",
        "chicane_quad": "#8fd19e",
        "bend1": "#f28e8e",
        "bend2": "#f28e8e",
    }

    fig, ax = plt.subplots(figsize=(16.5, 6.3), dpi=180)
    ax.hlines(0.0, 0.0, 23.3, color="0.25", linewidth=0.6, alpha=0.22)

    # Section guide bands.
    ax.axvspan(0.0, 2.0, color="#f6c85f", alpha=0.10)
    ax.axvspan(2.0, 11.3, color="#82c7e6", alpha=0.08)
    ax.axvspan(11.3, 23.3, color="#8fd19e", alpha=0.07)
    ax.text(1.0, -385, "target + horn", ha="center", va="center", fontsize=9)
    ax.text(6.65, -385, "pion decay channel: 3 identical triplets", ha="center", va="center", fontsize=9)
    ax.text(17.3, -385, "chicane + matching quads", ha="center", va="center", fontsize=9)

    # Horn radial geometry from target_capture_stage.g4bl.
    add_radius_lines(ax, 0.0, 2000.0, 150.0, color="#8a6f13", linewidth=1.1, linestyle="-")
    add_radius_lines(ax, 0.0, 900.0, 6.0, color="black", linewidth=1.2, linestyle="-")
    ax.text(0.45, 18, "target\nr=6 mm", ha="center", va="bottom", fontsize=6.8)
    horn_inner = [
        (927.5, 26.4229548),
        (982.5, 34.2446771),
        (1037.5, 40.6939765),
        (1092.5, 48.624333),
        (1147.5, 57.0850213),
        (1202.5, 64.3336947),
        (1257.5, 71.3786997),
        (1312.5, 78.0219532),
        (1367.5, 84.3623389),
        (1422.5, 90.3277407),
        (1477.5, 95.8763534),
        (1532.5, 100.9758045),
        (1587.5, 103.9108589),
        (1642.5, 108.6833562),
        (1697.5, 112.8007331),
        (1752.5, 116.1068024),
        (1807.5, 118.6713218),
        (1862.5, 120.502913),
        (1917.5, 121.730284),
        (1972.5, 122.3458667),
    ]
    z_inner = [mm_to_m(z) for z, _ in horn_inner]
    r_inner = [r for _, r in horn_inner]
    ax.plot(z_inner, r_inner, color="0.35", linewidth=1.0)
    ax.plot(z_inner, [-r for r in r_inner], color="0.35", linewidth=1.0)
    ax.text(1.58, 130, "horn conductor", ha="center", va="bottom", fontsize=6.8, color="0.25")

    rows = []
    for kind, z0, z1, label, field, style in sorted(elements, key=lambda e: e[1]):
        rows.append((label, z0, z1, field))
        if kind == "score":
            z = mm_to_m(z0)
            ax.axvline(z, color="0.25", linestyle=":", linewidth=1.0)
            score_y = 245.0 if z0 < 3000 else 390.0
            score_x_offset = 0.10 if z0 < 3000 else 0.0
            ax.text(z + score_x_offset, score_y, f"{label}\n{field}", ha="center", va="bottom", fontsize=7.5)
            continue
        if kind == "horn":
            add_radial_box(ax, z0, z1, 150.0, colors[style], label, field, text_y=400.0, text_x_offset=-0.18, alpha=0.28)
        elif kind == "quad":
            text_y = 330.0
            text_x_offset = 0.0
            if label in {"CQ1", "CQ3", "CQ5", "CQ7"}:
                text_y = 410.0
            elif label in {"CQ4", "CQ6", "CQ8"}:
                text_y = 350.0
            add_radial_box(ax, z0, z1, 300.0, colors[style], label, field, text_y=text_y, text_x_offset=text_x_offset, alpha=0.38)
            add_radius_lines(ax, z0, z1, 200.0, color="black", linewidth=0.6, linestyle="--")
        elif kind == "bend":
            add_radial_box(ax, z0, z1, 300.0, colors[style], label, field, text_y=410.0, alpha=0.42)
            add_radius_lines(ax, z0, z1, 200.0, color="black", linewidth=0.6, linestyle="--")

    ax.set_xlim(-0.2, 23.8)
    ax.set_ylim(-450, 490)
    ax.set_ylabel("radial dimension r [mm]")
    ax.set_yticks([-300, -200, -150, 0, 150, 200, 300])
    ax.set_xlabel("z [m]")
    ax.set_title("G4Beamline stitched beamline schematic with magnetic field settings and radial dimensions")
    ax.grid(axis="both", linewidth=0.35, alpha=0.35)

    legend_handles = [
        Rectangle((0, 0), 1, 1, facecolor=colors["horn"], edgecolor="black", alpha=0.28, label="horn field region, |x|,|y| <= 150 mm"),
        Rectangle((0, 0), 1, 1, facecolor=colors["decay_quad"], edgecolor="black", alpha=0.38, label="quad iron radius 300 mm; dashed bore radius 200 mm"),
        Rectangle((0, 0), 1, 1, facecolor=colors["chicane_quad"], edgecolor="black", alpha=0.38, label="chicane quadrupoles"),
        Rectangle((0, 0), 1, 1, facecolor=colors["bend1"], edgecolor="black", alpha=0.42, label="sector dipoles: iron half-height 300 mm; dashed field half-height 200 mm"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
        fontsize=7.5,
        frameon=False,
    )

    fig.subplots_adjust(left=0.055, right=0.995, top=0.90, bottom=0.24)
    output = PLOTS / "beamline_schematic_with_fields.png"
    fig.savefig(output)

    table = COMBINED / "beamline_schematic_fields.csv"
    with table.open("w") as f:
        f.write("element,z_start_mm,z_end_mm,field_label\n")
        for label, z0, z1, field in rows:
            f.write(f"{label},{z0:.3f},{z1:.3f},\"{field}\"\n")

    print(output)
    print(table)


if __name__ == "__main__":
    main()
