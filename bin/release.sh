#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# UCB Radio – ISP Changeover 2026
# File:        bin/release.sh
# Purpose:     Release orchestration:
#              - compute new version (major/minor/patch)
#              - call bump_version.sh (single source of truth)
#              - commit + tag
#              - call create_archive.sh (single source of truth)
#              - generate SHA256 sidecar for the release ZIP (if created)
#              - optionally push
#              - optionally create GitHub release (attach ZIP + sha)
#
# Repo Standards:
#   - Release zips are required to have a .sha256 sidecar
#   - Release zips do NOT require timestamps in filename (SemVer is sufficient)
#   - See: docs/01-governance/FILE_STANDARDS.md
# ==============================================================================

die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO] $*"; }

usage() {
  cat <<'USAGE'
Usage: ./bin/release.sh <major|minor|patch> "<description>" [--push] [--github-release] [--no-archive]

Arguments:
  major|minor|patch    SemVer bump type
  "<description>"      One-line release description

Options:
  --push               Push commit + tag to origin
  --github-release     Create a GitHub release via gh (implies --push)
  --no-archive         Skip generating the clean ZIP archive

Examples:
  ./bin/release.sh patch "Docs: tighten README + add IP plan placeholder"
  ./bin/release.sh minor "Add preflight checks scaffolding" --push
  ./bin/release.sh patch "Firewall exports updated" --github-release
USAGE
}

generate_sha256() {
  local file="$1"

  [[ -f "$file" ]] || die "Cannot generate SHA256 — file not found: $file"
  command -v shasum >/dev/null 2>&1 || die "shasum is required to generate SHA256 sidecar."

  info "Generating SHA256 for $(basename "$file")"
  shasum -a 256 "$file" > "${file}.sha256" || die "SHA256 generation failed"

  # Verify immediately (guards against write/corruption issues)
  shasum -a 256 -c "${file}.sha256" >/dev/null 2>&1 || die "Checksum verification failed"

  info "Created ${file}.sha256"
}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

[[ $# -lt 2 || "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 1; }

command -v git >/dev/null 2>&1 || die "git is required."

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
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
  shift
done

# Ensure clean working tree at start
if [[ -n "$(git status --porcelain)" ]]; then
  die "Working tree is not clean. Commit or stash changes before releasing."
fi

[[ -f VERSION ]] || die "VERSION not found."

CURRENT_VERSION="$(tr -d '[:space:]' < VERSION)"
[[ "$CURRENT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "Invalid VERSION: '$CURRENT_VERSION'"

IFS='.' read -r MAJOR MINOR PATCH <<<"$CURRENT_VERSION"

case "$BUMP_TYPE" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
  *) die "Invalid bump type: $BUMP_TYPE (use major|minor|patch)" ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
TAG="v${NEW_VERSION}"

info "Preparing release $TAG – $DESCRIPTION"

# Single source of truth for VERSION/README/CHANGELOG updates
./bin/bump_version.sh "$NEW_VERSION" "$DESCRIPTION"

# Commit + tag
git add VERSION CHANGELOG.md
[[ -f README.md ]] && git add README.md

git commit -m "Release $TAG: $DESCRIPTION"
git tag -a "$TAG" -m "$DESCRIPTION"
info "Created commit + tag $TAG"

# Archive (single source of truth) + SHA256 sidecar
ARCHIVE_PATH=""
if [[ "$DO_ARCHIVE" == "yes" ]]; then
  ARCHIVE_PATH="$(./bin/create_archive.sh "$TAG")"
  [[ -n "$ARCHIVE_PATH" ]] || die "create_archive.sh did not return an archive path"
  [[ -f "$ARCHIVE_PATH" ]] || die "Archive not found at returned path: $ARCHIVE_PATH"

  info "Archive created: $ARCHIVE_PATH"

  # Ensure SHA256 sidecar always exists for release zips
  generate_sha256 "$ARCHIVE_PATH"
fi

# Push optional
if [[ "$DO_PUSH" == "yes" ]]; then
  info "Pushing commit + tags..."
  git push
  git push --tags
fi

# GitHub release optional (attach zip + sha256 if present)
if [[ "$DO_GH" == "yes" ]]; then
  command -v gh >/dev/null 2>&1 || die "gh CLI not found; install GitHub CLI or omit --github-release."

  info "Creating GitHub release $TAG"
  if [[ "$DO_ARCHIVE" == "yes" && -n "$ARCHIVE_PATH" && -f "$ARCHIVE_PATH" ]]; then
    assets=("$ARCHIVE_PATH")
    [[ -f "${ARCHIVE_PATH}.sha256" ]] && assets+=("${ARCHIVE_PATH}.sha256")

    gh release create "$TAG" \
      --title "$TAG" \
      --notes "$DESCRIPTION" \
      "${assets[@]}"
  else
    gh release create "$TAG" --title "$TAG" --notes "$DESCRIPTION"
  fi

  info "GitHub release created: $TAG"
fi

info "Done."
