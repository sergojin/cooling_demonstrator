#!/usr/bin/env bash
set -eo pipefail

JOB_ID="${1:?job id is required}"
N_EVENTS="${2:-100000}"

if [[ -d "${PWD}/inputs" ]]; then
    BASE_DIR="${PWD}"
else
    BASE_DIR="${CONDOR_BASE_DIR:-/uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor/option_b/source_z2000}"
fi

RUN_DIR="${BASE_DIR}/rescue_job_${JOB_ID}"
SEED=$((1300000 + JOB_ID * 1009))

mkdir -p "${RUN_DIR}"
cd "${RUN_DIR}"

cleanup() {
    rm -f "${RUN_DIR}/g4beamline.root"
}
trap cleanup EXIT

cp "${BASE_DIR}/inputs/"*.g4bl .

{
    echo "randomseed now ${SEED}"
    echo "include target_capture_source_option_b.g4bl"
} > job_target_capture_source.g4bl

echo "option B rescue source job ${JOB_ID}: n_events=${N_EVENTS}"
echo "source job ${JOB_ID}: seed=${SEED}"
echo "source job ${JOB_ID}: run directory ${RUN_DIR}"

export SPACK_USER_CACHE_PATH="${SPACK_USER_CACHE_PATH:-/tmp/spack-cache-${USER}}"
mkdir -p "${SPACK_USER_CACHE_PATH}"
source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh
spack load g4beamline

g4bl job_target_capture_source.g4bl n_events="${N_EVENTS}" viewer=none > g4bl.stdout 2> g4bl.stderr
python3 "${BASE_DIR}/summarize_source_job.py" "${RUN_DIR}/source_z2000.txt" "${RUN_DIR}/source_summary.txt" "${JOB_ID}" "${N_EVENTS}"
