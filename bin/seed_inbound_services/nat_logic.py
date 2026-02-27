#!/usr/bin/env python3
# bin/seed_inbound_services/nat_logic.py
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/nat_logic.py
Purpose: Stateless NAT parsing logic helpers.
"""

from __future__ import annotations

from common import extract_ip, is_private_ip


def _is_original(s: str) -> bool:
    return (s or "").strip().lower() == "original"


def nat_is_inbound_candidate(ingress_iface: str, dst_translated: str) -> tuple[bool, str, str]:
    """
    Return (ok, internal_ip, target_object)

    Inbound NAT commonly uses address objects (not literal IPs).

    Rules:
      - ingress interface must exist
      - destination translated must be present and not "Original"
      - Accept:
          * private literal IPs (e.g., 192.168.x.x)
          * object names (e.g., "SRV-APP Private")
      - Reject:
          * public literal IPs in Destination Translated (usually not a LAN-forward target)
    """
    if not (ingress_iface or "").strip():
        return False, "", ""

    raw = (dst_translated or "").strip()
    if not raw or _is_original(raw):
        return False, "", ""

    ip = extract_ip(raw)
    if ip:
        if is_private_ip(ip):
            return True, ip, ""
        # Public IP literal in translated destination is not a normal inbound-forward target
        return False, "", ""

    # Object name case
    return True, "", raw


def effective_service_name(svc_original: str, svc_translated: str) -> tuple[str, bool]:
    """
    If service_translated is "Original", the effective service is the original service.
    Returns (effective_name, translated_is_original)
    """
    o = (svc_original or "").strip()
    t = (svc_translated or "").strip()
    translated_is_original = _is_original(t)
    eff = o if translated_is_original else (t or o)
    return eff, translated_is_original
