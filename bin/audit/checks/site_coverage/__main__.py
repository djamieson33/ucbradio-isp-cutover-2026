#!/usr/bin/env python3
"""
Audit: site_coverage (metadata-driven)

Goal:
  - Ensure every device inventory YAML has explicit site metadata:
      site:
        id: <canonical site id>

Canonical:
  - sites[].id is canonical (lowercase like bell-102)
  - sites[].site_code is alias (e.g. BELL-102)

Accepted device refs (explicit only):
  1) site: { id }
  2) site_id (legacy support if present)
  3) site_code (mapped to id via sites.yaml, case-insensitive)

This audit ALWAYS prints a summary.
"""

from __future__ import annotations

import argparse
import glob
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from bin.audit.lib.common import EXIT_ISSUES, EXIT_OK, load_yaml, normalize_sites_structure


DEFAULT_SITES_YAML = "inventory/sites.yaml"
DEFAULT_DEVICE_ROOT = "inventory/devices"


def norm_token(s: str) -> str:
    return s.strip().lower().replace("_", "-").replace(" ", "-")


def _as_str(v: Any) -> Optional[str]:
    if isinstance(v, str) and v.strip():
        return v.strip()
    return None


def discover_device_files(device_root: str) -> List[str]:
    pat = os.path.join(device_root, "**", "*.yaml")
    candidates = glob.glob(pat, recursive=True)
    out: List[str] = []
    for p in candidates:
        norm = p.replace("\\", "/")
        if "/inventory/seed/" in norm:
            continue
        out.append(p)
    return sorted(set(out))


def load_sites_index(sites_path: str) -> Tuple[Set[str], Dict[str, str]]:
    sites_doc = load_yaml(sites_path)
    sites_by_key, _shape = normalize_sites_structure(sites_doc)

    valid_ids: Set[str] = set()
    site_code_to_id: Dict[str, str] = {}

    for _k, site in sites_by_key.items():
        if not isinstance(site, dict):
            continue
        sid = _as_str(site.get("id"))
        scode = _as_str(site.get("site_code"))
        if sid:
            valid_ids.add(norm_token(sid))
        if sid and scode:
            site_code_to_id[norm_token(scode)] = norm_token(sid)

    return valid_ids, site_code_to_id


def extract_site_id(doc: Any, site_code_to_id: Dict[str, str]) -> Tuple[str, Optional[str]]:
    """
    Returns (source, normalized_site_id|None)
    """
    if not isinstance(doc, dict):
        return ("none", None)

    site = doc.get("site")
    if isinstance(site, dict):
        sid = _as_str(site.get("id"))
        if sid:
            return ("site.id", norm_token(sid))

    # legacy support
    sid2 = _as_str(doc.get("site_id"))
    if sid2:
        return ("site_id", norm_token(sid2))

    # alias mapping support
    sc = _as_str(doc.get("site_code"))
    if sc:
        mapped = site_code_to_id.get(norm_token(sc))
        if mapped:
            return ("site_code(mapped)", mapped)

    if isinstance(site, dict):
        sc2 = _as_str(site.get("site_code"))
        if sc2:
            mapped = site_code_to_id.get(norm_token(sc2))
            if mapped:
                return ("site.site_code(mapped)", mapped)

    return ("none", None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", default=DEFAULT_SITES_YAML)
    ap.add_argument("--device-root", default=DEFAULT_DEVICE_ROOT)
    args = ap.parse_args()

    valid_ids, site_code_to_id = load_sites_index(args.sites)
    device_files = discover_device_files(args.device_root)

    ok = 0
    missing: List[str] = []
    unknown: List[Tuple[str, str, str]] = []  # (file, source, value)

    for path in device_files:
        try:
            doc = load_yaml(path)
        except Exception:
            unknown.append((path, "parse_error", "unable_to_parse_yaml"))
            continue

        src, sid = extract_site_id(doc, site_code_to_id)
        if not sid:
            missing.append(path)
            continue

        if sid in valid_ids:
            ok += 1
        else:
            unknown.append((path, src, sid))

    print(f"[INFO] sites file: {args.sites}")
    print(f"[INFO] known canonical site ids: {len(valid_ids)}")
    print(f"[INFO] device files scanned: {len(device_files)}")
    print(f"[INFO] device files with valid explicit site refs: {ok}")

    if missing:
        print(f"[WARN] device files missing explicit site metadata: {len(missing)}")
        for p in missing[:25]:
            print(f"       - {p}")
        if len(missing) > 25:
            print(f"       ... ({len(missing)-25} more)")

    if unknown:
        print(f"[WARN] device files with unknown site refs / parse errors: {len(unknown)}")
        for p, src, val in unknown[:50]:
            print(f"       - {p}  ({src}={val})")
        if len(unknown) > 50:
            print(f"       ... ({len(unknown)-50} more)")

    print("------------------------------------------------------------")
    print(f"[SUMMARY] Device files scanned: {len(device_files)}")
    print(f"[SUMMARY] Valid explicit site refs: {ok}")
    print(f"[SUMMARY] Missing explicit site refs: {len(missing)}")
    print(f"[SUMMARY] Unknown explicit site refs / parse errors: {len(unknown)}")
    print("------------------------------------------------------------")

    return EXIT_OK if (ok == len(device_files) and not unknown and not missing) else EXIT_ISSUES


if __name__ == "__main__":
    raise SystemExit(main())
