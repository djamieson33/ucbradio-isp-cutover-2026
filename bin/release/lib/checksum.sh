#!/usr/bin/env bash
set -euo pipefail

sha256_sidecar_create_and_verify() {
  local file="$1"
  [[ -f "$file" ]] || die "Cannot generate SHA256 — file not found: $file"
  require_cmd shasum

  info "Generating SHA256 for $(basename "$file")"
  shasum -a 256 "$file" > "${file}.sha256" || die "SHA256 generation failed"

  shasum -a 256 -c "${file}.sha256" >/dev/null 2>&1 || die "Checksum verification failed"
  info "Created ${file}.sha256"
}
