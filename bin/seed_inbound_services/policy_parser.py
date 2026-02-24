#!/usr/bin/env python3
# bin/seed_inbound_services/policy_parser.py
"""
Parse SonicWall security-policy CSV and build a list of ALLOW rules for matching NAT.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Any

from common import safe_slug
from io_csv import read_csv_normalized, is_duplicate_header_row


@dataclass(frozen=True)
class AllowRule:
    rule_id: str
    name: str
    action: str
    src_zone: str
    dst_addr: str
    service: str
    dst_addr_norm: str
    service_norm: str


def build_allow_rules(policy_csv: Path) -> Tuple[List[AllowRule], Dict[str, int]]:
    headers, rows = read_csv_normalized(policy_csv)
    first_key = headers[0] if headers else "uuid"

    allow_rules: List[AllowRule] = []

    rows_total = 0
    allow_total = 0

    for r in rows:
        rows_total += 1
        if is_duplicate_header_row(r, first_key):
            continue

        action = (r.get("action") or "").strip().lower()
        if action != "allow":
            continue

        # These keys MUST match what read_csv_normalized() produces.
        # In your raw CSV, columns are "Source Zone", "Destination Address", "Service".
        src_zone = (r.get("source_zone") or "").strip()
        dst_addr = (r.get("destination_address") or "").strip()
        service = (r.get("service") or "").strip()

        # If these come back empty, your normalized header keys differ.
        if not dst_addr or not service:
            continue

        # Optional: restrict to inbound WAN rules only.
        # If you want broader matching, comment this out.
        if src_zone.strip().lower() not in ("wan",):
            continue

        rule_id = (r.get("rule_id") or "").strip()
        name = (r.get("name") or r.get("rule_name") or "").strip()

        ar = AllowRule(
            rule_id=rule_id,
            name=name,
            action=action,
            src_zone=src_zone,
            dst_addr=dst_addr,
            service=service,
            dst_addr_norm=safe_slug(dst_addr),
            service_norm=safe_slug(service),
        )
        allow_rules.append(ar)
        allow_total += 1

    stats = {
        "rows_total": rows_total,
        "allow_rules": allow_total,
    }
    return allow_rules, stats
