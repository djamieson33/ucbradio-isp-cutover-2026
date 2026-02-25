#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# UCB Radio – ISP Changeover 2026
# File:        bin/nettest/ssh_mgmt.sh
# Purpose:     SSH connectivity test to a site's management host (WAN/LAN),
#              using resolve_site() from bin/helpers/lib/env.sh.
#
# Behavior:
#   - Resolves SITE_CODE -> device YAML -> management URLs
#   - Selects host (prefer WAN unless --prefer lan)
#   - Performs a safe SSH probe (no password prompts by default)
#
# Usage:
#   bin/nettest/ssh_mgmt.sh <SITE_CODE> [--prefer wan|lan] [--user USER]
#                           [--port N] [--timeout N] [--cmd "command"]
#                           [--interactive] [--dry-run] [--insecure-hostkey]
#
# Examples:
#   bin/nettest/ssh_mgmt.sh BELL-102 --dry-run
#   bin/nettest/ssh_mgmt.sh BROC-100 --prefer wan --user admin --timeout 6
#   bin/nettest/ssh_mgmt.sh BROC-100 --interactive --user admin
# ==============================================================================
die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO]  $*"; }

usage() {
  cat <<'USAGE'
Usage:
  bin/nettest/ssh_mgmt.sh <SITE_CODE> [options]

Options:
  --prefer wan|lan        Which management URL to prefer (default: wan)
  --user USER             SSH username (default: from device YAML if available, else "admin")
  --port N                Override SSH port (default: 22, or parsed from host:port)
  --timeout N             Connection timeout seconds (default: 8)
  --cmd "..."             Command to run (default: "exit")
  --interactive           Start interactive SSH session (ignores --cmd)
  --insecure-hostkey      Disable host key checking (NOT recommended; use only if needed)
  --dry-run               Print resolved target and SSH command; do not connect
  -h, --help              Show help

Notes:
  - By default this is a probe: it will NOT prompt for passwords (BatchMode).
  - If you want to actually log in, use --interactive.
USAGE
}

[[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 1; }

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

SITE_CODE="$1"
shift

PREFER="wan"
USER_OVERRIDE=""
PORT_OVERRIDE=""
TIMEOUT="8"
CMD="exit"
INTERACTIVE="no"
DRY_RUN="no"
INSECURE_HOSTKEY="no"

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --prefer)
      shift
      [[ "${1:-}" == "wan" || "${1:-}" == "lan" ]] || die "--prefer must be wan|lan"
      PREFER="$1"
      ;;
    --user)
      shift
      [[ -n "${1:-}" ]] || die "--user requires a value"
      USER_OVERRIDE="$1"
      ;;
    --port)
      shift
      [[ "${1:-}" =~ ^[0-9]+$ ]] || die "--port must be an integer"
      PORT_OVERRIDE="$1"
      ;;
    --timeout)
      shift
      [[ "${1:-}" =~ ^[0-9]+$ ]] || die "--timeout must be an integer"
      TIMEOUT="$1"
      ;;
    --cmd)
      shift
      [[ -n "${1:-}" ]] || die "--cmd requires a value"
      CMD="$1"
      ;;
    --interactive)
      INTERACTIVE="yes"
      ;;
    --insecure-hostkey)
      INSECURE_HOSTKEY="yes"
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

command -v ssh >/dev/null 2>&1 || die "ssh is required."

# Helpers (no external deps)
host_from_urlish() {
  local u="${1:-}"
  u="${u#http://}"
  u="${u#https://}"
  u="${u%%/*}"
  printf '%s' "$u"
}

split_host_port() {
  # input: host[:port]  -> echoes "host" then "port" (port may be empty)
  local hp="${1:-}"
  local host="${hp}"
  local port=""
  if [[ "$hp" == *:* ]]; then
    host="${hp%:*}"
    port="${hp##*:}"
    # if host itself had ":" (ipv6), ignore (we're not using ipv6 literals here)
    [[ "$host" == *:* ]] && { host="$hp"; port=""; }
  fi
  echo "$host"
  echo "$port"
}

# Resolve site context
HELPERS_ENV="$ROOT/bin/helpers/lib/env.sh"
[[ -f "$HELPERS_ENV" ]] || die "Missing: bin/helpers/lib/env.sh (needed for resolve_site)"

# shellcheck source=bin/helpers/lib/env.sh
source "$HELPERS_ENV"

resolve_site "$SITE_CODE" >/dev/null 2>&1 || die "Unable to resolve site: $SITE_CODE"

# Expected exports from resolve_site:
#   DEVICE_YAML, DEVICE_NAME, MGMT_WAN_URL, MGMT_LAN_URL, MGMT_USER (best-effort)

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

PORT="${PORT_OVERRIDE:-${PARSED_PORT:-22}}"
[[ "$PORT" =~ ^[0-9]+$ ]] || PORT="22"

USER="${USER_OVERRIDE:-${MGMT_USER:-admin}}"

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
echo "SSH user:      $USER"
echo "SSH host:      $HOST"
echo "SSH port:      $PORT"
echo "Timeout:       ${TIMEOUT}s"
echo "Interactive:   $INTERACTIVE"
echo

SSH_OPTS=(
  "-p" "$PORT"
  "-o" "ConnectTimeout=$TIMEOUT"
  "-o" "ServerAliveInterval=5"
  "-o" "ServerAliveCountMax=2"
)

if [[ "$INSECURE_HOSTKEY" == "yes" ]]; then
  SSH_OPTS+=("-o" "StrictHostKeyChecking=no" "-o" "UserKnownHostsFile=/dev/null")
fi

if [[ "$INTERACTIVE" == "no" ]]; then
  # Probe mode: avoid prompts; fail fast if auth isn't preconfigured
  SSH_OPTS+=("-o" "BatchMode=yes")
fi

TARGET="${USER}@${HOST}"

if [[ "$DRY_RUN" == "yes" ]]; then
  info "Dry-run only; not connecting."
  if [[ "$INTERACTIVE" == "yes" ]]; then
    echo "ssh ${SSH_OPTS[*]} $TARGET"
  else
    echo "ssh ${SSH_OPTS[*]} $TARGET $(printf '%q' "$CMD")"
  fi
  exit 0
fi

if [[ "$INTERACTIVE" == "yes" ]]; then
  info "Starting interactive SSH session: $TARGET"
  exec ssh "${SSH_OPTS[@]}" "$TARGET"
else
  info "SSH probe: $TARGET (cmd: $CMD)"
  ssh "${SSH_OPTS[@]}" "$TARGET" "$CMD" && {
    echo
    echo "[OK] SSH probe succeeded."
    exit 0
  }

  echo
  echo "[FAIL] SSH probe failed."
  echo "Tip: if auth is not set up yet, run with --interactive to log in manually."
  exit 1
fi
