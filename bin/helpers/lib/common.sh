#!/usr/bin/env bash
# Common “aggregator” that other scripts can source once.
# Important: do NOT set strict mode here.

# shellcheck disable=SC2155

# Determine repo root (works from anywhere)
repo_root() {
  (cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
}

ROOT="$(repo_root)"

# shellcheck source=bin/helpers/lib/log.sh
source "$ROOT/bin/helpers/lib/log.sh"
# shellcheck source=bin/helpers/lib/time.sh
source "$ROOT/bin/helpers/lib/time.sh"
# shellcheck source=bin/helpers/lib/require.sh
source "$ROOT/bin/helpers/lib/require.sh"
# shellcheck source=bin/helpers/lib/url.sh
source "$ROOT/bin/helpers/lib/url.sh"
# shellcheck source=bin/helpers/lib/json.sh
source "$ROOT/bin/helpers/lib/json.sh"
# shellcheck source=bin/helpers/lib/wpcli.sh
source "$ROOT/bin/helpers/lib/wpcli.sh"
