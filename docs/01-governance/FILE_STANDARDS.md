# FILE STANDARDS

UCB Radio -- ISP Changeover 2026\
Location: docs/01-governance/FILE_STANDARDS.md

------------------------------------------------------------------------

## Purpose

This document defines mandatory naming conventions, timestamp formats,
and file classification rules for the `ucbradio-isp-cutover-2026`
repository.

The goal is:

-   Deterministic reproducibility
-   Audit traceability
-   Rollback integrity
-   UTC consistency
-   Clear separation between canonical vs generated artifacts

These standards apply to all contributors.

------------------------------------------------------------------------

# 1. Timestamp Standard (Mandatory)

All timestamps MUST:

-   Use UTC (never local time)
-   Follow format:

```{=html}
<!-- -->
```
    YYYYMMDDThhmmZ

Example:

    20260224T1718Z

Rules: - No seconds - No timezone offsets - No lowercase `z` - No
spaces - No dashes inside timestamp

Correct:

    nat-policies-20260224T1718Z.csv

Incorrect:

    nat-policies-2026-02-24-1718.csv
    nat-policies-20260224-1718Z.csv
    nat-policies-20260224T1718z.csv

------------------------------------------------------------------------

# 2. Firewall Export Standards

All SonicWall exports MUST live in:

    firewall/sonicwall/exports/

NAT exports MUST follow:

    nat-policies-YYYYMMDDThhmmZ.csv

Examples:

    nat-policies-20260224T1718Z.csv
    nat-policies-20260225T0930Z.csv

Rules: - Only NAT exports use `nat-policies-` - No generic filenames
like `export.csv` - No overwriting previous exports - Always commit
exports before cutover activity

------------------------------------------------------------------------

# 3. Generated vs Canonical Files

## Canonical Files (Authoritative)

These files are human-reviewed and version-controlled:

    inventory/03-inbound-services.yaml
    dns/current-records.yaml
    docs/*

Canonical files: - Must not be automatically overwritten - Require
intentional commit changes - Represent source-of-truth documentation

------------------------------------------------------------------------

## Generated Files

Generated files must:

-   Include `.seed.` or similar marker
-   Be clearly documented as non-authoritative
-   Never replace canonical files automatically

Example:

    inventory/03-inbound-services.seed.yaml

Generated files are: - Review inputs - Intermediate artifacts -
Validation outputs

------------------------------------------------------------------------

# 4. Release Archive Naming

All release archives must follow:

    releases/ucbradio-isp-cutover-<semver>-YYYYMMDDThhmmZ.zip

Example:

    ucbradio-isp-cutover-0.1.2-20260224T1609Z.zip

Rules: - SemVer required - UTC timestamp required - SHA256 checksum must
accompany release

------------------------------------------------------------------------

# 5. Evidence Storage Standards

Pre-change evidence:

    evidence/pre-change/

Post-change evidence:

    evidence/post-change/

Evidence must: - Include UTC timestamp in filename - Include service
identifier when possible - Be immutable once committed

Example:

    sw-mgmt-curl-20260224T1732Z.txt

------------------------------------------------------------------------

# 6. Inventory Schema Discipline

All inventory files must:

-   Follow defined YAML schema

-   Use stable keys

-   Avoid ad-hoc fields

-   Reference device IDs from:

        inventory/devices/

Service entries must include:

-   id
-   internal_target
-   public_entry
-   nat rules
-   status block

------------------------------------------------------------------------

# 7. Cutover Safety Rules

Before any change to:

-   NAT policies
-   WAN interfaces
-   DNS records
-   Default routes

You MUST:

1.  Export current configuration.
2.  Rename export using UTC format.
3.  Commit export to git.
4.  Confirm clean working tree.
5.  Document intent in CHANGELOG.md.
6.  Update inventory if applicable.

No exceptions.

------------------------------------------------------------------------

# 8. Git Hygiene

Before running any script that modifies state:

    git status

Working tree must be clean.

Commits must: - Be descriptive - Reference change purpose - Avoid vague
messages like "update"

Good:

    Add pre-cutover NAT export (UTC timestamped)

Bad:

    update stuff

------------------------------------------------------------------------

# 9. Script Standards

All scripts in `bin/` must:

-   Include header block referencing these standards
-   Use `set -euo pipefail` (bash)
-   Use explicit return codes
-   Avoid destructive overwrites
-   Prefer read-only defaults

------------------------------------------------------------------------

# 10. Enforcement Philosophy

This repository is treated as:

> A controlled infrastructure change log.

It must be possible to:

-   Reconstruct pre-cutover state
-   Identify exact export used
-   Determine validation steps performed
-   Roll back confidently

Documentation quality equals operational safety.

------------------------------------------------------------------------

# Final Principle

If a file cannot be:

-   Deterministically reproduced
-   Time-correlated
-   Audited
-   Rolled back

It does not belong in this repository.

------------------------------------------------------------------------

End of FILE_STANDARDS.md
