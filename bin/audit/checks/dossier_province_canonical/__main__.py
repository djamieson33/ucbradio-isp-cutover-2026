from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from bin.audit.lib.common import EXIT_OK, EXIT_ISSUES, load_yaml, normalize_sites_structure


SITES_FILE = Path("inventory/sites.yaml")
DOSSIERS_DIR = Path("inventory/sites")


def _info(msg: str) -> None:
    print(f"[INFO] {msg}")


def _warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def _as_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        # prevent province: true from being treated as valid
        return ""
    return str(v).strip()


def _canonical_map() -> Dict[str, Dict[str, Any]]:
    doc = load_yaml(str(SITES_FILE)) or {}
    sites_by_id, _shape = normalize_sites_structure(doc)
    return sites_by_id


def _load_dossier(path: Path) -> Dict[str, Any]:
    doc = load_yaml(str(path)) or {}
    return doc if isinstance(doc, dict) else {}


def main() -> int:
    _info(f"sites file: {SITES_FILE}")
    _info(f"dossiers dir: {DOSSIERS_DIR}")

    sites_by_id = _canonical_map()
    canonical = {sid: _as_str(meta.get("province")) for sid, meta in sites_by_id.items()}
    _info(f"canonical sites indexed: {len(canonical)}")

    if not DOSSIERS_DIR.exists():
        _warn("dossiers folder not found")
        return EXIT_ISSUES

    mismatches: list[Tuple[str, str, str]] = []
    missing: list[str] = []

    for sid, canon_prov in sorted(canonical.items()):
        dossier_path = DOSSIERS_DIR / f"{sid}.yaml"
        if not dossier_path.exists():
            missing.append(str(dossier_path))
            continue

        d = _load_dossier(dossier_path)
        site = d.get("site") if isinstance(d.get("site"), dict) else {}
        dossier_prov = _as_str(site.get("province")) if isinstance(site, dict) else ""

        if canon_prov != dossier_prov:
            mismatches.append((sid, canon_prov, dossier_prov))

    if missing:
        _warn(f"dossiers missing: {len(missing)}")
        for p in missing[:25]:
            _warn(f"  - {p}")

    if mismatches:
        _warn(f"province mismatches: {len(mismatches)}")
        for sid, canon, got in mismatches[:25]:
            _warn(f"  - {sid}: canonical={canon!r} dossier={got!r}")

    print("------------------------------------------------------------")
    print(f"[SUMMARY] Canonical sites: {len(canonical)}")
    print(f"[SUMMARY] Dossiers missing: {len(missing)}")
    print(f"[SUMMARY] Province mismatches: {len(mismatches)}")
    print("------------------------------------------------------------")

    return EXIT_OK if (not missing and not mismatches) else EXIT_ISSUES


if __name__ == "__main__":
    raise SystemExit(main())
