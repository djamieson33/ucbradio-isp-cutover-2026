#!/usr/bin/env bash
set -euo pipefail

check_bin_exec_bits() {
  local root="$1"
  local bin_dir="$root/bin"

  [[ -d "$bin_dir" ]] || return 0

  while IFS= read -r -d '' f; do
    local base
    base="$(basename "$f")"
    if [[ "$base" =~ \.sh$ ]] && [[ ! -x "$f" ]]; then
      fail "bin script not executable: bin/$base (run: chmod +x bin/$base)"
    fi
  done < <(find "$bin_dir" -maxdepth 1 -type f -name "*.sh" -print0)
}
