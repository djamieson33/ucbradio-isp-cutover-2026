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

from common import normalize_obj
from nat_logic import effective_service_name
from policy_parser import AllowRule


def _norm(s: str) -> str:
    # normalize_obj is trim-only; we also force lowercase for reliable matching
    return normalize_obj(s).lower()


def _dst_candidates(dst_translated: str, dst_original: str) -> set[str]:
    cands: set[str] = set()
    for raw in (dst_translated, dst_original):
        n = _norm(raw)
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

    Note: We don't expand service groups; names are treated literally.
    """
    dst_cands = _dst_candidates(dst_translated, dst_original)
    if not dst_cands:
        return False

    eff_service, _translated_is_original = effective_service_name(svc_original, svc_translated)
    eff_service_norm = _norm(eff_service)

    for ar in allow_rules:
        # Must be allow
        action = (getattr(ar, "action", "") or "").strip().lower()
        if action != "allow":
            continue

        # Destination match (Any wildcard)
        dst_norm = getattr(ar, "dst_obj_norm", "") or getattr(ar, "dst_obj", "") or ""
        dst_norm = _norm(dst_norm)
        if dst_norm and dst_norm != "any":
            if dst_norm not in dst_cands:
                continue
        # else blank/any => wildcard

        # Service match (Any wildcard)
        svc_norm = getattr(ar, "svc_norm", "") or getattr(ar, "svc", "") or ""
        svc_norm = _norm(svc_norm)
        if svc_norm and svc_norm != "any":
            if not eff_service_norm:
                continue
            if svc_norm != eff_service_norm:
                continue
        # else blank/any => wildcard

        return True

    return False
