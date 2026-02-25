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
  ./bin/rename_export.sh <filename> [--dry-run]

Example:
  ./bin/rename_export.sh firewall/sonicwall/exports/security-policy.csv
  ./bin/rename_export.sh route-configurations.csv
  ./bin/rename_export.sh nat-configurations-20260224T1917Z.csv --dry-run

Notes:
  - Timestamp is generated in UTC.
  - File is renamed in-place inside firewall/sonicwall/exports/.
  - Original file extension is preserved (if present).
  - If the filename already includes a UTC stamp (YYYYMMDDThhmmZ), the script will refuse by default.
USAGE
}

[[ $# -lt 1 ]] && { usage; exit 1; }

INPUT=""
DRY_RUN="no"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN="yes" ;;
    -h|--help) usage; exit 0 ;;
    *)
      [[ -z "$INPUT" ]] || die "Unexpected extra argument: $1"
      INPUT="$1"
      ;;
  esac
  shift
done

[[ -n "$INPUT" ]] || { usage; exit 1; }

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
[[ "$DIR" == "firewall/sonicwall/exports" ]] || die "File must be inside firewall/sonicwall/exports/"

# Guard: avoid double-stamping
TS_RE='[0-9]{8}T[0-9]{4}Z'
if [[ "$BASE" =~ $TS_RE ]]; then
  die "Filename already contains a UTC timestamp (refusing to double-stamp): $BASE"
fi

TIMESTAMP="$(date -u +"%Y%m%dT%H%MZ")"

# Handle extension safely (files may have no dot)
if [[ "$BASE" == *.* ]]; then
  EXT="${BASE##*.}"
  NAME="${BASE%.*}"
  NEW_NAME="${NAME}-${TIMESTAMP}.${EXT}"
else
  NEW_NAME="${BASE}-${TIMESTAMP}"
fi

NEW_PATH="${DIR}/${NEW_NAME}"
[[ -f "$NEW_PATH" ]] && die "Target already exists: $NEW_PATH"

if [[ "$DRY_RUN" == "yes" ]]; then
  info "Dry run — would rename:"
  info "  $INPUT"
  info "→ $NEW_PATH"
  exit 0
fi

mv "$INPUT" "$NEW_PATH"

info "Renamed:"
info "  $INPUT"
info "→ $NEW_PATH"
