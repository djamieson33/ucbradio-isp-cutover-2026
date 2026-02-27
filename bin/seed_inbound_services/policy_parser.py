#!/usr/bin/env python3
# bin/seed_inbound_services/policy_parser.py
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/policy_parser.py
Purpose: Parse SonicWall security-policy CSV and build a list of ALLOW rules for NAT matching.

Notes:
- Default behavior restricts to Source Zone = WAN (inbound-ish rules).
  If you want broader matching, pass restrict_src_zones=None.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from common import normalize_obj
from io_csv import read_csv_normalized, is_duplicate_header_row


@dataclass(frozen=True)
class AllowRule:
    # Identifiers / metadata
    rule_id: str
    name: str
    action: str

    # Zones (as exported)
    src_zone: str
    dst_zone: str

    # Objects (as exported)
    dst_obj: str
    svc: str

    # Normalized for matching
    dst_obj_norm: str
    svc_norm: str


def build_allow_rules(
    policy_csv: Path,
    restrict_src_zones: Optional[tuple[str, ...]] = ("wan",),
) -> Tuple[List[AllowRule], Dict[str, int]]:
    """
    Build a list of AllowRule from a SonicWall security-policy export.

    restrict_src_zones:
      - ("wan",)  => keep only rules whose Source Zone is WAN (default)
      - None      => do not filter by source zone
    """
    headers, rows = read_csv_normalized(policy_csv)
    first_key = headers[0] if headers else "uuid"

    allow_rules: List[AllowRule] = []
    rows_total = 0
    allow_total = 0

    # Normalize zone filter for comparisons
    restrict_norm = None
    if restrict_src_zones is not None:
        restrict_norm = {z.strip().lower() for z in restrict_src_zones if (z or "").strip()}

    for r in rows:
        rows_total += 1
        if is_duplicate_header_row(r, first_key):
            continue

        action = (r.get("action") or "").strip().lower()
        if action != "allow":
            continue

        # Normalized keys from read_csv_normalized():
        # "Source Zone" -> source_zone
        # "Destination Zone" -> destination_zone
        # "Destination Address" -> destination_address
        # "Service" -> service
        src_zone = (r.get("source_zone") or "").strip()
        dst_zone = (r.get("destination_zone") or "").strip()
        dst_obj = (r.get("destination_address") or "").strip()
        svc = (r.get("service") or "").strip()

        if not dst_obj or not svc:
            # If these are empty, either the export is missing columns
            # or the normalized header names differ.
            continue

        if restrict_norm is not None:
            if src_zone.strip().lower() not in restrict_norm:
                continue

        rule_id = (r.get("rule_id") or r.get("uuid") or "").strip()
        name = (r.get("name") or r.get("rule_name") or "").strip()

        ar = AllowRule(
            rule_id=rule_id,
            name=name,
            action=action,
            src_zone=src_zone,
            dst_zone=dst_zone,
            dst_obj=dst_obj,
            svc=svc,
            dst_obj_norm=normalize_obj(dst_obj),
            svc_norm=normalize_obj(svc),
        )
        allow_rules.append(ar)
        allow_total += 1

    stats = {
        "rows_total": rows_total,
        "allow_rules": allow_total,
    }
    return allow_rules, stats
