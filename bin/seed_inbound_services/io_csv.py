# bin/seed_inbound_services/io_csv.py
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/io_csv.py
Purpose: CSV IO helpers (normalized headers/rows, newest file selection).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Tuple, List, Dict

from common import norm_key, norm_val


def newest_matching(directory: Path, pattern: str) -> Path | None:
    """
    Return newest file matching glob pattern.
    Deterministic: sort by (mtime, filename).
    """
    files = list(directory.glob(pattern))
    if not files:
        return None

    return max(files, key=lambda p: (p.stat().st_mtime, p.name))


def read_csv_normalized(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Returns:
        (normalized_headers, normalized_rows)

    - Headers are normalized via norm_key()
    - Values are trimmed via norm_val()
    - Duplicate header row (sometimes present in SonicWall exports) is skipped
    """
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise RuntimeError(f"CSV has no header row: {path}")

        orig_headers = list(reader.fieldnames)
        headers = [norm_key(h) for h in orig_headers]

        rows: List[Dict[str, str]] = []

        for raw in reader:
            r: Dict[str, str] = {}
            for oh, nh in zip(orig_headers, headers):
                r[nh] = norm_val(raw.get(oh, ""))

            # Skip duplicated header rows
            if headers and is_duplicate_header_row(r, headers[0]):
                continue

            rows.append(r)

        return headers, rows


def is_duplicate_header_row(row: dict, header_first_key: str) -> bool:
    """
    SonicWall exports sometimes duplicate the header row as the first data row.
    Detect by: if the value of the first column resembles the header label.
    """
    v = (row.get(header_first_key) or "").strip().lower()

    normalized_label = header_first_key.lower()
    normalized_spaced = header_first_key.replace("_", " ").lower()

    return v in {normalized_label, normalized_spaced}
