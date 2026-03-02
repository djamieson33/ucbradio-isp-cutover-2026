#!/usr/bin/env bash
set -euo pipefail

# field_value <item_json> <label>
field_value() {
  local json="$1"
  local label="$2"
  echo "$json" | jq -r --arg label "$label" '
    ((.fields // []) | map(select(.label == $label)) | .[0].value) // ""
  '
}

# add_field_if_needed <label> <value> <overwrite_yesno> <item_json> <EDIT_ARGS array name> <CHANGES array name>
add_field_if_needed() {
  local label="$1"
  local value="$2"
  local overwrite="$3"
  local item_json="$4"
  local -n _edit_args="$5"
  local -n _changes="$6"

  local current
  current="$(field_value "$item_json" "$label")"

  if [[ -n "$current" ]]; then
    if [[ "$overwrite" == "yes" && "$current" != "$value" ]]; then
      _edit_args+=("$label[text]=$value")
      _changes+=("$label: '$current' -> '$value'")
    fi
  else
    _edit_args+=("$label[text]=$value")
    _changes+=("$label: (missing) -> '$value'")
  fi
}

# validate_required_fields <item_json>
validate_required_fields() {
  local json="$1"
  local missing=0
  local labels=("asset_id" "site_id" "identity_role" "identity_vendor" "identity_model" "credentials_location")

  for label in "${labels[@]}"; do
    local v
    v="$(field_value "$json" "$label")"
    if [[ -z "$v" ]]; then
      warn "Validation: missing/empty field '$label'"
      missing=$((missing+1))
    fi
  done

  [[ "$missing" -eq 0 ]]
}

# seed_required_fields_by_tag --vault V --tag T --role R --credentials-prefix P --overwrite yes/no --dry-run yes/no
seed_required_fields_by_tag() {
  local vault="" tag="" role="" cred_prefix="" overwrite="no" dry_run="no"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --vault) vault="$2"; shift 2 ;;
      --tag) tag="$2"; shift 2 ;;
      --role) role="$2"; shift 2 ;;
      --credentials-prefix) cred_prefix="$2"; shift 2 ;;
      --overwrite) overwrite="$2"; shift 2 ;;
      --dry-run) dry_run="$2"; shift 2 ;;
      *) die "seed_required_fields_by_tag: unknown arg: $1" ;;
    esac
  done

  [[ -n "$vault" && -n "$tag" && -n "$role" && -n "$cred_prefix" ]] || die "seed_required_fields_by_tag: missing required args"

  local tag_lc
  tag_lc="$(echo "$tag" | tr '[:upper:]' '[:lower:]')"

  local items_tsv
  items_tsv="$(op_list_items_by_tag "$vault" "$tag")"
  [[ -n "$items_tsv" ]] || die "No items found with tag '$tag' in vault '$vault'"

  echo "$items_tsv" | while IFS=$'\t' read -r item_id title; do
    [[ -n "${item_id:-}" && -n "${title:-}" ]] || continue
    info "Processing: $title"

    local parsed
    if ! parsed="$(parse_title_strict "$title")"; then
      warn "Skipping (title format mismatch): $title"
      continue
    fi

    local asset_id vendor model site_code site_id
    IFS=$'\t' read -r asset_id vendor model site_code site_id <<<"$parsed"

    # --------------------------------------------------------------------------
    # GUARD: refuse to proceed unless parsed site_id matches the --tag
    # This prevents accidental writes due to parsing bugs or unexpected titles.
    # --------------------------------------------------------------------------
    if [[ "$site_id" != "$tag_lc" ]]; then
      warn "Skipping (site_id mismatch): title='$title' parsed_site_id='$site_id' expected_tag='$tag_lc'"
      continue
    fi

    local credentials_location
    credentials_location="$cred_prefix $title"

    local item_json
    item_json="$(op_get_item_json "$vault" "$item_id")"

    local EDIT_ARGS=()
    local CHANGES=()

    # Required fields (asset_id always from title)
    add_field_if_needed "asset_id" "$asset_id" "$overwrite" "$item_json" EDIT_ARGS CHANGES
    add_field_if_needed "site_id" "$site_id" "$overwrite" "$item_json" EDIT_ARGS CHANGES
    add_field_if_needed "identity_role" "$role" "$overwrite" "$item_json" EDIT_ARGS CHANGES
    add_field_if_needed "identity_vendor" "$vendor" "$overwrite" "$item_json" EDIT_ARGS CHANGES
    add_field_if_needed "identity_model" "$model" "$overwrite" "$item_json" EDIT_ARGS CHANGES
    add_field_if_needed "credentials_location" "$credentials_location" "$overwrite" "$item_json" EDIT_ARGS CHANGES

    if [[ "${#EDIT_ARGS[@]}" -eq 0 ]]; then
      info "No changes needed."
      continue
    fi

    if [[ "$dry_run" == "yes" ]]; then
      echo "[DRY-RUN] Would edit item_id=$item_id title='$title'"
      printf "  - %s\n" "${CHANGES[@]}"
      continue
    fi

    op_edit_item "$vault" "$item_id" "${EDIT_ARGS[@]}"
    info "Updated:"
    printf "  - %s\n" "${CHANGES[@]}"

    local updated_json
    updated_json="$(op_get_item_json "$vault" "$item_id")"
    if validate_required_fields "$updated_json"; then
      info "Validation OK."
    else
      warn "Post-edit validation failed for: $title (item_id=$item_id)"
    fi
  done

  info "Done."
}
