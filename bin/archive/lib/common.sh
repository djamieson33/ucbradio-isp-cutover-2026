#!/usr/bin/env bash
set -euo pipefail

die() { echo "[ERROR] $*" >&2; exit 2; }
info() { echo "[INFO] $*" >&2; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is required."
}
