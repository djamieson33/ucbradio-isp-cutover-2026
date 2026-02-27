#!/usr/bin/env python3
"""
UCB Radio – ISP Changeover 2026
File:        bin/overrides/upsert_sonicwall_overrides.py
Purpose:     Upsert scoped SonicWall object overrides (address_objects/service_objects/ip_map)
             without overwriting existing values, and bump updated_utc (UTC).

Examples:

  # Add unresolved address objects as placeholders (no overwrite), bump updated_utc
  python3 bin/overrides/upsert_sonicwall_overrides.py \
    --firewall-device-key 8-fw-sonicwall-nipi-100 \
    --address-objects "Nautel,ZIPONE"

  # Fill in IP + device_id in one shot (still no overwrite unless --overwrite)
  python3 bin/overrides/upsert_sonicwall_overrides.py \
    --firewall-device-key 8-fw-sonicwall-nipi-100 \
    --set-address "Nautel=192.168.0.50:nautel-nipi-100,ZIPONE=192.168.0.60:zipone-nipi-100"

  # Overwrite existing values (use carefully)
  python3 bin/overrides/upsert_sonicwall_overrides.py \
    --firewall-device-key 8-fw-sonicwall-nipi-100 \
    --set-address "Nautel=192.168.0.50:nautel-nipi-100" \
    --overwrite
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from typing import Dict, Tuple, Optional

try:
    import yaml
except ImportError:
    print("[ERROR] Missing dependency: PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


DEFAULT_OVERRIDES_PATH = "inventory/sonicwall-object-overrides.yaml"


def utc_now_iso() -> str:
    # Example: 2026-02-27T14:16:00Z
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_csv_list(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]


def parse_set_address(value: Optional[str]) -> Dict[str, Tuple[str, str]]:
    """
    Parse:
      "Nautel=192.168.0.50:nautel-nipi-100,ZIPONE=192.168.0.60:zipone-nipi-100"

    Returns dict: { "Nautel": ("192.168.0.50", "nautel-nipi-100"), ... }
    """
    out: Dict[str, Tuple[str, str]] = {}
    if not value:
        return out

    items = [x.strip() for x in value.split(",") if x.strip()]
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid --set-address item (missing '='): {item}")
        name, rhs = item.split("=", 1)
        name = name.strip()
        rhs = rhs.strip()

        if ":" not in rhs:
            raise ValueError(f"Invalid --set-address RHS (missing ':'): {item}  (expected ip:device_id)")
        ip, device_id = rhs.split(":", 1)
        ip = ip.strip()
        device_id = device_id.strip()

        if not name:
            raise ValueError(f"Invalid --set-address item (empty name): {item}")
        if not ip:
            raise ValueError(f"Invalid --set-address item (empty ip): {item}")
        if not device_id:
            raise ValueError(f"Invalid --set-address item (empty device_id): {item}")

        out[name] = (ip, device_id)

    return out


def ensure_root_structure(doc: dict) -> dict:
    # Minimal stable schema
    doc.setdefault("version", 1)
    doc.setdefault("updated_utc", utc_now_iso())
    doc.setdefault("address_objects", {})
    doc.setdefault("service_objects", {})
    doc.setdefault("ip_map", {})
    doc.setdefault("scoped", {})
    return doc


def ensure_scoped_firewall(doc: dict, fw_key: str) -> dict:
    scoped = doc.setdefault("scoped", {})
    fw = scoped.setdefault(fw_key, {})
    fw.setdefault("address_objects", {})
    fw.setdefault("service_objects", {})
    fw.setdefault("ip_map", {})
    return fw


def upsert_address_placeholder(fw: dict, name: str) -> None:
    ao = fw.setdefault("address_objects", {})
    ao.setdefault(name, {"ip": "", "device_id": ""})


def upsert_address_values(fw: dict, name: str, ip: str, device_id: str, overwrite: bool) -> None:
    ao = fw.setdefault("address_objects", {})
    entry = ao.setdefault(name, {"ip": "", "device_id": ""})

    if overwrite or not entry.get("ip"):
        entry["ip"] = ip
    if overwrite or not entry.get("device_id"):
        entry["device_id"] = device_id


def load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        # Create empty doc with schema
        return ensure_root_structure({})

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Overrides YAML must be a mapping at top-level: {path}")
        return ensure_root_structure(data)


def dump_yaml(path: str, doc: dict) -> None:
    # Keep it readable and stable; preserve insertion order (PyYAML 5.1+)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            doc,
            f,
            sort_keys=False,
            default_flow_style=False,
            width=120,
        )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--overrides", default=DEFAULT_OVERRIDES_PATH, help=f"Path to overrides YAML (default: {DEFAULT_OVERRIDES_PATH})")
    p.add_argument("--firewall-device-key", required=True, help='Firewall device key, e.g. "8-fw-sonicwall-nipi-100"')
    p.add_argument("--address-objects", help='Comma list of address objects to ensure exist as placeholders, e.g. "Nautel,ZIPONE"')
    p.add_argument("--set-address", help='Comma list of NAME=IP:DEVICE_ID to upsert, e.g. "Nautel=192.168.0.50:nautel-nipi-100"')
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing ip/device_id values if already present")
    args = p.parse_args()

    doc = load_yaml(args.overrides)

    # Always bump updated_utc on write
    doc["updated_utc"] = utc_now_iso()

    fw_key = args.firewall_device_key
    fw = ensure_scoped_firewall(doc, fw_key)

    placeholders = parse_csv_list(args.address_objects)
    for name in placeholders:
        upsert_address_placeholder(fw, name)

    set_map = parse_set_address(args.set_address)
    for name, (ip, device_id) in set_map.items():
        upsert_address_values(fw, name, ip, device_id, overwrite=args.overwrite)

    dump_yaml(args.overrides, doc)

    print(f"[OK] Updated: {args.overrides}")
    print(f"[OK] firewall-device-key: {fw_key}")
    if placeholders:
        print(f"[OK] ensured placeholders: {', '.join(placeholders)}")
    if set_map:
        print(f"[OK] upserted values: {', '.join(set_map.keys())}")
    print(f"[OK] updated_utc: {doc['updated_utc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
