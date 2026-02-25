#!/usr/bin/env bash
set -euo pipefail

warn_non_utc_timestamps() {
  local root="$1"

  local check_dirs=(
    "$root/firewall/sonicwall/exports"
    "$root/releases"
    "$root/evidence"
  )

  local d
  for d in "${check_dirs[@]}"; do
    [[ -d "$d" ]] || continue
    while IFS= read -r -d '' f; do
      local base
      base="$(basename "$f")"
      if [[ "$base" =~ [0-9]{4}-[0-9]{2}-[0-9]{2} ]]; then
        warn "Possible non-standard timestamp (contains YYYY-MM-DD): ${f#$root/}"
      fi
    done < <(find "$d" -type f -print0)
  done
}
