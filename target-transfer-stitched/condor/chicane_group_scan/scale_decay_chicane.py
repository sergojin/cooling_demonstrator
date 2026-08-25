#!/usr/bin/env python3
import re
import sys
from pathlib import Path


NOMINAL = {
    "decay_QF_gradient": 0.973,
    "decay_QD_gradient": -1.85,
    "ch_q1_gradient": 0.874131397,
    "ch_q2_gradient": -0.700898219,
    "ch_q3_gradient": -0.784936358,
    "ch_q4_gradient": 1.59657119,
    "ch_q5_gradient": -0.784936358,
    "ch_q6_gradient": 1.17927583,
    "ch_q7_gradient": -1.11734632,
    "ch_q8_gradient": 0.299730689,
}


def main():
    if len(sys.argv) != 7:
        raise SystemExit(
            "usage: scale_decay_chicane.py path decay_qf_scale decay_qd_scale "
            "g12_scale g345_scale g678_scale"
        )
    path = Path(sys.argv[1])
    decay_qf_scale = float(sys.argv[2])
    decay_qd_scale = float(sys.argv[3])
    g12_scale = float(sys.argv[4])
    g345_scale = float(sys.argv[5])
    g678_scale = float(sys.argv[6])

    replacements = dict(NOMINAL)
    replacements["decay_QF_gradient"] *= decay_qf_scale
    replacements["decay_QD_gradient"] *= decay_qd_scale
    for name in ("ch_q1_gradient", "ch_q2_gradient"):
        replacements[name] *= g12_scale
    for name in ("ch_q3_gradient", "ch_q4_gradient", "ch_q5_gradient"):
        replacements[name] *= g345_scale
    for name in ("ch_q6_gradient", "ch_q7_gradient", "ch_q8_gradient"):
        replacements[name] *= g678_scale

    names = "|".join(re.escape(name) for name in replacements)
    pattern = re.compile(rf"^(param\s+)({names})(=.*)$")
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
