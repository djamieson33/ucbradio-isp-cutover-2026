#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# File:        bin/bump_version.sh
# Purpose:     Update VERSION + README.md + CHANGELOG.md (no git commit/tag)
#
# Usage:
#   ./bin/bump_version.sh <new_version> "<description>" [--no-readme] [--no-changelog]
#
# Notes:
#   - Uses UTC dates
#   - Does NOT commit/tag/push
# ==============================================================================

die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO] $*"; }

usage() {
  cat <<'USAGE'
Usage: ./bin/bump_version.sh <new_version> "<description>" [--no-readme] [--no-changelog]

Arguments:
  <new_version>        SemVer, e.g. 0.2.0
  "<description>"      One-line summary added to CHANGELOG

Options:
  --no-readme          Skip README.md updates
  --no-changelog       Skip CHANGELOG.md updates

Examples:
  ./bin/bump_version.sh 0.2.0 "Add DNS + IP plan folders"
  ./bin/bump_version.sh 0.1.2 "Docs cleanup" --no-changelog
USAGE
}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

[[ $# -lt 2 || "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 1; }

NEW_VERSION="${1:-}"
DESCRIPTION="${2:-}"
shift 2

DO_README="yes"
DO_CHANGELOG="yes"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-readme) DO_README="no" ;;
    --no-changelog) DO_CHANGELOG="no" ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
  shift
done

[[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "Invalid SemVer: '$NEW_VERSION'"
[[ -f VERSION ]] || die "VERSION file not found."

DATE_UTC="$(date -u +%Y-%m-%d)"

# --- VERSION ---
printf '%s\n' "$NEW_VERSION" > VERSION
info "VERSION -> $NEW_VERSION"

# --- README (best-effort) ---
if [[ "$DO_README" == "yes" ]]; then
  if [[ -f README.md ]]; then
    # macOS/Linux portable edits
    perl -pi -e "s/(\\*\\*Version:\\*\\*\\s*)\\d+\\.\\d+\\.\\d+/\$1$NEW_VERSION/g" README.md
    perl -pi -e "s/(\\*\\*Last updated:\\*\\*\\s*)\\d{4}-\\d{2}-\\d{2}/\$1$DATE_UTC/g" README.md
    info "README.md updated (Version + Last updated)"
  else
    info "README.md not found; skipping."
  fi
fi

# --- CHANGELOG ---
if [[ "$DO_CHANGELOG" == "yes" ]]; then
  [[ -f CHANGELOG.md ]] || die "CHANGELOG.md not found."

  tmpfile="$(mktemp)"
  {
    echo "## [$NEW_VERSION] - $DATE_UTC"
    echo "- $DESCRIPTION"
    echo
    cat CHANGELOG.md
  } >"$tmpfile"
  mv "$tmpfile" CHANGELOG.md
  info "CHANGELOG.md prepended with [$NEW_VERSION]"
fi

info "Done."
