#!/usr/bin/env bash
# ==============================================================================
# UCB Radio – ISP Changeover 2026
# ------------------------------------------------------------------------------
# File:        bin/helpers/lib/env.sh
# Purpose:     Resolve a site/device "environment" from inventory YAML:
#                site_code -> device yaml -> mgmt urls -> base_host
#
# Notes:
#   - Do NOT enable strict mode here; scripts that source this file decide.
#   - This helper expects Python + PyYAML for safe YAML reads.
#       pip install pyyaml
#
# Exports (after resolve_site):
#   SITE_CODE        e.g., "BROC-100"
#   DEVICE_YAML      path to matching inventory YAML
#   DEVICE_NAME      from YAML (device.name)
#   MGMT_WAN_URL     from YAML (management.wan_url)
#   MGMT_LAN_URL     from YAML (management.lan_url) if present
#   MGMT_HOST        derived host from MGMT_WAN_URL (or MGMT_LAN_URL fallback)
# ==============================================================================

# shellcheck disable=SC2155

# ------------------------------------------------------------------------------
# Minimal logging (caller can override these if desired)
# ------------------------------------------------------------------------------
_env_info() { echo "[INFO]  $*"; }
_env_warn() { echo "[WARN]  $*" >&2; }
_env_die()  { echo "[ERROR] $*" >&2; return 2; }

