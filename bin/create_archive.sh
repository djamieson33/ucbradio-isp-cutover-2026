#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# File:        bin/create_archive.sh
# Purpose:     Create a clean ZIP archive via git archive (+ optional sha256)
#
# Usage:
#   ./bin/create_archive.sh <git-ref> [--out <path>] [--no-sha]
#
# Examples:
#   ./bin/create_archive.sh HEAD
#   ./bin/create_archive.sh v0.2.0
#   ./bin/create_archive.sh v0.2.0 --out releases/custom.zip
# ==============================================================================

die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO] $*"; }

usage() {
  cat <<'USAGE'
Usage: ./bin/create_archive.sh <git-ref> [--out <path>] [--no-sha]

Arguments:
  <git-ref>          Git ref (HEAD, tag, commit)

Options:
  --out <path>       Output zip path (default: releases/<repo>-<ref>-<UTC>.zip)
  --no-sha           Skip SHA256 file generation
USAGE
}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

[[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 1; }

command -v git >/dev/null 2>&1 || die "git is required."

REF="${1:-}"
shift

DO_SHA="yes"
OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out)
      shift
      OUT="${1:-}"
      [[ -n "$OUT" ]] || die "--out requires a value"
      ;;
    --no-sha) DO_SHA="no" ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
  shift
done

# Validate ref exists
git rev-parse --verify "$REF^{commit}" >/dev/null 2>&1 || die "Invalid git ref: $REF"

mkdir -p releases

TS_UTC="$(date -u +%Y%m%dT%H%MZ)"
VERSION="$(cat VERSION 2>/dev/null | tr -d '[:space:]' || true)"
[[ -n "$VERSION" ]] || VERSION="unknown"

# Normalize ref for filename
REF_SAFE="$(echo "$REF" | tr '/' '-' | tr -cd 'A-Za-z0-9._-')"

if [[ -z "$OUT" ]]; then
  OUT="releases/ucbradio-isp-cutover-${VERSION}-${REF_SAFE}-${TS_UTC}.zip"
fi

info "Creating clean archive: $OUT (ref: $REF)"
git archive --format=zip --output="$OUT" "$REF"

if [[ "$DO_SHA" == "yes" ]]; then
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$OUT" > "${OUT}.sha256"
    info "SHA256 -> ${OUT}.sha256"
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$OUT" > "${OUT}.sha256"
    info "SHA256 -> ${OUT}.sha256"
  else
    info "No sha256 tool found; skipping checksum."
  fi
fi

info "Done."
echo "$OUT"
