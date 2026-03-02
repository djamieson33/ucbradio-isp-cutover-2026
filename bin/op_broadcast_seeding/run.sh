#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# UCB Radio – ISP Changeover 2026
# Tool:        op_broadcast_seeding
# Entry:       op_broadcast_seeding/run.sh
#
# Purpose:
#   Seed/repair canonical required fields on 1Password items in a vault,
#   filtered by tag, using title parsing:
#     "<ASSET_ID> - <VENDOR> <MODEL...> - <SITE_CODE>"
#
# Seeds (by label):
#   - asset_id                (ALWAYS derived from leading number in TITLE)
#   - site_id                 (derived from trailing SITE_CODE in TITLE -> lowercase)
#   - identity_role           (from --role)
#   - identity_vendor         (derived from device segment in TITLE)
#   - identity_model          (derived from device segment in TITLE)
#   - credentials_location    (derived from prefix + TITLE)
#
# Usage:
#   op_broadcast_seeding/run.sh --tag broc-100 [options]
#
# Options:
#   --vault NAME                 (default: Broadcasting)
#   --tag SITE_TAG               (required)
#   --role ROLE                  (default: transmitter)
#   --credentials-prefix STRING  (default: "1Password > UCB > Broadcast >")
#   --overwrite                  (update existing fields if different)
#   --dry-run                    (show planned edits; no writes)
#   -h|--help
# ==============================================================================

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load libs in a visible, numbered order.
# shellcheck source=op_broadcast_seeding/lib/00_common.sh
source "$ROOT/lib/00_common.sh"
# shellcheck source=op_broadcast_seeding/lib/10_op.sh
source "$ROOT/lib/10_op.sh"
# shellcheck source=op_broadcast_seeding/lib/20_parse_title.sh
source "$ROOT/lib/20_parse_title.sh"
# shellcheck source=op_broadcast_seeding/lib/30_seed_fields.sh
source "$ROOT/lib/30_seed_fields.sh"

VAULT="Broadcasting"
TAG=""
ROLE="transmitter"
CRED_PREFIX="1Password > UCB > Broadcast >"
OVERWRITE="no"
DRY_RUN="no"

usage() {
  cat <<'USAGE'
Usage:
  op_broadcast_seeding/run.sh --tag broc-100 [options]

Options:
  --vault NAME                 1Password vault name (default: Broadcasting)
  --tag SITE_TAG               Site tag to filter (required), e.g. broc-100
  --role ROLE                  identity_role value (default: transmitter)
  --credentials-prefix STRING  Prefix for credentials_location (default: "1Password > UCB > Broadcast >")
  --overwrite                  Update existing fields when different
  --dry-run                    Do not write; show what would change
  -h, --help                   Show help

Notes:
  - asset_id ALWAYS derived from the leading number in the 1Password item title.
  - Title must follow: "<ASSET_ID> - <VENDOR> <MODEL...> - <SITE_CODE>"
USAGE
}

if [[ $# -eq 0 ]]; then
  usage
  exit 2
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --vault) VAULT="${2:-}"; shift 2 ;;
    --tag) TAG="${2:-}"; shift 2 ;;
    --role) ROLE="${2:-}"; shift 2 ;;
    --credentials-prefix) CRED_PREFIX="${2:-}"; shift 2 ;;
    --overwrite) OVERWRITE="yes"; shift ;;
    --dry-run) DRY_RUN="yes"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
done

[[ -n "$TAG" ]] || die "--tag is required"

need_cmd op
need_cmd jq

info "Vault:              $VAULT"
info "Tag filter:         $TAG"
info "identity_role:      $ROLE"
info "credentials prefix: $CRED_PREFIX"
info "Overwrite:          $OVERWRITE"
info "Dry-run:            $DRY_RUN"

seed_required_fields_by_tag \
  --vault "$VAULT" \
  --tag "$TAG" \
  --role "$ROLE" \
  --credentials-prefix "$CRED_PREFIX" \
  --overwrite "$OVERWRITE" \
  --dry-run "$DRY_RUN"
