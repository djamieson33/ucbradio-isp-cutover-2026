#!/usr/bin/env bash
set -euo pipefail

git_require_clean_tree() {
  if [[ -n "$(git status --porcelain)" ]]; then
    die "Working tree is not clean. Commit or stash changes before releasing."
  fi
}

git_release_commit_and_tag() {
  local tag="$1"
  local desc="$2"

  git add VERSION CHANGELOG.md
  [[ -f README.md ]] && git add README.md

  git commit -m "Release $tag: $desc"
  git tag -a "$tag" -m "$desc"
  info "Created commit + tag $tag"
}

git_release_push() {
  info "Pushing commit + tags..."
  git push
  git push --tags
}
