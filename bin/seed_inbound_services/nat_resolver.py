#!/usr/bin/env python3
# bin/seed_inbound_services/nat_resolver.py
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/nat_resolver.py
Purpose: Resolve address/service objects for NAT parsing.

- address object name -> (ip, device_id) using overrides (tolerant match)
- service/group name -> [(proto, port, port_range), ...] using overrides

Supports scoped overrides via firewall_device_key.
"""

from __future__ import annotations

from common import safe_slug
from nat_overrides import addr_override, svc_override_entries, expand_ports_from_entries, get_map


def resolve_addr(overrides: dict | None, obj_name: str, firewall_device_key: str = "") -> tuple[str, str]:
    """
    Resolve an address object name -> (ip, device_id)

    Strategies:
      1) nat_overrides.addr_override() (scoped-first, then global)
      2) exact key match (strip)
      3) case-insensitive match
      4) safe_slug match
    """
    if not overrides or not obj_name:
        return "", ""

    name = (obj_name or "").strip()
    if not name:
        return "", ""

    # 1) exact helper (scoped-first)
    ov = addr_override(overrides, name, firewall_device_key=firewall_device_key)
    if ov and getattr(ov, "ip", ""):
        return (ov.ip or "").strip(), (ov.device_id or "").strip()

    # Build merged view (global + scoped where scoped overrides)
    ao = get_map(overrides, firewall_device_key, "address_objects")
    if not isinstance(ao, dict) or not ao:
        return "", ""

    # 2) exact (after strip)
    v = ao.get(name)
    if isinstance(v, dict) and (v.get("ip") or "").strip():
        return (v.get("ip") or "").strip(), (v.get("device_id") or "").strip()

    # 3) case-insensitive
    name_cf = name.casefold()
    for k, v in ao.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            continue
        if k.strip().casefold() == name_cf and (v.get("ip") or "").strip():
            return (v.get("ip") or "").strip(), (v.get("device_id") or "").strip()

    # 4) slug match
    want = safe_slug(name)
    for k, v in ao.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            continue
        if safe_slug(k) == want and (v.get("ip") or "").strip():
            return (v.get("ip") or "").strip(), (v.get("device_id") or "").strip()

    return "", ""


def resolve_service_variants(
    overrides: dict | None,
    effective_service_name: str,
    firewall_device_key: str = "",
) -> list[tuple[str, int | None, str | None]]:
    """
    Resolve a service object/group into concrete protocol + port / port_range variants.

    Returns list of (protocol, port, port_range).
    """
    name = (effective_service_name or "").strip()
    if not overrides or not name:
        return []

    entries = svc_override_entries(overrides, name, firewall_device_key=firewall_device_key)
    if not entries:
        return []

    expanded = expand_ports_from_entries(entries)
    return [(v.protocol, v.port, v.port_range) for v in expanded]
