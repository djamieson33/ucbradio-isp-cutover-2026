#!/usr/bin/env bash

require_file() { [[ -f "$1" ]] || die "Missing required file: $1"; }

require_dir()  { [[ -d "$1" ]] || die "Missing required directory: $1"; }

require_cmd()  { command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"; }
