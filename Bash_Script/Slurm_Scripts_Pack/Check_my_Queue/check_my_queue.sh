#!/usr/bin/env bash
# =============================================================================
# check_my_queue.sh
# -----------------------------------------------------------------------------
# Purpose:
#   Display the current user's SLURM jobs in a clean, compact table.
#
# Description:
#   - Uses the SLURM command 'squeue'
#   - Filters jobs by user
#   - Formats output into readable columns
#
# Usage:
#   bash check_my_queue.sh
#   bash check_my_queue.sh username
#
# Examples:
#   bash check_my_queue.sh
#   bash check_my_queue.sh soheil
#
# Notes:
#   - If no username is provided, the script uses the current system user ($USER)
#   - Requires SLURM to be installed and available (e.g., HPC clusters)
# =============================================================================

set -euo pipefail

# ---------------------------
# Read input argument
# ---------------------------
user_name="${1:-$USER}"

# ---------------------------
# Check if squeue exists
# ---------------------------
if ! command -v squeue >/dev/null 2>&1; then
    echo "Error: 'squeue' command not found."
    echo "Make sure SLURM is installed and loaded."
    exit 1
fi

# ---------------------------
# Print header (for clarity)
# ---------------------------
echo "SLURM Job Queue for user: ${user_name}"
echo "=============================================================="

# ---------------------------
# Run squeue with custom format
# ---------------------------
# Format explanation:
# %.18i  → Job ID
# %.10P  → Partition
# %.30j  → Job name
# %.8T   → Job state (RUNNING, PENDING, etc.)
# %.10M  → Time used
# %.6D   → Number of nodes
# %R     → Reason or node list

squeue -u "${user_name}" -o "%.18i %.10P %.30j %.8T %.10M %.6D %R"
