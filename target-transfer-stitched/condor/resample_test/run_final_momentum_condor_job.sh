#!/usr/bin/env bash
set -eo pipefail

JOB_ID="${1:?job id is required}"
N_EVENTS="${2:-100000}"
PARTICLE="${3:-pi+}"
SEED_BASE="${4:-800000}"
RUN_PREFIX="${5:-finalmom_job}"

if [[ -d "${PWD}/inputs" ]]; then
    BASE_DIR="${PWD}"
else
    BASE_DIR="${CONDOR_BASE_DIR:-/uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor/resample_test}"
fi

RUN_DIR="${BASE_DIR}/${RUN_PREFIX}_${JOB_ID}"
SEED=$((SEED_BASE + JOB_ID * 1009))

if [[ -f "${BASE_DIR}/source_z2000_pi_mu.csv" ]]; then
    SOURCE_CSV="${BASE_DIR}/source_z2000_pi_mu.csv"
else
    SOURCE_CSV="${BASE_DIR}/../source_z2000/combined/source_z2000_pi_mu.csv"
fi

mkdir -p "${RUN_DIR}"
cp "${BASE_DIR}/inputs/resample_downstream.g4bl" "${RUN_DIR}/"

echo "final momentum job ${JOB_ID}: n_events=${N_EVENTS}"
echo "final momentum job ${JOB_ID}: particle=${PARTICLE}"
echo "final momentum job ${JOB_ID}: seed=${SEED}"
echo "final momentum job ${JOB_ID}: source=${SOURCE_CSV}"
echo "final momentum job ${JOB_ID}: run directory ${RUN_DIR}"

python3 "${BASE_DIR}/make_resampled_beam.py" "${SOURCE_CSV}" "${RUN_DIR}/beam.tmp" \
    --n "${N_EVENTS}" --seed "${SEED}" --particle "${PARTICLE}"

cd "${RUN_DIR}"

source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh
spack load g4beamline

/usr/bin/time -v g4bl resample_downstream.g4bl last_event="${N_EVENTS}" viewer=none \
    > g4bl.stdout 2> g4bl.stderr

python3 "${BASE_DIR}/summarize_resample.py" "${RUN_DIR}"

rm -f "${RUN_DIR}/g4beamline.root" "${RUN_DIR}/beam.tmp"
find "${RUN_DIR}" -maxdepth 1 -name 'score_z*.txt' ! -name 'score_z23300.txt' -delete
