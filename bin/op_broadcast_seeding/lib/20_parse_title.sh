#!/usr/bin/env bash
set -euo pipefail

# parse_title_strict "<TITLE>"
#
# Expected:
#   "<ASSET_ID> - <VENDOR> <MODEL...> - <SITE_CODE>"
#
# Example:
#   "84 - Nautel VS300 - BROC-100"
#
# Outputs TSV:
#   asset_id<TAB>vendor<TAB>model<TAB>site_code<TAB>site_id
#
# Returns non-zero if title doesn't match.
parse_title_strict() {
  local title="$1"
  local delim=" - "

  # Must contain the delimiter twice
  [[ "$title" == *"$delim"*"$delim"* ]] || return 1

  # Split on the FIRST " - "
  local left="${title%%"$delim"*}"
  local rest="${title#*"$delim"}"

  # Split remaining on the NEXT " - "
  local middle="${rest%%"$delim"*}"
  local right="${rest#*"$delim"}"

  # Basic validation
  [[ -n "${left:-}" && -n "${middle:-}" && -n "${right:-}" ]] || return 1
  [[ "$left" =~ ^[0-9]+$ ]] || return 1

  local asset_id="$left"
  local device_segment="$middle"
  local site_code="$right"

  # Vendor = first token; Model = rest
  local vendor model
  vendor="$(echo "$device_segment" | awk '{print $1}')"
  model="$(echo "$device_segment" | sed -E 's/^[^[:space:]]+[[:space:]]*//')"
  [[ -n "$model" ]] || model="$vendor"

  local site_id
  site_id="$(echo "$site_code" | tr '[:upper:]' '[:lower:]')"

  printf "%s\t%s\t%s\t%s\t%s\n" \
    "$asset_id" \
    "$vendor" \
    "$model" \
    "$site_code" \
    "$site_id"
}
