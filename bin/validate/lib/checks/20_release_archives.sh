#!/usr/bin/env bash
set -euo pipefail

check_release_archives() {
  local root="$1"
  local rel_dir="$root/releases"

  [[ -d "$rel_dir" ]] || return 0

  while IFS= read -r -d '' zip; do
    local zip_base sha sha_base
    zip_base="$(basename "$zip")"

    if [[ ! "$zip_base" =~ ^ucbradio-isp-cutover-[0-9]+\.[0-9]+\.[0-9]+.*\.zip$ ]]; then
      fail "Release zip name invalid: releases/$zip_base (expected ucbradio-isp-cutover-X.Y.Z.zip)"
      continue
    fi

    sha="${zip}.sha256"
    sha_base="$(basename "$sha")"
    [[ -f "$sha" ]] || fail "Missing SHA256 sidecar for releases/$zip_base (expected $sha_base)"
  done < <(find "$rel_dir" -maxdepth 1 -type f -name "*.zip" -print0)
}
