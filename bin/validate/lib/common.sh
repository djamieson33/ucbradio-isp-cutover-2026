#!/usr/bin/env bash
set -euo pipefail

FAIL_COUNT=0

die() { echo "[ERROR] $*" >&2; exit 2; }
warn() { echo "[WARN]  $*" >&2; }
info() { echo "[INFO]  $*"; }

fail() {
  FAIL_COUNT=$((FAIL_COUNT+1))
  echo "[FAIL]  $*" >&2
}

pass() {
  echo "[PASS]  $*"
}
