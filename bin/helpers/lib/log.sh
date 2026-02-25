#!/usr/bin/env bash
# Logging helpers (no strict mode here)

supports_color() {
  [[ -t 1 ]] || return 1
  [[ "${TERM:-}" == "dumb" ]] && return 1
  [[ "${NO_COLOR:-0}" == "1" ]] && return 1
  return 0
}

if supports_color; then
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  C_DIM=$'\033[2m'
  C_RED=$'\033[31m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_CYAN=$'\033[36m'
else
  C_RESET='' C_BOLD='' C_DIM='' C_RED='' C_GREEN='' C_YELLOW='' C_CYAN=''
fi

SYM_OK="+"
SYM_INFO="i"
SYM_WARN="!"
SYM_FAIL="x"
SYM_DEBUG="d"

ok() {
  printf "%s %s%s[OK]%s   %s\n" \
    "$SYM_OK" "$C_BOLD$C_GREEN" "" "$C_RESET" "$*"
}

warn() {
  printf "%s %s%s[WARN]%s %s\n" \
    "$SYM_WARN" "$C_BOLD$C_YELLOW" "" "$C_RESET" "$*" >&2
}

fail_msg() {
  printf "%s %s%s[FAIL]%s %s\n" \
    "$SYM_FAIL" "$C_BOLD$C_RED" "" "$C_RESET" "$*" >&2
}

info() {
  [[ "${HC_VERBOSE:-0}" -eq 1 ]] || return 0
  printf "%s %s%s[INFO]%s %s\n" \
    "$SYM_INFO" "$C_BOLD$C_CYAN" "" "$C_RESET" "$*"
}

debug() {
  [[ "${HC_DEBUG:-0}" -eq 1 ]] || return 0
  printf "%s %s[DEBUG]%s %s\n" \
    "$SYM_DEBUG" "$C_DIM" "$C_RESET" "$*"
}

die() { fail_msg "$*"; exit 2; }
