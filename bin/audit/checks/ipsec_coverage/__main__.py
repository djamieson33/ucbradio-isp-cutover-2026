#!/usr/bin/env python3
"""
Audit: ipsec_coverage

Checks:
  1) Sites have ipsec.enabled set (strict by default)
  2) Counts enabled/disabled/missing/invalid
  3) For ipsec.enabled=true sites: ensure at least one firewall device exists referencing the site

Canonical site identity:
  - sites[].id is canonical (lowercase like bell-102)
  - sites[].site_code is alias (uppercase like BELL-102), used only for mapping device metadata

Device site reference resolution (priority):
  - site.id
  - site_id (legacy)
  - site_code mapped -> sites[].id (case-insensitive)

Firewall devices scanned:
  - inventory/devices/firewalls/**/*.yaml (excluding inventory/seed/)
"""

from __future__ import annotations

import argparse
import glob
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from bin.audit.lib.common import EXIT_OK, EXIT_ISSUES, load_yaml, normalize_sites_structure


DEFAULT_SITES_YAML = "inventory/sites.yaml"
DEFAULT_FIREWALL_ROOT = "inventory/devices/firewalls"


def norm_token(s: str) -> str:
    return s.strip().lower().replace("_", "-").replace(" ", "-")


def _as_str(v: Any) -> Optional[str]:
    if isinstance(v, str) and v.strip():
        return v.strip()
    return None


def discover_firewall_files(fw_root: str) -> List[str]:
    pat = os.path.join(fw_root, "**", "*.yaml")
    candidates = glob.glob(pat, recursive=True)
    out: List[str] = []
    for p in candidates:
        norm = p.replace("\\", "/")
        if "/inventory/seed/" in norm:
            continue
        out.append(p)
    return sorted(set(out))


def load_sites_index(sites_path: str) -> Tuple[Dict[str, Dict[str, Any]], Set[str], Dict[str, str]]:
    """
    Returns:
      - sites_by_id (normalized id -> site dict)
      - valid_site_ids (set)
      - site_code_to_id (normalized site_code -> normalized id)
    """
    sites_doc = load_yaml(sites_path)
    sites_by_key, _shape = normalize_sites_structure(sites_doc)

    sites_by_id: Dict[str, Dict[str, Any]] = {}
    valid_ids: Set[str] = set()
    site_code_to_id: Dict[str, str] = {}

    for _k, site in sites_by_key.items():
        if not isinstance(site, dict):
            continue
        sid = _as_str(site.get("id"))
        scode = _as_str(site.get("site_code"))
        if sid:
            sid_n = norm_token(sid)
            sites_by_id[sid_n] = site
            valid_ids.add(sid_n)
        if sid and scode:
            site_code_to_id[norm_token(scode)] = norm_token(sid)

    return sites_by_id, valid_ids, site_code_to_id


def extract_site_id_from_device(doc: Any, site_code_to_id: Dict[str, str], valid_ids: Set[str]) -> Tuple[str, Optional[str]]:
    if not isinstance(doc, dict):
        return ("none", None)

    site = doc.get("site")
    if isinstance(site, dict):
        sid = _as_str(site.get("id"))
        if sid:
            return ("site.id", norm_token(sid))

    sid2 = _as_str(doc.get("site_id"))
    if sid2:
        return ("site_id", norm_token(sid2))

    sc = _as_str(doc.get("site_code"))
    if sc:
        mapped = site_code_to_id.get(norm_token(sc))
        if mapped:
            return ("site_code(mapped)", mapped)
        scn = norm_token(sc)
        if scn in valid_ids:
            return ("site_code(as_id)", scn)

    if isinstance(site, dict):
        sc2 = _as_str(site.get("site_code"))
        if sc2:
            mapped = site_code_to_id.get(norm_token(sc2))
            if mapped:
                return ("site.site_code(mapped)", mapped)
            scn = norm_token(sc2)
            if scn in valid_ids:
                return ("site.site_code(as_id)", scn)

    return ("none", None)


