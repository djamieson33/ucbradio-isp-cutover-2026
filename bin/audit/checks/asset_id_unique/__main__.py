#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys
from collections import defaultdict

EXIT_OK = 0
EXIT_ISSUES = 1

ROOT = Path(__file__).resolve().parents[4]
DEVICES = ROOT / "inventory" / "devices"

ASSET_RE = re.compile(r"^(?P<asset>\d+)-.+\.ya?ml$", re.IGNORECASE)

def info(msg: str) -> None:
    print(f"[INFO] {msg}")

def warn(msg: str) -> None:
    print(f"[WARN] {msg}")

def main() -> int:
    if not DEVICES.exists():
        warn(f"devices folder not found: {DEVICES}")
        return EXIT_ISSUES

    by_asset: dict[str, list[str]] = defaultdict(list)
    scanned = 0
    skipped = 0

    for p in sorted(DEVICES.rglob("*.yaml")):
        scanned += 1
        name = p.name
        m = ASSET_RE.match(name)
        if not m:
            skipped += 1
            continue
        asset = m.group("asset")
        by_asset[asset].append(str(p.relative_to(ROOT)))

    dups = {k: v for k, v in by_asset.items() if len(v) > 1}

    info(f"device files scanned: {scanned}")
    info(f"skipped (non-matching filenames): {skipped}")
    info(f"unique asset ids: {len(by_asset)}")

    if not dups:
        print("------------------------------------------------------------")
        print("[SUMMARY] No duplicate asset ids found.")
        print("------------------------------------------------------------")
        return EXIT_OK

    warn(f"duplicate asset ids found: {len(dups)}")
    for asset in sorted(dups.keys(), key=lambda x: int(x)):
        print(f"  - asset {asset}:")
        for f in dups[asset]:
            print(f"      - {f}")

    print("------------------------------------------------------------")
    print(f"[SUMMARY] Duplicate asset ids: {len(dups)}")
    print("------------------------------------------------------------")
    return EXIT_ISSUES

if __name__ == "__main__":
    raise SystemExit(main())
