#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CHECKS_DIR="$ROOT/bin/audit/checks"

usage() {
  cat <<'USAGE'
Usage:
  bin/audit/run.sh list
  bin/audit/run.sh <audit-name>
  bin/audit/run.sh all

Audits are namespace packages:
  bin/audit/checks/<name>/__main__.py

Run logic uses:
  python3 -m bin.audit.checks.<name>
USAGE
}

list_audits() {
  echo "[INFO] Available audits:"
  local names=()

  if [[ -d "$CHECKS_DIR" ]]; then
    while IFS= read -r -d '' d; do
      local base
      base="$(basename "$d")"
      [[ "$base" == "__pycache__" ]] && continue
      [[ "$base" == "__init__" ]] && continue
      [[ -f "$d/__main__.py" ]] || continue
      names+=("$base")
    done < <(find "$CHECKS_DIR" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null || true)
  fi

  IFS=$'\n' names=($(sort <<<"${names[*]:-}"))
  unset IFS

  for n in "${names[@]:-}"; do
    echo "  - $n"
  done
}

run_one() {
  local name="$1"
  cd "$ROOT"

  if [[ -f "$CHECKS_DIR/$name/__main__.py" ]]; then
    python3 -m "bin.audit.checks.$name"
    return
  fi

  echo "[ERROR] Unknown audit: $name" >&2
  exit 2
}

main() {
  case "${1:-all}" in
    -h|--help|help)
      usage
      ;;
    list)
      list_audits
      ;;
    all|"")
      local audits=()
      while IFS= read -r -d '' d; do
        local base
        base="$(basename "$d")"
        [[ -f "$d/__main__.py" ]] && audits+=("$base")
      done < <(find "$CHECKS_DIR" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null || true)

      IFS=$'\n' audits=($(sort <<<"${audits[*]:-}"))
      unset IFS

      for a in "${audits[@]:-}"; do
        run_one "$a"
      done
      ;;
    *)
      run_one "$1"
      ;;
  esac
}

main "$@"
