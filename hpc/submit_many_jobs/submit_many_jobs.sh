#!/usr/bin/env bash
# =============================================================================
# submit_many_jobs.sh
# -----------------------------------------------------------------------------
# Purpose:
#   Submit all SLURM job scripts inside a given folder.
#
# Description:
#   - Finds all .slurm and .sh files in a directory
#   - Submits each one using the 'sbatch' command
#   - Counts how many jobs were submitted
#
# Usage:
#   bash submit_many_jobs.sh path/to/jobs_folder
#
# Examples:
#   bash submit_many_jobs.sh jobs/
#   bash submit_many_jobs.sh ./slurm_scripts
#
# Notes:
#   - Requires SLURM (sbatch command must be available)
#   - Only looks at files in the specified folder (not recursive)
# =============================================================================

set -euo pipefail

# ---------------------------
# Read input argument
# ---------------------------
jobs_dir="${1:-}"

# ---------------------------
# Show usage if missing input
# ---------------------------
show_usage() {
    cat <<EOF
Usage:
  bash submit_many_jobs.sh path/to/jobs_folder

Description:
  Submit all .slurm and .sh job files inside a folder using sbatch.
EOF
}

if [[ -z "${jobs_dir}" ]]; then
    echo "Error: missing jobs folder."
    echo
    show_usage
    exit 1
fi

# ---------------------------
# Validate folder
# ---------------------------
if [[ ! -d "${jobs_dir}" ]]; then
    echo "Error: folder does not exist: ${jobs_dir}"
    exit 1
fi

# ---------------------------
# Check if sbatch exists
# ---------------------------
if ! command -v sbatch >/dev/null 2>&1; then
    echo "Error: 'sbatch' command not found."
    echo "Make sure you are on an HPC system with SLURM loaded."
    exit 1
fi

# ---------------------------
# Submit jobs
# ---------------------------
count=0

# Enable safe globbing (no errors if no files found)
shopt -s nullglob

for file in "${jobs_dir}"/*.slurm "${jobs_dir}"/*.sh; do
    echo "--------------------------------------------------"
    echo "Submitting: ${file}"

    sbatch "${file}"

    count=$((count + 1))
done

# ---------------------------
# Final summary
# ---------------------------
echo "=================================================="

if [[ ${count} -eq 0 ]]; then
    echo "No .slurm or .sh files found in: ${jobs_dir}"
else
    echo "Successfully submitted ${count} job(s)."
fi
