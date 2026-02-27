#!/usr/bin/env bash

wpcli_detect() {
  command -v wp >/dev/null 2>&1
}

wpcli_home_host() {
  local home site host
  home="$(wp option get home 2>/dev/null || true)"
  site="$(wp option get siteurl 2>/dev/null || true)"

  host="$(host_from_url "${home:-}")"
  [[ -n "$host" ]] || host="$(host_from_url "${site:-}")"
  printf '%s' "$host"
}

wpcli_host_matches_base() {
  [[ -n "${BASE_HOST:-}" ]] || return 1
  wpcli_detect || return 1
  local wp_host
  wp_host="$(wpcli_home_host)"
  [[ -n "$wp_host" ]] || return 1
  [[ "$wp_host" == "$BASE_HOST" ]]
}
