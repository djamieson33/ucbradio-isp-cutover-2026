# Rollback Plan (ISP Changeover 2026)

Last Updated: 2026-02-26 (UTC)

## Objective

Provide a fast, low-risk procedure to revert NMC hub routing from Bell (X3) back to Cogeco (X1) if stability or
on-air continuity is at risk.

## Rollback Triggers

Execute rollback immediately if any of the following occur and cannot be resolved quickly:
- Multiple STL/IPsec tunnels drop and do not re-establish
- Live audio transport is disrupted (confirmed)
- Critical inbound services fail (where applicable)
- Severe routing instability (default route flapping, high packet loss)

## Preconditions

- Cogeco (X1) remains configured and physically connected.
- No destructive changes have been made to IPsec policies that would prevent re-establishment on X1.
- Evidence baseline exists for pre-cutover state (interfaces, routing, tunnels).

## Rollback Steps (Hub: BELL-102)

1. **Announce rollback**
   - Notify internal stakeholders (Ops / Programming) that rollback is being executed to protect on-air continuity.

2. **Restore default routing to Cogeco (X1)**
   - In SonicWall routing / failover configuration:
     - Set active/default WAN to **X1**
     - Ensure X3 is not the active default route
   - Do not disable X3 unless required; simply remove it as default.

3. **Validate Internet egress**
   - Confirm public egress IP returns to Cogeco public IP (24.51.249.34) for a controlled test host.

4. **Validate IPsec tunnels**
   - Check **Network > IPsec VPN > Active Tunnels**
   - Confirm all STL tunnels re-establish and remain stable.

5. **Validate on-air transport**
   - Confirm transmitter status / on-air monitoring signals.
   - Confirm live audio transport is stable for BROC-100 and other critical sites.

6. **Capture evidence**
   - Save screenshots of routing + tunnels after rollback.

## Post-Rollback Actions

- Record trigger reason, start/end time (UTC), impacted sites (if any).
- Preserve Bell configuration for later analysis.
- Create remediation task list before reattempting cutover.

## Notes

- Prefer changing default route/failover settings over disabling interfaces.
