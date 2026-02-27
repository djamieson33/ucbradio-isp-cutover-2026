#!/usr/bin/env python3
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/run.py
Purpose: Orchestrate generation of inbound-services seed YAML from
         the most recent SonicWall NAT + Security Policy CSV exports.

Inputs (firewall/sonicwall/exports/**):
  - nat-configurations-YYYYMMDDThhmmZ.csv
  - security-policy-YYYYMMDDThhmmZ.csv

Optional:
  - inventory/sonicwall-object-overrides.yaml

Outputs:
  - If --firewall-device-key is set (recommended):
      inventory/seed/inbound-services/<firewall-device-key>.seed.yaml
  - Else:
      inventory/03-inbound-services.seed.yaml
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

from common import DEFAULT_OUT, DEFAULT_OVERRIDES, EXPORTS_BASE_DIR, SEED_OUT_DIR
from io_csv import newest_matching, read_csv_normalized
from nat_parser import build_services_from_nat
from policy_parser import build_allow_rules
from writer import write_seed_yaml

from overrides_apply import apply_unresolved_address_objects, ensure_scope_block


def load_overrides(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else None
    except Exception as e:
        print(f"[ERROR] Failed to parse overrides YAML: {path} ({e})", file=sys.stderr)
        return None


def _print_unresolved(nat_stats: dict, limit: int) -> None:
    ut = nat_stats.get("unresolved_target_objects") or []
    us = nat_stats.get("unresolved_service_objects") or []

    if ut:
        print(f"[WARN] Unresolved target objects list ({len(ut)}):")
        for x in ut[: max(0, limit)]:
            print(f"       - {x}")
        if len(ut) > limit:
            print(f"       … ({len(ut) - limit} more; re-run with --unresolved-limit {len(ut)})")

    if us:
        print(f"[WARN] Unresolved service objects list ({len(us)}):")
        for x in us[: max(0, limit)]:
            print(f"       - {x}")
        if len(us) > limit:
            print(f"       … ({len(us) - limit} more; re-run with --unresolved-limit {len(us)})")


def _yaml_quote(s: str) -> str:
    return '"' + (s or "").replace('"', '\\"') + '"'


def _print_unresolved_overrides_skeleton(nat_stats: dict, firewall_device_key: str) -> None:
    ut = nat_stats.get("unresolved_target_objects") or []
    if not ut:
        return

    print("\n============================================================")
    print("Paste the following into inventory/sonicwall-object-overrides.yaml")
    print("============================================================\n")

    if firewall_device_key:
        fw_q = _yaml_quote(firewall_device_key)
        print("scoped:")
        print(f"  {fw_q}:")
        print("    address_objects:")
        for obj in ut:
            obj_q = _yaml_quote(obj)
            print(f"      {obj_q}:")
            print('        ip: ""')
            print('        device_id: ""')
    else:
        print("address_objects:")
        for obj in ut:
            obj_q = _yaml_quote(obj)
            print(f"  {obj_q}:")
            print('    ip: ""')
            print('    device_id: ""')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nat", help="Path to nat-configurations CSV (optional; newest nat-configurations-*.csv is used)")
    ap.add_argument("--policy", help="Path to security-policy CSV (optional; newest security-policy-*.csv is used)")

    ap.add_argument(
        "--out",
        default="",
        help="Output YAML path (default: per-firewall seed if --firewall-device-key is set; else inventory/03-inbound-services.seed.yaml)",
    )

    ap.add_argument("--site", default="belleville", help="Site slug")
    ap.add_argument("--default-inbound-iface", default="X1", help="Default inbound interface if NAT CSV lacks it")
    ap.add_argument("--overrides", default=str(DEFAULT_OVERRIDES), help="Overrides YAML path (optional)")
    ap.add_argument(
        "--exports-dir",
        default=str(EXPORTS_BASE_DIR),
        help="Exports directory (default: firewall/sonicwall/exports under repo root)",
    )

    ap.add_argument(
        "--show-unresolved",
        action="store_true",
        default=True,
        help="Print unresolved target/service object names (default: enabled)",
    )
    ap.add_argument(
        "--no-show-unresolved",
        action="store_false",
        dest="show_unresolved",
        help="Disable printing unresolved lists",
    )
    ap.add_argument(
        "--unresolved-limit",
        type=int,
        default=50,
        help="Max unresolved items to print per list (default: 50)",
    )
    ap.add_argument(
        "--print-unresolved-overrides",
        action="store_true",
        default=False,
        help="Print a ready-to-paste SCOPED address_objects skeleton for unresolved targets (recommended)",
    )

    ap.add_argument(
        "--firewall-device-key",
        default="",
        help="Firewall device_key (enables per-firewall seed output default + scoped overrides)",
    )

    # NEW: write to overrides file automatically (scoped-only; no globals)
    ap.add_argument(
        "--apply-unresolved-overrides",
        action="store_true",
        default=False,
        help="Write unresolved target objects into overrides file under scoped.<firewall_device_key> (no overwrite)",
    )
    ap.add_argument(
        "--apply-unresolved-dry-run",
        action="store_true",
        default=False,
        help="Dry-run for --apply-unresolved-overrides (shows what would change, does not write)",
    )
    ap.add_argument(
        "--ensure-scope",
        action="store_true",
        default=False,
        help="Ensure scoped.<firewall_device_key> exists in overrides file even if there are no unresolveds",
    )

    args = ap.parse_args()

    exports_dir = Path(args.exports_dir).expanduser().resolve()
    if not exports_dir.exists():
        print(f"[ERROR] exports directory not found: {exports_dir}", file=sys.stderr)
        return 2

    nat_csv = Path(args.nat).expanduser().resolve() if args.nat else newest_matching(exports_dir, "nat-configurations-*.csv")
    if not nat_csv or not nat_csv.exists():
        print(f"[ERROR] No nat-configurations-*.csv found in {exports_dir}", file=sys.stderr)
        return 2

    policy_csv = Path(args.policy).expanduser().resolve() if args.policy else newest_matching(exports_dir, "security-policy-*.csv")
    if not policy_csv or not policy_csv.exists():
        print(f"[ERROR] No security-policy-*.csv found in {exports_dir}", file=sys.stderr)
        return 2

    overrides_path = Path(args.overrides).expanduser().resolve() if args.overrides else Path(DEFAULT_OVERRIDES)
    overrides = load_overrides(overrides_path)

    if overrides:
        print(f"[INFO] Using overrides: {overrides_path}")

    print(f"[INFO] Using exports dir: {exports_dir}")
    print(f"[INFO] Using NAT CSV: {nat_csv}")
    print(f"[INFO] Using Security Policy CSV: {policy_csv}")

    # Output path selection
    if args.out:
        out_path = Path(args.out).expanduser().resolve()
    elif args.firewall_device_key:
        SEED_OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = (SEED_OUT_DIR / f"{args.firewall_device_key}.seed.yaml").resolve()
    else:
        out_path = Path(DEFAULT_OUT).expanduser().resolve()

    if args.firewall_device_key:
        print(f"[INFO] Firewall device key: {args.firewall_device_key}")
        if not args.out:
            print(f"[INFO] Seed output (per-firewall): {out_path}")

    # Optional: ensure scope exists up-front (even before parsing)
    if args.ensure_scope:
        if not args.firewall_device_key:
            print("[ERROR] --ensure-scope requires --firewall-device-key", file=sys.stderr)
            return 2
        doc, changed = ensure_scope_block(overrides_path, args.firewall_device_key)
        if changed:
            if args.apply_unresolved_dry_run:
                print(f"[INFO] Would ensure overrides scope exists: scoped.{args.firewall_device_key}")
            else:
                # write happens inside apply helper for unresolved; here we must write explicitly
                # reuse apply_unresolved with empty list to persist the scope
                apply_unresolved_address_objects(
                    overrides_path,
                    args.firewall_device_key,
                    [],
                    dry_run=False,
                )
                print(f"[INFO] Ensured overrides scope exists: scoped.{args.firewall_device_key}")

        # reload overrides after potential write
        overrides = load_overrides(overrides_path)

    # Build allow rules (default restrict_src_zones=("wan",))
    allow_rules, policy_stats = build_allow_rules(policy_csv)

    # Debug visibility: show which Source Zones exist in this export
    try:
        _h, _rows = read_csv_normalized(policy_csv)
        zones = sorted({(r.get("source_zone") or "").strip() for r in _rows if (r.get("source_zone") or "").strip()})
        if zones:
            print(f"[INFO] Policy source zones observed: {zones}")
    except Exception:
        pass

    services, nat_stats = build_services_from_nat(
        nat_csv=nat_csv,
        allow_rules=allow_rules,
        site=args.site,
        default_inbound_iface=args.default_inbound_iface,
        overrides=overrides,
        firewall_device_key=args.firewall_device_key,
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
    print(f"[OK] Seeded services: {nat_stats.get('seeded_services', 0)}")
    print(f"[INFO] Policy allow rules: {policy_stats.get('allow_rules', 0)} (from {policy_stats.get('rows_total', 0)} rows)")

    if nat_stats.get("skipped_rows", 0):
        print(f"[WARN] Skipped rows: {nat_stats['skipped_rows']}")
        for k, v in (nat_stats.get("skip_reasons") or {}).items():
            print(f"       - {k}: {v}")

    if nat_stats.get("unresolved_target_objects_count", 0):
        print(f"[WARN] Unresolved target objects: {nat_stats['unresolved_target_objects_count']}")
    if nat_stats.get("unresolved_service_objects_count", 0):
        print(f"[WARN] Unresolved service objects: {nat_stats['unresolved_service_objects_count']}")

    if args.show_unresolved:
        _print_unresolved(nat_stats, limit=args.unresolved_limit)

    if args.print_unresolved_overrides:
        _print_unresolved_overrides_skeleton(nat_stats, firewall_device_key=args.firewall_device_key)

    # NEW: auto-apply unresolved target objects into overrides (scoped only)
    if args.apply_unresolved_overrides:
        if not args.firewall_device_key:
            print("[ERROR] --apply-unresolved-overrides requires --firewall-device-key", file=sys.stderr)
            return 2

        ut = nat_stats.get("unresolved_target_objects") or []
        changed = apply_unresolved_address_objects(
            overrides_path,
            args.firewall_device_key,
            ut,
            dry_run=args.apply_unresolved_dry_run,
        )

        if args.apply_unresolved_dry_run:
            if changed:
                print(f"[INFO] Would update overrides file (scoped.{args.firewall_device_key}.address_objects) for {len(ut)} unresolved targets.")
            else:
                print("[INFO] No overrides changes needed (dry-run).")
        else:
            if changed:
                print(f"[OK] Updated overrides file: {overrides_path}")
            else:
                print("[INFO] No overrides changes needed.")

    # Helpful context for "seeded 0"
    if nat_stats.get("seeded_services", 0) == 0:
        sr = nat_stats.get("skip_reasons") or {}
        only_reason = (len(sr) == 1 and "translated_destination_is_original_or_empty" in sr)
        if only_reason:
            print("[INFO] No inbound-ish NAT policies found (Destination Translated was 'Original' for all candidate rows).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
