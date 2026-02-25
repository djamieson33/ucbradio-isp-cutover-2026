#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Load modular libs
source "$ROOT/bin/release/lib/common.sh"
source "$ROOT/bin/release/lib/semver.sh"
source "$ROOT/bin/release/lib/git.sh"
source "$ROOT/bin/release/lib/archive.sh"
source "$ROOT/bin/release/lib/checksum.sh"
source "$ROOT/bin/release/lib/github.sh"

usage() {
  cat <<'USAGE'
Usage: ./bin/release/run.sh <major|minor|patch> "<description>" [--push] [--github-release] [--no-archive]
USAGE
}

[[ $# -lt 2 || "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 1; }

require_cmd git

BUMP_TYPE="${1:-}"
DESCRIPTION="${2:-}"
shift 2

DO_PUSH="no"
DO_GH="no"
DO_ARCHIVE="yes"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --push) DO_PUSH="yes" ;;
    --github-release) DO_GH="yes"; DO_PUSH="yes" ;;
    --no-archive) DO_ARCHIVE="no" ;;
    *) die "Unknown option: $1" ;;
  esac
  shift
done

cd "$ROOT"

git_require_clean_tree

CURRENT_VERSION="$(version_read)"
NEW_VERSION="$(semver_bump "$CURRENT_VERSION" "$BUMP_TYPE")"
TAG="v${NEW_VERSION}"

info "Preparing release $TAG – $DESCRIPTION"

./bin/bump_version.sh "$NEW_VERSION" "$DESCRIPTION"

git_release_commit_and_tag "$TAG" "$DESCRIPTION"

ARCHIVE_PATH=""
if [[ "$DO_ARCHIVE" == "yes" ]]; then
  ARCHIVE_PATH="$(archive_create_from_tag "$TAG")"
  info "Archive created: $ARCHIVE_PATH"
  sha256_sidecar_create_and_verify "$ARCHIVE_PATH"
fi

[[ "$DO_PUSH" == "yes" ]] && git_release_push
[[ "$DO_GH" == "yes" ]] && gh_release_create "$TAG" "$DESCRIPTION" "$ARCHIVE_PATH"

info "Done."
