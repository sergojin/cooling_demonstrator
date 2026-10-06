# Chicane surrogate-model example

This directory contains the restored [student guide](STUDENT_SURROGATE_GUIDE.txt)
and two reusable scripts:

- `propose_chicane_points.py` reads compatible simulation-summary CSVs,
  trains a surrogate, and proposes new parameter points.
- `plot_chicane_surrogate.py` plots a two-parameter slice of that surrogate.

Install NumPy, scikit-learn, and Matplotlib in a virtual environment; see
the guide for commands and CSV requirements. The scripts do **not** run
G4Beamline or submit Condor jobs. The former `chicane_group_scan` runner and
its outputs were removed, so examples referencing that runner are historical.

Do not pool its old results with corrected chicane runs: the old
`genericsectorbend` field model had an overlap artifact. Train only on
results with consistent field geometry, source sample, and acceptance metric.
