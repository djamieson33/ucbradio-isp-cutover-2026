#!/usr/bin/env bash
set -euo pipefail

die()  { echo "[ERROR] $*" >&2; exit 2; }
warn() { echo "[WARN]  $*" >&2; }
info() { echo "[INFO]  $*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing dependency: $1"
}

lower() {
  echo "$1" | tr '[:upper:]' '[:lower:]'
}
