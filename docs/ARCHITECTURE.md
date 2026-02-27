# ARCHITECTURE

*UCB ISP Changeover Repository*

Generated: 2026-02-27 18:41:17 UTC

------------------------------------------------------------------------

# 1. Architectural Philosophy

This repository is a **metadata-driven infrastructure system**.

All automation, validation, and firewall workflows derive from
structured YAML under `inventory/`.

Design goals:

-   Deterministic
-   Idempotent
-   Auditable
-   Canonical identity--driven
-   Safe for production migration

------------------------------------------------------------------------

# 2. Canonical Identity Model

## site.id (Authoritative)

-   Lowercase
-   Used in filenames
-   Used in device metadata
-   Used in audits
-   Used in automation logic

Example:

    id: bell-102

## site_code (Alias)

-   Uppercase
-   Vendor-facing / export-aligned
-   Informational only
-   Never authoritative

Example:

    site_code: BELL-102

------------------------------------------------------------------------

# 3. Repository Structure

inventory/ sites.yaml → canonical site registry
sites/`<site-id>`{=html}.yaml → site operational dossiers
devices/`<category>`{=html}/\*.yaml → device metadata

bin/ audit/ → validation layer tools/ → repo utilities firewall/ →
export/seed workflows

docs/ Architecture and governance documentation

------------------------------------------------------------------------

# 4. Data Flow Model

inventory/sites.yaml ↓ device YAML (references site.id) ↓ audits
validate integrity ↓ firewall export tooling derives state ↓ seed
manifests drive cutover planning

------------------------------------------------------------------------

# 5. Engineering Standards

-   One canonical key: site.id
-   No duplicated authority
-   Scripts must be idempotent
-   Structured data edits use Python
-   Audits must exit non-zero on violations
-   Prefer clarity over cleverness

------------------------------------------------------------------------

# 6. Evolution Strategy

When modifying schema:

1.  Update ARCHITECTURE.md
2.  Update relevant audits
3.  Maintain backward safety
4.  Ensure deterministic outputs
