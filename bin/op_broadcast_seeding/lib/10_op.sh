#!/usr/bin/env bash
set -euo pipefail

# op_list_items_by_tag <vault> <tag>
# Output TSV: "<id>\t<title>"
op_list_items_by_tag() {
  local vault="$1"
  local tag="$2"
  local tag_lc
  tag_lc="$(echo "$tag" | tr '[:upper:]' '[:lower:]')"

  op item list --vault "$vault" --format json \
  | jq -r --arg tag "$tag_lc" '
      .[]
      | select((.tags // []) | map(ascii_downcase) | index($tag))
      | "\(.id)\t\(.title)"
    '
}

# op_get_item_json <vault> <id>
op_get_item_json() {
  local vault="$1"
  local id="$2"
  op item get "$id" --vault "$vault" --format json
}

# op_edit_item <vault> <id> <args...>
# args are op assignments, e.g. "asset_id[text]=84"
op_edit_item() {
  local vault="$1"
  local id="$2"
  shift 2
  op item edit "$id" --vault "$vault" "$@" >/dev/null
}
