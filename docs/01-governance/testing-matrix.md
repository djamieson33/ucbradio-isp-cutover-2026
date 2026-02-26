# Testing Matrix (ISP Changeover 2026)

Last Updated: 2026-02-26 (UTC)

## Purpose

Repeatable validation set for the hub WAN change and ongoing site stability.

## Global Checks (Hub: BELL-102)

| Test | Method | Expected Result | Evidence |
|---|---|---|---|
| X3 interface config | UI | X3 shows 207.236.163.98/27, GW 207.236.163.97, DNS set, link up | Screenshot |
| Default route | UI | Default route via X1 (pre) / X3 (post) as intended | Screenshot |
| Controlled egress via Bell | curl | Test host egress public IP = 207.236.163.98 | Command output |
| Active tunnels list | UI | STL-* tunnels established | Screenshot |

## Site Checks (Each Spoke)

| Site | Device Key | Tunnel | Site LAN | Test | Expected |
|---|---|---|---|---|---|
| BELL-100 | 2-fw-sonicwall-bell-100 | STL-BELL-100 IPsec | 192.168.101.0/24 | Ping site gateway | Replies over tunnel |
| BROC-100 | 9-fw-sonicwall-broc-100 | STL-BROC-100 IPsec | 192.168.104.0/24 | Ping site gateway | Replies over tunnel |
| COBO-100 | 3-fw-sonicwall-cobo-100 | STL-COBO-100 IPsec | 192.168.102.0/24 | Ping site gateway | Replies over tunnel |
| KING-100 | 5-fw-sonicwall-king-100 | STL-KING-100 IPsec | 192.168.105.0/24 | Ping site gateway | Replies over tunnel |
| WIND-100 | 7-fw-sonicwall-wind-100 | STL-WIND-100 IPsec | 192.168.106.0/24 | Ping site gateway | Replies over tunnel |
| NIPI-100 | 8-fw-sonicwall-nipi-100 | STL-NIPI-100 IPsec | 192.168.0.0/24 | Ping site gateway | Replies over tunnel |
| TBAY-100 | 6-fw-sonicwall-tbay-100 | STL-TBAY-100 IPsec | 192.168.35.0/24 | Ping site gateway | Replies over tunnel |
| CHAT-101 | 431-fw-peplink-chat-101 | STL-CHAT-100 IPsec | 192.168.103.0/24 | Ping site gateway | Replies if allowed |

## Evidence Capture Standard

- `evidence/pre-change/<vendor>/<site>/<YYYYMMDD>/` for pre-cutover
- `evidence/post-change/<vendor>/<site>/<YYYYMMDD>/` for post-cutover
