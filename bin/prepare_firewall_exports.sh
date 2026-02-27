#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# File:        bin/prepare_firewall_exports.sh
# Purpose:     Prepare and seed a firewall export folder end-to-end (by ASSET ID),
#              using inventory YAML as source of truth (device_key + site slug).
#
# Usage:
#   ./bin/prepare_firewall_exports.sh <asset-id> [options]
#
# Options:
#   --dry-run
#   --timestamp YYYYMMDDThhmmZ
#   --unresolved-limit N
#   --no-show-unresolved
#   --apply-unresolved-dry-run     (passes through to run.py when applying)
#   --ensure-scope                 (pre-creates scoped.<fw_key> in overrides)
#
# Examples:
#   ./bin/prepare_firewall_exports.sh 1
#   ./bin/prepare_firewall_exports.sh 1 --dry-run
#   ./bin/prepare_firewall_exports.sh 1 --timestamp 20260226T2334Z
#   ./bin/prepare_firewall_exports.sh 6 --unresolved-limit 200
#   ./bin/prepare_firewall_exports.sh 6 --apply-unresolved-dry-run
#   ./bin/prepare_firewall_exports.sh 6 --ensure-scope
#
# Behavior:
#   - Finds firewall inventory file:
#       inventory/devices/firewalls/<asset-id>-fw-*.yaml
#   - Reads from YAML:
#       device.device_key   => firewall device key
#       site.short          => site slug (fallback: site.code)
#   - Finds exports folder (preferred):
#       firewall/sonicwall/exports/<device_key>/
#     Fallback:
#       any folder starting with "<asset-id>-fw-" under firewall/sonicwall/exports/
#   - Applies ONE shared UTC timestamp to unstamped CSVs in that folder
#   - Validates required exports exist
#   - Runs bin/seed_inbound_services/run.py with:
#       --exports-dir <folder>
#       --firewall-device-key <device_key>
#       --site <site.short>
#       --apply-unresolved-overrides  (AUTO-add scoped skeletons to overrides file)
# ==============================================================================

die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO]  $*"; }

[[ $# -lt 1 ]] && die "Usage: $0 <asset-id> [--dry-run] [--timestamp YYYYMMDDThhmmZ] [--unresolved-limit N] [--no-show-unresolved] [--apply-unresolved-dry-run] [--ensure-scope]"

ASSET_ID="$1"
shift || true

DRY_RUN="no"
USER_TS=""
SHOW_UNRESOLVED="yes"
UNRESOLVED_LIMIT="50"
APPLY_UNRESOLVED_DRY_RUN="no"
ENSURE_SCOPE="no"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN="yes" ;;
    --timestamp)
      shift || die "--timestamp requires a value"
      USER_TS="${1:-}"
      ;;
    --unresolved-limit)
      shift || die "--unresolved-limit requires a value"
      UNRESOLVED_LIMIT="${1:-}"
      ;;
    --no-show-unresolved)
      SHOW_UNRESOLVED="no"
      ;;
    --apply-unresolved-dry-run)
      APPLY_UNRESOLVED_DRY_RUN="yes"
      ;;
    --ensure-scope)
      ENSURE_SCOPE="yes"
      ;;
    -h|--help)
      sed -n '1,200p' "$0"
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
  shift || true
done

[[ "$UNRESOLVED_LIMIT" =~ ^[0-9]+$ ]] || die "--unresolved-limit must be an integer"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

INV_DIR="inventory/devices/firewalls"
EXPORTS_ROOT="firewall/sonicwall/exports"

[[ -d "$INV_DIR" ]] || die "Inventory folder not found: $INV_DIR"
[[ -d "$EXPORTS_ROOT" ]] || die "Exports root not found: $EXPORTS_ROOT"

# --------------------------------------------------
# 1) Find firewall inventory YAML for this asset
# --------------------------------------------------
shopt -s nullglob
inv_matches=( "$INV_DIR/${ASSET_ID}-fw-"*.yaml )

