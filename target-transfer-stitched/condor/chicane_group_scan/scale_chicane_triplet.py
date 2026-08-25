#!/usr/bin/env python3
import re
import sys
from pathlib import Path


NOMINAL = {
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


def main():
    if len(sys.argv) != 5:
        raise SystemExit("usage: scale_chicane_triplet.py path g12_scale g345_scale g678_scale")
    path = Path(sys.argv[1])
    scales = {
        "G12": float(sys.argv[2]),
        "G345": float(sys.argv[3]),
        "G678": float(sys.argv[4]),
    }

    replacements = dict(NOMINAL)
    for group_name, names in GROUPS.items():
        for name in names:
            replacements[name] = NOMINAL[name] * scales[group_name]

    pattern = re.compile(r"^(param\s+)(ch_q[1-8]_gradient)(=.*)$")
    output = []
    for line in path.read_text().splitlines():
        match = pattern.match(line)
        if match:
            name = match.group(2)
            line = f"{match.group(1)}{name}={replacements[name]:.9g}"
        output.append(line)
    path.write_text("\n".join(output) + "\n")

    for name in sorted(replacements):
        print(f"{name} {replacements[name]:.9g}")


if __name__ == "__main__":
    main()
