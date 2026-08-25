# Option B Downstream Studies

This directory is the active workspace for Horn Option B studies.

The first stage is `source_z2000`, which mirrors the previous Option A source
sample production:

- run G4Beamline from protons on target through the Option B target/horn;
- score `pi+` and `mu+` tracks at `z = 2000 mm` inside `r < 200 mm`;
- combine the per-job `source_z2000.txt` files into `combined/source_z2000_pi_mu.csv`;
- use that CSV as the resampling source for downstream decay-channel/chicane
  studies.

Submit the initial 1M proton sample with:

```bash
cd /uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor/option_b/source_z2000
condor_submit submit_source_z2000.sub
```

After jobs finish:

```bash
python3 combine_source.py
```
