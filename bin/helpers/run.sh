#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# shellcheck source=bin/helpers/lib/common.sh
source "$ROOT/bin/helpers/lib/common.sh"

usage() {
  cat <<'USAGE'
Usage:
  bin/helpers/run.sh --test
  bin/helpers/run.sh --print-ts
  bin/helpers/run.sh --print-root

Notes:
  - This is a tiny entrypoint for validating helpers wiring.
  - Other scripts should source specific helper libs from bin/helpers/lib/.
USAGE
}

case "${1:-}" in
  --test)
    HC_VERBOSE=1 HC_DEBUG=1
    info "This is info (HC_VERBOSE=1)"
    debug "This is debug (HC_DEBUG=1)"
    warn "This is a warning"
    ok "This is OK"

    echo
    echo "Repo root: $(repo_root)"
    echo "UTC time:  $(ts_utc)"
    echo

    echo "URL parse demo:"
    echo "  host_from_url https://example.com:8443/path -> $(host_from_url "https://example.com:8443/path")"
    echo

    echo "JSON emit demo:"
    emit_json "helpers" "n/a" "ok" 0 "Helpers wiring OK"
    ;;
  --print-ts)
    ts_utc
    ;;
  --print-root)
    repo_root
    ;;
  -h|--help|"")
    usage
    exit 0
    ;;
  *)
    die "Unknown option: $1 (try --help)"
    ;;
esac
