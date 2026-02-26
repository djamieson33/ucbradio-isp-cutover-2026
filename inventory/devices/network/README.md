# inventory/devices/network

## Purpose

Non-firewall network devices (switches, APs, bridges, radios, etc.) that are part of the cutover inventory.

**Note:** WAN edge devices that terminate Internet, perform NAT, or terminate IPsec must be tracked under:
`inventory/devices/firewalls/` (even if they are not SonicWall).

## Device Key Convention

Use stable, non-model device keys:

- Firewalls: `<asset>-fw-<vendor>-<site>`
- Network: `<asset>-net-<function>-<site>` (only if needed), otherwise `<asset>-<function>-<site>`

Last Updated: 2026-02-26 (UTC)