if [[ ${#inv_matches[@]} -eq 0 ]]; then
  die "No inventory YAML found for asset ${ASSET_ID} (expected: ${INV_DIR}/${ASSET_ID}-fw-*.yaml)"
fi
if [[ ${#inv_matches[@]} -gt 1 ]]; then
  echo "[ERROR] Multiple inventory YAML files match asset ${ASSET_ID}. Please disambiguate:" >&2
  for f in "${inv_matches[@]}"; do
    echo "  - $(basename "$f")" >&2
  done
  die "Ensure only one ${ASSET_ID}-fw-*.yaml exists for this asset."
fi

INV_FILE="${inv_matches[0]}"
info "Inventory file: $INV_FILE"

# --------------------------------------------------
# 2) Read device_key + site slug from YAML (via python)
# --------------------------------------------------
PY_OUT="$(
python - "$INV_FILE" <<'PY'
import sys, pathlib
try:
    import yaml
except Exception as e:
    print(f"[ERROR] PyYAML not installed: {e}", file=sys.stderr)
    sys.exit(2)

p = pathlib.Path(sys.argv[1])
data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

device_key = ((data.get("device") or {}).get("device_key") or "").strip()
site_short = ((data.get("site") or {}).get("short") or "").strip()
site_code  = ((data.get("site") or {}).get("code") or "").strip()

site = site_short or site_code

if not device_key:
    print("[ERROR] Missing device.device_key in inventory YAML", file=sys.stderr)
    sys.exit(2)
if not site:
    print("[ERROR] Missing site.short (or site.code fallback) in inventory YAML", file=sys.stderr)
    sys.exit(2)

print(device_key)
print(site)
PY
)" || exit $?

FW_KEY="$(printf '%s\n' "$PY_OUT" | sed -n '1p')"
SITE_SLUG="$(printf '%s\n' "$PY_OUT" | sed -n '2p')"

[[ -n "$FW_KEY" ]] || die "Could not read device_key from inventory YAML"
[[ -n "$SITE_SLUG" ]] || die "Could not read site slug from inventory YAML"

info "Firewall device key: $FW_KEY"
info "Site slug (from inventory): $SITE_SLUG"

# --------------------------------------------------
# 3) Locate exports folder (prefer device_key folder)
# --------------------------------------------------
EXPORT_DIR="$EXPORTS_ROOT/$FW_KEY"

if [[ ! -d "$EXPORT_DIR" ]]; then
  shopt -s nullglob
  ex_matches=( "$EXPORTS_ROOT/${ASSET_ID}-fw-"* )
  if [[ ${#ex_matches[@]} -eq 1 && -d "${ex_matches[0]}" ]]; then
    EXPORT_DIR="${ex_matches[0]}"
    info "Exports folder fallback match: $EXPORT_DIR"
  else
    die "Exports folder not found. Expected: $EXPORTS_ROOT/$FW_KEY (or a single ${ASSET_ID}-fw-* folder)."
  fi
fi

info "Exports folder: $EXPORT_DIR"
info "Dry run: $DRY_RUN"

# --------------------------------------------------
# 4) Stamp unstamped CSV files (single shared timestamp)
# --------------------------------------------------
TS_RE='[0-9]{8}T[0-9]{4}Z'
if [[ -n "$USER_TS" ]]; then
  [[ "$USER_TS" =~ ^[0-9]{8}T[0-9]{4}Z$ ]] || die "Invalid --timestamp. Expected YYYYMMDDThhmmZ"
  TIMESTAMP="$USER_TS"
else
  TIMESTAMP="$(date -u +"%Y%m%dT%H%MZ")"
fi

info "Using timestamp: $TIMESTAMP"

for f in "$EXPORT_DIR"/*.csv; do
  [[ -e "$f" ]] || continue
  base="$(basename "$f")"

  if [[ "$base" =~ $TS_RE ]]; then
    info "Already stamped: $base"
    continue
  fi

  name="${base%.*}"
  ext="${base##*.}"
  new="${EXPORT_DIR}/${name}-${TIMESTAMP}.${ext}"

  [[ -f "$new" ]] && die "Target already exists: $new"

  if [[ "$DRY_RUN" == "yes" ]]; then
    info "Would stamp: $base → $(basename "$new")"
  else
    mv "$f" "$new"
    info "Stamped: $base → $(basename "$new")"
  fi
done

# --------------------------------------------------
# 5) Validate required exports exist
# --------------------------------------------------
NAT_FILE=$(ls "$EXPORT_DIR"/nat-configurations-*.csv 2>/dev/null | tail -n1 || true)
POLICY_FILE=$(ls "$EXPORT_DIR"/security-policy-*.csv 2>/dev/null | tail -n1 || true)

[[ -f "$NAT_FILE" ]] || die "nat-configurations-*.csv not found in $EXPORT_DIR"
[[ -f "$POLICY_FILE" ]] || die "security-policy-*.csv not found in $EXPORT_DIR"

info "NAT file: $(basename "$NAT_FILE")"
info "Policy file: $(basename "$POLICY_FILE")"

# --------------------------------------------------
# 6) Run seed_inbound_services (per-firewall output)
#     + auto-apply unresolved targets into overrides (scoped-only)
# --------------------------------------------------
RUN_ARGS=(
  "bin/seed_inbound_services/run.py"
  "--exports-dir" "$EXPORT_DIR"
  "--site" "$SITE_SLUG"
  "--firewall-device-key" "$FW_KEY"
  "--apply-unresolved-overrides"
  "--unresolved-limit" "$UNRESOLVED_LIMIT"
)

if [[ "$SHOW_UNRESOLVED" != "yes" ]]; then
  RUN_ARGS+=( "--no-show-unresolved" )
fi

if [[ "$APPLY_UNRESOLVED_DRY_RUN" == "yes" ]]; then
  RUN_ARGS+=( "--apply-unresolved-dry-run" )
fi

if [[ "$ENSURE_SCOPE" == "yes" ]]; then
  RUN_ARGS+=( "--ensure-scope" )
fi

if [[ "$DRY_RUN" == "yes" ]]; then
  info "Would run:"
  printf '[INFO]   python %q' "${RUN_ARGS[@]}"
  echo
  exit 0
fi

info "Running seed_inbound_services..."
python "${RUN_ARGS[@]}"

info "Done."
