#!/usr/bin/env bash
# =============================================================================
# slurm_array_job_template.sh
# -----------------------------------------------------------------------------
# Purpose:
#   Submit many similar jobs using a SLURM job array.
#
# Description:
#   This script is a generic SLURM array-job template for HPC systems that use
#   the SLURM workload manager.
#
#   A job array lets you run the same workflow many times, where each task uses
#   a different input item. This is useful for:
#     - processing many files
#     - running many simulations
#     - parameter sweeps
#     - batch data analysis
#
# Important:
#   The SLURM settings in this file are examples. Different HPC systems may use
#   different partition names, account names, memory policies, or time limits.
#   Always check your cluster documentation before submitting.
#
# Usage:
#   1. Edit the SBATCH settings for your HPC system
#   2. Replace the example input list with your real inputs
#   3. Replace the example command with your actual workflow
#   4. Submit with:
#
#        sbatch slurm_array_job_template.sh
#
# Example:
#   If you have 10 files and want one task per file, use:
#     #SBATCH --array=0-9
#
# =============================================================================

#SBATCH --job-name=array_job
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err

# Example resource requests.
# These values depend on your HPC system and workflow.
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G

# Example partition/queue name.
# Replace with a valid partition on your HPC system.
#SBATCH --partition=compute

# Example array range: 10 tasks with IDs 0 through 9.
#SBATCH --array=0-9

# Example account line.
# Uncomment and replace if your HPC system requires an account/allocation.
##SBATCH --account=REPLACE_WITH_YOUR_ACCOUNT

set -euo pipefail

# Create a folder for SLURM output/error logs.
mkdir -p logs

# -----------------------------------------------------------------------------
# Example input list
# -----------------------------------------------------------------------------
# Replace this with your real inputs.
# Each array task will use one element from this list.
inputs=(
    input_0.txt
    input_1.txt
    input_2.txt
    input_3.txt
    input_4.txt
    input_5.txt
    input_6.txt
    input_7.txt
    input_8.txt
    input_9.txt
)

# Select the input that belongs to the current array task.
current_input="${inputs[$SLURM_ARRAY_TASK_ID]}"

echo "============================================================"
echo "SLURM job ID        : ${SLURM_JOB_ID:-N/A}"
echo "SLURM array job ID  : ${SLURM_ARRAY_JOB_ID:-N/A}"
echo "SLURM task ID       : ${SLURM_ARRAY_TASK_ID:-N/A}"
echo "Current input       : ${current_input}"
echo "Running on host     : $(hostname)"
echo "Start time          : $(date)"
echo "============================================================"

# -----------------------------------------------------------------------------
# Example workflow command
# -----------------------------------------------------------------------------
# Replace the line below with your actual workflow.
echo "Pretend processing ${current_input}"

# Example real command:
# python process_one_file.py --input "${current_input}"

echo "Finished at: $(date)"
