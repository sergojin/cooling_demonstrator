#!/usr/bin/env bash
set -eo pipefail

POINT_ID="${1:?point id is required}"
QF_GRADIENT="${2:?QF gradient is required}"
QD_GRADIENT="${3:?QD gradient is required}"
N_EVENTS="${4:-100000}"

if [[ -d "${PWD}/inputs" ]]; then
    BASE_DIR="${PWD}"
    if [[ -n "${_CONDOR_SCRATCH_DIR:-}" ]]; then
        RUN_PARENT="${BASE_DIR}"
    else
        RUN_PARENT="${BASE_DIR}/jobs"
    fi
else
    BASE_DIR="${CONDOR_BASE_DIR:-/uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor/quad_gradient_scan}"
    RUN_PARENT="${BASE_DIR}/jobs"
fi

RUN_DIR="${RUN_PARENT}/point_${POINT_ID}"
SEED=$((200000 + POINT_ID * 1009))

mkdir -p "${RUN_DIR}"
cd "${RUN_DIR}"

cp "${BASE_DIR}/inputs/"*.g4bl .

sed -i \
    -e "s/^param decay_QF_gradient=.*/param decay_QF_gradient=${QF_GRADIENT}/" \
    -e "s/^param decay_QD_gradient=.*/param decay_QD_gradient=${QD_GRADIENT}/" \
    stitched_target_decay_chicane.g4bl

{
    echo "randomseed now ${SEED}"
    echo "include stitched_target_decay_chicane.g4bl"
} > job_stitched_target_decay_chicane.g4bl

echo "point ${POINT_ID}: QF=${QF_GRADIENT} T/m QD=${QD_GRADIENT} T/m n_events=${N_EVENTS}"
echo "point ${POINT_ID}: run directory ${RUN_DIR}"

source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh
spack load g4beamline

g4bl job_stitched_target_decay_chicane.g4bl n_events="${N_EVENTS}" viewer=none > g4bl.stdout 2> g4bl.stderr
python3 "${BASE_DIR}/summarize_job.py" "${RUN_DIR}/stitched_output.txt" "${RUN_DIR}/job_summary.txt" "${POINT_ID}" "${N_EVENTS}"

{
    echo "point_id ${POINT_ID}"
    echo "qf_gradient ${QF_GRADIENT}"
    echo "qd_gradient ${QD_GRADIENT}"
    echo "n_events ${N_EVENTS}"
} > scan_point.txt

rm -f "${RUN_DIR}/g4beamline.root"
