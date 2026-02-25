#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# UCB Radio – ISP Changeover 2026
# File:        bin/nettest/ping_mgmt.sh
# Purpose:     Ping the resolved management host for a site_code/device.
#
# Usage:
#   bin/nettest/ping_mgmt.sh <SITE_CODE> [--prefer lan|wan] [--count N]
#
# Examples:
#   bin/nettest/ping_mgmt.sh BROC-100
#   bin/nettest/ping_mgmt.sh BELL-102 --prefer lan
#   bin/nettest/ping_mgmt.sh BROC-100 --prefer wan --count 2
#
# Depends on:
#   - bin/helpers/lib/env.sh (resolve_site)
# ==============================================================================

die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO]  $*"; }

usage() {
  cat <<'USAGE'
Usage:
  bin/nettest/ping_mgmt.sh <SITE_CODE> [--prefer lan|wan] [--count N] [--dry-run]

Arguments:
  SITE_CODE              e.g., BELL-102, BROC-100, CHAT-101

Options:
  --prefer lan|wan        Prefer which management URL to derive host from.
                          Default: wan (then lan fallback).
  --count N               Ping count (macOS default supports -c). Default: 3
  --dry-run               Show resolved context only, do not ping
  -h, --help              Show help

Notes:
  - Uses inventory/devices/** YAML to determine management targets.
  - If a device has only LAN URL, host will be derived from that.
USAGE
}

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PREFER="wan"
COUNT="3"
DRY_RUN="no"

[[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 1; }

SITE_CODE="${1:-}"
shift

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --prefer)
      shift
      [[ "${1:-}" == "lan" || "${1:-}" == "wan" ]] || die "--prefer must be lan or wan"
      PREFER="$1"
      ;;
    --count)
      shift
      [[ "${1:-}" =~ ^[0-9]+$ ]] || die "--count must be an integer"
      COUNT="$1"
      ;;
    --dry-run)
      DRY_RUN="yes"
      ;;
    -h|--help)
      usage; exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
  shift
done

# shellcheck source=bin/helpers/lib/env.sh
source "$ROOT/bin/helpers/lib/env.sh"

resolve_site "$SITE_CODE" || die "Unable to resolve site: $SITE_CODE"

# Choose host based on preference.
HOST=""
if [[ "$PREFER" == "lan" ]]; then
  if [[ -n "${MGMT_LAN_URL:-}" ]]; then
    HOST="$(host_from_url "$MGMT_LAN_URL")"
  fi
  [[ -n "$HOST" ]] || HOST="${MGMT_HOST:-}"
else
  if [[ -n "${MGMT_WAN_URL:-}" ]]; then
    HOST="$(host_from_url "$MGMT_WAN_URL")"
  fi
  [[ -n "$HOST" ]] || HOST="${MGMT_HOST:-}"
fi

[[ -n "$HOST" ]] || die "No management host could be derived (missing management.wan_url/lan_url in $DEVICE_YAML)"

echo
echo "Resolved context"
echo "----------------"
print_context
echo "Prefer:       $PREFER"
echo "Ping target:  $HOST"
echo "Count:        $COUNT"
echo

if [[ "$DRY_RUN" == "yes" ]]; then
  info "Dry-run only; not pinging."
  exit 0
fi

info "Pinging $HOST ..."
ping -c "$COUNT" "$HOST"
