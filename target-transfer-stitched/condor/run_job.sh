#!/usr/bin/env bash
set -eo pipefail

JOB_ID="${1:?job id is required}"
N_EVENTS="${2:-10000}"

if [[ -d "${PWD}/inputs" ]]; then
    BASE_DIR="${PWD}"
    RUN_PARENT="${BASE_DIR}"
else
    BASE_DIR="${CONDOR_BASE_DIR:-/uscms/homes/s/sergo/g4beamline/cooling_demonstrator/target-transfer-stitched/condor}"
    RUN_PARENT="${BASE_DIR}/jobs"
fi

RUN_DIR="${RUN_PARENT}/job_${JOB_ID}"
SEED=$((100000 + JOB_ID * 1009))

mkdir -p "${RUN_DIR}"
cd "${RUN_DIR}"

cp "${BASE_DIR}/inputs/"*.g4bl .

{
    echo "randomseed now ${SEED}"
    echo "include stitched_target_decay_chicane.g4bl"
} > job_stitched_target_decay_chicane.g4bl

echo "job ${JOB_ID}: starting in ${PWD}"
echo "job ${JOB_ID}: run directory ${RUN_DIR}"

source /cvmfs/mu2e.opensciencegrid.org/spackages/241207/spack/setup-env.sh
echo "job ${JOB_ID}: sourced spack setup-env.sh"
spack load g4beamline
echo "job ${JOB_ID}: loaded g4beamline from $(command -v g4bl)"

g4bl job_stitched_target_decay_chicane.g4bl n_events="${N_EVENTS}" viewer=none > g4bl.stdout 2> g4bl.stderr
echo "job ${JOB_ID}: g4bl finished"

python3 "${BASE_DIR}/summarize_job.py" "${RUN_DIR}/stitched_output.txt" "${RUN_DIR}/job_summary.txt" "${JOB_ID}" "${N_EVENTS}"
echo "job ${JOB_ID}: summary finished"

# Keep the ASCII scoring output for later resampling studies; the ROOT file
# is not needed by the current downstream scripts.
rm -f "${RUN_DIR}/g4beamline.root"
