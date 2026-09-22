#!/usr/bin/env bash
# =============================================================================
# change_any_line.sh
# =============================================================================
# PURPOSE:
#   Safely replace lines across many files with flexible matching options.
#
# KEY FEATURES:
#   ✔ exact / contains / regex matching
#   ✔ dry-run (preview changes)
#   ✔ automatic backups
#   ✔ flexible file selection (glob or recursive)
#   ✔ avoids rewriting unchanged files
#
# -----------------------------------------------------------------------------
# QUICK EXAMPLES
# -----------------------------------------------------------------------------
#
# 1) Exact match (replace only identical lines)
# --------------------------------------------------
# ./change_any_line.sh \
#   --search "#SBATCH --time=72:00:00" \
#   --to "#SBATCH --time=48:00:00" \
#   --glob "max_*" \
#   --file "src/slurm.sh"
#
#
# 2) Replace using regex (all .sh files recursively)
# --------------------------------------------------
# ./change_any_line.sh \
#   --mode regex \
#   --search '^#SBATCH[[:space:]]+--time=.*$' \
#   --to '#SBATCH --time=48:00:00' \
#   --root . \
#   --name '*.sh'
#
#
# 3) Dry-run (see what would change, no modification)
# --------------------------------------------------
# ./change_any_line.sh \
#   --search "OLD_LINE" \
#   --to "NEW_LINE" \
#   --root . \
#   --name "*.txt" \
#   --dry-run
#
#
# 4) Replace ALL matches instead of first match
# --------------------------------------------------
# ./change_any_line.sh \
#   --search "module load old" \
#   --to "module load new" \
#   --root . \
#   --name "*.sh" \
#   --all
#
# =============================================================================

# -----------------------------------------------------------------------------
# STRICT MODE (fail early if anything is wrong)
# -----------------------------------------------------------------------------
set -euo pipefail

# -----------------------------------------------------------------------------
# DEFAULT SETTINGS
# -----------------------------------------------------------------------------
MODE="exact"          # exact | contains | regex
SEARCH=""
REPLACE=""
REPLACE_ALL="false"
DRY_RUN="false"
BACKUP_EXT=".bak"

# File selection (two modes)
GLOB_DIR="*"
REL_PATH=""
ROOT_DIR="."
NAME_PATTERN=""

# -----------------------------------------------------------------------------
# HELP FUNCTION
# -----------------------------------------------------------------------------
usage() {
  cat <<EOF
Usage:
  $(basename "$0") --search TEXT --to TEXT [options]

Options:
  --mode exact|contains|regex   Matching type (default: exact)
  --all                         Replace all matches (default: first match only)
  --dry-run                     Preview changes only
  --backup EXT                  Backup extension (default: .bak)

File selection (choose ONE):

  Method A:
    --glob GLOB                 Directory pattern (default: *)
    --file RELPATH              File path inside each directory

  Method B:
    --root DIR                  Root directory (default: .)
    --name PATTERN              File pattern (e.g. "*.sh")

EOF
}

# -----------------------------------------------------------------------------
# PARSE INPUT ARGUMENTS
# -----------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="${2:?}"; shift 2 ;;
    --search) SEARCH="${2:?}"; shift 2 ;;
    --to) REPLACE="${2:?}"; shift 2 ;;
    --all) REPLACE_ALL="true"; shift ;;
    --dry-run) DRY_RUN="true"; shift ;;
    --backup) BACKUP_EXT="${2-}"; shift 2 ;;
    --glob) GLOB_DIR="${2:?}"; shift 2 ;;
    --file) REL_PATH="${2:?}"; shift 2 ;;
    --root) ROOT_DIR="${2:?}"; shift 2 ;;
    --name) NAME_PATTERN="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

# -----------------------------------------------------------------------------
# VALIDATION
# -----------------------------------------------------------------------------
if [[ -z "$SEARCH" || -z "$REPLACE" ]]; then
  echo "Error: --search and --to are required."
  usage
  exit 1
fi

if [[ ! "$MODE" =~ ^(exact|contains|regex)$ ]]; then
  echo "Error: invalid mode: $MODE"
  exit 1
fi

# -----------------------------------------------------------------------------
# BUILD FILE LIST
# -----------------------------------------------------------------------------
declare -a FILES=()

# Method A: structured directories
if [[ -n "$REL_PATH" ]]; then
  shopt -s nullglob
  for d in ${GLOB_DIR}; do
    if [[ -d "$d" && -f "$d/$REL_PATH" ]]; then
      FILES+=("$d/$REL_PATH")
    fi
  done

# Method B: recursive search
elif [[ -n "$NAME_PATTERN" ]]; then
  while IFS= read -r -d '' f; do
    FILES+=("$f")
  done < <(find "$ROOT_DIR" -type f -name "$NAME_PATTERN" -print0)

else
  echo "Error: you must specify file selection method."
  exit 1
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No files found."
  exit 2
fi

# -----------------------------------------------------------------------------
# PROCESS FILES
# -----------------------------------------------------------------------------
changed_files=0

for file in "${FILES[@]}"; do
  tmp="${file}.tmp.$$"
  status=0

  # Choose matching strategy
  case "$MODE" in

    exact)
      awk -v s="$SEARCH" -v r="$REPLACE" -v all="$REPLACE_ALL" '
        BEGIN {changed=0; done=0}
        {
          if ($0 == s) {
            if (all == "true") { print r; changed=1; next }
            else if (done == 0) { print r; changed=1; done=1; next }
          }
          print
        }
        END { if (!changed) exit 3 }
      ' "$file" > "$tmp" || status=$?
      ;;

    contains)
      awk -v s="$SEARCH" -v r="$REPLACE" -v all="$REPLACE_ALL" '
        BEGIN {changed=0; done=0}
        {
          if (index($0, s)) {
            if (all == "true") { print r; changed=1; next }
            else if (done == 0) { print r; changed=1; done=1; next }
          }
          print
        }
        END { if (!changed) exit 3 }
      ' "$file" > "$tmp" || status=$?
      ;;

    regex)
      awk -v s="$SEARCH" -v r="$REPLACE" -v all="$REPLACE_ALL" '
        BEGIN {changed=0; done=0}
        {
          if ($0 ~ s) {
            if (all == "true") { print r; changed=1; next }
            else if (done == 0) { print r; changed=1; done=1; next }
          }
          print
        }
        END { if (!changed) exit 3 }
      ' "$file" > "$tmp" || status=$?
      ;;
  esac

  # No match → skip
  if [[ "$status" -eq 3 ]]; then
    rm -f "$tmp"
    echo "No change: $file"
    continue
  fi

  # Error → stop
  if [[ "$status" -ne 0 ]]; then
    rm -f "$tmp"
    echo "Error processing: $file"
    exit 1
  fi

  # No difference → skip
  if cmp -s "$file" "$tmp"; then
    rm -f "$tmp"
    echo "No difference: $file"
    continue
  fi

  # Dry run → preview only
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "Would change: $file"
    rm -f "$tmp"
    ((changed_files++)) || true
    continue
  fi

  # Backup (if enabled)
  if [[ -n "$BACKUP_EXT" ]]; then
    cp "$file" "${file}${BACKUP_EXT}"
  fi

  # Apply change
  mv "$tmp" "$file"
  echo "Changed: $file"
  ((changed_files++)) || true
done

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------
if [[ "$changed_files" -eq 0 ]]; then
  echo "No files were changed."
  exit 3
fi

echo "Done. Changed files: $changed_files"
