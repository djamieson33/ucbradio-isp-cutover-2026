from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LintConfig:
    repo_root: Path
    strict: bool = False
    output_format: str = "text"

    @property
    def inventory_dir(self) -> Path:
        return self.repo_root / "inventory"

    @property
    def devices_dir(self) -> Path:
        return self.inventory_dir / "devices"

    @property
    def deprecated_dir(self) -> Path:
        return self.inventory_dir / "deprecated"

    @property
    def ipsec_topology_file(self) -> Path:
        return self.inventory_dir / "ipsec-topology.yaml"

    @property
    def ipsec_tunnels_file(self) -> Path:
        return self.inventory_dir / "ipsec-tunnels.yaml"
    