#!/usr/bin/env python3
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/writer.py
Purpose: Write inventory/03-inbound-services.seed.yaml in canonical shape.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

import yaml

from common import utc_now_iso


def write_seed_yaml(
    out_path: Path,
    nat_csv: Path,
    policy_csv: Path,
    services: List[Dict[str, Any]],
    nat_stats: Dict[str, Any],
    policy_stats: Dict[str, Any],
) -> None:
    out = {
        "version": 1,
        "updated_utc": utc_now_iso(),
        "source": {
            "type": "sonicwall_nat_and_security_policy_exports",
            "nat_csv": str(nat_csv.as_posix()),
            "security_policy_csv": str(policy_csv.as_posix()),
        },
        "summary": {
            "policy": policy_stats,
            **nat_stats,
        },
        "services": services,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(out, sort_keys=False), encoding="utf-8")
