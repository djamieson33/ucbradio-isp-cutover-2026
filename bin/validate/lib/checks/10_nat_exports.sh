#!/usr/bin/env bash
set -euo pipefail

check_nat_exports() {
  local root="$1"
  local nat_dir="$root/firewall/sonicwall/exports"

  [[ -d "$nat_dir" ]] || return 0

  # Any CSVs in NAT exports must match nat-policies-YYYYMMDDThhmmZ.csv
  while IFS= read -r -d '' f; do
    local base
    base="$(basename "$f")"
    if [[ ! "$base" =~ ^nat-policies-${TS_RE}\.csv$ ]]; then
      fail "NAT export CSV name invalid: firewall/sonicwall/exports/$base (expected nat-policies-YYYYMMDDThhmmZ.csv)"
    fi
  done < <(find "$nat_dir" -maxdepth 1 -type f -name "*.csv" -print0)

  # Optional: flag “export.csv” or other common mistakes
  while IFS= read -r -d '' f; do
    local base
    base="$(basename "$f")"
    if [[ "$base" == "export.csv" || "$base" == "nat.csv" ]]; then
      fail "Generic NAT export filename detected: firewall/sonicwall/exports/$base (rename to nat-policies-YYYYMMDDThhmmZ.csv)"
    fi
  done < <(find "$nat_dir" -maxdepth 1 -type f -print0)
}
