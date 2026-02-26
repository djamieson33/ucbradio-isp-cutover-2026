from __future__ import annotations

from loader import InventoryContext
from reporter import Reporter
from rules.base import Rule


class DeviceKeyMatchesFilenameRule(Rule):
    name = "device-key-filename"

    def run(self, ctx: InventoryContext, reporter: Reporter) -> None:
        for item in ctx.device_files:
            path = item.path
            data = item.data
            if not isinstance(data, dict):
                continue
            device = data.get("device")
            if not isinstance(device, dict):
                continue

            dk = device.get("device_key")
            if not isinstance(dk, str) or not dk.strip():
                continue

            stem = path.stem
            if dk.strip() != stem:
                reporter.error(
                    self.name,
                    path,
                    "device.device_key must match filename stem.",
                    pointer=f"expected {stem}, got {dk.strip()}",
                )