# ------------------------------------------------------------------------------
# Repo root
# ------------------------------------------------------------------------------
repo_root() {
  (cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
}

# ------------------------------------------------------------------------------
# Requirements
# ------------------------------------------------------------------------------
require_cmd() {
  command -v "$1" >/dev/null 2>&1 || _env_die "Missing required command: $1"
}

python_has_pyyaml() {
  python3 - <<'PY' >/dev/null 2>&1
import yaml  # noqa: F401
PY
}

# ------------------------------------------------------------------------------
# URL helpers
# ------------------------------------------------------------------------------
host_from_url() {
  # Extract host from a URL-ish string (handles http(s)://host[:port]/path)
  local u="${1:-}"
  [[ -n "$u" ]] || { printf '%s' ""; return 0; }
  u="${u#http://}"
  u="${u#https://}"
  u="${u%%/*}"
  u="${u%%:*}"
  printf '%s' "$u"
}

# ------------------------------------------------------------------------------
# YAML helpers (safe read via PyYAML)
# ------------------------------------------------------------------------------
py_yaml_get() {
  # Usage: py_yaml_get <yaml_file> <dot.path>
  # Example: py_yaml_get inventory/devices/firewalls/9-fw-sonicwall-broc-100.yaml management.wan_url
  local file="${1:-}"
  local keypath="${2:-}"
  [[ -f "$file" ]] || _env_die "YAML not found: $file"
  [[ -n "$keypath" ]] || _env_die "py_yaml_get: missing keypath"

  python3 - "$file" "$keypath" <<'PY'
import sys
from pathlib import Path

try:
  import yaml
except Exception:
  sys.stderr.write("[ERROR] Python PyYAML not available. Install with: pip install pyyaml\n")
  sys.exit(2)

p = Path(sys.argv[1])
keypath = sys.argv[2]
data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

cur = data
for part in keypath.split("."):
  if isinstance(cur, dict) and part in cur:
    cur = cur[part]
  else:
    cur = None
    break

if cur is None:
  sys.exit(0)

# Emit scalars as strings; lists/dicts as JSON for debugging (rarely needed here).
if isinstance(cur, (dict, list)):
  import json
  sys.stdout.write(json.dumps(cur, ensure_ascii=False))
else:
  sys.stdout.write(str(cur))
PY
}

# ------------------------------------------------------------------------------
# Device YAML discovery
# ------------------------------------------------------------------------------
_find_device_yaml_candidates() {
  # Emits newline-separated paths under inventory/devices/**.y*ml
  local root
  root="$(repo_root)"
  find "$root/inventory/devices" -type f \( -name "*.yaml" -o -name "*.yml" \) 2>/dev/null
}

_find_device_yaml_by_site_code() {
  # Usage: _find_device_yaml_by_site_code <SITE_CODE>
  # Match priority:
  #   1) device.site_code == SITE_CODE
  #   2) device.name      == SITE_CODE
  local want="${1:-}"
  [[ -n "$want" ]] || return 1

  require_cmd python3
  python_has_pyyaml || _env_die "PyYAML missing. Run: pip install pyyaml (inside your venv)"

  # We do the matching in Python to avoid fragile grep-parsing YAML.
  local root
  root="$(repo_root)"

  python3 - "$root" "$want" <<'PY'
import sys
from pathlib import Path

try:
  import yaml
except Exception:
  sys.stderr.write("[ERROR] Python PyYAML not available. Install with: pip install pyyaml\n")
  sys.exit(2)

root = Path(sys.argv[1])
want = sys.argv[2].strip()

def norm(s: str) -> str:
  return (s or "").strip().lower()

paths = sorted((root / "inventory" / "devices").rglob("*.y*ml"))
best = None
fallback = None

for p in paths:
  try:
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
  except Exception:
    continue
  dev = data.get("device") or {}
  site_code = dev.get("site_code")
  name = dev.get("name")
  if norm(site_code) == norm(want):
    best = p
    break
  if fallback is None and norm(name) == norm(want):
    fallback = p

out = best or fallback
if out:
  sys.stdout.write(str(out))
PY
}

# ------------------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------------------
resolve_site() {
  # Usage: resolve_site <SITE_CODE>
  # Exports:
  #   SITE_CODE DEVICE_YAML DEVICE_NAME MGMT_WAN_URL MGMT_LAN_URL MGMT_HOST
  local sc="${1:-}"
  [[ -n "$sc" ]] || _env_die "resolve_site: missing SITE_CODE (e.g., BROC-100)"

  local yaml_path
  yaml_path="$(_find_device_yaml_by_site_code "$sc")" || return 2
  [[ -n "$yaml_path" ]] || _env_die "No device YAML found for site_code/name: $sc"

  local name wan lan
  name="$(py_yaml_get "$yaml_path" "device.name" || true)"
  wan="$(py_yaml_get "$yaml_path" "management.wan_url" || true)"
  lan="$(py_yaml_get "$yaml_path" "management.lan_url" || true)"

  # Determine mgmt host preference: WAN first, then LAN.
  local host=""
  if [[ -n "$wan" ]]; then
    host="$(host_from_url "$wan")"
  elif [[ -n "$lan" ]]; then
    host="$(host_from_url "$lan")"
  fi

  export SITE_CODE="$sc"
  export DEVICE_YAML="$yaml_path"
  export DEVICE_NAME="${name:-}"
  export MGMT_WAN_URL="${wan:-}"
  export MGMT_LAN_URL="${lan:-}"
  export MGMT_HOST="${host:-}"

  return 0
}

print_context() {
  # Usage: print_context
  echo "Site code:    ${SITE_CODE:-}"
  echo "Device YAML:  ${DEVICE_YAML:-}"
  echo "Device name:  ${DEVICE_NAME:-}"
  echo "Mgmt WAN URL: ${MGMT_WAN_URL:-}"
  echo "Mgmt LAN URL: ${MGMT_LAN_URL:-}"
  echo "Mgmt host:    ${MGMT_HOST:-}"
}

get_mgmt_wan_url() { printf '%s' "${MGMT_WAN_URL:-}"; }
get_mgmt_lan_url() { printf '%s' "${MGMT_LAN_URL:-}"; }
get_mgmt_host()    { printf '%s' "${MGMT_HOST:-}"; }
get_device_yaml()  { printf '%s' "${DEVICE_YAML:-}"; }

# ------------------------------------------------------------------------------
# Self-test / demo
# ------------------------------------------------------------------------------
if [[ "${1:-}" == "--test" ]]; then
  shift || true
  sc="${1:-BELL-102}"
  if resolve_site "$sc"; then
    _env_info "Resolved $sc"
    print_context
    exit 0
  fi
  exit 2
fi
