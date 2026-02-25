#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# UCB Radio – ISP Changeover 2026
# Tool:        bin/archive/run.sh
# Purpose:     Create a clean release archive ZIP from a git ref/tag.
#
# Output contract (IMPORTANT):
# - Logs go to STDERR.
# - The final line to STDOUT is the archive path (and ONLY that).
#
# Naming:
#   releases/ucbradio-isp-cutover-<X.Y.Z>-v<X.Y.Z>-<YYYYMMDDThhmmZ>.zip
# Example:
#   releases/ucbradio-isp-cutover-0.2.0-v0.2.0-20260225T2028Z.zip
# ==============================================================================

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# shellcheck source=bin/archive/lib/common.sh
source "$ROOT/bin/archive/lib/common.sh"

usage() {
  cat <<'USAGE' >&2
Usage: ./bin/archive/run.sh <git-ref>

Examples:
  ./bin/archive/run.sh v0.2.0
  ./bin/archive/run.sh HEAD
USAGE
}

[[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 1; }

require_cmd git
require_cmd date

REF="${1:-}"

cd "$ROOT"

# Validate ref exists
if ! git rev-parse --verify --quiet "$REF^{commit}" >/dev/null; then
  die "Invalid git ref (cannot resolve to commit): $REF"
fi

# Derive version from tag/ref:
# - If ref looks like vX.Y.Z => version = X.Y.Z
# - Else if VERSION file exists at ref and looks semver => use that
# - Else fallback to ref name sanitized (rare)
version_from_ref() {
  local ref="$1"
  if [[ "$ref" =~ ^v([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    echo "${BASH_REMATCH[1]}"
    return
  fi

  # Try reading VERSION from the ref (only if file exists in that ref)
  local v
  if git cat-file -e "$ref:VERSION" 2>/dev/null; then
    v="$(git show "${ref}:VERSION" 2>/dev/null | tr -d '[:space:]' || true)"
    if [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      echo "$v"
      return
    fi
  fi

  # Fallback: sanitize ref (not ideal, but prevents hard fail)
  echo "$ref" | tr -cd '[:alnum:]._-'
}

VERSION_STR="$(version_from_ref "$REF")"

TS_UTC="$(date -u +"%Y%m%dT%H%MZ")"
OUT_DIR="$ROOT/releases"
mkdir -p "$OUT_DIR"

ZIP_PATH="$OUT_DIR/ucbradio-isp-cutover-${VERSION_STR}-v${VERSION_STR}-${TS_UTC}.zip"

info "Creating clean archive: ${ZIP_PATH} (ref: ${REF})"

# Create archive from tracked files at ref
git archive --format=zip --output="$ZIP_PATH" "$REF" || die "git archive failed"

# Basic sanity
[[ -s "$ZIP_PATH" ]] || die "Archive was created but is empty: $ZIP_PATH"

info "Done."

# Output contract: ONLY the path on stdout
printf "%s\n" "$ZIP_PATH"
