# Bell WAN validation (without impacting Cogeco)

## Context
- Cogeco (X1) must remain the production/default Internet path for now.
- Bell is provisioned on X3 with static IP **207.236.163.98/27**, gateway **207.236.163.97**.
- ICMP to the public IP may be blocked; failed `ping 207.236.163.98` is not definitive.

## What “online” means for Bell right now
You want evidence that:
1. **Physical link is up** (interface shows link speed/duplex).
2. **L3 config is correct** (IP/mask/gateway/DNS).
3. You can **source traffic out X3** for a controlled test without changing the default route for everyone.
4. (Optional) The firewall can **accept inbound management** on X3 if/when you enable it and have rules.

## Checks on the SonicWall (BELL-102 / NMC)
1. **Network > Interfaces**
   - Confirm **X3**: Zone = WAN, Static IP, correct mask/gateway, Status = Link Up.
   - Confirm **X1** remains the Default WAN (do not change).

2. **Network > Network Monitor**
   - Run a **DNS lookup** test (e.g., `example.com`) and an **HTTP/HTTPS** test.
   - If the UI allows selecting a **source interface**, run the test with **source = X3**.
   - If it does not allow a source selection, these tests usually follow the default route (X1) and are less useful.

3. **Policy-based / route-based test (preferred)**
   Create a *temporary*, narrowly scoped rule that forces a single test host to use X3:
   - Source: your Mac’s IP (or a small test subnet)
   - Destination: a single test IP (or a small allowlist)
   - Service: HTTPS (443)
   - Next hop / interface: X3

   Then verify from the test host:
   - `curl -4 https://ifconfig.me` (or similar) and confirm the **public IP** equals **207.236.163.98**.

4. **Capture evidence**
   Save screenshots into `evidence/pre-change/sonicwall/bell-102-nmc/YYYYMMDD/`.

## Notes
- Don’t rely on ICMP ping to the WAN IP as the sole proof.
- If you need inbound tests (e.g., `sw.ucbradio.com` over Bell), that requires:
  - Public DNS pointing to the Bell IP **or** a hosts-file override for testing
  - WAN management enabled (or NAT to an internal host) plus matching access rules.
