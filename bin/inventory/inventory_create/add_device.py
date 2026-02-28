from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from bin.inventory.inventory_update.sync_site_dossiers import cmd_sync_site_dossiers


@dataclass(frozen=True)
class ParsedFilename:
    asset_id: int
    token: str
    vendor: str
    model: str
    site_id: str


FILENAME_RE = re.compile(
    r"^(?P<asset>\d+)-(?P<token>[a-z0-9]+)-(?P<vendor>[a-z0-9]+)-(?P<model>[a-z0-9]+)-(?P<site>[a-z0-9]+-\d+)\.ya?ml$",
    re.IGNORECASE,
)

TOKEN_TO_CATEGORY_ROLE = {
    "fw": ("firewalls", "firewall"),
    "firewall": ("firewalls", "firewall"),
    "tx": ("broadcast", "transmitter"),
    "transmitter": ("broadcast", "transmitter"),
    "codec": ("broadcast", "codec"),
    "svr": ("servers", "server"),
    "srv": ("servers", "server"),
    "server": ("servers", "server"),
    "sw": ("network", "switch"),
    "switch": ("network", "switch"),
    "ap": ("network", "access-point"),
}


def _repo_root() -> Path:
    # .../repo/bin/inventory/inventory_create/add_device.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def _die(msg: str, code: int = 2) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def _info(msg: str) -> None:
    print(f"[INFO] {msg}")


def parse_device_filename(name: str) -> ParsedFilename:
    base = os.path.basename(name)
    m = FILENAME_RE.match(base)
    if not m:
        _die(f"Unsupported filename format: {base}")

    asset_id = int(m.group("asset"))
    token = m.group("token").lower()
    vendor = m.group("vendor").strip()
    model = m.group("model").strip()
    site_id = m.group("site").lower()

    # normalize vendor/model for display
    vendor_norm = vendor[:1].upper() + vendor[1:].lower()
    model_norm = model.upper()

    return ParsedFilename(
        asset_id=asset_id,
        token=token,
        vendor=vendor_norm,
        model=model_norm,
        site_id=site_id,
    )


def _prompt(label: str, current: str = "", *, allow_blank: bool = True) -> str:
    suffix = f" [{current}]" if current else " []"
    val = input(f"{label}{suffix}: ").strip()
    if val == "":
        return current if current != "" else ("" if allow_blank else current)
    return val


def _prompt_bool(label: str, current: bool = False) -> bool:
    cur = "y" if current else "n"
    val = input(f"{label} (y/n) [{cur}]: ").strip().lower()
    if val == "":
        return current
    if val in ("y", "yes", "true", "1"):
        return True
    if val in ("n", "no", "false", "0"):
        return False
    print("[WARN] invalid input; keeping current")
    return current


def _ensure_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if str(x).strip()]
    if isinstance(v, str):
        return [v] if v.strip() else []
    return []


def _parse_fqdns(raw: str) -> List[str]:
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


def _target_path(parsed: ParsedFilename) -> Tuple[Path, str, str]:
    """Return (absolute_path, devices_subdir, role)."""
    cat_role = TOKEN_TO_CATEGORY_ROLE.get(parsed.token)
    if not cat_role:
        devices_subdir, role = ("network", parsed.token)
    else:
        devices_subdir, role = cat_role

    rel = (
        Path("inventory/devices")
        / devices_subdir
        / f"{parsed.asset_id}-{parsed.token}-{parsed.vendor.lower()}-{parsed.model.lower()}-{parsed.site_id}.yaml"
    )
    return _repo_root() / rel, devices_subdir, role


def _starter_doc(
    parsed: ParsedFilename,
    role: str,
    *,
    site_dns_zone: str = "ucbradio.local",
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "asset": {"id": parsed.asset_id},
        "identity": {"role": role, "vendor": parsed.vendor, "model": parsed.model},
        "site": {"id": parsed.site_id},
        "network": {
            "management": {
                "hostname": "",
                "ip": "",
                "dns_zone": site_dns_zone,
            }
        },
        "internet": {
            "wan_public_ip": "",
            "nat_exposed": False,
            "public_dns": {"active": [], "deprecated": []},
            "transitional": False,
        },
        "lifecycle": {
            "target_state": "internal-only",
            "public_dns_planned_removal": False,
        },
        "monitoring": {"enabled": False},
        "hardware": {"serial_number": "", "location_detail": ""},
        "notes": "",
    }


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        _die(f"Failed to parse YAML: {path}: {e}")
    if not isinstance(data, dict):
        _die(f"Expected mapping at root of YAML: {path}")
    return data


def _write_yaml(path: Path, doc: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)
    path.write_text(s, encoding="utf-8")


