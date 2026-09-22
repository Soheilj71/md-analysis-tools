#!/usr/bin/env bash
# =============================================================================
# gather_files.sh
# =============================================================================
# PURPOSE:
#   General-purpose file collection tool.
#
#   Recursively finds files matching a pattern and copies or moves them into
#   a single output directory, optionally preserving structure and generating
#   a manifest CSV.
#
# USE CASES:
#   - Collect .npy files from experiments
#   - Gather logs from multiple runs
#   - Aggregate outputs from simulations
#   - Merge scattered results into one folder
#
# FEATURES:
#   - Pattern-based search (e.g., *.npy, *.log, *.txt)
#   - Copy or move files
#   - Optional overwrite protection
#   - Optional directory structure preservation
#   - Manifest CSV generation (file size + path)
#   - Cross-platform (Linux/macOS)
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# DEFAULT CONFIGURATION
# -----------------------------------------------------------------------------
SEARCH_ROOT="."
OUTPUT_DIR="./collected_files"
PATTERN="*.npy"
ACTION="copy"              # copy | move
OVERWRITE=0
PRESERVE_STRUCTURE=0
GENERATE_MANIFEST=1

# -----------------------------------------------------------------------------
# HELP
# -----------------------------------------------------------------------------
print_help() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --search-root=PATH     Root directory to search (default: .)
  --output-dir=PATH      Output directory (default: ./collected_files)
  --pattern=PATTERN      File pattern (default: *.npy)
  --action=copy|move     Copy or move files (default: copy)
  --overwrite            Overwrite existing files
  --preserve-structure   Preserve directory tree in output
  --no-manifest          Do not generate manifest CSV
  -h, --help             Show this help

Examples:
  Collect all .npy files:
    ./gather_files.sh --pattern="*.npy"

  Collect logs and preserve structure:
    ./gather_files.sh --pattern="*.log" --preserve-structure

  Move instead of copy:
    ./gather_files.sh --action=move
EOF
}

# -----------------------------------------------------------------------------
# ARGUMENT PARSING
# -----------------------------------------------------------------------------
for arg in "$@"; do
  case "$arg" in
    --search-root=*) SEARCH_ROOT="${arg#*=}" ;;
    --output-dir=*) OUTPUT_DIR="${arg#*=}" ;;
    --pattern=*) PATTERN="${arg#*=}" ;;
    --action=copy) ACTION="copy" ;;
    --action=move) ACTION="move" ;;
    --overwrite) OVERWRITE=1 ;;
    --preserve-structure) PRESERVE_STRUCTURE=1 ;;
    --no-manifest) GENERATE_MANIFEST=0 ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "[ERROR] Unknown option: $arg" >&2; exit 1 ;;
  esac
done

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
msg()  { printf "[INFO] %s\n" "$*"; }
warn() { printf "[WARN] %s\n" "$*"; }

# -----------------------------------------------------------------------------
# VALIDATION
# -----------------------------------------------------------------------------
[[ -d "$SEARCH_ROOT" ]] || { echo "[ERROR] Invalid search root"; exit 1; }

mkdir -p "$OUTPUT_DIR"

msg "Search root : $SEARCH_ROOT"
msg "Output dir  : $OUTPUT_DIR"
msg "Pattern     : $PATTERN"
msg "Action      : $ACTION"

# -----------------------------------------------------------------------------
# MAIN LOGIC
# -----------------------------------------------------------------------------
count=0
declare -a FILES_WRITTEN=()

while IFS= read -r -d '' file; do
  rel_path="${file#$SEARCH_ROOT/}"

  if [[ "$PRESERVE_STRUCTURE" -eq 1 ]]; then
    dst="$OUTPUT_DIR/$rel_path"
    mkdir -p "$(dirname "$dst")"
  else
    base="$(basename "$file")"
    dst="$OUTPUT_DIR/$base"
  fi

  if [[ -e "$dst" && "$OVERWRITE" -ne 1 ]]; then
    warn "Skipping existing: $dst"
    continue
  fi

  tmp="${dst}.tmp.$$"

  if [[ "$ACTION" == "copy" ]]; then
    cp "$file" "$tmp"
  else
    mv "$file" "$tmp"
  fi

  mv "$tmp" "$dst"

  FILES_WRITTEN+=("$dst")
  ((count++)) || true

done < <(find "$SEARCH_ROOT" -type f -name "$PATTERN" -print0)

msg "Processed files: $count"

# -----------------------------------------------------------------------------
# MANIFEST
# -----------------------------------------------------------------------------
if [[ "$GENERATE_MANIFEST" -eq 1 ]]; then
  manifest="$OUTPUT_DIR/manifest.csv"

  {
    echo "filename,bytes,path"

    for f in "${FILES_WRITTEN[@]}"; do
      bytes="$(stat -c '%s' "$f" 2>/dev/null || stat -f '%z' "$f")"
      name="$(basename "$f")"
      printf '%s,%s,%s\n' "$name" "$bytes" "$f"
    done

  } > "$manifest"

  msg "Manifest written: $manifest"
fi
