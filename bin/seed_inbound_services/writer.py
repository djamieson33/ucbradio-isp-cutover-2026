#!/usr/bin/env python3
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/writer.py
Purpose: Write per-firewall inbound-services seed YAML in canonical shape.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from common import utc_now_iso


def write_seed_yaml(
    out_path: Path,
    nat_csv: Path,
    policy_csv: Path,
    services: list[dict[str, Any]],
    nat_stats: dict[str, Any],
    policy_stats: dict[str, Any],
    *,
    firewall_device_key: str | None = None,
    site: str | None = None,
    exports_dir: Path | None = None,
) -> None:
    """
    Writes a per-firewall seed YAML file.

    The output is firewall-scoped and includes metadata identifying
    the source firewall and export location.
    """

    source_block: dict[str, Any] = {
        "type": "sonicwall_nat_and_security_policy_exports",
        "nat_csv": str(nat_csv.as_posix()),
        "security_policy_csv": str(policy_csv.as_posix()),
    }

    if firewall_device_key:
        source_block["firewall_device_key"] = firewall_device_key

    if site:
        source_block["site"] = site

    if exports_dir:
        source_block["exports_dir"] = str(exports_dir.as_posix())

    out = {
        "version": 1,
        "updated_utc": utc_now_iso(),
        "source": source_block,
        "summary": {
            "policy": policy_stats,
            **nat_stats,
        },
        "services": services,
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
    