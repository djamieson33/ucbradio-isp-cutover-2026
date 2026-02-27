# REPO GOVERNANCE

*UCB ISP Changeover Repository*

Generated: 2026-02-27 18:41:17 UTC

------------------------------------------------------------------------

# Governance Rules

## 1. Identity Enforcement

All structural linkage must use:

    site.id (lowercase)

site_code is informational only.

------------------------------------------------------------------------

## 2. Naming Conventions

-   Filenames: lowercase site.id
-   Device filenames include site.id
-   Site dossiers: inventory/sites/`<site-id>`{=html}.yaml

------------------------------------------------------------------------

## 3. Audit Compliance

All structural assumptions must be validated through:

    bin/audit/run.sh

Commits that break audits must not be merged.

------------------------------------------------------------------------

## 4. Change Control

Schema changes require:

-   Updated documentation
-   Updated audits
-   Deterministic migration strategy

------------------------------------------------------------------------

## 5. Production Safety

Scripts must:

-   Be idempotent
-   Support dry-run when destructive
-   Avoid fragile sed-based YAML mutation
