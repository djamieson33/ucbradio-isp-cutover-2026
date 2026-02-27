#!/usr/bin/env python3
# bin/seed_inbound_services/overrides_apply.py
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/overrides_apply.py
Purpose: Ensure overrides YAML has canonical "scoped-first" shape and
         optionally apply unresolved object skeletons under a firewall scope.

We intentionally do NOT assume object names are global/unique across firewalls.
All real mappings should live under:
  scoped:
    "<firewall_device_key>":
      address_objects: ...
      service_objects: ...
      ip_map: ...

This helper will:
- create the file if missing
- ensure top-level keys exist
- ensure scoped.<fw_key> block exists
- add unresolved address_objects skeleton entries under that scope (without overwriting)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _as_dict(x: Any) -> dict:
    return x if isinstance(x, dict) else {}


def _ensure_top_level_shape(doc: dict) -> dict:
    """
    Canonical shape:
      version: int (keep if present)
      updated_utc: string (keep if present)
      address_objects: {}
      service_objects: {}
      ip_map: {}
      scoped: {}
    """
    out = _as_dict(doc).copy()

    # preserve if present
    if "version" not in out:
        out["version"] = 1
    if "updated_utc" not in out:
        out["updated_utc"] = ""

    # force empty globals unless already dict (but we still recommend empty)
    out["address_objects"] = _as_dict(out.get("address_objects"))
    out["service_objects"] = _as_dict(out.get("service_objects"))
    out["ip_map"] = _as_dict(out.get("ip_map"))

    out["scoped"] = _as_dict(out.get("scoped"))

    return out


def ensure_scope_block(
    overrides_path: Path,
    firewall_device_key: str,
) -> tuple[dict, bool]:
    """
    Ensure overrides file exists and has scoped.<fw_key> with address_objects/service_objects/ip_map dicts.

    Returns: (doc, changed)
    """
    if not firewall_device_key:
        raise ValueError("firewall_device_key is required")

    changed = False
    if overrides_path.exists():
        raw = overrides_path.read_text(encoding="utf-8")
        doc = yaml.safe_load(raw) or {}
        if not isinstance(doc, dict):
            doc = {}
            changed = True
    else:
        doc = {}
        changed = True

    doc2 = _ensure_top_level_shape(doc)
    if doc2 != doc:
        doc = doc2
        changed = True

    scoped = _as_dict(doc.get("scoped"))
    blk = scoped.get(firewall_device_key)
    if not isinstance(blk, dict):
        blk = {}
        scoped[firewall_device_key] = blk
        doc["scoped"] = scoped
        changed = True

    # Ensure maps exist in this scope
    for k in ("address_objects", "service_objects", "ip_map"):
        if not isinstance(blk.get(k), dict):
            blk[k] = {}
            changed = True

    return doc, changed


def apply_unresolved_address_objects(
    overrides_path: Path,
    firewall_device_key: str,
    unresolved_targets: list[str],
    *,
    dry_run: bool = False,
) -> bool:
    """
    Add skeleton entries for unresolved address objects under scoped.<fw_key>.address_objects,
    without overwriting existing entries.

    Returns: changed (whether file would be/was modified)
    """
    if not unresolved_targets:
        # still ensure scope exists (useful), but no skeletons needed
        doc, changed = ensure_scope_block(overrides_path, firewall_device_key)
        if changed and not dry_run:
            _write_yaml(overrides_path, doc)
        return changed

    doc, changed = ensure_scope_block(overrides_path, firewall_device_key)

    scoped = doc["scoped"]
    blk = scoped[firewall_device_key]
    ao = blk["address_objects"]

    for obj in unresolved_targets:
        if not obj or not isinstance(obj, str):
            continue
        if obj in ao and isinstance(ao[obj], dict) and (ao[obj].get("ip") or "").strip():
            # already has a real mapping; leave it alone
            continue
        if obj in ao and isinstance(ao[obj], dict):
            # exists but empty; also leave it
            continue
        if obj not in ao:
            ao[obj] = {"ip": "", "device_id": ""}
            changed = True

    if changed and not dry_run:
        _write_yaml(overrides_path, doc)

    return changed


def _write_yaml(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        doc,
        sort_keys=False,
        default_flow_style=False,
        width=120,
        indent=2,
    )
    path.write_text(text, encoding="utf-8")
    