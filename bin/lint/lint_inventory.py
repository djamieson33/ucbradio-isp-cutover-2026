#!/usr/bin/env python3
"""
UCB ISP Changeover — Inventory Linter

Run from repo root:
  python3 bin/lint/lint_inventory.py
  python3 bin/lint/lint_inventory.py --format json
  python3 bin/lint/lint_inventory.py --strict

Exit codes:
  0 = no issues (or warnings only, if not strict)
  2 = errors found (or warnings found in --strict mode)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure local imports work when executing this file directly.
# (Without this, Python can't resolve "bin.*" style imports.)
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import LintConfig
from loader import InventoryLoader
from reporter import Reporter
from rules import (
    DeprecatedRefsRule,
    DeviceKeyMatchesFilenameRule,
    DeviceSchemaRule,
    ForbiddenSecretsRule,
    TopologyRefsRule,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lint inventory YAML files for structure and consistency.")
    p.add_argument("--root", default=".", help="Repo root (default: .)")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (non-zero exit if any warnings).",
    )
    p.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Alias for --strict (kept for ergonomics).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.root).resolve()

    cfg = LintConfig(
        repo_root=repo_root,
        strict=bool(args.strict or args.fail_on_warn),
        output_format=args.format,
    )

    loader = InventoryLoader(cfg)
    reporter = Reporter(cfg)

    rules = [
        DeviceSchemaRule(cfg),
        DeviceKeyMatchesFilenameRule(cfg),
        ForbiddenSecretsRule(cfg),
        DeprecatedRefsRule(cfg),
        TopologyRefsRule(cfg),
    ]

    context = loader.load()

    for rule in rules:
        rule.run(context, reporter)

    return reporter.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
