#!/usr/bin/env bash

host_from_url() {
  local u="${1:-}"
  [[ -n "$u" ]] || { printf '%s' ""; return 0; }
  u="${u#http://}"
  u="${u#https://}"
  u="${u%%/*}"
  u="${u%%:*}"
  printf '%s' "$u"
}

validate_base_url() {
  local url="${1:-}"
  [[ -n "$url" ]] || die "BASE_URL is empty"
  [[ "$url" =~ ^https?:// ]] || die "BASE_URL must start with http:// or https:// (got: $url)"
  local host
  host="$(host_from_url "$url")"
  [[ -n "$host" ]] || die "Unable to parse host from BASE_URL (got: $url)"
}
