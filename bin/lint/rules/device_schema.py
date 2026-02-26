from __future__ import annotations

from loader import InventoryContext
from reporter import Reporter
from rules.base import Rule
from utils import get_nested


class DeviceSchemaRule(Rule):
    name = "device-schema"

    def run(self, ctx: InventoryContext, reporter: Reporter) -> None:
        for item in ctx.device_files:
            path = item.path
            data = item.data

            if isinstance(data, dict) and "__lint_error__" in data:
                reporter.error(self.name, path, data["__lint_error__"])
                continue

            if not isinstance(data, dict):
                reporter.error(self.name, path, "YAML root must be a mapping (dict).")
                continue

            device = data.get("device")
            site = data.get("site")

            if not isinstance(device, dict):
                reporter.error(self.name, path, "Missing required mapping: device")
                continue
            if not isinstance(site, dict):
                reporter.error(self.name, path, "Missing required mapping: site")
                continue

            asset_id = device.get("asset_id")
            if not isinstance(asset_id, int):
                reporter.error(self.name, path, "device.asset_id must be an integer.")
            category = device.get("category")
            if category not in {"firewall", "network", "broadcast", "server"}:
                reporter.error(self.name, path, "device.category must be one of: firewall|network|broadcast|server")

            vendor = device.get("vendor")
            if not isinstance(vendor, str) or not vendor.strip():
                reporter.error(self.name, path, "device.vendor must be a non-empty string (lowercase).")

            role = device.get("role")
            if not isinstance(role, str) or not role.strip():
                reporter.warn(self.name, path, "device.role should be a non-empty string.")

            device_key = device.get("device_key")
            if not isinstance(device_key, str) or not device_key.strip():
                reporter.error(self.name, path, "device.device_key must be a non-empty string.")

            # Site required fields
            for k in ("code", "name", "province"):
                v = site.get(k)
                if not isinstance(v, str) or not v.strip():
                    reporter.error(self.name, path, f"site.{k} must be a non-empty string.")
