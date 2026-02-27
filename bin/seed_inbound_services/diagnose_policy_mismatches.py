#!/usr/bin/env python3
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/diagnose_policy_mismatches.py
Purpose: Print NAT rows that fail to match an ALLOW rule in the Security Policy export.

Why:
- When seeding inbound services, we only keep NAT rules that have a corresponding inbound "allow"
  in the Security Policy CSV.
- This script prints the specific NAT rows that are being skipped so you can chase them down in
  SonicWall UI and/or add overrides.

Default inputs:
  firewall/sonicwall/exports/nat-configurations-*.csv
  firewall/sonicwall/exports/security-policy-*.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

# Allow running directly from repo root
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from io_csv import newest_matching

EXPORTS_DIR = Path("firewall/sonicwall/exports")


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _effective_service(svc: str, svc_translated: str) -> str:
    svc = (svc or "").strip()
    svc_t = (svc_translated or "").strip()
    return svc if _norm(svc_t) == "original" else (svc_t or svc)


def _get(row: dict[str, Any], *keys: str) -> str:
    """
    Return first non-empty value for provided CSV column names.
    Helps when SonicWall exports vary slightly between models/firmware.
    """
    for k in keys:
        v = row.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return ""


def read_allow_triples(policy_csv: Path) -> set[tuple[str, str, str]]:
    """
    Return a set of (dst_addr, service, dst_zone) for ALLOW rules.
    Matching is string-based (normalized), not object-membership based.
    """
    allow: set[tuple[str, str, str]] = set()
    with policy_csv.open(newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            if _norm(_get(row, "Action")) != "allow":
                continue

            dst_addr = _norm(_get(row, "Destination Address", "Destination"))
            svc = _norm(_get(row, "Service"))
            dst_zone = _norm(_get(row, "Destination Zone", "To Zone", "To"))

            allow.add((dst_addr, svc, dst_zone))
    return allow


def nat_inboundish(row: dict[str, Any]) -> bool:
    """
    Cheap filter so we don't print noise:
      - has ingress interface
      - destination translated is present and not 'Original'
    """
    ingress = _get(row, "Ingress Interface", "Inbound Interface")
    dst_t = _get(row, "Destination Translated", "Destination NAT IP", "Dest Translated")

    if not ingress:
        return False
    if not dst_t or _norm(dst_t) == "original":
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nat", help="Path to NAT CSV (default: newest nat-configurations-*.csv)")
    ap.add_argument("--policy", help="Path to Security Policy CSV (default: newest security-policy-*.csv)")
    ap.add_argument("--limit", type=int, default=50, help="Max rows to print")
    ap.add_argument(
        "--match-zone",
        action="store_true",
        help="Also require Destination Zone match (stricter; may reduce false positives).",
    )
    args = ap.parse_args()

    if not EXPORTS_DIR.exists():
        print("[ERROR] exports directory not found: firewall/sonicwall/exports", file=sys.stderr)
        return 2

    nat_csv = Path(args.nat) if args.nat else newest_matching(EXPORTS_DIR, "nat-configurations-*.csv")
    if not nat_csv or not nat_csv.exists():
        print("[ERROR] No nat-configurations-*.csv found", file=sys.stderr)
        return 2

    policy_csv = Path(args.policy) if args.policy else newest_matching(EXPORTS_DIR, "security-policy-*.csv")
    if not policy_csv or not policy_csv.exists():
        print("[ERROR] No security-policy-*.csv found", file=sys.stderr)
        return 2

    allow = read_allow_triples(policy_csv)

    print(f"[INFO] NAT CSV: {nat_csv}")
    print(f"[INFO] Policy CSV: {policy_csv}")
    print(f"[INFO] Allow rules indexed: {len(allow)}")
    print(f"[INFO] Zone matching: {'ON' if args.match_zone else 'OFF'}")

    misses: list[dict[str, str]] = []

    with nat_csv.open(newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for line_no, row in enumerate(r, start=2):
            if not nat_inboundish(row):
                continue

            nat_name = _get(row, "Name")
            comment = _get(row, "cmt", "Comment", "Comments")
            ingress = _get(row, "Ingress Interface", "Inbound Interface")
            egress = _get(row, "Egress Interface", "Outbound Interface")

            dst_t = _get(row, "Destination Translated", "Destination NAT IP", "Dest Translated")
            svc = _get(row, "Service")
            svc_t = _get(row, "Service Translated", "Service (Translated)")
            eff = _effective_service(svc, svc_t)

            dst_n = _norm(dst_t)
            svc_n = _norm(eff)

            if args.match_zone:
                # If matching zone, attempt a best-effort guess from NAT ingress interface.
                # This is imperfect, but helpful when policy CSV is cleanly zoned.
                # If it creates noise, run without --match-zone.
                zone_guess = _norm(ingress)
                has = (dst_n, svc_n, zone_guess) in allow
            else:
                # Match ignoring zone (zone often not directly derivable from NAT CSV)
                has = any((a == dst_n and s == svc_n) for (a, s, _z) in allow)

            if has:
                continue

            misses.append(
                {
                    "csv_line": str(line_no),
                    "nat_name": nat_name,
                    "comment": comment,
                    "ingress": ingress,
                    "egress": egress,
                    "dst_translated": dst_t,
                    "effective_service": eff,
                    "service": svc,
                    "service_translated": svc_t,
                    "lookup_key": f"{dst_n} :: {svc_n}",
                }
            )

    print(f"[RESULT] Unmatched inbound-ish NAT rows: {len(misses)}")

    for m in misses[: max(0, args.limit)]:
        print("\n---")
        for k in (
            "csv_line",
            "nat_name",
            "comment",
            "ingress",
            "egress",
            "dst_translated",
            "effective_service",
            "service",
            "service_translated",
            "lookup_key",
        ):
            print(f"{k:>18}: {m.get(k,'')}")

    if len(misses) > args.limit:
        print(f"\n[INFO] Showing first {args.limit}; re-run with --limit {len(misses)} to print all.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
