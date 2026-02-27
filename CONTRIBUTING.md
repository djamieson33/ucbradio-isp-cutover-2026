# CONTRIBUTING

*UCB ISP Changeover Repository*

Generated: 2026-02-27 18:41:17 UTC

------------------------------------------------------------------------

# Contribution Standards

## 1. Follow Canonical Model

-   site.id (lowercase) is authoritative
-   site_code (uppercase) is alias only

------------------------------------------------------------------------

## 2. Do Not Bypass Audits

Before committing:

    bin/audit/run.sh all

All audits must pass.

------------------------------------------------------------------------

## 3. Script Standards

Scripts must:

-   Be idempotent
-   Avoid destructive side effects
-   Prefer Python for structured data
-   Provide summary output

------------------------------------------------------------------------

## 4. Documentation Discipline

If architecture changes:

-   Update ARCHITECTURE.md
-   Update relevant audits
-   Document reasoning

------------------------------------------------------------------------

# Philosophy

Optimize for reliability over cleverness. Prefer explicit logic over
magic behavior.
