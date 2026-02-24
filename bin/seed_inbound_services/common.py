# bin/seed_inbound_services/common.py
"""
UCB Radio – ISP Changeover 2026
Tool:    seed_inbound_services
File:    bin/seed_inbound_services/common.py
Purpose: Small, reusable helper functions shared by this tool.
"""

from __future__ import annotations

import datetime as dt
import ipaddress
import re


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").strip().lower()).strip("_")


def norm_val(s: str) -> str:
    return (s or "").strip()


def safe_slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").strip().lower()).strip("-") or "unknown"


def is_private_ip(s: str) -> bool:
    try:
        return ipaddress.ip_address(s.strip()).is_private
    except Exception:
        return False


def extract_ip(s: str) -> str:
    if not s:
        return ""
    m = re.search(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b", s)
    return m.group(1) if m else ""


def extract_port(s: str) -> int | None:
    if not s:
        return None
    m = re.search(r"\b(\d{1,5})\b", s)
    if not m:
        return None
    p = int(m.group(1))
    return p if 1 <= p <= 65535 else None


def extract_proto(s: str) -> str:
    if not s:
        return ""
    s2 = s.strip().lower()
    if "udp" in s2:
        return "udp"
    if "tcp" in s2:
        return "tcp"
    if "any" in s2:
        return "any"
    return ""


def normalize_zone(z: str) -> str:
    return (z or "").strip().upper()


def normalize_obj(o: str) -> str:
    return (o or "").strip()
