#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# UCB Radio – ISP Changeover 2026
# File:        bin/nettest/tcp_port.sh
# Purpose:     TCP port reachability test against a site's management host (WAN/LAN),
#              using resolve_site() from bin/helpers/lib/env.sh.
#
# Usage:
#   bin/nettest/tcp_port.sh <SITE_CODE> [--prefer wan|lan] [--ports "22,443,80"]
#                           [--timeout N] [--dry-run]
#
# Examples:
#   bin/nettest/tcp_port.sh BELL-102 --ports "443,22"
#   bin/nettest/tcp_port.sh BROC-100 --prefer wan --ports "22,443" --timeout 3
#   bin/nettest/tcp_port.sh BROC-100 --dry-run
# ==============================================================================
die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO]  $*"; }

usage() {
  cat <<'USAGE'
Usage:
  bin/nettest/tcp_port.sh <SITE_CODE> [options]

Options:
  --prefer wan|lan        Which management URL to prefer (default: wan)
  --ports "a,b,c"         Comma-separated ports (default: "443,22")
  --timeout N             Timeout seconds per port (default: 4)
  --dry-run               Print resolved target and planned checks; do not connect
  -h, --help              Show help

Notes:
  - Prefers nc(1) if available; otherwise uses /dev/tcp (bash/zsh compatible in many cases).
  - This is a reachability test only (no TLS/HTTP validation).
USAGE
}

[[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 1; }

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

SITE_CODE="$1"
shift

PREFER="wan"
PORTS_CSV="443,22"
TIMEOUT="4"
DRY_RUN="no"

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --prefer)
      shift
      [[ "${1:-}" == "wan" || "${1:-}" == "lan" ]] || die "--prefer must be wan|lan"
      PREFER="$1"
      ;;
    --ports)
      shift
      [[ -n "${1:-}" ]] || die "--ports requires a value"
      PORTS_CSV="$1"
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

# Helpers
host_from_urlish() {
  local u="${1:-}"
  u="${u#http://}"
  u="${u#https://}"
  u="${u%%/*}"
  printf '%s' "$u"
}

split_host_port() {
  # input: host[:port] -> echoes host then port (port may be empty)
  local hp="${1:-}"
  local host="${hp}"
  local port=""
  if [[ "$hp" == *:* ]]; then
    host="${hp%:*}"
    port="${hp##*:}"
    [[ "$host" == *:* ]] && { host="$hp"; port=""; } # ipv6 literal not handled here
  fi
  echo "$host"
  echo "$port"
}

have_nc() { command -v nc >/dev/null 2>&1; }

tcp_check_nc() {
  local host="$1" port="$2" timeout="$3"
  # -z: zero-I/O mode, -v: verbose, -w: timeout seconds
  nc -z -v -w "$timeout" "$host" "$port" >/dev/null 2>&1
}

tcp_check_devtcp() {
  local host="$1" port="$2" timeout="$3"
  # Best-effort fallback. Uses a background open and kills if it hangs.
  # Note: /dev/tcp works in bash; may work in zsh depending on settings.
  (exec 3<>"/dev/tcp/${host}/${port}") >/dev/null 2>&1 &
  local pid=$!
  local elapsed=0
  while kill -0 "$pid" >/dev/null 2>&1; do
    sleep 1
    elapsed=$((elapsed+1))
    if [[ "$elapsed" -ge "$timeout" ]]; then
      kill "$pid" >/dev/null 2>&1 || true
      wait "$pid" >/dev/null 2>&1 || true
      return 1
    fi
  done
  wait "$pid" >/dev/null 2>&1
}

# Resolve site context
HELPERS_ENV="$ROOT/bin/helpers/lib/env.sh"
[[ -f "$HELPERS_ENV" ]] || die "Missing: bin/helpers/lib/env.sh (needed for resolve_site)"

# shellcheck source=bin/helpers/lib/env.sh
source "$HELPERS_ENV"

resolve_site "$SITE_CODE" >/dev/null 2>&1 || die "Unable to resolve site: $SITE_CODE"

SELECTED_URL=""
if [[ "$PREFER" == "wan" ]]; then
  SELECTED_URL="${MGMT_WAN_URL:-}"
else
  SELECTED_URL="${MGMT_LAN_URL:-}"
fi

# Fallback if preferred missing
if [[ -z "$SELECTED_URL" || "$SELECTED_URL" == "unknown" || "$SELECTED_URL" == "null" ]]; then
  if [[ "$PREFER" == "wan" ]]; then
    SELECTED_URL="${MGMT_LAN_URL:-}"
    PREFER="lan"
  else
    SELECTED_URL="${MGMT_WAN_URL:-}"
    PREFER="wan"
  fi
fi

[[ -n "$SELECTED_URL" && "$SELECTED_URL" != "unknown" && "$SELECTED_URL" != "null" ]] \
  || die "No usable management URL found in device YAML for $SITE_CODE"

HOST_PORT="$(host_from_urlish "$SELECTED_URL")"
read -r HOST PARSED_PORT < <(split_host_port "$HOST_PORT")
[[ -n "$HOST" ]] || die "Unable to parse host from: $SELECTED_URL"

# Build port list; if URL included a port and user didn't override ports, keep defaults + parsed.
IFS=',' read -r -a PORTS <<<"$PORTS_CSV"

echo
echo "Resolved context"
echo "----------------"
echo "Site code:     $SITE_CODE"
echo "Device YAML:   $DEVICE_YAML"
echo "Device name:   ${DEVICE_NAME:-unknown}"
echo "Mgmt WAN URL:  ${MGMT_WAN_URL:-unknown}"
echo "Mgmt LAN URL:  ${MGMT_LAN_URL:-unknown}"
echo "Prefer:        $PREFER"
echo "Selected URL:  $SELECTED_URL"
echo "Host:          $HOST"
echo "Ports:         ${PORTS_CSV}"
echo "Timeout:       ${TIMEOUT}s"
echo

if [[ "$DRY_RUN" == "yes" ]]; then
  info "Dry-run only; not checking ports."
  exit 0
fi

METHOD="dev/tcp"
if have_nc; then
  METHOD="nc"
fi

info "TCP check method: $METHOD"
echo "Results"
echo "-------"

fail_count=0
for p in "${PORTS[@]}"; do
  p="$(echo "$p" | tr -d '[:space:]')"
  [[ "$p" =~ ^[0-9]+$ ]] || { echo "[SKIP] invalid port: $p"; continue; }

  if [[ "$METHOD" == "nc" ]]; then
    if tcp_check_nc "$HOST" "$p" "$TIMEOUT"; then
      echo "[OK]   $HOST:$p reachable"
    else
      echo "[FAIL] $HOST:$p not reachable"
      fail_count=$((fail_count+1))
    fi
  else
    if tcp_check_devtcp "$HOST" "$p" "$TIMEOUT"; then
      echo "[OK]   $HOST:$p reachable"
    else
      echo "[FAIL] $HOST:$p not reachable"
      fail_count=$((fail_count+1))
    fi
  fi
done

echo
if [[ "$fail_count" -gt 0 ]]; then
  echo "[RESULT] FAIL — $fail_count port(s) failed."
  exit 1
fi

echo "[RESULT] PASS — all requested ports reachable."
exit 0
