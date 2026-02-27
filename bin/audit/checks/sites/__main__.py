#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from typing import Any, Dict, List, Tuple

from bin.audit.lib.common import (
    EXIT_ISSUES,
    EXIT_OK,
    die,
    load_yaml,
    normalize_sites_structure,
)

DEFAULT_SITES_YAML = "inventory/sites.yaml"
DEFAULT_REQUIRED_FIELDS = ["id", "name"]

ID_PATTERN = re.compile(r"^[a-z]+-\d{3}$")


def site_missing_fields(site: Dict[str, Any], required: List[str]) -> List[str]:
    missing = []
    for key in required:
        val = site.get(key)
        if val is None:
            missing.append(key)
        elif isinstance(val, str) and not val.strip():
            missing.append(key)
    return missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", default=DEFAULT_SITES_YAML)
    ap.add_argument("--required", default=",".join(DEFAULT_REQUIRED_FIELDS))
    args = ap.parse_args()

    required = [x.strip() for x in args.required.split(",") if x.strip()]

    try:
        sites_doc = load_yaml(args.sites)
        sites_by_key, shape = normalize_sites_structure(sites_doc)
    except Exception as e:
        die(f"Failed to parse sites file: {e}")

    keys = sorted(sites_by_key.keys())
    total_sites = len(keys)

    print(f"[INFO] sites file: {args.sites}")
    print(f"[INFO] sites structure: {shape}")
    print(f"[INFO] required fields: {', '.join(required)}")

    issues: List[Tuple[str, List[str]]] = []

    for key in keys:
        site = sites_by_key.get(key) or {}
        if not isinstance(site, dict):
            issues.append((key, ["<invalid entry>"]))
            continue

        missing = site_missing_fields(site, required)
        if missing:
            issues.append((key, missing))
            continue

        # enforce lowercase id pattern
        sid = site.get("id")
        if not ID_PATTERN.match(sid):
            issues.append((key, ["id format must match ^[a-z]+-\\d{3}$ (e.g., bell-102)"]))

    if issues:
        print(f"[WARN] sites with issues: {len(issues)}")
        for key, missing in issues:
            print(f"       - {key}: {', '.join(missing)}")
    else:
        print("[OK] all sites valid")

    print("------------------------------------------------------------")
    print(f"[SUMMARY] Total sites listed: {total_sites}")
    print("------------------------------------------------------------")

    return EXIT_ISSUES if issues else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
