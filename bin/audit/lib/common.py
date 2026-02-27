from __future__ import annotations

import os
import sys
from typing import Any, Dict, Tuple
import yaml


EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_ERROR = 2


def die(msg: str, code: int = EXIT_ERROR) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_yaml(path: str) -> Any:
    if not os.path.exists(path):
        die(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_sites_structure(sites_doc: Any) -> Tuple[Dict[str, Dict[str, Any]], str]:
    """
    Key priority for sites:
      - id  (canonical lowercase bell-102)
      - site_code
      - slug
    """

    def _get_key(item: Dict[str, Any]) -> str | None:
        for k in ("id", "site_code", "slug", "site_slug", "code"):
            v = item.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None

    if isinstance(sites_doc, dict):
        if "sites" in sites_doc:
            sites = sites_doc["sites"]
            if isinstance(sites, dict):
                return {k: v for k, v in sites.items() if isinstance(v, dict)}, "sites.map"
            if isinstance(sites, list):
                out: Dict[str, Dict[str, Any]] = {}
                for item in sites:
                    if isinstance(item, dict):
                        key = _get_key(item)
                        if key:
                            out[key] = item
                return out, "sites.list"

        if all(isinstance(v, dict) for v in sites_doc.values()):
            return {k: v for k, v in sites_doc.items() if isinstance(v, dict)}, "top.map"

    if isinstance(sites_doc, list):
        out2: Dict[str, Dict[str, Any]] = {}
        for item in sites_doc:
            if isinstance(item, dict):
                key = _get_key(item)
                if key:
                    out2[key] = item
        return out2, "top.list"

    die(f"Unrecognized sites.yaml structure: {type(sites_doc).__name__}")
    return {}, "unknown"
