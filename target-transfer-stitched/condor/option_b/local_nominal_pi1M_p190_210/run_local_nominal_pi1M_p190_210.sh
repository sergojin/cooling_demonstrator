#!/usr/bin/env bash
set -eo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="/uscms/homes/s/sergo/g4beamline/cooling_demonstrator"
SOURCE_CSV="${REPO_DIR}/target-transfer-stitched/condor/option_b/source_z2000/combined/source_z2000_pi_mu.csv"
MAKE_BEAM="${REPO_DIR}/target-transfer-stitched/condor/option_b/nominal_pi10M/make_resampled_beam.py"
DOWNSTREAM_INPUT="${REPO_DIR}/target-transfer-stitched/condor/option_b/nominal_pi10M/inputs/resample_downstream.g4bl"

N_EVENTS="${1:-1000000}"
SEED="${2:-240814}"

cd "${BASE_DIR}"
cp "${DOWNSTREAM_INPUT}" resample_downstream.g4bl

python3 "${MAKE_BEAM}" "${SOURCE_CSV}" beam.tmp \
    --n "${N_EVENTS}" --seed "${SEED}" --particle pi+

export SPACK_USER_CACHE_PATH="${SPACK_USER_CACHE_PATH:-/tmp/spack-cache-${USER}}"
mkdir -p "${SPACK_USER_CACHE_PATH}"
source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh
spack load g4beamline

/usr/bin/time -v g4bl resample_downstream.g4bl last_event="${N_EVENTS}" viewer=none \
    > g4bl.stdout 2> g4bl.stderr

python3 summarize_scoring_planes_p190_210.py
rm -f g4beamline.root
