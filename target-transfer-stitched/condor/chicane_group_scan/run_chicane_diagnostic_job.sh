#!/usr/bin/env bash
set -eo pipefail

POINT_ID="${1:?point id is required}"
CONFIG="${2:?config is required}"
G12_SCALE="${3:?G12 scale is required}"
G678_SCALE="${4:?G678 scale is required}"
N_EVENTS="${5:-1000000}"
PARTICLE="${6:-pi+}"
SEED_BASE="${7:-1600000}"
RUN_LABEL="${8:-manual_diag}"

if [[ -d "${PWD}/inputs" ]]; then
    BASE_DIR="${PWD}"
    RUN_PARENT="${BASE_DIR}/jobs"
else
    BASE_DIR="${CONDOR_BASE_DIR:-/uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor/chicane_group_scan}"
    RUN_PARENT="${BASE_DIR}/jobs"
fi

RUN_DIR="${RUN_PARENT}/${RUN_LABEL}_diag_${POINT_ID}"
SEED=$((SEED_BASE + POINT_ID * 1009))

if [[ -f "${BASE_DIR}/source_z2000_pi_mu.csv" ]]; then
    SOURCE_CSV="${BASE_DIR}/source_z2000_pi_mu.csv"
else
    SOURCE_CSV="${BASE_DIR}/../source_z2000/combined/source_z2000_pi_mu.csv"
fi

mkdir -p "${RUN_DIR}"
cp "${BASE_DIR}/inputs/resample_downstream.g4bl" "${RUN_DIR}/"

cleanup() {
    rm -f "${RUN_DIR}/g4beamline.root" "${RUN_DIR}/beam.tmp"
    find "${RUN_DIR}" -maxdepth 1 -name 'score_z*.txt' -delete
}
trap cleanup EXIT

if [[ "${CONFIG}" != "nominal" ]]; then
    python3 "${BASE_DIR}/scale_chicane_combo.py" \
        "${RUN_DIR}/resample_downstream.g4bl" "${G12_SCALE}" "${G678_SCALE}"
fi

echo "diagnostic point ${POINT_ID}: config=${CONFIG} G12_scale=${G12_SCALE} G678_scale=${G678_SCALE} n_events=${N_EVENTS}"
echo "diagnostic point ${POINT_ID}: particle=${PARTICLE}"
echo "diagnostic point ${POINT_ID}: seed=${SEED}"
echo "diagnostic point ${POINT_ID}: source=${SOURCE_CSV}"
echo "diagnostic point ${POINT_ID}: run directory ${RUN_DIR}"

python3 "${BASE_DIR}/make_resampled_beam.py" "${SOURCE_CSV}" "${RUN_DIR}/beam.tmp" \
    --n "${N_EVENTS}" --seed "${SEED}" --particle "${PARTICLE}"

cd "${RUN_DIR}"

source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh
spack load g4beamline

/usr/bin/time -v g4bl resample_downstream.g4bl last_event="${N_EVENTS}" viewer=none \
    > g4bl.stdout 2> g4bl.stderr

python3 "${BASE_DIR}/summarize_chicane_diagnostic.py" "${RUN_DIR}" "${POINT_ID}" "${CONFIG}" "${G12_SCALE}" "${G678_SCALE}" "${N_EVENTS}"
