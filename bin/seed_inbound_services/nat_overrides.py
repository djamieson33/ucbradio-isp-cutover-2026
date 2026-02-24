#!/usr/bin/env python3
# bin/seed_inbound_services/nat_overrides.py
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/nat_overrides.py
Purpose: Override helpers for SonicWall object/service resolution.

Overrides file: inventory/sonicwall-object-overrides.yaml

Supported keys:
  address_objects:
    "<Object Name>":
      ip: "192.168.100.10"
      device_id: "svr-mj01a1dt"

  service_objects:
    "<Service/Group Name>":
      entries:
        - protocol: tcp|udp
          port: 443
        - protocol: tcp
          port_range: "3136-3137"

  ip_map:
    "192.168.100.18": "srvpathfind1"
    "192.168.100.97": "zettaserver"
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


def addr_override(overrides: dict | None, obj_name: str) -> AddressOverride | None:
    if not overrides or not obj_name:
        return None
    m = overrides.get("address_objects") or {}
    v = m.get(obj_name)
    if not isinstance(v, dict):
        return None
    ip = (v.get("ip") or "").strip()
    device_id = (v.get("device_id") or "").strip()
    if not ip:
        return None
    return AddressOverride(ip=ip, device_id=device_id)


def ip_map_device_id(overrides: dict | None, ip: str) -> str:
    if not overrides or not ip:
        return ""
    m = overrides.get("ip_map") or {}
    v = m.get(ip)
    return v.strip() if isinstance(v, str) else ""


def svc_override_entries(overrides: dict | None, svc_name: str) -> list[dict[str, Any]]:
    if not overrides or not svc_name:
        return []
    m = overrides.get("service_objects") or {}
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
