#!/usr/bin/env bash
set -eo pipefail

JOB_ID="${1:?job id is required}"
N_EVENTS="${2:-100000}"

if [[ -d "${PWD}/inputs" ]]; then
    BASE_DIR="${PWD}"
else
    BASE_DIR="${CONDOR_BASE_DIR:-/uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor/source_z2000}"
fi

RUN_DIR="${BASE_DIR}/job_${JOB_ID}"
SEED=$((300000 + JOB_ID * 1009))

mkdir -p "${RUN_DIR}"
cd "${RUN_DIR}"

cp "${BASE_DIR}/inputs/"*.g4bl .

{
    echo "randomseed now ${SEED}"
    echo "include target_capture_source.g4bl"
} > job_target_capture_source.g4bl

echo "source job ${JOB_ID}: n_events=${N_EVENTS}"
echo "source job ${JOB_ID}: run directory ${RUN_DIR}"

source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh
spack load g4beamline

g4bl job_target_capture_source.g4bl n_events="${N_EVENTS}" viewer=none > g4bl.stdout 2> g4bl.stderr
python3 "${BASE_DIR}/summarize_source_job.py" "${RUN_DIR}/source_z2000.txt" "${RUN_DIR}/source_summary.txt" "${JOB_ID}" "${N_EVENTS}"

rm -f "${RUN_DIR}/g4beamline.root"
