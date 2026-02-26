# inventory/devices-unassigned

## Purpose

This folder contains device definition files that **do not yet have a confirmed asset number**
in the official master asset list import.

### Why this matters

In this repo, **every device file that lives under `inventory/devices/` MUST start with an asset number**
to prevent duplicates and to make future automation reliable.

### Canonical structure

- `inventory/devices/firewalls/<asset>-<slug>.yaml`
- `inventory/devices/servers/<asset>-<slug>.yaml`
- `inventory/devices/network/<asset>-<slug>.yaml`

### Promotion rules (quick)

A device in `devices-unassigned/` can be promoted when we can confidently map it to:

- Asset number
- Brand / model (or at least a unique name)
- Location (optional but ideal)

Once promoted, the file is moved into the appropriate subfolder under `inventory/devices/`
and renamed to the standard `<asset>-<slug>.yaml`.

## Current contents (still unassigned)

The remaining files here need asset-number confirmation (or a decision that they will **never** be asset-tracked):

- `bell-modem.yaml`
- `cogeco-modem.yaml`
- `core-switch.yaml`
- `stream-encoder.yaml`

> Note: `sonicwall-nmc.yaml` was moved to `inventory/deprecated/devices/` because the hub firewall is now tracked as `inventory/devices/firewalls/1-fw-sonicwall-bell-102.yaml`.
