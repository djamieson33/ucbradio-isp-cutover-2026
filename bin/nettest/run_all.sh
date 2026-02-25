#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# UCB Radio – ISP Changeover 2026
# File:        bin/nettest/run_all.sh
# Purpose:     Run a standard management reachability suite for a given SITE_CODE.
#              Uses helpers/lib/log.sh for consistent output.
#
# Runs (in order):
#   1) ping_mgmt.sh
#   2) tcp_port.sh
#   3) curl_mgmt.sh
#   4) ssh_mgmt.sh (optional; WARN by default, FAIL only with --require-ssh)
#
# Usage:
#   bin/nettest/run_all.sh <SITE_CODE> [options]
#
# Options:
#   --prefer wan|lan        Prefer WAN or LAN mgmt URL (default: wan)
#   --ports "a,b,c"         Ports for tcp_port.sh (default: 443,22)
#   --timeout N             Timeout seconds (passed to tcp/curl/ssh; default: 4)
#   --count N               Ping count (default: 3)
#   --insecure              Pass through to curl_mgmt.sh
#   --dry-run               Do not execute; print what would run
#   --interactive           For SSH: allow interactive login (passes to ssh_mgmt.sh)
#   --require-ssh           Treat SSH failure as suite failure (default: optional)
#   --verbose               HC_VERBOSE=1
#   --debug                 HC_DEBUG=1
# ==============================================================================

usage() {
  cat <<'USAGE'
Usage:
  bin/nettest/run_all.sh <SITE_CODE> [options]

Options:
  --prefer wan|lan        Prefer WAN or LAN mgmt URL (default: wan)
  --ports "a,b,c"         Ports for tcp_port.sh (default: "443,22")
  --timeout N             Timeout seconds (default: 4)
  --count N               Ping count (default: 3)
  --insecure              Use insecure TLS for curl_mgmt.sh
  --dry-run               Print commands only; do not run
  --interactive           For SSH: allow interactive login (password prompt, etc.)
  --require-ssh           Fail the suite if SSH test fails (default: warn-only)
  --verbose               Enable info logs (HC_VERBOSE=1)
  --debug                 Enable debug logs (HC_DEBUG=1)
  -h, --help              Show help

Examples:
  bin/nettest/run_all.sh BELL-102
  bin/nettest/run_all.sh BROC-100 --prefer wan --ports "443,22" --insecure
  bin/nettest/run_all.sh BELL-102 --require-ssh
  bin/nettest/run_all.sh BELL-102 --interactive
USAGE
}

[[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 1; }

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

# ----------------------------------------------------------------------
# Load logging helpers
# ----------------------------------------------------------------------
LOG_HELPERS="$ROOT/bin/helpers/lib/log.sh"
[[ -f "$LOG_HELPERS" ]] || { echo "[ERROR] Missing: bin/helpers/lib/log.sh" >&2; exit 2; }

# shellcheck source=bin/helpers/lib/log.sh
source "$LOG_HELPERS"

SITE_CODE="$1"
shift

PREFER="wan"
PORTS="443,22"
TIMEOUT="4"
COUNT="3"
INSECURE="no"
DRY_RUN="no"
SSH_INTERACTIVE="no"
REQUIRE_SSH="no"

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
      PORTS="$1"
      ;;
    --timeout)
      shift
      [[ "${1:-}" =~ ^[0-9]+$ ]] || die "--timeout must be an integer"
      TIMEOUT="$1"
      ;;
    --count)
      shift
      [[ "${1:-}" =~ ^[0-9]+$ ]] || die "--count must be an integer"
      COUNT="$1"
      ;;
    --insecure)
      INSECURE="yes"
      ;;
    --dry-run)
      DRY_RUN="yes"
      ;;
    --interactive)
      SSH_INTERACTIVE="yes"
      ;;
    --require-ssh)
      REQUIRE_SSH="yes"
      ;;
    --verbose)
      export HC_VERBOSE=1
      ;;
    --debug)
      export HC_DEBUG=1
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

PING_SCRIPT="$ROOT/bin/nettest/ping_mgmt.sh"
TCP_SCRIPT="$ROOT/bin/nettest/tcp_port.sh"
CURL_SCRIPT="$ROOT/bin/nettest/curl_mgmt.sh"
SSH_SCRIPT="$ROOT/bin/nettest/ssh_mgmt.sh"

