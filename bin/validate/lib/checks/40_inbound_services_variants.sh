#!/usr/bin/env bash
set -euo pipefail

check_inbound_services_variants() {
  local root="$1"
  local seed_file="$root/inventory/03-inbound-services.seed.yaml"
  local canon_file="$root/inventory/03-inbound-services.yaml"

  [[ -f "$seed_file" ]] && pass "Found generated seed file: inventory/03-inbound-services.seed.yaml"

  if [[ -f "$canon_file" ]]; then
    pass "Found canonical file: inventory/03-inbound-services.yaml"
  else
    warn "Canonical file missing: inventory/03-inbound-services.yaml (ok if still being created)"
  fi

  # Guardrail: unexpected variants in inventory/
  while IFS= read -r -d '' f; do
    local rel base
    rel="${f#$root/}"
    base="$(basename "$f")"

    if [[ "$base" =~ ^03-inbound-services.*\.ya?ml$ ]] \
      && [[ "$base" != "03-inbound-services.yaml" ]] \
      && [[ "$base" != "03-inbound-services.seed.yaml" ]]; then
      warn "Unexpected inbound-services variant file found: $rel (confirm canonical vs generated intent)"
    fi
  done < <(find "$root/inventory" -maxdepth 1 -type f \( -name "03-inbound-services*.yml" -o -name "03-inbound-services*.yaml" \) -print0 2>/dev/null || true)
}
