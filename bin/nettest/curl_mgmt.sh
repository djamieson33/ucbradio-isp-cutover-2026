#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# UCB Radio – ISP Changeover 2026
# File:        bin/nettest/curl_mgmt.sh
# Purpose:     Fetch HTTP status/headers and (if HTTPS) show TLS cert subject/issuer/dates
#              for the resolved management URL for a site_code/device.
#
# Usage:
#   bin/nettest/curl_mgmt.sh <SITE_CODE> [--prefer lan|wan] [--timeout N] [--insecure] [--dry-run]
#
# Examples:
#   bin/nettest/curl_mgmt.sh BELL-102
#   bin/nettest/curl_mgmt.sh BROC-100 --prefer wan
#   bin/nettest/curl_mgmt.sh BELL-102 --prefer lan --dry-run
#
# Depends on:
#   - bin/helpers/lib/env.sh (resolve_site, host_from_url, print_context)
# ==============================================================================

die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO]  $*"; }

usage() {
  cat <<'USAGE'
Usage:
  bin/nettest/curl_mgmt.sh <SITE_CODE> [--prefer lan|wan] [--timeout N] [--insecure] [--dry-run]

Arguments:
  SITE_CODE              e.g., BELL-102, BROC-100, CHAT-101

Options:
  --prefer lan|wan        Prefer which management URL to use. Default: wan (then lan fallback).
  --timeout N             Curl connect+transfer max time (seconds). Default: 8
  --insecure              Allow insecure TLS (curl -k). Useful for self-signed mgmt certs.
  --dry-run               Print resolved context and selected URL only; do not curl/openssl.
  -h, --help              Show help

Output:
  - Selected management URL
  - HTTP status line + response headers (HEAD request)
  - If HTTPS: TLS cert subject/issuer/notBefore/notAfter

Notes:
  - This does not change routing/SD-WAN; it tests whatever path your client currently uses.
USAGE
}

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PREFER="wan"
TIMEOUT="8"
INSECURE="no"
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
    --timeout)
      shift
      [[ "${1:-}" =~ ^[0-9]+$ ]] || die "--timeout must be an integer"
      TIMEOUT="$1"
      ;;
    --insecure)
      INSECURE="yes"
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

require_cmd curl

resolve_site "$SITE_CODE" || die "Unable to resolve site: $SITE_CODE"

# Select URL based on preference, with fallback
URL=""
if [[ "$PREFER" == "lan" ]]; then
  [[ -n "${MGMT_LAN_URL:-}" ]] && URL="$MGMT_LAN_URL"
  [[ -z "$URL" && -n "${MGMT_WAN_URL:-}" ]] && URL="$MGMT_WAN_URL"
else
  [[ -n "${MGMT_WAN_URL:-}" ]] && URL="$MGMT_WAN_URL"
  [[ -z "$URL" && -n "${MGMT_LAN_URL:-}" ]] && URL="$MGMT_LAN_URL"
fi

# Treat "unknown" as empty (in case YAML uses that string)
[[ "${URL:-}" == "unknown" ]] && URL=""

[[ -n "$URL" ]] || die "No management URL found (management.wan_url/lan_url missing or unknown in $DEVICE_YAML)"

# Parse URL: scheme, host, port
scheme_from_url() {
  local u="${1:-}"
  if [[ "$u" == https://* ]]; then echo "https"; return 0; fi
  if [[ "$u" == http://* ]]; then echo "http"; return 0; fi
  echo ""
}
port_from_url() {
  local u="${1:-}"
  u="${u#http://}"; u="${u#https://}"
  u="${u%%/*}"
  if [[ "$u" == *:* ]]; then
    echo "${u##*:}"
  else
    echo ""
  fi
}

SCHEME="$(scheme_from_url "$URL")"
HOST="$(host_from_url "$URL")"
PORT="$(port_from_url "$URL")"

[[ -n "$SCHEME" ]] || die "Mgmt URL must start with http:// or https:// (got: $URL)"
[[ -n "$HOST" ]] || die "Unable to parse host from URL: $URL"

if [[ -z "$PORT" ]]; then
  if [[ "$SCHEME" == "https" ]]; then PORT="443"; else PORT="80"; fi
fi

echo
echo "Resolved context"
echo "----------------"
print_context
echo "Prefer:        $PREFER"
echo "Selected URL:  $URL"
echo "Scheme:        $SCHEME"
echo "Host:          $HOST"
echo "Port:          $PORT"
echo "Timeout:       ${TIMEOUT}s"
echo "Insecure TLS:  $INSECURE"
echo

if [[ "$DRY_RUN" == "yes" ]]; then
  info "Dry-run only; not curling/openssl."
  exit 0
fi

CURL_ARGS=(-sS -I -D - -o /dev/null --max-time "$TIMEOUT")
if [[ "$INSECURE" == "yes" ]]; then
  CURL_ARGS+=(-k)
fi

info "HTTP HEAD: $URL"
echo "----------------"
# Print headers to stdout
curl "${CURL_ARGS[@]}" "$URL" || die "curl failed for: $URL"
echo

if [[ "$SCHEME" == "https" ]]; then
  require_cmd openssl
  info "TLS certificate (best-effort): $HOST:$PORT"
  echo "------------------------------"
  # Best-effort: fetch server cert and print subject/issuer/dates
  # Using -servername for SNI (important for hostnames)
  CERT_OUT="$(
    echo | openssl s_client -servername "$HOST" -connect "${HOST}:${PORT}" 2>/dev/null \
      | openssl x509 -noout -subject -issuer -dates 2>/dev/null || true
  )"
  if [[ -n "$CERT_OUT" ]]; then
    echo "$CERT_OUT"
  else
    echo "[WARN] Unable to read TLS certificate (may be blocked, non-HTTPS, or using non-standard port/cipher)."
  fi
  echo
fi

info "Done."
