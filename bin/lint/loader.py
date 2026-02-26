from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import LintConfig
from utils import is_yaml_file

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    yaml = None  # type: ignore


@dataclass
class LoadedYaml:
    path: Path
    data: Any


@dataclass
class InventoryContext:
    repo_root: Path
    inventory_dir: Path
    devices_dir: Path
    deprecated_dir: Path
    yaml_files: list[LoadedYaml]
    device_files: list[LoadedYaml]
    device_key_index: dict[str, Path]
    raw_by_path: dict[Path, Any]


class InventoryLoader:
    def __init__(self, cfg: LintConfig):
        self.cfg = cfg

    def _read_yaml(self, path: Path) -> Any:
        if yaml is None:
            raise RuntimeError("PyYAML not installed. Install with: pip install pyyaml")
        txt = path.read_text(encoding="utf-8")
        return yaml.safe_load(txt) if txt.strip() else None

    def load(self) -> InventoryContext:
        inv = self.cfg.inventory_dir
        devices = self.cfg.devices_dir
        deprecated = self.cfg.deprecated_dir

        yaml_paths: list[Path] = []
        if inv.exists():
            for p in inv.rglob("*"):
                if is_yaml_file(p):
                    yaml_paths.append(p)

        loaded: list[LoadedYaml] = []
        raw_by_path: dict[Path, Any] = {}
        for p in sorted(yaml_paths):
            try:
                data = self._read_yaml(p)
            except Exception as e:
                data = {"__lint_error__": f"YAML parse error: {e!r}"}
            loaded.append(LoadedYaml(path=p, data=data))
            raw_by_path[p] = data

        device_files = [x for x in loaded if devices in x.path.parents]

        device_key_index: dict[str, Path] = {}
        for item in device_files:
            data = item.data if isinstance(item.data, dict) else {}
            device = data.get("device") if isinstance(data, dict) else None
            if isinstance(device, dict):
                dk = device.get("device_key")
                if isinstance(dk, str) and dk.strip():
                    device_key_index[dk.strip()] = item.path

        return InventoryContext(
            repo_root=self.cfg.repo_root,
            inventory_dir=inv,
            devices_dir=devices,
            deprecated_dir=deprecated,
            yaml_files=loaded,
            device_files=device_files,
            device_key_index=device_key_index,
            raw_by_path=raw_by_path,
        )
