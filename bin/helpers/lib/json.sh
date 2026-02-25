#!/usr/bin/env bash

json_escape_py() {
  python3 - <<'PY'
import json,sys
print(json.dumps(sys.stdin.read()))
PY
}

emit_json() {
  # Args: check env status exit_code message
  local check="${1:-}"
  local env="${2:-}"
  local status="${3:-}"
  local code="${4:-1}"
  local msg="${5:-}"

  local msg_json
  msg_json="$(printf "%s" "$msg" | json_escape_py)"

  printf '{'
  printf '"timestamp":"%s",' "$(ts_utc)"
  printf '"check":"%s",' "$check"
  printf '"env":"%s",' "$env"
  printf '"status":"%s",' "$status"
  printf '"exit_code":%s,' "$code"
  printf '"message":%s' "$msg_json"
  printf '}\n'
}
