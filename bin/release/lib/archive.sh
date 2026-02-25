#!/usr/bin/env bash
set -euo pipefail

archive_create_from_tag() {
  local tag="$1"
  local out

  # create_archive.sh prints INFO lines; last line is the path
  out="$(./bin/create_archive.sh "$tag" | tail -n 1 | tr -d '\r' | xargs)"
  [[ -n "$out" ]] || die "create_archive.sh did not return an archive path"
  [[ -f "$out" ]] || die "Archive not found at returned path: $out"
  echo "$out"
}
