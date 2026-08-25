#!/usr/bin/env bash
set -eo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_CSV="${BASE_DIR}/../source_z2000/combined/source_z2000_pi_mu.csv"
N_EVENTS=1000000
SEED=4600000

cd "${BASE_DIR}"

python3 make_resampled_beam_p0_400.py "${SOURCE_CSV}" beam.tmp \
    --n "${N_EVENTS}" --seed "${SEED}" --p-min-mev 0 --p-max-mev 400

export SPACK_USER_CACHE_PATH="${SPACK_USER_CACHE_PATH:-/tmp/spack-cache-${USER}}"
mkdir -p "${SPACK_USER_CACHE_PATH}"
source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh
spack load g4beamline

/usr/bin/time -v g4bl resample_downstream.g4bl last_event="${N_EVENTS}" viewer=none \
    > g4bl.stdout 2> g4bl.stderr

python3 summarize_nominal_job.py "${BASE_DIR}" 0 "${N_EVENTS}"

rm -f g4beamline.root beam.tmp
