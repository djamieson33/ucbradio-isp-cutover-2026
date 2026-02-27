#!/usr/bin/env bash
set -euo pipefail

version_read() {
  [[ -f VERSION ]] || die "VERSION not found."
  local v
  v="$(tr -d '[:space:]' < VERSION)"
  [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "Invalid VERSION: '$v'"
  echo "$v"
}

semver_bump() {
  local current="$1"
  local bump_type="$2"
  local major minor patch
  IFS='.' read -r major minor patch <<<"$current"

  case "$bump_type" in
    major) major=$((major + 1)); minor=0; patch=0 ;;
    minor) minor=$((minor + 1)); patch=0 ;;
    patch) patch=$((patch + 1)) ;;
    *) die "Invalid bump type: $bump_type (use major|minor|patch)" ;;
  esac

  echo "${major}.${minor}.${patch}"
}
