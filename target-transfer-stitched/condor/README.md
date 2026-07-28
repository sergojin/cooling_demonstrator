# Stitched Beamline Condor Run

This folder is self-contained for the stitched target/capture plus decay-channel plus chicane test.

Submit:

```bash
cd /uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor
condor_submit submit_stitched.sub
```

Each of the 20 jobs runs 10000 protons. Per-job outputs are written under `jobs/job_N/`.

After all jobs finish, combine outputs and make plots:

```bash
cd /uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor
python3 combine_and_plot.py
```

Combined tables are written under `combined/`; plots are written under `plots/`.

`stitched_output.txt` is retained in each returned `job_N/` directory. Its
`Z2000` ntuple is the all-supported-particle horn-exit sample for downstream
resampling studies.
