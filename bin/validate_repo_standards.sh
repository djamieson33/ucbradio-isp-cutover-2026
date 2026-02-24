#!/usr/bin/env bash
# ==============================================================================
# UCB Radio – ISP Changeover 2026
# File: bin/validate_repo_standards.sh
# Purpose: Validate repo file naming + placement standards (UTC timestamps, exports,
#          releases, evidence) as defined in docs/01-governance/FILE_STANDARDS.md.
#
# Read-only: does not modify files.
# Exits non-zero if violations are found.
# ==============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

die() { echo "[ERROR] $*" >&2; exit 2; }
warn() { echo "[WARN]  $*" >&2; }
info() { echo "[INFO]  $*"; }

# UTC timestamp pattern: YYYYMMDDThhmmZ
TS_RE='[0-9]{8}T[0-9]{4}Z'

fail_count=0

fail() {
  fail_count=$((fail_count+1))
  echo "[FAIL]  $*" >&2
}

pass() {
  echo "[PASS]  $*"
}

# ------------------------------------------------------------------------------
# 0) Basic sanity
# ------------------------------------------------------------------------------
[[ -f "$ROOT/docs/01-governance/FILE_STANDARDS.md" ]] || fail "Missing docs/01-governance/FILE_STANDARDS.md"
[[ -d "$ROOT/firewall/sonicwall/exports" ]] || warn "Missing firewall/sonicwall/exports (ok if not created yet)"
[[ -d "$ROOT/releases" ]] || warn "Missing releases/ (ok if not created yet)"
[[ -d "$ROOT/evidence" ]] || warn "Missing evidence/ (ok if not created yet)"

# ------------------------------------------------------------------------------
# 1) SonicWall NAT export naming
# ------------------------------------------------------------------------------
NAT_DIR="$ROOT/firewall/sonicwall/exports"
if [[ -d "$NAT_DIR" ]]; then
  # Any CSVs in NAT exports must match nat-policies-YYYYMMDDThhmmZ.csv
  while IFS= read -r -d '' f; do
    base="$(basename "$f")"
    if [[ ! "$base" =~ ^nat-policies-${TS_RE}\.csv$ ]]; then
      fail "NAT export CSV name invalid: firewall/sonicwall/exports/$base (expected nat-policies-YYYYMMDDThhmmZ.csv)"
    fi
  done < <(find "$NAT_DIR" -maxdepth 1 -type f -name "*.csv" -print0)

  # Optional: flag “export.csv” or other common mistakes anywhere under exports/
  while IFS= read -r -d '' f; do
    base="$(basename "$f")"
    if [[ "$base" == "export.csv" || "$base" == "nat.csv" ]]; then
      fail "Generic NAT export filename detected: firewall/sonicwall/exports/$base (rename to nat-policies-YYYYMMDDThhmmZ.csv)"
    fi
  done < <(find "$NAT_DIR" -maxdepth 1 -type f -print0)
fi

# ------------------------------------------------------------------------------
# 2) Release archives (SemVer required, timestamp NOT required)
# ------------------------------------------------------------------------------

REL_DIR="$ROOT/releases"
if [[ -d "$REL_DIR" ]]; then
  while IFS= read -r -d '' zip; do
    zip_base="$(basename "$zip")"

    # Require semantic version in filename
    if [[ ! "$zip_base" =~ ^ucbradio-isp-cutover-[0-9]+\.[0-9]+\.[0-9]+.*\.zip$ ]]; then
      fail "Release zip name invalid: releases/$zip_base (expected ucbradio-isp-cutover-X.Y.Z.zip)"
      continue
    fi

    sha="${zip}.sha256"
    sha_base="$(basename "$sha")"

    if [[ ! -f "$sha" ]]; then
      fail "Missing SHA256 sidecar for releases/$zip_base (expected $sha_base)"
    fi
  done < <(find "$REL_DIR" -maxdepth 1 -type f -name "*.zip" -print0)
fi

# ------------------------------------------------------------------------------
# 3) Evidence filenames should include UTC timestamp
# ------------------------------------------------------------------------------
EVID_DIR="$ROOT/evidence"
if [[ -d "$EVID_DIR" ]]; then
  # Check any file under evidence/pre-change and evidence/post-change
  while IFS= read -r -d '' f; do
    rel="${f#$ROOT/}"
    base="$(basename "$f")"
    # allow README.md inside evidence directories without timestamp
    if [[ "$base" == "README.md" || "$base" == ".gitkeep" ]]; then
      continue
    fi
    if [[ ! "$base" =~ ${TS_RE} ]]; then
      fail "Evidence file missing UTC timestamp (YYYYMMDDThhmmZ): $rel"
    fi
  done < <(find "$EVID_DIR" -type f -print0)
fi

# ------------------------------------------------------------------------------
# 4) Generated vs canonical file sanity checks
# ------------------------------------------------------------------------------
# Generated seed files are allowed, but should be clearly marked.
SEED_FILE="$ROOT/inventory/03-inbound-services.seed.yaml"
CANON_FILE="$ROOT/inventory/03-inbound-services.yaml"

if [[ -f "$SEED_FILE" ]]; then
  pass "Found generated seed file: inventory/03-inbound-services.seed.yaml"
fi

if [[ -f "$CANON_FILE" ]]; then
  pass "Found canonical file: inventory/03-inbound-services.yaml"
else
  warn "Canonical file missing: inventory/03-inbound-services.yaml (ok if still being created)"
fi

# Guardrail: if someone accidentally created a canonical-looking file under inventory/ with ".seed" missing
# (lightweight heuristic)
while IFS= read -r -d '' f; do
  rel="${f#$ROOT/}"
  base="$(basename "$f")"
  if [[ "$base" =~ ^03-inbound-services.*\.ya?ml$ ]] && [[ "$base" != "03-inbound-services.yaml" ]] && [[ "$base" != "03-inbound-services.seed.yaml" ]]; then
    warn "Unexpected inbound-services variant file found: $rel (confirm canonical vs generated intent)"
  fi
done < <(find "$ROOT/inventory" -maxdepth 1 -type f -name "03-inbound-services*.yml" -o -name "03-inbound-services*.yaml" -print0 2>/dev/null || true)

# ------------------------------------------------------------------------------
# 5) Optional: flag non-UTC timestamps in filenames across key directories
# ------------------------------------------------------------------------------
# This is intentionally narrow to avoid false positives.
CHECK_DIRS=(
  "$ROOT/firewall/sonicwall/exports"
  "$ROOT/releases"
  "$ROOT/evidence"
)
for d in "${CHECK_DIRS[@]}"; do
  [[ -d "$d" ]] || continue
  while IFS= read -r -d '' f; do
    base="$(basename "$f")"
    # If it contains something that looks like a local timestamp pattern (common mistakes),
    # warn (do not fail) to avoid being too noisy.
    if [[ "$base" =~ [0-9]{4}-[0-9]{2}-[0-9]{2} ]]; then
      warn "Possible non-standard timestamp (contains YYYY-MM-DD): ${f#$ROOT/}"
    fi
  done < <(find "$d" -type f -print0)
done

# ------------------------------------------------------------------------------
# Final
# ------------------------------------------------------------------------------
if [[ "$fail_count" -gt 0 ]]; then
  echo
  echo "[RESULT] FAIL — $fail_count issue(s) found."
  echo "Fix the items above to comply with docs/01-governance/FILE_STANDARDS.md"
  exit 1
fi

echo
echo "[RESULT] PASS — repo file standards look good."
exit 0
