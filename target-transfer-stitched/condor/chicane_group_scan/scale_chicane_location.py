#!/usr/bin/env python3
import re
import sys
from pathlib import Path


NOMINAL_GRADIENTS = {
    "ch_q1_gradient": 0.874131397,
    "ch_q2_gradient": -0.700898219,
    "ch_q3_gradient": -0.784936358,
    "ch_q4_gradient": 1.59657119,
    "ch_q5_gradient": -0.784936358,
    "ch_q6_gradient": 1.17927583,
    "ch_q7_gradient": -1.11734632,
    "ch_q8_gradient": 0.299730689,
}

GROUPS = {
    "G12": ("ch_q1_gradient", "ch_q2_gradient"),
    "G345": ("ch_q3_gradient", "ch_q4_gradient", "ch_q5_gradient"),
    "G678": ("ch_q6_gradient", "ch_q7_gradient", "ch_q8_gradient"),
}

SHIFT_GROUPS = {
    "G345": {"ch_q3", "ch_q4", "ch_q5"},
    "G678": {"ch_q6", "ch_q7", "ch_q8"},
}


def main():
    if len(sys.argv) != 7:
        raise SystemExit(
            "usage: scale_chicane_location.py path g12_scale g345_scale g678_scale "
            "g345_shift_mm g678_shift_mm"
        )
    path = Path(sys.argv[1])
    scales = {
        "G12": float(sys.argv[2]),
        "G345": float(sys.argv[3]),
        "G678": float(sys.argv[4]),
    }
    shifts = {
        "G345": float(sys.argv[5]),
        "G678": float(sys.argv[6]),
    }

    gradients = dict(NOMINAL_GRADIENTS)
    for group_name, names in GROUPS.items():
        for name in names:
            gradients[name] = NOMINAL_GRADIENTS[name] * scales[group_name]

    gradient_names = "|".join(re.escape(name) for name in gradients)
    gradient_pattern = re.compile(rf"^(param\s+)({gradient_names})(=.*)$")
    place_pattern = re.compile(r"^(place\s+chicane_quad\s+z=)([-+0-9.]+)(.*\srename=(ch_q[1-8])\s*)$")

    output = []
    for line in path.read_text().splitlines():
        gradient_match = gradient_pattern.match(line)
        if gradient_match:
            name = gradient_match.group(2)
            line = f"{gradient_match.group(1)}{name}={gradients[name]:.9g}"
        else:
            place_match = place_pattern.match(line)
            if place_match:
                z = float(place_match.group(2))
                quad_name = place_match.group(4)
                for group_name, quad_names in SHIFT_GROUPS.items():
                    if quad_name in quad_names:
                        z += shifts[group_name]
                        line = f"{place_match.group(1)}{z:.3f}{place_match.group(3)}"
                        break
        output.append(line)
    path.write_text("\n".join(output) + "\n")

    for name in sorted(gradients):
        print(f"{name} {gradients[name]:.9g}")
    for name in sorted(shifts):
        print(f"{name}_z_shift_mm {shifts[name]:.3f}")


if __name__ == "__main__":
    main()