def get_ipsec_enabled(site: Dict[str, Any]) -> Tuple[str, Optional[bool]]:
    """
    Returns:
      ("ok", bool) if valid boolean present
      ("missing", None) if missing
      ("invalid", None) if present but not boolean
    """
    ipsec = site.get("ipsec")
    if ipsec is None:
        return ("missing", None)
    if not isinstance(ipsec, dict):
        return ("invalid", None)

    enabled = ipsec.get("enabled")
    if enabled is None:
        return ("missing", None)
    if isinstance(enabled, bool):
        return ("ok", enabled)
    return ("invalid", None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", default=DEFAULT_SITES_YAML)
    ap.add_argument("--firewalls-root", default=DEFAULT_FIREWALL_ROOT)
    ap.add_argument("--allow-missing", action="store_true", help="Do not fail if sites are missing ipsec.enabled")
    args = ap.parse_args()

    sites_by_id, valid_ids, site_code_to_id = load_sites_index(args.sites)
    fw_files = discover_firewall_files(args.firewalls_root)

    # Map site_id -> list of firewall files
    fw_by_site: Dict[str, List[str]] = {sid: [] for sid in valid_ids}
    fw_unmapped: List[str] = []
    fw_unknown_site: List[Tuple[str, str, str]] = []  # (file, source, site_id)

    for p in fw_files:
        try:
            doc = load_yaml(p)
        except Exception:
            fw_unmapped.append(p)
            continue

        src, sid = extract_site_id_from_device(doc, site_code_to_id, valid_ids)
        if not sid:
            fw_unmapped.append(p)
            continue
        if sid not in valid_ids:
            fw_unknown_site.append((p, src, sid))
            continue
        fw_by_site.setdefault(sid, []).append(p)

    enabled_sites: List[str] = []
    disabled_sites: List[str] = []
    missing_sites: List[str] = []
    invalid_sites: List[str] = []
    enabled_missing_firewall: List[str] = []

    for sid, site in sorted(sites_by_id.items(), key=lambda x: x[0]):
        status, enabled = get_ipsec_enabled(site)
        if status == "missing":
            missing_sites.append(sid)
            continue
        if status == "invalid":
            invalid_sites.append(sid)
            continue

        # ok
        if enabled is True:
            enabled_sites.append(sid)
            if len(fw_by_site.get(sid, [])) == 0:
                enabled_missing_firewall.append(sid)
        else:
            disabled_sites.append(sid)

    print(f"[INFO] sites file: {args.sites}")
    print(f"[INFO] firewall files scanned: {len(fw_files)}")
    print(f"[INFO] canonical sites indexed: {len(valid_ids)}")
    print(f"[INFO] ipsec.enabled=true: {len(enabled_sites)}")
    print(f"[INFO] ipsec.enabled=false: {len(disabled_sites)}")
    print(f"[INFO] ipsec.enabled missing: {len(missing_sites)}")
    print(f"[INFO] ipsec.enabled invalid: {len(invalid_sites)}")

    if enabled_sites:
        print(f"[INFO] IPSec-enabled sites (showing up to 25): {len(enabled_sites)}")
        for sid in enabled_sites[:25]:
            scode = _as_str(sites_by_id[sid].get("site_code")) or ""
            name = _as_str(sites_by_id[sid].get("name")) or ""
            print(f"       - {sid} {('('+scode+')') if scode else ''} {('- '+name) if name else ''}".rstrip())
        if len(enabled_sites) > 25:
            print(f"       ... ({len(enabled_sites)-25} more)")

    if enabled_missing_firewall:
        print(f"[WARN] IPSec-enabled sites missing firewall inventory: {len(enabled_missing_firewall)}")
        for sid in enabled_missing_firewall:
            scode = _as_str(sites_by_id[sid].get("site_code")) or ""
            name = _as_str(sites_by_id[sid].get("name")) or ""
            print(f"       - {sid} {('('+scode+')') if scode else ''} {('- '+name) if name else ''}".rstrip())

    if missing_sites:
        print(f"[WARN] sites missing ipsec.enabled: {len(missing_sites)}")
        for sid in missing_sites[:25]:
            print(f"       - {sid}")
        if len(missing_sites) > 25:
            print(f"       ... ({len(missing_sites)-25} more)")

    if invalid_sites:
        print(f"[WARN] sites with invalid ipsec.enabled (must be boolean): {len(invalid_sites)}")
        for sid in invalid_sites[:25]:
            print(f"       - {sid}")
        if len(invalid_sites) > 25:
            print(f"       ... ({len(invalid_sites)-25} more)")

    if fw_unmapped:
        print(f"[WARN] firewall device files missing site reference / parse errors: {len(fw_unmapped)}")
        for p in fw_unmapped[:25]:
            print(f"       - {p}")
        if len(fw_unmapped) > 25:
            print(f"       ... ({len(fw_unmapped)-25} more)")

    if fw_unknown_site:
        print(f"[WARN] firewall device files reference unknown site ids: {len(fw_unknown_site)}")
        for p, src, sid in fw_unknown_site[:25]:
            print(f"       - {p} ({src}={sid})")
        if len(fw_unknown_site) > 25:
            print(f"       ... ({len(fw_unknown_site)-25} more)")

    print("------------------------------------------------------------")
    print(f"[SUMMARY] Total sites: {len(valid_ids)}")
    print(f"[SUMMARY] IPSec enabled: {len(enabled_sites)}")
    print(f"[SUMMARY] IPSec disabled: {len(disabled_sites)}")
    print(f"[SUMMARY] Missing ipsec.enabled: {len(missing_sites)}")
    print(f"[SUMMARY] Invalid ipsec.enabled: {len(invalid_sites)}")
    print(f"[SUMMARY] IPSec enabled but missing firewall device: {len(enabled_missing_firewall)}")
    print("------------------------------------------------------------")

    fail = False
    if enabled_missing_firewall:
        fail = True
    if invalid_sites:
        fail = True
    if (missing_sites and not args.allow_missing):
        fail = True
    if fw_unknown_site:
        fail = True

    return EXIT_ISSUES if fail else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
