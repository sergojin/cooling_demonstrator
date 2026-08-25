# Chicane Surrogate Optimizer

This directory contains a lightweight surrogate-model loop for proposing the
next chicane-gradient scan points from existing summary CSVs.

The first version uses three grouped knobs:

- `G12_scale`: `ch_q1`, `ch_q2`
- `G345_scale`: `ch_q3`, `ch_q4`, `ch_q5`
- `G678_scale`: `ch_q6`, `ch_q7`, `ch_q8`

Rows from single-group scans, nominal scans, `GALL`, and `G12_G678` combo scans
are mapped onto those three features. Untouched groups are assigned scale `1.0`.

Example:

```bash
cd /uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched
python3 condor/surrogate_opt/propose_chicane_points.py \
  condor/chicane_group_scan/combined/chicane_group_scan_summary.csv \
  condor/chicane_group_scan/combined/chicane_highstat_summary_3752733.csv \
  condor/chicane_group_scan/combined/chicane_highstat_summary_3752962.csv \
  condor/chicane_group_scan/combined/chicane_highstat_summary_3753417.csv
```

To write a Condor point file for the existing G12/G678 combo runner:

```bash
python3 condor/surrogate_opt/propose_chicane_points.py \
  condor/chicane_group_scan/combined/chicane_group_scan_summary.csv \
  condor/chicane_group_scan/combined/chicane_highstat_summary_3753417.csv \
  --fix-g345 1.0 \
  --write-combo-points condor/chicane_group_scan/surrogate_g12_g678_points.txt \
  --point-id-start 14000
```

Default target is now `phase_ellipse_yield_per_track`: final `mu+` in the
`190-210 MeV/c` momentum window, then accepted if the track lies inside both
the fitted `x-x'` and `y-y'` 2 mm rad RMS phase-space ellipses. Older CSVs
without this column are skipped by the proposer.

`scikit-learn` is installed locally in `condor/surrogate_opt/python_packages`.
The proposer script adds that directory to `sys.path` automatically.

To visualize a 2D surrogate slice:

```bash
python3 condor/surrogate_opt/plot_chicane_surrogate.py \
  condor/chicane_group_scan/combined/chicane_group_scan_summary.csv \
  condor/chicane_group_scan/combined/chicane_highstat_summary_3752733.csv \
  condor/chicane_group_scan/combined/chicane_highstat_summary_3752962.csv \
  condor/chicane_group_scan/combined/chicane_highstat_summary_3753417.csv \
  --pair G12,G678 \
  --fixed-g345 1.0 \
  --output condor/surrogate_opt/surrogate_g12_g678.png
```

The plot has two panels: predicted target and model spread. The overlaid dots
are the simulated configurations used for training.
