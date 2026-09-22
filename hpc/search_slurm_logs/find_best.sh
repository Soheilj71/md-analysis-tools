#!/bin/bash
# Written by: Soheil Jamali
# Email: sjamali@uark.edu, soheil.jamali.dev@gmail.com
#
# Description:
# This script searches for a specific keyword (e.g., "best", "error", "converged") 
# inside slurm-*.out files located in the `src` folder of every subdirectory.
# You can change:
#   1. The SEARCH_TERM variable to search for a different word
#   2. The SLURM_PATTERN if your SLURM files use a different naming pattern
#   3. The SUBFOLDER if your files are in a different subfolder (e.g., "output" instead of "src")

# ======= USER SETTINGS =======
SEARCH_TERM="best"               # <-- change this to the word you're looking for
SLURM_PATTERN="slurm-*.out"      # <-- change this to match your SLURM file pattern
SUBFOLDER="src"                  # <-- change this if files are not inside 'src'
OUTPUT_FILE="result.txt"         # <-- name of the output summary file
# =============================

# Clear previous results
> "$OUTPUT_FILE"

# Enable nullglob so unmatched globs are silently ignored
shopt -s nullglob

# Loop over all directories in the current directory
for folder in */; do
  folder="${folder%/}"  # remove trailing slash
  subfolder_path="$folder/$SUBFOLDER"

  if [ -d "$subfolder_path" ]; then
    slurm_files=("$subfolder_path"/$SLURM_PATTERN)
    slurm_file="${slurm_files[0]}"  # only use the first match

    if [ -f "$slurm_file" ]; then
      if grep -q "$SEARCH_TERM" "$slurm_file"; then
        matched_line=$(grep "$SEARCH_TERM" "$slurm_file")
        echo "In folder $folder, found match:" >> "$OUTPUT_FILE"
        echo "$matched_line" >> "$OUTPUT_FILE"
      else
        echo "In folder $folder, '$SEARCH_TERM' not found." >> "$OUTPUT_FILE"
      fi
    else
      echo "In folder $folder, no SLURM file found." >> "$OUTPUT_FILE"
    fi
  else
    echo "Folder $subfolder_path does not exist." >> "$OUTPUT_FILE"
  fi
done

echo "Search complete. Results saved in $OUTPUT_FILE"