def cmd_add_device(args) -> int:
    """
    argparse handler for:
      python3 bin/inventory/run.py add-device <filename>
    """
    filename = args.filename
    overwrite = bool(getattr(args, "overwrite", False))
    no_sync = bool(getattr(args, "no_sync", False))
    site_dns_zone = getattr(args, "site_dns_zone", "ucbradio.local")

    parsed = parse_device_filename(filename)
    _info(
        f"Parsed filename: asset={parsed.asset_id}, token={parsed.token}, vendor={parsed.vendor}, "
        f"model={parsed.model}, site.id={parsed.site_id}"
    )

    target, devices_subdir, role = _target_path(parsed)
    _info(f"Target category: {devices_subdir} (role={role})")
    _info(f"Target device file: {target.relative_to(_repo_root())}")

    exists = target.exists()
    if exists and not overwrite:
        _info("Device file exists: entering verify/update mode.")
        doc = _load_yaml(target)
    else:
        if exists and overwrite:
            _info("Overwriting existing device file (as requested).")
        else:
            _info("Device file does not exist: creating starter doc.")
        doc = _starter_doc(parsed, role, site_dns_zone=site_dns_zone)

    print("--- Verify/update fields (Enter keeps current) ---")

    # Management plane (internal)
    network = doc.setdefault("network", {})
    if not isinstance(network, dict):
        network = {}
        doc["network"] = network

    mgmt = network.setdefault("management", {})
    if not isinstance(mgmt, dict):
        mgmt = {}
        network["management"] = mgmt

    mgmt["hostname"] = _prompt("management.hostname (internal)", str(mgmt.get("hostname", "")))
    mgmt["ip"] = _prompt("management.ip (private LAN)", str(mgmt.get("ip", "")))
    mgmt["dns_zone"] = _prompt("management.dns_zone", str(mgmt.get("dns_zone", site_dns_zone)))

    # Hardware basics
    hw = doc.setdefault("hardware", {})
    if isinstance(hw, dict):
        hw["serial_number"] = _prompt("hardware.serial_number", str(hw.get("serial_number", "")))
        hw["location_detail"] = _prompt("hardware.location_detail (rack/room)", str(hw.get("location_detail", "")))

    # Monitoring
    mon = doc.setdefault("monitoring", {})
    if isinstance(mon, dict):
        mon["enabled"] = _prompt_bool("monitoring.enabled", bool(mon.get("enabled", False)))

    # Notes
    doc["notes"] = _prompt("notes", str(doc.get("notes", "")))

    # Public DNS (transitional reality)
    internet = doc.setdefault("internet", {})
    if not isinstance(internet, dict):
        internet = {}
        doc["internet"] = internet

    public_dns = internet.setdefault("public_dns", {"active": [], "deprecated": []})
    if not isinstance(public_dns, dict):
        public_dns = {"active": [], "deprecated": []}
        internet["public_dns"] = public_dns

    has_public = _prompt_bool(
        "Does this device currently use any public FQDN(s) (ucbradio.com)?",
        bool(_ensure_list(public_dns.get("active"))),
    )

    if has_public:
        existing_active = _ensure_list(public_dns.get("active"))
        raw = _prompt("public_dns.active (comma-separated)", ",".join(existing_active))
        public_dns["active"] = _parse_fqdns(raw)

        internet["wan_public_ip"] = _prompt("internet.wan_public_ip", str(internet.get("wan_public_ip", "")))
        internet["nat_exposed"] = _prompt_bool("internet.nat_exposed", bool(internet.get("nat_exposed", True)))
        internet["transitional"] = True

        lifecycle = doc.setdefault("lifecycle", {})
        if isinstance(lifecycle, dict):
            lifecycle["target_state"] = _prompt(
                "lifecycle.target_state",
                str(lifecycle.get("target_state", "internal-only")),
            )
            lifecycle["public_dns_planned_removal"] = _prompt_bool(
                "lifecycle.public_dns_planned_removal",
                bool(lifecycle.get("public_dns_planned_removal", True)),
            )
    else:
        # keep existing values; ensure keys exist
        internet.setdefault("wan_public_ip", str(internet.get("wan_public_ip", "")))
        internet["nat_exposed"] = bool(internet.get("nat_exposed", False))
        internet.setdefault("transitional", False)

    # Ensure required identity fields are consistent
    doc.setdefault("asset", {})
    if isinstance(doc["asset"], dict):
        doc["asset"]["id"] = parsed.asset_id

    doc.setdefault("identity", {})
    if not isinstance(doc["identity"], dict):
        doc["identity"] = {}

    doc["identity"]["role"] = role
    doc["identity"]["vendor"] = parsed.vendor
    doc["identity"]["model"] = parsed.model

    doc.setdefault("site", {})
    if isinstance(doc["site"], dict):
        doc["site"]["id"] = parsed.site_id

    _write_yaml(target, doc)
    print(f"[OK] Wrote device file: {target.relative_to(_repo_root())}")

    if no_sync:
        _info("Skipping site dossier sync (--no-sync).")
        return 0

    _info("Syncing site dossiers...")

    class _SyncArgs:
        sites_file = "inventory/sites.yaml"
        devices_root = "inventory/devices"
        sites_dir = "inventory/sites"

    return int(cmd_sync_site_dossiers(_SyncArgs()))
