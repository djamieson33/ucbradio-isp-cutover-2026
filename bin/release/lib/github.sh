#!/usr/bin/env bash
set -euo pipefail

gh_release_create() {
  local tag="$1"
  local desc="$2"
  local archive_path="${3:-}"

  require_cmd gh

  info "Creating GitHub release $tag"
  if [[ -n "$archive_path" && -f "$archive_path" ]]; then
    local assets=("$archive_path")
    [[ -f "${archive_path}.sha256" ]] && assets+=("${archive_path}.sha256")

    gh release create "$tag" \
      --title "$tag" \
      --notes "$desc" \
      "${assets[@]}"
  else
    gh release create "$tag" --title "$tag" --notes "$desc"
  fi

  info "GitHub release created: $tag"
}
