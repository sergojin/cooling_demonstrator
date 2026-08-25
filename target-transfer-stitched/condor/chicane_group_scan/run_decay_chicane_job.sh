#!/usr/bin/env bash
set -eo pipefail

POINT_ID="${1:?point id is required}"
GROUP_NAME="${2:?group name is required}"
DECAY_QF_SCALE="${3:?decay QF scale is required}"
DECAY_QD_SCALE="${4:?decay QD scale is required}"
G12_SCALE="${5:?G12 scale is required}"
G345_SCALE="${6:?G345 scale is required}"
G678_SCALE="${7:?G678 scale is required}"
N_EVENTS="${8:-1000000}"
PARTICLE="${9:-pi+}"
SEED_BASE="${10:-3000000}"
RUN_LABEL="${11:-manual_decay_chicane}"

if [[ -d "${PWD}/inputs" ]]; then
    BASE_DIR="${PWD}"
    RUN_PARENT="${BASE_DIR}/jobs"
else
    BASE_DIR="${CONDOR_BASE_DIR:-/uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor/chicane_group_scan}"
    RUN_PARENT="${BASE_DIR}/jobs"
fi

RUN_DIR="${RUN_PARENT}/${RUN_LABEL}_point_${POINT_ID}"
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
    find "${RUN_DIR}" -maxdepth 1 -name 'score_z*.txt' ! -name 'score_z23300.txt' -delete
}
trap cleanup EXIT

python3 "${BASE_DIR}/scale_decay_chicane.py" \
    "${RUN_DIR}/resample_downstream.g4bl" \
    "${DECAY_QF_SCALE}" "${DECAY_QD_SCALE}" \
    "${G12_SCALE}" "${G345_SCALE}" "${G678_SCALE}"

echo "point ${POINT_ID}: group=${GROUP_NAME} decay_QF_scale=${DECAY_QF_SCALE} decay_QD_scale=${DECAY_QD_SCALE} G12_scale=${G12_SCALE} G345_scale=${G345_SCALE} G678_scale=${G678_SCALE} n_events=${N_EVENTS}"
echo "point ${POINT_ID}: particle=${PARTICLE}"
echo "point ${POINT_ID}: seed=${SEED}"
echo "point ${POINT_ID}: source=${SOURCE_CSV}"
echo "point ${POINT_ID}: run directory ${RUN_DIR}"

python3 "${BASE_DIR}/make_resampled_beam.py" "${SOURCE_CSV}" "${RUN_DIR}/beam.tmp" \
    --n "${N_EVENTS}" --seed "${SEED}" --particle "${PARTICLE}"

cd "${RUN_DIR}"

source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh
spack load g4beamline

/usr/bin/time -v g4bl resample_downstream.g4bl last_event="${N_EVENTS}" viewer=none \
    > g4bl.stdout 2> g4bl.stderr

python3 "${BASE_DIR}/summarize_chicane_group_job.py" \
    "${RUN_DIR}" "${POINT_ID}" "${GROUP_NAME}" \
    "${DECAY_QF_SCALE}_${DECAY_QD_SCALE}_${G12_SCALE}_${G345_SCALE}_${G678_SCALE}" "${N_EVENTS}"
