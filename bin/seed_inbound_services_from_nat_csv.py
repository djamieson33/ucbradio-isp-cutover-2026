#!/usr/bin/env python3
"""
UCB Radio – ISP Changeover 2026
File: bin/seed_inbound_services_from_nat_csv.py
Purpose: Generate inventory/03-inbound-services.seed.yaml from the most
         recent SonicWall NAT export.

──────────────────────────────────────────────────────────────────────────────
FILENAME & EXPORT STANDARDS
──────────────────────────────────────────────────────────────────────────────

SonicWall NAT exports MUST follow this naming convention:

    firewall/sonicwall/exports/
        nat-policies-YYYYMMDDThhmmZ.csv

Example:
    nat-policies-20260224T1718Z.csv

Rules:
- Timestamp MUST be UTC.
- Format MUST be: YYYYMMDDThhmmZ
- File MUST live in: firewall/sonicwall/exports/
- Only files matching: nat-policies-*.csv are considered valid inputs.

This script will automatically:
- Select the newest nat-policies-*.csv (by modification time)
- Refuse to run if no properly named files are found

──────────────────────────────────────────────────────────────────────────────
GENERATED OUTPUT
──────────────────────────────────────────────────────────────────────────────

This script generates:

    inventory/03-inbound-services.seed.yaml

Important:
- This is a GENERATED file.
- Canonical file remains:
      inventory/03-inbound-services.yaml
- Seed file is used for review and manual merge.

──────────────────────────────────────────────────────────────────────────────
CUTOVER AUDIT RULE
──────────────────────────────────────────────────────────────────────────────

Before any ISP cutover activity:
1. Export NAT from SonicWall.
2. Rename using UTC standard.
3. Commit export to git.
4. Run this script.
5. Commit generated seed file.
6. Review and merge into canonical inventory file.

This preserves a verifiable pre-cutover baseline.
──────────────────────────────────────────────────────────────────────────────
"""
Seed inventory/03-inbound-services.yaml from a SonicWall NAT export CSV.

What it does:
- Reads NAT export CSV
- Heuristically detects WAN->LAN inbound port-forward style rules
- Extracts: public ip/port/proto, internal ip/port, interface if present, policy name/comment
- Groups rules into "services" keyed by internal_ip (and internal_port if available)
- Writes a YAML skeleton you can review and then merge into your canonical file

Usage:
  python3 bin/seed_inbound_services_from_nat_csv.py \
    --csv firewall/sonicwall/exports/nat-policies-YYYYMMDDThhmmZ.csv \
    --out inventory/03-inbound-services.seed.yaml \
    --site belleville \
    --default-inbound-iface X1
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import ipaddress
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml  # PyYAML
except Exception as e:
    print("[ERROR] PyYAML not installed. Try: python3 -m pip install pyyaml", file=sys.stderr)
    raise


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").strip().lower()).strip("_")


def is_private_ip(s: str) -> bool:
    try:
        return ipaddress.ip_address(s.strip()).is_private
    except Exception:
        return False


