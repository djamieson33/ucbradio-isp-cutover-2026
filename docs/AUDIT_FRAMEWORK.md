# AUDIT FRAMEWORK

*UCB ISP Changeover Repository*

Generated: 2026-02-27 18:41:17 UTC

------------------------------------------------------------------------

# Audit Architecture

Each audit lives under:

    bin/audit/checks/<audit_name>/

Each audit must include:

-   **main**.py
-   Deterministic logic
-   Clear summary output
-   Exit codes

------------------------------------------------------------------------

# Required Characteristics

-   No side effects
-   Canonical identity validation
-   Structured summary statistics
-   Non-zero exit on violations

------------------------------------------------------------------------

# Current Audit Domains

-   sites → registry integrity
-   site_coverage → device linkage validation
-   filename_site_id → filename correctness
-   ipsec_coverage → IPSec governance

------------------------------------------------------------------------

# Future Audit Opportunities

-   device_inventory_completeness
-   firewall_export_integrity
-   critical_chain_validation
-   cross-site NAT consistency
