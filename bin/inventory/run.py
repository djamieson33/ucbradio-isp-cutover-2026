#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _bootstrap_repo_root() -> None:
    """
    Allow running as:
      - python3 bin/inventory/run.py <cmd>
    while still supporting package imports from repo root:
      - python3 -m bin.inventory.run <cmd>

    This inserts the repo root into sys.path when executed as a script.
    """
    # .../repo/bin/inventory/run.py -> repo root is two parents up from this file
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


_bootstrap_repo_root()

# Now imports work whether invoked via `python3 bin/inventory/run.py` or `python3 -m ...`
from bin.inventory.inventory_create.add_device import cmd_add_device  # noqa: E402
from bin.inventory.inventory_update.sync_site_dossiers import cmd_sync_site_dossiers  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bin/inventory/run.py",
        description="Inventory CLI (create/read/update/delete) for device + site records.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add-device", help="Create or update a device YAML interactively.")
    p_add.add_argument("filename", help="Device filename (e.g. 84-tx-nautel-vs300-broc-100.yaml)")
    p_add.add_argument("--overwrite", action="store_true", help="Overwrite if file exists (dangerous).")
    p_add.add_argument("--no-sync", action="store_true", help="Do not run sync-site-dossiers after write.")
    p_add.add_argument("--site-dns-zone", default=os.environ.get("UCB_SITE_DNS_ZONE", "ucbradio.local"),
                       help="Default internal DNS zone (default: ucbradio.local; env: UCB_SITE_DNS_ZONE)")
    p_add.set_defaults(func=cmd_add_device)

    p_sync = sub.add_parser("sync-site-dossiers", help="Rebuild/update inventory/sites/<site-id>.yaml dossiers.")
    p_sync.add_argument("--sites-file", default="inventory/sites.yaml", help="Canonical sites registry YAML.")
    p_sync.add_argument("--devices-root", default="inventory/devices", help="Devices root folder.")
    p_sync.add_argument("--sites-dir", default="inventory/sites", help="Output dossiers folder.")
    p_sync.set_defaults(func=cmd_sync_site_dossiers)

    return p


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
