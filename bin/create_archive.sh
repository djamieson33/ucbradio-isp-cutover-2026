#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# File:        bin/create_archive.sh
# Purpose:     Create a clean distributable ZIP archive of the project
# Description:
#   - Uses git archive to exclude .git automatically
#   - Uses UTC timestamp in filename
#   - Ensures working tree is clean (optional override)
#   - Places archive in ./releases/
# ==============================================================================

die() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*"; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ARCHIVE_DIR="$ROOT/releases"
mkdir -p "$ARCHIVE_DIR"

TIMESTAMP="$(date -u +%Y%m%dT%H%MZ)"
VERSION="$(cat VERSION 2>/dev/null || echo "unknown")"

ARCHIVE_NAME="ucbradio-isp-cutover-${VERSION}-${TIMESTAMP}.zip"
ARCHIVE_PATH="$ARCHIVE_DIR/$ARCHIVE_NAME"

# ------------------------------------------------------------------------------
# Ensure working tree is clean
# ------------------------------------------------------------------------------

if [[ -n "$(git status --porcelain)" ]]; then
  die "Working tree is not clean. Commit or stash changes before archiving."
fi

# ------------------------------------------------------------------------------
# Create archive using git (excludes .git automatically)
# ------------------------------------------------------------------------------

info "Creating clean archive..."
git archive --format=zip --output="$ARCHIVE_PATH" HEAD

info "Archive created:"
echo "  $ARCHIVE_PATH"

# ------------------------------------------------------------------------------
# Optional: display size
# ------------------------------------------------------------------------------

echo
du -h "$ARCHIVE_PATH"

info "Done."
