#!/bin/bash
###################################################################################################
# Written by: Soheil Jamali
# Email: sjamali@uark.edu, soheil.jamali.dev@gmail.com
# University of Arkansas
#
# Description:
#   This script automates the submission of SLURM jobs across selected simulation folders.
#   It is important to have the folders named simulation_1, simulation_2, ..., simulation_N.
#   The user can either:
#       1. Provide a range of folder numbers (e.g. 1 10 → simulation_1 to simulation_10), or
#       2. Provide a custom list of folder numbers (e.g. 3 5 7 12)
#
#   The script then checks if a `slurm.sh` file exists in each folder's `src` directory.
#   If it exists, the script submits it using `sbatch`. Otherwise, it prints a warning.
#
# Usage:
#   1. Make the script executable:
#         chmod +x run_selected_folders.sh
#
#   2. Run with a range:
#         ./run_selected_folders.sh range 1 10
#
#   3. Run with a custom list:
#         ./run_selected_folders.sh list 3 5 7 12
#
# Notes:
#   - Ensure you run this script from the parent directory containing all simulation folders.
#   - Requires SLURM (`sbatch`) to be available in your environment.
#
###################################################################################################

# Get base directory
BASE_DIR=$(pwd)

# Function to submit jobs for given folder numbers
submit_jobs() {
    for i in "$@"; do
        SIM_DIR="${BASE_DIR}/simulation_${i}/src"

        if [ -f "${SIM_DIR}/slurm.sh" ]; then
            echo "✅ Submitting slurm.sh in simulation_${i}/src"
            (cd "$SIM_DIR" && sbatch slurm.sh)
        else
            echo "⚠️  slurm.sh not found in simulation_${i}/src"
        fi
    done
}

# Check input arguments
if [ "$1" == "range" ] && [ $# -eq 3 ]; then
    # Example: ./run_selected_folders.sh range 1 10
    start=$2
    end=$3
    submit_jobs $(seq $start $end)

elif [ "$1" == "list" ] && [ $# -ge 2 ]; then
    # Example: ./run_selected_folders.sh list 3 5 7 12
    shift
    submit_jobs "$@"

else
    echo "Usage:"
    echo "  $0 range <start> <end>      # Run for a range of folders"
    echo "  $0 list <n1> <n2> ...       # Run for a custom list of folders"
    exit 1
fi

echo "🎯 Job submission completed."
