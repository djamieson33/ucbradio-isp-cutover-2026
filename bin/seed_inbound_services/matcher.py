#!/usr/bin/env python3
# bin/seed_inbound_services/matcher.py
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/matcher.py
Purpose: Decide whether a Security Policy allow rule permits a given NAT rule.

Key behaviors:
- Policy destination "Any" matches any destination (wildcard)
- Policy service "Any" matches any service (wildcard)
- Match can succeed against dst_translated OR dst_original
"""

from __future__ import annotations

from typing import Iterable, Optional

from common import normalize_obj
from nat_logic import effective_service_name
from policy_parser import AllowRule


def _dst_candidates(dst_translated: str, dst_original: str) -> set[str]:
    cands = set()
    for raw in (dst_translated, dst_original):
        n = normalize_obj(raw)
        if n:
            cands.add(n)
    return cands


def policy_allows_nat(
    allow_rules: list[AllowRule],
    dst_translated: str,
    svc_translated: str,
    svc_original: str,
    dst_original: str = "",
) -> bool:
    """
    True if ANY allow rule matches the NAT characteristics.

    Matching rules:
      - Destination: rule.destination_address matches dst_translated OR dst_original
        (unless destination is "Any", which matches everything)
      - Service: rule.service matches effective NAT service
        (unless service is "Any", which matches everything)

    Note: We don't try to expand service groups from policy export; we treat names literally.
    """
    dst_cands = _dst_candidates(dst_translated, dst_original)

    eff_service, _translated_is_original = effective_service_name(svc_original, svc_translated)
    eff_service_norm = normalize_obj(eff_service)

    # If we truly have nothing to compare, bail
    if not dst_cands:
        return False

    for ar in allow_rules:
        # Defensive: older AllowRule objects might not have normalized attrs
        dst_norm = getattr(ar, "dst_obj_norm", "") or normalize_obj(getattr(ar, "dst_obj", ""))
        svc_norm = getattr(ar, "svc_norm", "") or normalize_obj(getattr(ar, "svc", ""))

        # Must be allow
        if (getattr(ar, "action", "") or "").strip().lower() != "allow":
            continue

        # Destination match (Any wildcard)
        if dst_norm and dst_norm != "any":
            if dst_norm not in dst_cands:
                continue
        # else dst is any/blank -> wildcard

        # Service match (Any wildcard)
        if svc_norm and svc_norm != "any":
            if not eff_service_norm:
                continue
            if svc_norm != eff_service_norm:
                continue
        # else service is any/blank -> wildcard

        return True

    return False
