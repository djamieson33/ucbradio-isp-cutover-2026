# Inventory Starter Pack

Generated (UTC): 2026-02-23 20:18 UTC

This folder is intended to be copied into your repo (recommended location: `inventory/` at repo root).

## What this gives you
- One YAML file per device under `inventory/devices/`
- Shared lookups: `inventory/sites.yaml`, `inventory/owners.yaml`
- Safe references to secrets using 1Password item names (`auth_ref`), never actual credentials

## Conventions
- File names: `kebab-case.yaml`
- IDs: stable, kebab-case (e.g., `sonicwall-nmc`, `zettaserver`)
- Evidence folders use UTC timestamps: `YYYYMMDDTHHMMZ`

## Next steps
1. Fill in any `TODO:` placeholders.
2. Add/adjust interface details as you confirm them.
3. Keep vendor exports in `exports/` (raw), and keep curated inventory in `inventory/` (source of truth).
