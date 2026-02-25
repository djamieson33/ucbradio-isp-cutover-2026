#!/usr/bin/env python3
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/run.py
Purpose: Orchestrate generation of inventory/03-inbound-services.seed.yaml from
         the most recent SonicWall NAT + Security Policy CSV exports.

Inputs (firewall/sonicwall/exports/):
  - nat-configurations-YYYYMMDDThhmmZ.csv
  - security-policy-YYYYMMDDThhmmZ.csv

Optional:
  - inventory/sonicwall-object-overrides.yaml

Output:
  - inventory/03-inbound-services.seed.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
except Exception:
    print("[ERROR] PyYAML not installed. Activate .venv and install pyyaml.", file=sys.stderr)
    raise

# Ensure local imports work regardless of where script is invoked from
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from io_csv import newest_matching
from policy_parser import build_allow_rules
from nat_parser import build_services_from_nat
from writer import write_seed_yaml


EXPORTS_DIR = Path("firewall/sonicwall/exports")
DEFAULT_OUT = Path("inventory/03-inbound-services.seed.yaml")
DEFAULT_OVERRIDES = Path("inventory/sonicwall-object-overrides.yaml")


def load_overrides(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            return None
        return data
    except Exception as e:
        print(f"[ERROR] Failed to parse overrides YAML: {path} ({e})", file=sys.stderr)
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nat", help="Path to nat-configurations CSV (optional; newest nat-configurations-*.csv is used)")
    ap.add_argument("--policy", help="Path to security-policy CSV (optional; newest security-policy-*.csv is used)")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Output YAML path")
    ap.add_argument("--site", default="belleville", help="Site slug")
    ap.add_argument("--default-inbound-iface", default="X1", help="Default inbound interface if NAT CSV lacks it")
    ap.add_argument("--overrides", default=str(DEFAULT_OVERRIDES), help="Overrides YAML path (optional)")
    args = ap.parse_args()

    if not EXPORTS_DIR.exists():
        print("[ERROR] exports directory not found: firewall/sonicwall/exports", file=sys.stderr)
        return 2

    nat_csv = Path(args.nat) if args.nat else newest_matching(EXPORTS_DIR, "nat-configurations-*.csv")
    if not nat_csv or not nat_csv.exists():
        print("[ERROR] No nat-configurations-*.csv found in firewall/sonicwall/exports", file=sys.stderr)
        return 2

    policy_csv = Path(args.policy) if args.policy else newest_matching(EXPORTS_DIR, "security-policy-*.csv")
    if not policy_csv or not policy_csv.exists():
        print("[ERROR] No security-policy-*.csv found in firewall/sonicwall/exports", file=sys.stderr)
        return 2

    out_path = Path(args.out)

    overrides_path = Path(args.overrides) if args.overrides else DEFAULT_OVERRIDES
    overrides = load_overrides(overrides_path)

    if overrides:
        print(f"[INFO] Using overrides: {overrides_path}")

    print(f"[INFO] Using NAT CSV: {nat_csv}")
    print(f"[INFO] Using Security Policy CSV: {policy_csv}")

    allow_rules, policy_stats = build_allow_rules(policy_csv)

    services, nat_stats = build_services_from_nat(
        nat_csv=nat_csv,
        allow_rules=allow_rules,
        site=args.site,
        default_inbound_iface=args.default_inbound_iface,
        overrides=overrides,  # ✅ THIS is the critical missing piece
    )

    write_seed_yaml(
        out_path=out_path,
        nat_csv=nat_csv,
        policy_csv=policy_csv,
        services=services,
        nat_stats=nat_stats,
        policy_stats=policy_stats,
    )

    print(f"[OK] Wrote: {out_path}")
    print(f"[OK] Seeded services: {nat_stats['seeded_services']}")
    print(f"[INFO] Policy allow rules: {policy_stats['allow_rules']} (from {policy_stats['rows_total']} rows)")

    if nat_stats["skipped_rows"]:
        print(f"[WARN] Skipped rows: {nat_stats['skipped_rows']}")
        for k, v in nat_stats["skip_reasons"].items():
            print(f"       - {k}: {v}")

    if nat_stats["unresolved_target_objects_count"]:
        print(f"[WARN] Unresolved target objects: {nat_stats['unresolved_target_objects_count']}")
    if nat_stats["unresolved_service_objects_count"]:
        print(f"[WARN] Unresolved service objects: {nat_stats['unresolved_service_objects_count']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
