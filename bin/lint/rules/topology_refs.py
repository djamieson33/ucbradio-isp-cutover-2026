from __future__ import annotations

from pathlib import Path
from typing import Any

from loader import InventoryContext
from reporter import Reporter
from rules.base import Rule
from utils import flatten_dict


class TopologyRefsRule(Rule):
    name = "topology-refs"

    def _check_device_key_exists(self, ctx: InventoryContext, reporter: Reporter, file_path: Path, kpath: str, value: Any) -> None:
        if not isinstance(value, str):
            return
        v = value.strip()
        if not v:
            return
        # Only validate likely device key fields
        if not (kpath.endswith("device_key") or kpath.endswith("hub_device_key") or kpath.endswith("spoke_device_key")):
            return

        if v not in ctx.device_key_index:
            reporter.error(
                self.name,
                file_path,
                "Topology references unknown device_key (no matching device file found).",
                pointer=f"{kpath}={v}",
            )

    def _forbid_device_file_paths(self, reporter: Reporter, file_path: Path, kpath: str, value: Any) -> None:
        if not isinstance(value, str):
            return
        if "inventory/devices/" in value and kpath.endswith("device_file"):
            reporter.error(
                self.name,
                file_path,
                "Do not reference device_file paths in topology; reference by device_key instead.",
                pointer=f"{kpath}={value}",
            )

    def run(self, ctx: InventoryContext, reporter: Reporter) -> None:
        # Validate inventory/ipsec-topology.yaml and inventory/ipsec-tunnels.yaml if present
        targets = [self.cfg.ipsec_topology_file, self.cfg.ipsec_tunnels_file]
        for target in targets:
            if not target.exists():
                # Not an error; some repos may be mid-build
                reporter.warn(self.name, target, "Expected file not found (skipping).")
                continue

            data = ctx.raw_by_path.get(target)
            if isinstance(data, dict) and "__lint_error__" in data:
                reporter.error(self.name, target, data["__lint_error__"])
                continue

            for kpath, value in flatten_dict(data):
                self._check_device_key_exists(ctx, reporter, target, kpath, value)
                self._forbid_device_file_paths(reporter, target, kpath, value)
