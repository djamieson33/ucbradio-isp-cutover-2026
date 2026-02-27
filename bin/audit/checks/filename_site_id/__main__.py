#!/usr/bin/env python3
"""
Audit: filename_site_id
Ensures device inventory filenames contain the correct canonical site id (sites[].id).

Expected site id sources (priority):
  1) device.site_id
  2) device.site.id
  3) device.site_code mapped -> sites[].id (case-insensitive)

If a device YAML has no site metadata, it is UNVERIFIABLE (cannot know "correct" id).

Match rules:
  - case-insensitive
  - tolerant of '-' vs '_' and compact forms
"""

from __future__ import annotations

import argparse
import glob
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from bin.audit.lib.common import (
    EXIT_ISSUES,
    EXIT_OK,
    die,
    load_yaml,
    normalize_sites_structure,
)

DEFAULT_SITES_YAML = "inventory/sites.yaml"
DEFAULT_DEVICE_ROOT = "inventory/devices"


def norm_token(s: str) -> str:
    return s.strip().lower().replace("_", "-").replace(" ", "-")


def norm_compact(s: str) -> str:
    return norm_token(s).replace("-", "")


def _as_str(v: Any) -> Optional[str]:
    if isinstance(v, str) and v.strip():
        return v.strip()
    return None


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


def build_site_indexes(sites_path: str) -> Tuple[Set[str], Dict[str, str]]:
    """
    Returns:
      - valid_site_ids (normalized)
      - site_code_to_id (normalized site_code -> normalized id)
    """
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


def expected_site_id_from_device(doc: Any, valid_site_ids: Set[str], site_code_to_id: Dict[str, str]) -> Tuple[str, Optional[str]]:
    if not isinstance(doc, dict):
        return ("none", None)

    v = _as_str(doc.get("site_id"))
    if v:
        return ("site_id", norm_token(v))

    site = doc.get("site")
    if isinstance(site, dict):
        v2 = _as_str(site.get("id"))
        if v2:
            return ("site.id", norm_token(v2))

    sc = _as_str(doc.get("site_code"))
    if sc:
        mapped = site_code_to_id.get(norm_token(sc))
        if mapped:
            return ("site_code(mapped)", mapped)
        scn = norm_token(sc)
        if scn in valid_site_ids:
            return ("site_code(as_id)", scn)

    if isinstance(site, dict):
        sc2 = _as_str(site.get("site_code"))
        if sc2:
            mapped = site_code_to_id.get(norm_token(sc2))
            if mapped:
                return ("site.site_code(mapped)", mapped)
            scn = norm_token(sc2)
            if scn in valid_site_ids:
                return ("site.site_code(as_id)", scn)

    return ("none", None)


def filename_contains_site_id(path: str, site_id: str) -> bool:
    base = os.path.basename(path)
    base_no_ext = base[:-5] if base.lower().endswith(".yaml") else base

    b_norm = norm_token(base_no_ext)
    b_compact = norm_compact(base_no_ext)

    sid_norm = norm_token(site_id)
    sid_compact = norm_compact(site_id)

    return (sid_norm in b_norm) or (sid_compact in b_compact)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", default=DEFAULT_SITES_YAML)
    ap.add_argument("--device-root", default=DEFAULT_DEVICE_ROOT)
    ap.add_argument("--include-glob", action="append", default=[])
    args = ap.parse_args()

    valid_site_ids, site_code_to_id = build_site_indexes(args.sites)
    device_files = discover_device_files(args.device_root, args.include_glob)

    ok: List[str] = []
    mismatches: List[Tuple[str, str, str]] = []  # (file, expected_id, source)
    unverifiable: List[str] = []
    parse_errors: List[str] = []
    unknown_site_ids: List[Tuple[str, str, str]] = []  # (file, expected_id, source)

    for path in device_files:
        try:
            doc = load_yaml(path)
        except Exception:
            parse_errors.append(path)
            continue

        source, expected_id = expected_site_id_from_device(doc, valid_site_ids, site_code_to_id)
        if not expected_id:
            unverifiable.append(path)
            continue

        if expected_id not in valid_site_ids:
            unknown_site_ids.append((path, expected_id, source))
            continue

        if filename_contains_site_id(path, expected_id):
            ok.append(path)
        else:
            mismatches.append((path, expected_id, source))

    print(f"[INFO] sites file: {args.sites}")
    print(f"[INFO] known canonical site ids: {len(valid_site_ids)}")
    print(f"[INFO] device files scanned: {len(device_files)}")
    print(f"[INFO] ok filename matches: {len(ok)}")

    if mismatches:
        print(f"[WARN] filename/site_id mismatches: {len(mismatches)}")
        for p, sid, src in mismatches[:50]:
            print(f"       - {p}  (expected site_id={sid} via {src})")
        if len(mismatches) > 50:
            print(f"       ... ({len(mismatches)-50} more)")

    if unverifiable:
        print(f"[WARN] unverifiable (no site metadata in YAML): {len(unverifiable)}")
        for p in unverifiable[:25]:
            print(f"       - {p}")
        if len(unverifiable) > 25:
            print(f"       ... ({len(unverifiable)-25} more)")

    if unknown_site_ids:
        print(f"[WARN] device metadata references unknown site ids: {len(unknown_site_ids)}")
        for p, sid, src in unknown_site_ids[:50]:
            print(f"       - {p}  (expected site_id={sid} via {src})")
        if len(unknown_site_ids) > 50:
            print(f"       ... ({len(unknown_site_ids)-50} more)")

    if parse_errors:
        print(f"[WARN] parse errors: {len(parse_errors)}")
        for p in parse_errors[:25]:
            print(f"       - {p}")
        if len(parse_errors) > 25:
            print(f"       ... ({len(parse_errors)-25} more)")

    print("------------------------------------------------------------")
    print(f"[SUMMARY] Device files scanned: {len(device_files)}")
    print(f"[SUMMARY] OK filename matches: {len(ok)}")
    print(f"[SUMMARY] Mismatches: {len(mismatches)}")
    print(f"[SUMMARY] Unverifiable (missing site metadata): {len(unverifiable)}")
    print(f"[SUMMARY] Unknown site ids (from metadata): {len(unknown_site_ids)}")
    print(f"[SUMMARY] Parse errors: {len(parse_errors)}")
    print("------------------------------------------------------------")

    return EXIT_ISSUES if (mismatches or unverifiable or unknown_site_ids or parse_errors) else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
