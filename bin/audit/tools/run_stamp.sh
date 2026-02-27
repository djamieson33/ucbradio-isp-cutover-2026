#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../" && pwd)"
cd "$ROOT"

exec python3 -m bin.audit.tools.stamp_site_id_into_site_block "$@"
