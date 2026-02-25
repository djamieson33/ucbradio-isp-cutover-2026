#!/usr/bin/env bash
set -euo pipefail

check_evidence_timestamps() {
  local root="$1"
  local evid_dir="$root/evidence"

  [[ -d "$evid_dir" ]] || return 0

  # Good UTC token: 20260225T1456Z
  local ts_good_re="${TS_RE}"

  # Bad timestamp-ish patterns to forbid in filenames (if any timestamp is present)
  local ts_bad_date_dash='[0-9]{4}-[0-9]{2}-[0-9]{2}'   # YYYY-MM-DD
  local ts_bad_date_us='[0-9]{4}_[0-9]{2}_[0-9]{2}'     # YYYY_MM_DD
  local ts_bad_time_dash='[0-9]{2}-[0-9]{2}-[0-9]{2}'   # HH-MM-SS

  while IFS= read -r -d '' f; do
    local rel base
    rel="${f#$root/}"
    base="$(basename "$f")"

    # Ignore macOS junk / placeholders
    if [[ "$base" == ".DS_Store" || "$base" == "README.md" || "$base" == ".gitkeep" ]]; then
      continue
    fi

    # 1) If it contains non-standard timestamp formats -> FAIL
    if [[ "$base" =~ $ts_bad_date_dash || "$base" =~ $ts_bad_date_us || "$base" =~ $ts_bad_time_dash ]]; then
      fail "Evidence filename contains non-standard timestamp pattern: $rel (use ${TS_RE} if timestamp is included)"
      continue
    fi

    # 2) If it contains a partial UTC stamp (YYYYMMDDThhmm) but NOT the good token (YYYYMMDDThhmmZ) -> FAIL
    # Bash ERE doesn't do lookahead, so do it as a two-step check.
    if [[ "$base" =~ [0-9]{8}T[0-9]{4} ]] && [[ ! "$base" =~ $ts_good_re ]]; then
      fail "Evidence filename has partial UTC timestamp (missing Z): $rel (expected ${TS_RE})"
      continue
    fi

    # 3) If it contains a good UTC token, great; if it contains no timestamp at all, also allowed.
  done < <(find "$evid_dir" -type f -print0)
}
