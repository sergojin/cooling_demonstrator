# Validated chicane lattice pair (P0)

These are the paired G4Beamline configurations used for the corrected
one-million-pion comparison:

- `same_sign/ideal_expanded_full/lattice.g4bl`
- `opposite/ideal_expanded_full/lattice.g4bl`

Both use `idealsectorbend` instead of the earlier `genericsectorbend` field
model and explicitly expand the simulation world. The lattice files differ
only in bend 2's angle and vertical field sign. Q3–Q5 response-test lattices
elsewhere under `field_correction/` are exploratory and are **not** replacements
for this validated pair.

The two files are exact archived run inputs. Their `beam ascii file=...` line
points to a local, absolute path for `chicane_p0/full_beam.txt`. The 63 MB
beam file and larger scoring outputs are **not** included in this Git commit.
To run the lattices elsewhere, provide that same input beam (SHA-256 and
selection documented in `../full_manifest.json`) and update the beam path in
a *copy* of each lattice. The sample contains one million resampled pi+ at
z=2000 mm with total momentum 0–400 MeV/c. The source CSV is likewise not
included in this commit.

For the 190–210 MeV/c mu+ endpoint window, the paired run gave 64 same-sign
and 63 opposite-sign muons within r<=200 mm and the same fixed 2 mm-rad
x/x' and y/y' ellipses. The fixed ellipse is recorded in
`../q678/acceptance.json`, and the complete counts are in
`full_comparison.json`. The one-muon difference is not statistically
significant. This archive does not assert equivalence to the BDSIM model.
