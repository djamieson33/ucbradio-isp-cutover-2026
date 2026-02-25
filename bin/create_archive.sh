#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Wrapper: bin/create_archive.sh
# Purpose: Backward-compatible entrypoint for archive creation.
# Delegates to: bin/archive/run.sh
# ==============================================================================

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT/bin/archive/run.sh" "$@"
