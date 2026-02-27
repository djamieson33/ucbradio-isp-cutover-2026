#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# File:        bin/rename_export.sh
# Purpose:     Rename a SonicWall export file using repo UTC timestamp standard
# Standard:    <base>-YYYYMMDDThhmmZ.<ext>
# Location:    firewall/sonicwall/exports/** (per-site subfolders supported)
# ==============================================================================

die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO]  $*"; }

usage() {
  cat <<'USAGE'
Usage:
  ./bin/rename_export.sh <filename> [--dry-run]

Example:
  ./bin/rename_export.sh firewall/sonicwall/exports/wind-100/security-policy.csv
  ./bin/rename_export.sh firewall/sonicwall/exports/wind-100/route-configurations.csv
  ./bin/rename_export.sh firewall/sonicwall/exports/wind-100/nat-configurations-20260224T1917Z.csv --dry-run

Notes:
  - Timestamp is generated in UTC.
  - File is renamed in-place inside firewall/sonicwall/exports/** (site subfolders allowed).
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

EXPORTS_ROOT="firewall/sonicwall/exports"

# If only filename given, assume exports root (not a site folder)
if [[ ! "$INPUT" =~ / ]]; then
  INPUT="${EXPORTS_ROOT}/${INPUT}"
fi

[[ -f "$INPUT" ]] || die "File not found: $INPUT"

# Normalize to a path relative to repo root (no leading ./)
INPUT_CLEAN="${INPUT#./}"

DIR="$(dirname "$INPUT_CLEAN")"
BASE="$(basename "$INPUT_CLEAN")"

# Enforce correct directory tree (allow site subfolders)
case "$DIR" in
  "$EXPORTS_ROOT"|"$EXPORTS_ROOT"/*) ;;
  *) die "File must be inside ${EXPORTS_ROOT}/ (site subfolders allowed): $INPUT_CLEAN" ;;
esac

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
  info "  $INPUT_CLEAN"
  info "→ $NEW_PATH"
  exit 0
fi

mv "$INPUT_CLEAN" "$NEW_PATH"

info "Renamed:"
info "  $INPUT_CLEAN"
info "→ $NEW_PATH"
