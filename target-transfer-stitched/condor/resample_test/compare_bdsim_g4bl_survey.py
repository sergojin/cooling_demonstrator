#!/usr/bin/env python3
import math
import re
import sys
from pathlib import Path


START_Z = 2000.0
DECAY_START = 2000.0
CHICANE_START = 11300.0
R_BEND = 1685.1699856788916
ANGLE_DEG = -34.0


def advance_straight(state, length):
    x, z, yaw = state
    a = math.radians(yaw)
    return x + length * math.sin(a), z + length * math.cos(a), yaw


def advance_bend(state, length, angle_deg):
    x, z, yaw = state
    theta = math.radians(angle_deg)
    yaw0 = math.radians(yaw)
    radius = length / abs(theta)
    sign = 1.0 if theta >= 0 else -1.0
    dx_local = sign * radius * (1.0 - math.cos(abs(theta)))
    dz_local = radius * math.sin(abs(theta))
    x_new = x + dx_local * math.cos(yaw0) + dz_local * math.sin(yaw0)
    z_new = z - dx_local * math.sin(yaw0) + dz_local * math.cos(yaw0)
    return x_new, z_new, yaw + angle_deg


def element_center(state, length, kind):
    if kind == "bend":
        return advance_bend(state, length / 2.0, ANGLE_DEG / 2.0)
    return advance_straight(state, length / 2.0)


def element_back(state, length, kind):
    if kind == "bend":
        return advance_bend(state, length, ANGLE_DEG)
    return advance_straight(state, length)


def decay_elements():
    cell = [
        ("o1", "drift", 400),
        ("QF1", "quad", 500),
        ("o2", "drift", 400),
        ("QD", "quad", 500),
        ("o3", "drift", 400),
        ("QF2", "quad", 500),
        ("o4", "drift", 400),
    ]
    out = []
    for i in range(1, 4):
        for name, kind, length in cell:
            out.append((f"{name}_{i}", kind, length))
    return out


def chicane_elements():
    return [
        ("ch_q1", "quad", 500),
        ("d_500_a", "drift", 500),
        ("ch_q2", "quad", 500),
        ("d_500_b", "drift", 500),
        ("s_dp_1", "bend", 1000),
        ("d_1000_a", "drift", 1000),
        ("ch_q3", "quad", 500),
        ("d_500_c", "drift", 500),
        ("ch_q4", "quad", 500),
        ("d_500_d", "drift", 500),
        ("ch_q5", "quad", 500),
        ("d_1000_b", "drift", 1000),
        ("s_dp_2", "bend", 1000),
        ("d_500_e", "drift", 500),
        ("ch_q6", "quad", 500),
        ("d_500_f", "drift", 500),
        ("ch_q7", "quad", 500),
        ("d_500_g", "drift", 500),
        ("ch_q8", "quad", 500),
        ("d_500_h", "drift", 500),
    ]


def survey(elements, start_z):
    rows = []
    state = (0.0, start_z, 0.0)
    s = start_z
    for name, kind, length in elements:
        front = state
        center = element_center(state, length, kind)
        back = element_back(state, length, kind)
        construct_z = front[1] if kind == "bend" else center[1]
        rows.append(
            {
                "name": name,
                "kind": kind,
                "length": length,
                "s_front": s,
                "s_center": s + length / 2.0,
                "s_back": s + length,
                "x_center": center[0],
                "z_center": center[1],
                "yaw_center": center[2],
                "expected_g4bl_construct_z": construct_z,
            }
        )
        state = back
        s += length
    return rows


def parse_g4bl_construct(log_path):
    if not log_path or not log_path.exists():
        return {}
    pattern = re.compile(r"BLCMDgeneric(?:quad|sectorbend)::Construct ([^ ]+) .* relZ=([0-9.+-]+) globZ=([0-9.+-]+)")
    values = {}
    with log_path.open() as f:
        for line in f:
            match = pattern.search(line)
            if match:
                values[match.group(1)] = (float(match.group(2)), float(match.group(3)))
    return values


def print_rows(title, rows, g4bl):
    print(title)
    print("name,kind,L_mm,s_center_mm,x_center_mm,z_center_mm,yaw_deg,expected_construct_z_mm,g4bl_relZ_mm,g4bl_globZ_mm,dRelZ_mm")
    for row in rows:
        if row["kind"] not in ("quad", "bend"):
            continue
        g4name = row["name"]
        if g4name == "s_dp_1":
            g4name = "chicane_bend_1"
        elif g4name == "s_dp_2":
            g4name = "chicane_bend_2"
        elif g4name.startswith("QF1_"):
            g4name = "decay_QF1_" + g4name.rsplit("_", 1)[1]
        elif g4name.startswith("QF2_"):
            g4name = "decay_QF2_" + g4name.rsplit("_", 1)[1]
        elif g4name.startswith("QD_"):
            g4name = "decay_QD_" + g4name.rsplit("_", 1)[1]
        g4 = g4bl.get(g4name)
        relz = globz = None
        if g4:
            relz, globz = g4
        dz = "" if relz is None else f"{relz - row['expected_g4bl_construct_z']:.3f}"
        print(
            f"{row['name']},{row['kind']},{row['length']:.0f},{row['s_center']:.3f},"
            f"{row['x_center']:.3f},{row['z_center']:.3f},{row['yaw_center']:.3f},"
            f"{row['expected_g4bl_construct_z']:.3f},"
            f"{'' if relz is None else f'{relz:.3f}'},"
            f"{'' if globz is None else f'{globz:.3f}'},{dz}"
        )
    print()


def main():
    log_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    g4bl = parse_g4bl_construct(log_path)
    decay = survey(decay_elements(), DECAY_START)
    chicane = survey(chicane_elements(), CHICANE_START)
    print_rows("Decay channel survey", decay, g4bl)
    print_rows("Chicane survey", chicane, g4bl)


if __name__ == "__main__":
    main()
