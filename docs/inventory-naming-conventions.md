# Inventory Naming Conventions

## Purpose

This document defines the official naming standards for device records
within the UCB ISP Changeover inventory repository.

These conventions ensure:

-   Structural consistency
-   Predictable device_key formats
-   Automation safety
-   Long-term maintainability
-   Clean topology referencing

All new device records MUST follow this standard.

------------------------------------------------------------------------

## Core Principles

1.  Device keys must be stable.
2.  Model numbers must NOT be included in device_key.
3.  Device keys must not change unless absolutely required.
4.  File paths must reflect device category.
5.  Serial numbers must be unique across all devices.
6.  No credentials stored in repository.

------------------------------------------------------------------------

## Device Key Format

### Firewalls (All Vendors)

Format:

`<asset>`{=html}-fw-`<vendor>`{=html}-`<site>`{=html}

Examples:

1-fw-sonicwall-bell-102\
9-fw-sonicwall-broc-100\
431-fw-peplink-chat-101

Rules:

-   `fw` is mandatory for firewall devices.
-   Vendor is lowercase.
-   Site code is lowercase.
-   No model numbers in device_key.

------------------------------------------------------------------------

### Non-Firewall Devices

Format:

`<asset>`{=html}-`<function>`{=html}-`<site>`{=html}

Examples:

28-codec-zipone-broc-100\
84-tx-nautel-vs300-broc-100\
139-svr-mj01a1dt

Rules:

-   Use the functional identifier (codec, tx, svr, etc.)
-   Avoid including vendor unless required for clarity.
-   Avoid including model numbers unless functionally relevant.

------------------------------------------------------------------------

## Folder Structure

Devices must reside in the correct category directory:

inventory/devices/firewalls/\
inventory/devices/network/\
inventory/devices/broadcast/\
inventory/devices/servers/

### Classification Rule

A device belongs in `firewalls/` if it:

-   Terminates WAN
-   Performs NAT
-   Runs IPsec
-   Enforces firewall policy
-   Acts as site gateway

Example:

Peplink WAN routers are classified as firewalls.

------------------------------------------------------------------------

## Asset ID Standard

All device files must contain:

device: asset_id: `<integer>`{=html}

Do NOT use:

-   asset_number
-   schema_version (per device file)
-   unique_firewall_identifier (unless technically required)

------------------------------------------------------------------------

## Credentials Policy

Device files must never contain:

-   username
-   password
-   PSK values
-   Private keys

Instead use:

credentials_location: "1Password \> UCB \> `<Category>`{=html} \>
`<Device>`{=html}"

------------------------------------------------------------------------

## Serial Number Governance

-   Serial numbers must be verified directly from device UI.
-   No duplicate serial numbers allowed across inventory.
-   Copy/paste errors must be corrected immediately.

Verification command:

rg -n "`<serial_number>`{=html}" inventory/devices

Should return exactly one result.

------------------------------------------------------------------------

## Deprecation Workflow

Lifecycle:

Draft → Verified → Asset-Numbered → Active → Deprecated

When refactoring:

-   Update device_key references first.
-   Confirm no YAML references remain.
-   Move obsolete files to inventory/deprecated/.
-   Do not delete historical records.

------------------------------------------------------------------------

## Topology Reference Rules

Topology and tunnel files must reference devices using:

device_key

Never use:

-   File paths
-   Relative references
-   Hard-coded inventory paths

Example:

hub_device_key: 1-fw-sonicwall-bell-102

------------------------------------------------------------------------

## Change Discipline

Before committing structural changes:

1.  Run reference scan:

rg -n "`<old_device_key>`{=html}" inventory

2.  Confirm zero matches.
3.  Then commit.

------------------------------------------------------------------------

## Version Control Guidance

Structural changes to naming conventions should be:

-   Committed separately
-   Clearly labeled in commit message
-   Reviewed before tagging release

------------------------------------------------------------------------

Last Updated: 2026-02-26 (UTC)
