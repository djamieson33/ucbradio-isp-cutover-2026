# inventory/devices-unassigned

## Purpose

This folder contains device definition files that **do not yet have a confirmed asset ID**
from the official master asset list.

Keeping these files out of `inventory/devices/` prevents duplicates and protects automation.

## Canonical Structure (Once Asset ID Confirmed)

- `inventory/devices/firewalls/<asset>-fw-<vendor>-<site>.yaml`
- `inventory/devices/servers/<asset>-svr-<name>.yaml` (or equivalent stable server key)
- `inventory/devices/broadcast/<asset>-<function>-<vendor>-<site>.yaml` (function-first)
- `inventory/devices/network/<asset>-<function>-<site>.yaml`

## Rules

- Do **not** include model numbers in `device_key`.
- Do **not** store passwords, PSKs, or private keys in repo files.
- Prefer `credentials_location` referencing 1Password.

Last Updated: 2026-02-26 (UTC)
