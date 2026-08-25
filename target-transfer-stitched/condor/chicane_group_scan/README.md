# Chicane Group Gradient Scan

This scan resamples `pi+` tracks from the z=2000 source CSV and transports them
through the downstream decay-channel/chicane model while scaling selected
chicane quadrupole groups.

Submit from this directory:

```bash
condor_submit submit_chicane_group_scan.sub
```

The default scan has 19 points with 1,000,000 transported `pi+` tracks per point.

After jobs finish:

```bash
python3 combine_chicane_group_scan.py
```

Primary hard-count metric:

```text
p_190_210_MeVc_r_le_20mm
```

Use `smooth_score_per_track` and the looser `r <= 50/75/100 mm` counts for
low-stat ranking before confirming the best points with higher statistics.
