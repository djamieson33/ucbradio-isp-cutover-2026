#!/usr/bin/env python3
# bin/seed_inbound_services/nat_parser.py
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/nat_parser.py
Purpose: Parse SonicWall nat-configurations CSV and build inbound service objects.

Kept intentionally smaller by delegating:
- inbound candidate + effective service decisions -> nat_logic.py
- override resolution (address + service expansion) -> nat_resolver.py
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import List, Tuple, Dict, Any

from common import extract_ip, extract_port, extract_proto, safe_slug
from io_csv import read_csv_normalized, is_duplicate_header_row
from matcher import policy_allows_nat
from policy_parser import AllowRule

from nat_logic import nat_is_inbound_candidate, effective_service_name
from nat_resolver import resolve_addr, resolve_service_variants


def build_services_from_nat(
    nat_csv: Path,
    allow_rules: List[AllowRule],
    site: str,
    default_inbound_iface: str,
    overrides: dict | None = None,
) -> Tuple[List[Dict[str, Any]], Dict]:
    nat_headers, nat_rows = read_csv_normalized(nat_csv)
    nat_first_key = nat_headers[0] if nat_headers else "rule_id"

    skipped = 0
    reasons = defaultdict(int)
    unresolved_targets = set()
    unresolved_services = set()

    grouped: Dict[tuple, Dict[str, Any]] = {}

    for r in nat_rows:
        if is_duplicate_header_row(r, nat_first_key):
            skipped += 1
            reasons["duplicate_header_row"] += 1
            continue

        # NAT export fields (normalized)
        name = r.get("name", "")
        comment = r.get("cmt", "") or r.get("description", "")
        nat_method = r.get("nat_method", "")

        ingress = r.get("ingress_interface", "") or default_inbound_iface
        egress = r.get("egress_interface", "")

        dst_original = r.get("destination", "")
        dst_translated = r.get("destination_translated", "")

        svc_original = (r.get("service", "") or "").strip()
        svc_translated = (r.get("service_translated", "") or "").strip()

        ok, internal_ip, target_object = nat_is_inbound_candidate(ingress, dst_translated)
        if not ok:
            skipped += 1
            reasons["translated_destination_is_original_or_empty"] += 1
            continue

        # Resolve address object -> IP + device_id (from overrides)
        device_id_override = ""
        if not internal_ip and target_object:
            ip, did = resolve_addr(overrides, target_object)
            if ip:
                internal_ip = ip
                device_id_override = did

        # Policy allow match (must match translated OR original destination)
        if not policy_allows_nat(
            allow_rules=allow_rules,
            dst_translated=dst_translated,
            svc_translated=svc_translated,
            svc_original=svc_original,
            dst_original=dst_original,
        ):
            skipped += 1
            reasons["no_matching_allow_rule_in_security_policy"] += 1
            continue

        public_ip = extract_ip(dst_original)

        eff_svc_name, translated_is_original = effective_service_name(svc_original, svc_translated)

        # Best-effort parsing from service strings (often not present)
        proto_guess = extract_proto(svc_original) or extract_proto(svc_translated) or ""
        public_port_guess = extract_port(svc_original)

        internal_port_guess = extract_port(svc_translated) or public_port_guess
        if translated_is_original:
            internal_port_guess = public_port_guess

        # Expand service via overrides (preferred)
        variants = resolve_service_variants(overrides, eff_svc_name)

        # Skip junk "Any" rules with no ports and no overrides expansion
        if not variants:
            eff = (eff_svc_name or "").strip().lower()
            if (public_port_guess is None and internal_port_guess is None) and eff in ("any", ""):
                skipped += 1
                reasons["service_is_any_without_ports"] += 1
                continue

        # Track unresolved service objects/groups
        if not variants and (public_port_guess is None and internal_port_guess is None and proto_guess in ("", "any")):
            if eff_svc_name and eff_svc_name.lower() not in ("original", "any"):
                unresolved_services.add(eff_svc_name)

        # If no override expansion, seed single best-effort variant
        if not variants:
            variants = [(proto_guess or "tcp", internal_port_guess, None)]

        for proto, internal_port, port_range in variants:
            key_target = internal_ip if internal_ip else (target_object or dst_translated)
            key_port = int(internal_port or 0) if internal_port is not None else 0
            key = (key_target, key_port, proto, port_range or "")

            if key not in grouped:
                target_for_id = internal_ip if internal_ip else (target_object or dst_translated)
                safe_target = internal_ip.replace(".", "-") if internal_ip else safe_slug(target_for_id)

                port_for_id = internal_port if internal_port is not None else (port_range if port_range else "any")
                svc_id = f"in-{safe_target}-{port_for_id}-{proto}"

                if not internal_ip:
                    unresolved_targets.add(target_for_id)

                internal_target: Dict[str, Any] = {
                    "device_id": device_id_override or "TODO",
                    "ip": internal_ip,
                    "target_object": target_object or dst_translated,
                    "protocol": proto or "",
                    "port": internal_port,
                }
                if port_range:
                    internal_target["port_range"] = port_range

                grouped[key] = {
                    "id": svc_id,
                    "name": f"TODO: Name service on {target_for_id}:{port_for_id}",
                    "description": "TODO",
                    "criticality": "medium",
                    "exposure": "restricted",
                    "owner_id": "TODO",
                    "environment": "production",
                    "category": "other",
                    "site": site,
                    "internal_target": internal_target,
                    "public_entry": {
                        "fqdns": [],
                        "current_public_ip": public_ip,
                        "current_public_destination": dst_original,
                        "target_public_ip": "",
                        "target_public_destination": "",
                        "notes": "",
                    },
                    "nat": {"provider": "sonicwall", "rules": []},
                    "tests": [],
                    "status": {
                        "documented": False,
                        "validated_external": False,
                        "last_validated_utc": "",
                    },
                }

            grouped[key]["nat"]["rules"].append(
                {
                    "nat_policy_name": name or "",
                    "comment": comment or "",
                    "nat_method": nat_method or "",
                    "public_ip": public_ip,
                    "public_port": public_port_guess,
                    "protocol": proto or "",
                    "internal_ip": internal_ip,
                    "internal_port": internal_port,
                    "inbound_interface": ingress or "",
                    "outbound_interface": egress or "",
                    "original_destination_raw": dst_original or "",
                    "translated_destination_raw": dst_translated or "",
                    "original_service_raw": svc_original or "",
                    "translated_service_raw": svc_translated or "",
                    "effective_service_name": eff_svc_name or "",
                    "resolved_from_overrides": bool(resolve_service_variants(overrides, eff_svc_name)),
                    "resolved_port_range": port_range or "",
                }
            )

    services = list(grouped.values())

    stats = {
        "seeded_services": len(services),
        "skipped_rows": skipped,
        "skip_reasons": dict(sorted(reasons.items())),
        "unresolved_target_objects_count": len(unresolved_targets),
        "unresolved_service_objects_count": len(unresolved_services),
        "unresolved_target_objects": sorted(unresolved_targets),
        "unresolved_service_objects": sorted(unresolved_services),
    }

    return services, stats
