#!/usr/bin/env bash
set -eo pipefail

JOB_ID="${1:?job id is required}"
N_EVENTS="${2:-10000}"

BASE_DIR="/uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor"
RUN_DIR="${BASE_DIR}/rescue/job_${JOB_ID}"
SEED=$((200000 + JOB_ID * 1009))

mkdir -p "${RUN_DIR}"
cd "${RUN_DIR}"

cp "${BASE_DIR}/inputs/"*.g4bl .

{
    echo "randomseed now ${SEED}"
    echo "include stitched_target_decay_chicane.g4bl"
} > job_stitched_target_decay_chicane.g4bl

source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh
spack load g4beamline

g4bl job_stitched_target_decay_chicane.g4bl n_events="${N_EVENTS}" viewer=none > g4bl.stdout 2> g4bl.stderr
python3 "${BASE_DIR}/summarize_job.py" "${RUN_DIR}/stitched_output.txt" "${RUN_DIR}/job_summary.txt" "${JOB_ID}" "${N_EVENTS}"
