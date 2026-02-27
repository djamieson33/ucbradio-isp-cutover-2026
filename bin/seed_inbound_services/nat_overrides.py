#!/usr/bin/env python3
# bin/seed_inbound_services/nat_overrides.py
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/nat_overrides.py
Purpose: Override helpers for SonicWall object/service resolution.

Overrides file: inventory/sonicwall-object-overrides.yaml

Supports GLOBAL and PER-FIREWALL overrides.

Preferred structure (new):
  global:
    address_objects: { ... }
    service_objects: { ... }
    ip_map: { ... }

  firewalls:
    "<firewall_device_key>":
      address_objects: { ... }
      service_objects: { ... }
      ip_map: { ... }

Backward compatible with older structures:
  - top-level address_objects/service_objects/ip_map
  - scoped:
      "<firewall_device_key>": { address_objects/service_objects/ip_map }
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AddressOverride:
    ip: str
    device_id: str


@dataclass(frozen=True)
class PortVariant:
    protocol: str           # "tcp" | "udp"
    port: int | None        # single port
    port_range: str | None  # "start-end"


def _dict_or_empty(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _global_block(overrides: dict | None) -> dict:
    """
    Return the global override block.

    New structure: overrides["global"]
    Old structure: overrides itself (top-level maps)
    """
    if not overrides:
        return {}
    g = overrides.get("global")
    if isinstance(g, dict):
        return g
    return overrides  # old flat structure fallback


def _scoped_block(overrides: dict | None, firewall_device_key: str) -> dict:
    """
    Return the per-firewall scoped block.

    New structure: overrides["firewalls"][firewall_device_key]
    Old structure: overrides["scoped"][firewall_device_key]
    """
    if not overrides or not firewall_device_key:
        return {}

    fw = overrides.get("firewalls")
    if isinstance(fw, dict):
        blk = fw.get(firewall_device_key)
        if isinstance(blk, dict):
            return blk

    scoped = overrides.get("scoped")
    if isinstance(scoped, dict):
        blk = scoped.get(firewall_device_key)
        if isinstance(blk, dict):
            return blk

    return {}


def _get_map(overrides: dict | None, firewall_device_key: str, map_name: str) -> dict:
    """
    Return a merged view: firewall-scoped map (if present) takes precedence over global map.
    """
    if not overrides:
        return {}

    global_blk = _global_block(overrides)
    scoped_blk = _scoped_block(overrides, firewall_device_key)

    global_map = _dict_or_empty(global_blk.get(map_name))
    scoped_map = _dict_or_empty(scoped_blk.get(map_name))

    out: dict = {}
    out.update(global_map)
    out.update(scoped_map)  # scoped wins
    return out


# Public alias (so other modules don’t rely on a “private” name)
def get_map(overrides: dict | None, firewall_device_key: str, map_name: str) -> dict:
    return _get_map(overrides, firewall_device_key, map_name)


def addr_override(overrides: dict | None, obj_name: str, firewall_device_key: str = "") -> AddressOverride | None:
    if not overrides or not obj_name:
        return None

    m = _get_map(overrides, firewall_device_key, "address_objects")
    v = m.get(obj_name)
    if not isinstance(v, dict):
        return None

    ip = (v.get("ip") or "").strip()
    device_id = (v.get("device_id") or "").strip()
    if not ip:
        return None
    return AddressOverride(ip=ip, device_id=device_id)


def ip_map_device_id(overrides: dict | None, ip: str, firewall_device_key: str = "") -> str:
    if not overrides or not ip:
        return ""
    m = _get_map(overrides, firewall_device_key, "ip_map")
    v = m.get(ip)
    return v.strip() if isinstance(v, str) else ""


def svc_override_entries(overrides: dict | None, svc_name: str, firewall_device_key: str = "") -> list[dict[str, Any]]:
    if not overrides or not svc_name:
        return []
    m = _get_map(overrides, firewall_device_key, "service_objects")
    v = m.get(svc_name)
    if not isinstance(v, dict):
        return []
    entries = v.get("entries") or []
    return entries if isinstance(entries, list) else []


def expand_ports_from_entries(entries: list[dict[str, Any]]) -> list[PortVariant]:
    """
    Convert override entries into normalized variants.
    """
    out: list[PortVariant] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        proto = (e.get("protocol") or "").strip().lower()
        if proto not in ("tcp", "udp"):
            continue

        if "port" in e and e.get("port") is not None:
            try:
                p = int(e["port"])
            except Exception:
                continue
            if 1 <= p <= 65535:
                out.append(PortVariant(protocol=proto, port=p, port_range=None))
            continue

        if "port_range" in e and e.get("port_range"):
            pr = str(e["port_range"]).strip()
            if "-" in pr:
                out.append(PortVariant(protocol=proto, port=None, port_range=pr))

    return out