[[ -x "$PING_SCRIPT" ]] || die "Missing or not executable: bin/nettest/ping_mgmt.sh"
[[ -x "$TCP_SCRIPT" ]]  || die "Missing or not executable: bin/nettest/tcp_port.sh"
[[ -x "$CURL_SCRIPT" ]] || die "Missing or not executable: bin/nettest/curl_mgmt.sh"

have_ssh="no"
if [[ -f "$SSH_SCRIPT" && -x "$SSH_SCRIPT" ]]; then
  have_ssh="yes"
fi

echo
echo "Nettest suite"
echo "------------"
echo "Site code:    $SITE_CODE"
echo "Prefer:       $PREFER"
echo "Ports:        $PORTS"
echo "Timeout:      ${TIMEOUT}s"
echo "Ping count:   $COUNT"
echo "Curl TLS:     $([[ "$INSECURE" == "yes" ]] && echo "insecure" || echo "default")"
echo "SSH test:     $([[ "$have_ssh" == "yes" ]] && echo "enabled" || echo "missing (skipped)")"
echo "SSH mode:     $([[ "$SSH_INTERACTIVE" == "yes" ]] && echo "interactive" || echo "batch")"
echo "SSH required: $REQUIRE_SSH"
echo "Dry-run:      $DRY_RUN"
echo

run_cmd() {
  local label="$1"
  shift
  local cmd=( "$@" )

  echo
  echo "== $label =="
  debug "Command: ${cmd[*]}"

  if [[ "$DRY_RUN" == "yes" ]]; then
    info "Dry-run: ${cmd[*]}"
    return 0
  fi

  if "${cmd[@]}"; then
    ok "$label passed"
    return 0
  else
    fail_msg "$label failed"
    return 1
  fi
}

fail_count=0

# 1) Ping management
ping_args=( "$PING_SCRIPT" "$SITE_CODE" --prefer "$PREFER" --count "$COUNT" )
[[ "$DRY_RUN" == "yes" ]] && ping_args+=( --dry-run )
if ! run_cmd "Ping mgmt" "${ping_args[@]}"; then
  fail_count=$((fail_count+1))
fi

# 2) TCP ports
tcp_args=( "$TCP_SCRIPT" "$SITE_CODE" --prefer "$PREFER" --ports "$PORTS" --timeout "$TIMEOUT" )
[[ "$DRY_RUN" == "yes" ]] && tcp_args+=( --dry-run )
if ! run_cmd "TCP ports" "${tcp_args[@]}"; then
  fail_count=$((fail_count+1))
fi

# 3) Curl mgmt (HEAD)
curl_args=( "$CURL_SCRIPT" "$SITE_CODE" --prefer "$PREFER" --timeout "$TIMEOUT" )
[[ "$INSECURE" == "yes" ]] && curl_args+=( --insecure )
[[ "$DRY_RUN" == "yes" ]] && curl_args+=( --dry-run )
if ! run_cmd "HTTP(S) mgmt (HEAD)" "${curl_args[@]}"; then
  fail_count=$((fail_count+1))
fi

# 4) SSH mgmt (optional by default)
if [[ "$have_ssh" == "yes" ]]; then
  ssh_args=( "$SSH_SCRIPT" "$SITE_CODE" --prefer "$PREFER" --timeout "$TIMEOUT" )
  [[ "$SSH_INTERACTIVE" == "yes" ]] && ssh_args+=( --interactive )
  [[ "$DRY_RUN" == "yes" ]] && ssh_args+=( --dry-run )

  echo
  echo "== SSH mgmt =="
  debug "Command: ${ssh_args[*]}"

  if [[ "$DRY_RUN" == "yes" ]]; then
    info "Dry-run: ${ssh_args[*]}"
  else
    if "${ssh_args[@]}"; then
      ok "SSH mgmt passed"
    else
      if [[ "$REQUIRE_SSH" == "yes" ]]; then
        fail_count=$((fail_count+1))
        fail_msg "SSH mgmt failed (required)"
      else
        warn "SSH mgmt failed (optional). TCP 22 already validated; use --interactive to test login."
      fi
    fi
  fi
else
  warn "SSH test skipped (bin/nettest/ssh_mgmt.sh not present/executable)."
fi

echo
if [[ "$fail_count" -gt 0 ]]; then
  fail_msg "Suite FAIL — $fail_count check(s) failed for $SITE_CODE"
  exit 1
fi

ok "Suite PASS — all required checks passed for $SITE_CODE"
exit 0
