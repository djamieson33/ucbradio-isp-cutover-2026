#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# UCB Radio – ISP Changeover 2026
# Tool:        bin/validate/run.sh
# Purpose:     Validate repo file naming + placement standards as defined in
#              docs/01-governance/FILE_STANDARDS.md
#
# Read-only: does not modify files.
# Exits non-zero if violations are found.
# ==============================================================================

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

# shellcheck source=bin/validate/lib/common.sh
source "$ROOT/bin/validate/lib/common.sh"

usage() {
  cat <<'USAGE'
Usage:
  ./bin/validate/run.sh

Notes:
  - Read-only: does not modify files.
  - Exits non-zero if violations are found.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

# Timestamp pattern: YYYYMMDDThhmmZ
TS_RE='[0-9]{8}T[0-9]{4}Z'
export TS_RE

# Load checks
# shellcheck source=bin/validate/lib/checks/00_basic_sanity.sh
source "$ROOT/bin/validate/lib/checks/00_basic_sanity.sh"
# shellcheck source=bin/validate/lib/checks/10_nat_exports.sh
source "$ROOT/bin/validate/lib/checks/10_nat_exports.sh"
# shellcheck source=bin/validate/lib/checks/20_release_archives.sh
source "$ROOT/bin/validate/lib/checks/20_release_archives.sh"
# shellcheck source=bin/validate/lib/checks/30_evidence_timestamps.sh
source "$ROOT/bin/validate/lib/checks/30_evidence_timestamps.sh"
# shellcheck source=bin/validate/lib/checks/40_inbound_services_variants.sh
source "$ROOT/bin/validate/lib/checks/40_inbound_services_variants.sh"
# shellcheck source=bin/validate/lib/checks/50_non_utc_timestamps_warn.sh
source "$ROOT/bin/validate/lib/checks/50_non_utc_timestamps_warn.sh"
# shellcheck source=bin/validate/lib/checks/60_bin_exec_bits.sh
source "$ROOT/bin/validate/lib/checks/60_bin_exec_bits.sh"

# Run checks (order matters)
check_basic_sanity "$ROOT"
check_nat_exports "$ROOT"
check_release_archives "$ROOT"
check_evidence_timestamps "$ROOT"
check_inbound_services_variants "$ROOT"
warn_non_utc_timestamps "$ROOT"
check_bin_exec_bits "$ROOT"

# Final
if [[ "$FAIL_COUNT" -gt 0 ]]; then
  echo
  echo "[RESULT] FAIL — $FAIL_COUNT issue(s) found."
  echo "Fix the items above to comply with docs/01-governance/FILE_STANDARDS.md"
  exit 1
fi

echo
echo "[RESULT] PASS — repo file standards look good."
exit 0
