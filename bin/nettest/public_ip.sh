#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# UCB Radio – ISP Changeover 2026
# File:        bin/nettest/public_ip.sh
# Purpose:     Show current outbound public IP (egress) and compare to expected
#              Cogeco/Bell IPs. Useful for testing policy-routing a single host
#              out Bell X3 without impacting office traffic.
#
# Usage:
#   bin/nettest/public_ip.sh [SITE_CODE] [--expect <ip>]... [--timeout N] [--dry-run]
#
# Examples:
#   bin/nettest/public_ip.sh
#   bin/nettest/public_ip.sh --expect 24.51.249.34 --expect 207.236.163.98
#   bin/nettest/public_ip.sh BELL-102
#   bin/nettest/public_ip.sh BELL-102 --dry-run
#
# Notes:
# - If SITE_CODE is provided and bin/helpers/lib/env.sh is present, this script
#   will try to auto-load expected IPs from the device YAML (best-effort).
# - This does NOT change routing. It only reports what your machine is doing now.
# ==============================================================================

die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO]  $*"; }

usage() {
  cat <<'USAGE'
Usage:
  bin/nettest/public_ip.sh [SITE_CODE] [--expect <ip>]... [--timeout N] [--dry-run]

Arguments:
  SITE_CODE               Optional. e.g., BELL-102. If provided, attempts to
                          auto-load expected WAN IPs from its device YAML.

Options:
  --expect <ip>           Provide one or more expected public IPs to compare against.
                          Example: --expect 24.51.249.34 --expect 207.236.163.98
  --timeout N             Curl max-time seconds (default: 8)
  --dry-run               Print what would be checked, do not call external services.
  -h, --help              Show help

Output:
  - Current public IP (from 2 independent services if possible)
  - Match status vs expected IPs
USAGE
}

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TIMEOUT="8"
DRY_RUN="no"

SITE_CODE=""
EXPECTED=()

# Optional SITE_CODE (first arg if it doesn't start with -)
if [[ $# -gt 0 && "${1:-}" != -* ]]; then
  SITE_CODE="$1"
  shift
fi

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --expect)
      shift
      [[ -n "${1:-}" ]] || die "--expect requires an IP"
      EXPECTED+=("$1")
      ;;
    --timeout)
      shift
      [[ "${1:-}" =~ ^[0-9]+$ ]] || die "--timeout must be an integer"
      TIMEOUT="$1"
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

require_cmd() { command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"; }
require_cmd curl

# Best-effort YAML key fetch:
# 1) try python+yaml if available
# 2) fallback to simple grep for "key: value" (works for our flat fields)
yaml_get() {
  local file="$1"
  local keypath="$2"

  [[ -f "$file" ]] || return 1

  if python3 - <<'PY' >/dev/null 2>&1
import sys
try:
  import yaml  # type: ignore
  sys.exit(0)
except Exception:
  sys.exit(1)
PY
  then
    python3 - <<PY 2>/dev/null || true
import yaml,sys
file=sys.argv[1]
keypath=sys.argv[2].split(".")
with open(file,"r",encoding="utf-8") as f:
    data=yaml.safe_load(f)
cur=data
for k in keypath:
    if isinstance(cur, dict) and k in cur:
        cur=cur[k]
    else:
        cur=None
        break
if cur is None:
    sys.exit(0)
if isinstance(cur,(str,int,float)):
    print(cur)
PY
"$file" "$keypath"
    return 0
  fi

  # Grep fallback: only for simple keys like "public_ip_bell: ..."
  local key="${keypath##*.}"
  local line
  line="$(grep -E "^[[:space:]]*$key:[[:space:]]*" "$file" | head -n 1 || true)"
  [[ -n "$line" ]] || return 0
  echo "$line" | sed -E "s/^[[:space:]]*$key:[[:space:]]*//" | tr -d '"' | tr -d "'"
  return 0
}

# Auto-load expected WAN IPs from SITE_CODE device YAML (best-effort)
if [[ -n "$SITE_CODE" ]]; then
  if [[ -f "$ROOT/bin/helpers/lib/env.sh" ]]; then
    # shellcheck source=bin/helpers/lib/env.sh
    source "$ROOT/bin/helpers/lib/env.sh"
    if resolve_site "$SITE_CODE" >/dev/null 2>&1; then
      # Try common keys used in this repo
      bell_ip="$(yaml_get "$DEVICE_YAML" "interfaces.wan.public_ip_bell" | xargs || true)"
      cogeco_ip="$(yaml_get "$DEVICE_YAML" "interfaces.wan.public_ip_cogeco_previous" | xargs || true)"
      [[ -n "${cogeco_ip:-}" && "$cogeco_ip" != "unknown" && "$cogeco_ip" != "null" ]] && EXPECTED+=("$cogeco_ip")
      [[ -n "${bell_ip:-}" && "$bell_ip" != "unknown" && "$bell_ip" != "null" ]] && EXPECTED+=("$bell_ip")
    fi
  fi
fi

# De-dup EXPECTED
if [[ ${#EXPECTED[@]} -gt 0 ]]; then
  mapfile -t EXPECTED < <(printf "%s\n" "${EXPECTED[@]}" | awk 'NF' | awk '!seen[$0]++')
fi

echo
echo "Outbound public IP check"
echo "------------------------"
if [[ -n "$SITE_CODE" ]]; then
  echo "Site code:   $SITE_CODE"
fi
echo "Timeout:     ${TIMEOUT}s"
if [[ ${#EXPECTED[@]} -gt 0 ]]; then
  echo "Expected:    ${EXPECTED[*]}"
else
  echo "Expected:    (none provided)"
fi
echo

if [[ "$DRY_RUN" == "yes" ]]; then
  info "Dry-run only; not calling external IP services."
  exit 0
fi

# Query two independent services; accept first successful result
query_ip() {
  local url="$1"
  curl -sS --max-time "$TIMEOUT" "$url" | tr -d ' \t\r\n'
}

IP1="$(query_ip "https://api.ipify.org" || true)"
IP2="$(query_ip "https://ifconfig.me/ip" || true)"

# Choose a "best" IP (prefer IP1, fallback to IP2)
PUBLIC_IP="${IP1:-${IP2:-}}"

if [[ -z "$PUBLIC_IP" ]]; then
  die "Unable to determine public IP (both services failed)."
fi

echo "Public IP (ipify):     ${IP1:-"(failed)"}"
echo "Public IP (ifconfig):  ${IP2:-"(failed)"}"
echo "Chosen public IP:      $PUBLIC_IP"
echo

if [[ ${#EXPECTED[@]} -gt 0 ]]; then
  matched="no"
  for e in "${EXPECTED[@]}"; do
    if [[ "$PUBLIC_IP" == "$e" ]]; then
      matched="yes"
      break
    fi
  done

  if [[ "$matched" == "yes" ]]; then
    echo "[OK] Public IP matches an expected value."
  else
    echo "[WARN] Public IP does NOT match expected values."
    echo "       This is normal if you have not policy-routed this host out Bell yet."
  fi
  echo
else
  echo "[INFO] No expected IPs provided. (Tip: run with BELL-102 or --expect ...)"
  echo
fi

info "Done."
