#!/usr/bin/env python3
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/compile.py
Purpose: Merge per-firewall inbound service seed files into a single repo-wide seed.

Inputs:
  inventory/seed/inbound-services/*.seed.yaml

Output:
  inventory/03-inbound-services.seed.yaml

Rules:
- Each per-firewall seed MUST include source.firewall_device_key
- Services are de-duped by stable key:
    (internal_target.ip, internal_target.target_object, protocol, port, port_range)
- Each merged service keeps provenance:
    service.source_firewall_device_key
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:
    print("[ERROR] PyYAML not installed. Activate .venv and install pyyaml.", file=sys.stderr)
    raise

# Allow running from repo root
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from common import utc_now_iso


DEFAULT_SEED_DIR = Path("inventory/seed/inbound-services")
DEFAULT_OUT = Path("inventory/03-inbound-services.seed.yaml")


def _svc_key(svc: dict[str, Any]) -> tuple[str, str, str, str, str]:
    it = svc.get("internal_target") or {}
    ip = str(it.get("ip") or "").strip()
    obj = str(it.get("target_object") or "").strip()
    proto = str(it.get("protocol") or "").strip().lower()
    port = "" if it.get("port") is None else str(it.get("port"))
    pr = str(it.get("port_range") or "").strip()
    return (ip, obj, proto, port, pr)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"Seed YAML is not a mapping: {path}")
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-dir", default=str(DEFAULT_SEED_DIR), help="Folder containing *.seed.yaml files")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Merged output YAML path")
    args = ap.parse_args()

    seed_dir = Path(args.seed_dir).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    if not seed_dir.exists():
        print(f"[ERROR] seed dir not found: {seed_dir}", file=sys.stderr)
        return 2

    seed_files = sorted(seed_dir.glob("*.seed.yaml"))
    if not seed_files:
        print(f"[ERROR] no seed files found in: {seed_dir}", file=sys.stderr)
        return 2

    merged: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    source_files: list[str] = []

    totals = {
        "seed_files": 0,
        "services_in": 0,
        "services_out": 0,
        "deduped": 0,
    }

    for sf in seed_files:
        data = _load_yaml(sf)
        src = data.get("source") or {}
        fw_key = str(src.get("firewall_device_key") or "").strip()
        site = str(src.get("site") or "").strip()

        if not fw_key:
            print(f"[ERROR] missing source.firewall_device_key in {sf}", file=sys.stderr)
            return 2

        services = data.get("services") or []
        if not isinstance(services, list):
            print(f"[ERROR] services is not a list in {sf}", file=sys.stderr)
            return 2

        totals["seed_files"] += 1
        totals["services_in"] += len(services)
        source_files.append(str(sf.as_posix()))

        for svc in services:
            if not isinstance(svc, dict):
                continue

            # stamp provenance onto the service record (doesn't change per-firewall file)
            svc2 = dict(svc)
            svc2["source_firewall_device_key"] = fw_key
            if site and "site" not in svc2:
                svc2["site"] = site

            k = _svc_key(svc2)
            if k in merged:
                totals["deduped"] += 1
                # merge NAT rule lists if present
                try:
                    a_rules = merged[k].get("nat", {}).get("rules", []) or []
                    b_rules = svc2.get("nat", {}).get("rules", []) or []
                    if isinstance(a_rules, list) and isinstance(b_rules, list):
                        merged[k].setdefault("nat", {}).setdefault("rules", [])
                        merged[k]["nat"]["rules"] = a_rules + b_rules
                except Exception:
                    pass
                continue

            merged[k] = svc2

    merged_services = list(merged.values())
    totals["services_out"] = len(merged_services)

    out = {
        "version": 1,
        "updated_utc": utc_now_iso(),
        "source": {
            "type": "compiled_from_per_firewall_seeds",
            "seed_dir": str(seed_dir.as_posix()),
            "seed_files": source_files,
        },
        "summary": totals,
        "services": merged_services,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_text = yaml.safe_dump(
        out,
        sort_keys=False,
        default_flow_style=False,
        width=120,
        indent=2,
    )
    out_path.write_text(yaml_text, encoding="utf-8")

    print(f"[OK] Wrote: {out_path}")
    print(f"[OK] Seed files: {totals['seed_files']}")
    print(f"[OK] Services in: {totals['services_in']}")
    print(f"[OK] Services out: {totals['services_out']} (deduped {totals['deduped']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
