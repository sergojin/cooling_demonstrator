# target-transfer-stitched

Prototype G4Beamline stitching of:

1. the approximate FLUKA baseline A target/capture conversion;
2. the BDSIM `DemoPionDecayChannel.gmad` triplet decay channel;
3. the BDSIM `DemoChicane_CTF3.gmad` transfer/chicane line.

Run from this directory with:

```bash
source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh
spack load g4beamline
g4bl stitched_target_decay_chicane.g4bl n_events=10 viewer=none
```

Notes:

- `target_capture_stage.g4bl` is a copied local snapshot of `chicane/g4bl/target_capture_baseline_A.g4bl`.
- The decay-channel quadrupole strengths use the BDSIM `k1` values converted to G4BL gradients at `270/1.15 MeV/c`, including the BDSIM `scaling=1.15`.
- The chicane quadrupole and bend strengths use the BDSIM values converted at `200 MeV/c`.
- This is a structural prototype, not a validated BDSIM/FLUKA-equivalent model.
- It is currently one continuous G4BL job, so all produced particles continue into the downstream lattice unless they are absorbed or lost.
- `stitched_output.txt` records the target/capture handoff plane at `z=2000 mm` and the prototype end at `z=23300 mm`.
