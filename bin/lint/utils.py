from __future__ import annotations

import re
from pathlib import Path
from typing import Any


DEVICE_KEY_RE = re.compile(r"^\d+-[a-z0-9]+(?:-[a-z0-9]+)*$")


def is_yaml_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in {".yml", ".yaml"}


def get_nested(d: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        if part not in cur:
            return default
        cur = cur[part]
    return cur


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


def looks_like_secret_key(key_name: str) -> bool:
    """
    Heuristic keys that should never appear with literal values.
    We flag presence of these keys anywhere (unless value is clearly a vault reference).
    """
    k = key_name.strip().lower()
    bad = (
        "password",
        "passphrase",
        "psk",
        "pre_shared_key",
        "preshared",
        "private_key",
        "token",
        "api_key",
        "secret",
        "client_secret",
    )
    return any(b in k for b in bad)


def is_vault_reference(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip().lower()
    return (
        v.startswith("1password://")
        or "1password" in v
        or "vault" in v
        or "stored_elsewhere" in v
        or "secret_ref" in v
        or "credentials_location" in v
    )


def flatten_dict(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    """
    Returns list of (path, value) for all leaf nodes.
    """
    out: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            out.extend(flatten_dict(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            p = f"{prefix}[{i}]"
            out.extend(flatten_dict(v, p))
    else:
        out.append((prefix, obj))
    return out
