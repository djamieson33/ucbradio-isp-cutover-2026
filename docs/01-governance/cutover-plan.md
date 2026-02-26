# Cutover Plan (ISP Changeover 2026)

Last Updated: 2026-02-26 (UTC)

## Objective

Transition NMC (BELL-102 hub) Internet service from Cogeco (X1) to Bell (X3) with minimal disruption, while ensuring all
STL/IPsec spokes remain connected and on-air services remain stable.

This plan is designed to be executed during a controlled window with explicit rollback steps.

## Scope

- Hub: **BELL-102 (NMC)** SonicWall TZ470
- WANs:
  - X1: Cogeco (current production)
  - X3: Bell (target production)
- Spokes: BELL-100, BROC-100, COBO-100, KING-100, WIND-100, NIPI-100, TBAY-100, CHAT-101 (via Peplink)

## Preconditions

### 1) Inventory and Evidence Baseline (Required)
- Device inventory files updated and normalized under `inventory/devices/`
- Evidence captured for:
  - X1, X3 interface configuration
  - Active tunnels list
  - IPsec policy list
  - Routing default route status
- Verify hub and spoke serial numbers are correct (source of truth = device UI).

### 2) DNS Strategy (Required)
- `vpn.ucbradio.com` points to the hub public IP and is verified resolving correctly.
- For testing, use either:
  - FQDN-based peer references (preferred where supported), or
  - Pre-whitelist Bell IP (207.236.163.98) on spokes in advance.

### 3) IPsec Dual-Peer Readiness (Required)
- All spoke endpoints must accept the hub **Bell target IP (207.236.163.98)** before any WAN cutover.
- Where possible, maintain temporary dual-allow/dual-peer acceptance during the transition window.

## Cutover Phases

### Phase A — Non-Disruptive Validation (Before the Window)
Goal: Prove Bell works without moving production traffic off Cogeco.

- Confirm X3 link up, IP/mask/gateway/DNS correct.
- Perform controlled egress test using policy-based routing for a single test host (see `docs/04-validation/bell-wan-validation.md`).
- Capture evidence screenshots.

### Phase B — Spoke Pre-Whitelist (Before the Window)
Goal: Ensure spokes will accept the hub Bell IP as a valid peer.

For each spoke:
- Add/confirm Bell target IP is allowed as hub peer (`207.236.163.98`).
- Do NOT remove Cogeco peer (`24.51.249.34`) until post-cutover stabilization.
- Confirm tunnels remain established (no impact to on-air transport).

### Phase C — Production Cutover (Window)
Goal: Make Bell the production path, keep IPsec stable.

1. Confirm on-air monitoring / transmitter status visibility.
2. Confirm hub tunnels currently established.
3. Change routing so default Internet egress is via X3 (Bell).
4. Validate:
   - Outbound: egress public IP is 207.236.163.98 for a controlled test host then general traffic.
   - Inbound: any required inbound services (if applicable) reachable.
   - VPN: all STL tunnels remain established and audio transport remains stable.
5. Capture evidence snapshots.

### Phase D — Stabilization (After Cutover)
- Monitor active tunnels for flaps.
- Confirm no unexpected packet loss for RTP transport sites.
- Keep Cogeco configured for rollback until stability criteria met for an agreed period.

## Success Criteria

- Default Internet egress on hub uses Bell (X3).
- All critical IPsec tunnels remain established and stable.
- On-air sites remain broadcasting without audible interruption.
- Operational monitoring confirms expected behavior.

## References

- Validation guidance: `docs/04-validation/bell-wan-validation.md`
- Rollback procedure: `docs/01-governance/rollback-plan.md`
- Testing matrix: `docs/01-governance/testing-matrix.md`