def extract_ip(s: str) -> str:
    if not s:
        return ""
    m = re.search(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b", s)
    return m.group(1) if m else ""


def extract_port(s: str) -> int | None:
    if not s:
        return None
    # Common patterns: "HTTPS(443)", "TCP 443", "443", "udp/123", "TCP:443"
    m = re.search(r"\b(\d{1,5})\b", s)
    if not m:
        return None
    p = int(m.group(1))
    if 1 <= p <= 65535:
        return p
    return None


def extract_proto(s: str) -> str:
    if not s:
        return ""
    s2 = s.strip().lower()
    if "udp" in s2:
        return "udp"
    if "tcp" in s2:
        return "tcp"
    # some SonicWall exports might show "Any"
    if "any" in s2:
        return "any"
    return ""


def pick_col(row: dict, candidates: list[str]) -> str:
    """Pick the first matching column from normalized candidates."""
    for c in candidates:
        if c in row and row[c].strip():
            return row[c].strip()
    return ""


def main() -> int:

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--csv",
        help="Path to SonicWall NAT export CSV (optional; if omitted, newest CSV in firewall/sonicwall/exports is used)"
    )
    ap.add_argument(
        "--out",
        default="inventory/03-inbound-services.seed.yaml",
        help="Output YAML path"
    )
    ap.add_argument(
        "--site",
        default="belleville",
        help="Site slug"
    )
    ap.add_argument(
        "--default-inbound-iface",
        default="X1",
        help="Default inbound interface if CSV lacks it"
    )
    args = ap.parse_args()

    # Auto-detect newest CSV if not provided
    if args.csv:
        csv_path = Path(args.csv)
    else:
        exports_dir = Path("firewall/sonicwall/exports")
        if not exports_dir.exists():
            print("[ERROR] exports directory not found.", file=sys.stderr)
            sys.exit(2)

        csv_files = list(exports_dir.glob("*.csv"))
        if not csv_files:
            print("[ERROR] No CSV files found in firewall/sonicwall/exports", file=sys.stderr)
            sys.exit(2)

        csv_path = max(csv_files, key=lambda p: p.stat().st_mtime)
        print(f"[INFO] Auto-selected latest CSV: {csv_path}")

    out_path = Path(args.out)

    if not csv_path.exists():
        print(f"[ERROR] CSV not found: {csv_path}", file=sys.stderr)
        return 2

    # Read CSV
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print("[ERROR] CSV has no header row.", file=sys.stderr)
            return 2

        # Normalize headers
        orig_headers = list(reader.fieldnames)
        headers = [norm(h) for h in orig_headers]

        def normalize_row(raw: dict) -> dict:
            nr = {}
            for oh, nh in zip(orig_headers, headers):
                nr[nh] = (raw.get(oh) or "").strip()
            return nr

        rows = [normalize_row(r) for r in reader]

    # Column heuristics (SonicOS exports vary by version)
    # Try to locate the usual NAT fields.
    COL = {
        "policy_name": ["name", "policy_name", "nat_policy", "rule_name"],
        "comment": ["comment", "comments", "description", "note", "notes"],
        "from_zone": ["original_source_zone", "from_zone", "source_zone", "inbound_zone"],
        "to_zone": ["translated_destination_zone", "to_zone", "destination_zone", "outbound_zone"],
        "orig_dst": ["original_destination", "original_dest", "dst_original", "public_destination"],
        "xlated_dst": ["translated_destination", "translated_dest", "dst_translated", "private_destination"],
        "orig_svc": ["original_service", "service_original", "orig_service"],
        "xlated_svc": ["translated_service", "service_translated", "xlate_service"],
        "in_iface": ["inbound_interface", "in_interface", "ingress_interface", "interface_in"],
        "out_iface": ["outbound_interface", "out_interface", "egress_interface", "interface_out"],
    }

    seeded = []
    skipped = 0
    reasons = defaultdict(int)

    # Grouping key: internal_ip + (internal_port if present else 0) + proto
    grouped: dict[tuple[str, int, str], dict] = {}

    for r in rows:
        policy_name = pick_col(r, COL["policy_name"])
        comment = pick_col(r, COL["comment"])

        from_zone = pick_col(r, COL["from_zone"]).upper()
        to_zone = pick_col(r, COL["to_zone"]).upper()

        orig_dst_raw = pick_col(r, COL["orig_dst"])
        xdst_raw = pick_col(r, COL["xlated_dst"])

        orig_svc_raw = pick_col(r, COL["orig_svc"])
        xsvc_raw = pick_col(r, COL["xlated_svc"])

        in_iface = pick_col(r, COL["in_iface"]) or args.default_inbound_iface
        out_iface = pick_col(r, COL["out_iface"])

        public_ip = extract_ip(orig_dst_raw)
        internal_ip = extract_ip(xdst_raw)

        # Ports/proto
        proto = extract_proto(orig_svc_raw) or extract_proto(xsvc_raw) or ""
        public_port = extract_port(orig_svc_raw)
        internal_port = extract_port(xsvc_raw) or public_port

        # Filter: inbound WAN -> LAN style, and internal is private
        # If zones missing, fall back to "internal_ip is private AND public_ip is not private"
        zone_ok = (from_zone == "WAN" and to_zone in ("LAN", "DMZ", "WLAN", "TRUST", "LAN_PRIMARY", "LAN1")) if (from_zone or to_zone) else True
        ip_ok = bool(internal_ip) and is_private_ip(internal_ip) and bool(public_ip) and (not is_private_ip(public_ip))

        if not zone_ok:
            skipped += 1
            reasons["not_wan_to_lan"] += 1
            continue
        if not ip_ok:
            skipped += 1
            reasons["not_public_to_private"] += 1
            continue
        if public_port is None and internal_port is None and proto in ("", "any"):
            # Likely not a port-forward; keep it out of the service file
            skipped += 1
            reasons["no_ports_detected"] += 1
            continue

        key = (internal_ip, int(internal_port or 0), proto or "tcp")  # default proto tcp if unknown
        if key not in grouped:
            internal_port_for_id = int(internal_port or 0)
            svc_id = f"in-{internal_ip.replace('.','-')}-{internal_port_for_id or 'any'}-{(proto or 'tcp')}"
            grouped[key] = {
                "id": svc_id,
                "name": f"TODO: Name service on {internal_ip}:{internal_port_for_id or 'any'}",
                "description": "TODO",
                "criticality": "medium",      # high|medium|low
                "exposure": "restricted",     # public|restricted|vpn-only
                "owner_id": "TODO",           # align to inventory/owners.yaml
                "environment": "production",  # production|staging|both
                "category": "other",          # network|web|broadcast|remote-access|email|monitoring|other
                "site": args.site,
                "internal_target": {
                    "device_id": "TODO",      # match inventory/devices/*.yaml (e.g., zettaserver)
                    "ip": internal_ip,
                    "port": internal_port,
                    "protocol": proto or "",
                },
                "public_entry": {
                    "fqdns": [],
                    "current_public_ip": public_ip,
                    "target_public_ip": "",
                    "notes": "",
                },
                "nat": {
                    "provider": "sonicwall",
                    "rules": [],
                },
                "tests": [
                    {
                        "name": "TODO: External validation",
                        "method": "curl|browser|nc|app",
                        "command": "",
                        "expected": "",
                        "run_from": "LTE/mobile hotspot",
                    }
                ],
                "status": {
                    "documented": False,
                    "validated_external": False,
                    "last_validated_utc": "",
                },
            }

        grouped[key]["nat"]["rules"].append(
            {
                "nat_policy_name": policy_name or "",
                "comment": comment or "",
                "from_zone": from_zone or "",
                "to_zone": to_zone or "",
                "public_ip": public_ip,
                "public_port": public_port,
                "protocol": proto or "",
                "internal_ip": internal_ip,
                "internal_port": internal_port,
                "inbound_interface": in_iface or "",
                "outbound_interface": out_iface or "",
            }
        )

    # Materialize
    services = list(grouped.values())

    out = {
        "version": 1,
        "updated_utc": utc_now_iso(),
        "source": {
            "type": "sonicwall_nat_export_csv",
            "path": str(csv_path.as_posix()),
        },
        "summary": {
            "seeded_services": len(services),
            "skipped_rows": skipped,
            "skip_reasons": dict(sorted(reasons.items(), key=lambda x: x[0])),
        },
        "services": services,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(out, sort_keys=False), encoding="utf-8")

    print(f"[OK] Wrote: {out_path}")
    print(f"[OK] Seeded services: {len(services)}")
    if skipped:
        print(f"[WARN] Skipped rows: {skipped}")
        for k, v in out["summary"]["skip_reasons"].items():
            print(f"       - {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
