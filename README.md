# UCB Radio — ISP Changeover (2026)

**Current Version:** 0.4.1  
**Cutover Target:** February 28, 2026  
**Primary Change:** Cogeco → Bell (NMC / BELL-102)

## Mission

Execute the ISP transition with:

- No FM broadcast interruption
- No significant streaming outage
- Immediate rollback capability
- Full documentation and evidence trail

## Repo Layout

- `bin/` — automation and helper scripts
- `dns/` — DNS state, cutover records
- `docs/` — governance, validation, and standards (start at `docs/README.md`)
- `evidence/` — screenshots, exports, and validation outputs
- `firewall/` — firewall-specific artifacts, exports, and notes
- `inventory/` — canonical structured inventory (sites, devices, ipsec topology/tunnels)

## Inventory Conventions

Inventory standards are documented here:

- `docs/inventory-naming-conventions.md`

Key rule: device references should use **device_key**, not file paths.

## Quick Start

- Review `docs/README.md` for governance + validation docs
- Validate Bell WAN (X3) using `docs/04-validation/bell-wan-validation.md`
- Use `inventory/ipsec-topology.yaml` and `inventory/ipsec-tunnels.yaml` as the canonical STL view

## Notes

This repo is the source of truth for the ISP changeover project and is expected to evolve rapidly until cutover.
