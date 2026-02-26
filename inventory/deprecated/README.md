# inventory/deprecated

## Purpose

This directory contains inventory files that are no longer active but
are retained for:

- Historical reference
- Audit traceability
- Documentation continuity
- Post-cutover review

Deprecated files MUST NOT be used for:

- Active topology decisions
- Cutover planning
- Automation inputs
- Device configuration references

------------------------------------------------------------------------

## When to Move a File Here

Move a device or inventory file into `inventory/deprecated/` when:

- The device has been decommissioned
- The file was created based on incorrect assumptions
- A device record has been replaced by a corrected asset-numbered version
- A location code was misidentified and corrected
- A device category was reclassified (e.g., network → firewall)

------------------------------------------------------------------------

## Required Deprecation Header

Each deprecated file should contain a clear header at the top
explaining:

- Why it was deprecated
- What replaced it (if applicable)
- The date (UTC)
- Who confirmed the change (if relevant)

Example:

    # DEPRECATED (YYYY-MM-DD UTC)
    # Replaced by: inventory/devices/<category>/<asset>-<device_key>.yaml
    # Reason: Short description of correction or replacement.
    # Confirmed by: <name / role>

------------------------------------------------------------------------

## Governance Rule

Nothing inside this folder should be referenced by:

- ipsec-topology.yaml
- ipsec-tunnels.yaml
- sites.yaml
- inventory/devices/
- Any automation scripts

If a deprecated file is still referenced anywhere in the repo, that
reference must be removed immediately.

------------------------------------------------------------------------

## Lifecycle Principle

Draft → Verified → Asset-Numbered → Active → Deprecated (if replaced)

Never delete historical inventory unless legally required.
Move it here instead.

------------------------------------------------------------------------

Last Updated: 2026-02-26 (UTC)