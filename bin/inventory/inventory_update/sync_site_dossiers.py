from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

EXIT_OK = 0
EXIT_ISSUES = 1

DEVICE_FILENAME_RE = re.compile(
    r"^(?P<asset>\d+)-(?P<token>[a-z0-9]+)-(?P<vendor>[a-z0-9]+)-(?P<model>[a-z0-9]+)-(?P<site>[a-z0-9]+-\d+)\.ya?ml$",
    re.IGNORECASE,
)


def _die(msg: str, code: int = 2) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def _info(msg: str) -> None:
    print(f"[INFO] {msg}")


def _warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        _die(f"Failed to parse YAML: {path}: {e}")


def _write_yaml(path: Path, doc: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)
    path.write_text(s, encoding="utf-8")


def _normalize_sites_structure(sites_doc: Any) -> Tuple[Dict[str, Dict[str, Any]], str]:
    """
    Supports canonical sites.yaml shape:
      { schema_version: 1, sites: [ {id:..., site_code:..., city:..., province:...}, ... ] }

    Returns:
      (sites_by_id, shape_label)
    """
    if isinstance(sites_doc, dict) and isinstance(sites_doc.get("sites"), list):
        out: Dict[str, Dict[str, Any]] = {}
        for item in sites_doc["sites"]:
            if isinstance(item, dict):
                sid = item.get("id")
                if isinstance(sid, str) and sid.strip():
                    out[sid.strip()] = item
        return out, "sites.list"

    _die(f"Unsupported sites.yaml structure: {type(sites_doc).__name__}")
    return {}, "unknown"


def _scan_devices(devices_root: Path) -> List[Path]:
    if not devices_root.exists():
        return []
    return sorted([p for p in devices_root.rglob("*.yml")] + [p for p in devices_root.rglob("*.yaml")])


def _device_site_id_from_filename(path: Path) -> str | None:
    m = DEVICE_FILENAME_RE.match(path.name)
    if not m:
        return None
    return m.group("site").lower().strip() or None


def _device_ref_name_from_filename(path: Path) -> str:
    # dossiers should list filenames WITHOUT extension (matches what you’ve been doing)
    # e.g. 84-tx-nautel-vs300-broc-100.yaml -> 84-tx-nautel-vs300-broc-100
    return path.stem


def sync_site_dossiers(*, sites_file: str, devices_root: str, sites_dir: str) -> int:
    sites_path = Path(sites_file)
    devices_path = Path(devices_root)
    dossiers_path = Path(sites_dir)

    sites_doc = _load_yaml(sites_path) or {}
    sites_by_id, shape = _normalize_sites_structure(sites_doc)

    _info(f"sites file: {sites_file}")
    _info(f"sites structure: {shape}")
    _info(f"sites indexed: {len(sites_by_id)}")

    device_files = _scan_devices(devices_path)
    _info(f"device files scanned: {len(device_files)}")

    # Build per-site device lists
    per_site: Dict[str, Dict[str, List[str]]] = {}
    for p in device_files:
        site_id = _device_site_id_from_filename(p)
        if not site_id:
            continue
        ref = _device_ref_name_from_filename(p)

        # Determine bucket by folder name under inventory/devices/<bucket>/
        # e.g. inventory/devices/broadcast/... -> "broadcast"
        try:
            bucket = p.relative_to(devices_path).parts[0]
        except Exception:
            bucket = "unknown"

        site_entry = per_site.setdefault(
            site_id,
            {"firewalls": [], "broadcast": [], "servers": [], "network": []},
        )

        # Normalize bucket names to your dossier keys
        if bucket in ("firewalls", "broadcast", "servers", "network"):
            site_entry[bucket].append(ref)
        else:
            # Unknown buckets are ignored for now, or could go into "network"
            site_entry["network"].append(ref)

    created = 0
    updated = 0

    for site_id, site_meta in sites_by_id.items():
        dossier_file = dossiers_path / f"{site_id}.yaml"

        devices_block = per_site.get(
            site_id,
            {"firewalls": [], "broadcast": [], "servers": [], "network": []},
        )

        # Construct the normalized dossier doc
        dossier_doc: Dict[str, Any] = {
            "schema_version": 1,
            "site": {
                "id": site_id,
                "site_code": site_meta.get("site_code", ""),
                "city": site_meta.get("city", ""),
                "province": site_meta.get("province", ""),
            },
            "devices": {
                "firewalls": sorted(devices_block.get("firewalls", [])),
                "broadcast": sorted(devices_block.get("broadcast", [])),
                "servers": sorted(devices_block.get("servers", [])),
                "network": sorted(devices_block.get("network", [])),
            },
            "critical_chain": [],
            "notes": "",
        }

        # If dossier already exists, preserve user-maintained fields:
        if dossier_file.exists():
            existing = _load_yaml(dossier_file) or {}
            if isinstance(existing, dict):
                # Preserve critical_chain and notes if present
                cc = existing.get("critical_chain")
                if isinstance(cc, list):
                    dossier_doc["critical_chain"] = cc
                notes = existing.get("notes")
                if isinstance(notes, str):
                    dossier_doc["notes"] = notes

            updated += 1
        else:
            created += 1

        _write_yaml(dossier_file, dossier_doc)

    _info(f"dossiers created: {created}")
    _info(f"dossiers updated: {updated}")
    return EXIT_OK


def cmd_sync_site_dossiers(args) -> int:
    """
    argparse handler for:
      python3 bin/inventory/run.py sync-site-dossiers
    """
    sites_file = getattr(args, "sites_file", "inventory/sites.yaml")
    devices_root = getattr(args, "devices_root", "inventory/devices")
    sites_dir = getattr(args, "sites_dir", "inventory/sites")
    return sync_site_dossiers(sites_file=sites_file, devices_root=devices_root, sites_dir=sites_dir)


if __name__ == "__main__":
    # Allow ad-hoc direct execution for testing
    class _Args:
        sites_file = "inventory/sites.yaml"
        devices_root = "inventory/devices"
        sites_dir = "inventory/sites"

    raise SystemExit(cmd_sync_site_dossiers(_Args()))
