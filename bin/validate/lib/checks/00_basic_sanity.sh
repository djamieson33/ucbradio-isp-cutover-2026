#!/usr/bin/env bash
set -euo pipefail

check_basic_sanity() {
  local root="$1"

  [[ -f "$root/docs/01-governance/FILE_STANDARDS.md" ]] || fail "Missing docs/01-governance/FILE_STANDARDS.md"
  [[ -d "$root/firewall/sonicwall/exports" ]] || warn "Missing firewall/sonicwall/exports (ok if not created yet)"
  [[ -d "$root/releases" ]] || warn "Missing releases/ (ok if not created yet)"
  [[ -d "$root/evidence" ]] || warn "Missing evidence/ (ok if not created yet)"
}
