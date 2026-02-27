#!/usr/bin/env python3
"""
Tool: stamp_site_id_into_site_block

Adds or updates:
  site:
    id: <site-id>

in device inventory YAMLs.

Rules:
  - Canonical site ids come from inventory/sites.yaml (sites[].id)
  - Inferred from filename (must contain a known site id)
  - Writes ONLY site.id (no top-level site_id field)
  - --overwrite replaces existing site.id
  - --dry-run shows changes without writing
"""

from __future__ import annotations

import argparse
import glob
import os
from typing import Any, Dict, List, Optional, Set

import yaml

from bin.audit.lib.common import load_yaml, normalize_sites_structure


DEFAULT_SITES_YAML = "inventory/sites.yaml"
DEFAULT_DEVICE_ROOT = "inventory/devices"


def norm_token(s: str) -> str:
    return s.strip().lower().replace("_", "-").replace(" ", "-")


def norm_compact(s: str) -> str:
    return norm_token(s).replace("-", "")


def discover_device_files(device_root: str, include_globs: List[str]) -> List[str]:
    if include_globs:
        out: List[str] = []
        for pat in include_globs:
            out.extend(glob.glob(pat, recursive=True))
        return sorted(set(out))

    pat = os.path.join(device_root, "**", "*.yaml")
    candidates = glob.glob(pat, recursive=True)

    filtered: List[str] = []
    for p in candidates:
        norm = p.replace("\\", "/")
        if "/inventory/seed/" in norm:
            continue
        filtered.append(p)

    return sorted(set(filtered))


def build_valid_site_ids(sites_path: str) -> Set[str]:
    sites_doc = load_yaml(sites_path)
    sites_by_key, _shape = normalize_sites_structure(sites_doc)

    valid: Set[str] = set()
    for _k, site in sites_by_key.items():
        if not isinstance(site, dict):
            continue
        sid = site.get("id")
        if isinstance(sid, str) and sid.strip():
            valid.add(norm_token(sid))
    return valid


def infer_site_id_from_filename(path: str, valid_site_ids: Set[str]) -> Optional[str]:
    base = os.path.basename(path)
    base_no_ext = base[:-5] if base.lower().endswith(".yaml") else base

    b_norm = norm_token(base_no_ext)
    b_compact = norm_compact(base_no_ext)

    for sid in valid_site_ids:
        if sid in b_norm or sid.replace("-", "") in b_compact:
            return sid
    return None


def dump_yaml(path: str, doc: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=False, width=120)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", default=DEFAULT_SITES_YAML)
    ap.add_argument("--device-root", default=DEFAULT_DEVICE_ROOT)
    ap.add_argument("--include-glob", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    valid_site_ids = build_valid_site_ids(args.sites)
    device_files = discover_device_files(args.device_root, args.include_glob)

    changed = 0
    skipped = 0
    unable = 0

    for path in device_files:
        try:
            doc = load_yaml(path)
        except Exception:
            print(f"[WARN] parse error: {path}")
            unable += 1
            continue

        if not isinstance(doc, dict):
            print(f"[WARN] invalid YAML root (not dict): {path}")
            unable += 1
            continue

        inferred = infer_site_id_from_filename(path, valid_site_ids)
        if not inferred:
            print(f"[WARN] could not infer site id from filename (or site missing in sites.yaml): {path}")
            unable += 1
            continue

        site = doc.get("site")
        if site is None:
            site = {}
            doc["site"] = site
        if not isinstance(site, dict):
            print(f"[WARN] site field exists but is not a mapping: {path}")
            unable += 1
            continue

        existing = site.get("id")
        existing_norm = norm_token(existing) if isinstance(existing, str) else None

        if existing_norm and not args.overwrite:
            skipped += 1
            continue

        if existing_norm == inferred:
            skipped += 1
            continue

        site["id"] = inferred

        if args.dry_run:
            print(f"[DRY] {path}: site.id -> {inferred}")
        else:
            dump_yaml(path, doc)
            print(f"[OK]  {path}: site.id -> {inferred}")

        changed += 1

    print("------------------------------------------------------------")
    print(f"[SUMMARY] Device files scanned: {len(device_files)}")
    print(f"[SUMMARY] Updated: {changed}")
    print(f"[SUMMARY] Skipped: {skipped}")
    print(f"[SUMMARY] Unable to infer / parse errors: {unable}")
    print("------------------------------------------------------------")

    return 1 if unable else 0


if __name__ == "__main__":
    raise SystemExit(main())
