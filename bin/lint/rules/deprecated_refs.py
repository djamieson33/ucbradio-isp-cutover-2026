from __future__ import annotations

from loader import InventoryContext
from reporter import Reporter
from rules.base import Rule


class DeprecatedRefsRule(Rule):
    name = "deprecated-refs"

    def run(self, ctx: InventoryContext, reporter: Reporter) -> None:
        # Ensure nothing references inventory/deprecated/
        needle = "inventory/deprecated/"
        for item in ctx.yaml_files:
            path = item.path
            try:
                txt = path.read_text(encoding="utf-8")
            except Exception as e:
                reporter.warn(self.name, path, f"Could not read file as text: {e!r}")
                continue

            if needle in txt:
                reporter.error(
                    self.name,
                    path,
                    "File references inventory/deprecated/. Deprecated inventory must not be referenced by active logic.",
                )
