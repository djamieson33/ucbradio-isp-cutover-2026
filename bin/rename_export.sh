#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# File:        bin/rename_export.sh
# Purpose:     Rename a SonicWall export file using repo UTC timestamp standard
# Standard:    <base>-YYYYMMDDThhmmZ.<ext>
# Location:    firewall/sonicwall/exports/
# ==============================================================================

die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO]  $*"; }

usage() {
  cat <<'USAGE'
Usage:
  ./bin/rename_export.sh <filename>

Example:
  ./bin/rename_export.sh firewall/sonicwall/exports/security-policy.csv
  ./bin/rename_export.sh route-configurations.csv

Notes:
  - Timestamp is generated in UTC.
  - File is renamed in-place inside firewall/sonicwall/exports/.
  - Original file extension is preserved.
USAGE
}

[[ $# -lt 1 ]] && { usage; exit 1; }

INPUT="$1"

# Resolve repo root
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# If only filename given, assume exports directory
if [[ ! "$INPUT" =~ / ]]; then
  INPUT="firewall/sonicwall/exports/$INPUT"
fi

[[ -f "$INPUT" ]] || die "File not found: $INPUT"

DIR="$(dirname "$INPUT")"
BASE="$(basename "$INPUT")"

# Enforce correct directory
[[ "$DIR" == "firewall/sonicwall/exports" ]] \
  || die "File must be inside firewall/sonicwall/exports/"

EXT="${BASE##*.}"
NAME="${BASE%.*}"

TIMESTAMP="$(date -u +"%Y%m%dT%H%MZ")"
NEW_NAME="${NAME}-${TIMESTAMP}.${EXT}"
NEW_PATH="${DIR}/${NEW_NAME}"

[[ -f "$NEW_PATH" ]] && die "Target already exists: $NEW_PATH"

mv "$INPUT" "$NEW_PATH"

info "Renamed:"
info "  $BASE"
info "→ $NEW_NAME"
