# UCB Radio -- ISP Change Project (2026)

.1.2\
**Cutover Target:** February 28, 2026\
**Primary Change:** Cogeco → Bell ISP

------------------------------------------------------------------------

## Mission

Execute ISP transition with:

-   No FM broadcast interruption\
-   No significant streaming outage\
-   Immediate rollback capability\
-   Full documentation and evidence trail

------------------------------------------------------------------------

## Repository Structure

CHANGELOG.md\
VERSION\
bin/\
dns/\
docs/\
evidence/\
firewall/\
releases/\
servers/\
backups/

### Key Directories

**bin/**\
Release + archive automation scripts.

**dns/**\
Current and intended DNS state.

**docs/**\
Structured planning and governance documents.

-   01-governance\
-   02-architecture\
-   03-cutover\
-   04-validation\
-   05-rollback\
-   06-executive\
-   07-post-cutover

**evidence/**\
Pre- and post-change validation artifacts.

**firewall/**\
SonicWall documentation, exports, and diagrams.

**releases/**\
Versioned project snapshots.

------------------------------------------------------------------------

## Governance Model

1.  Governance & Risk Definition\
2.  Architecture Mapping\
3.  Cutover Planning\
4.  Validation Criteria\
5.  Rollback Definition\
6.  Executive Approval\
7.  Post-Cutover Review

No production changes occur without documented validation and rollback
readiness.

------------------------------------------------------------------------

## Versioning

-   0.x.x --- Discovery / planning only\
-   1.x.x --- Active cutover phase\
-   2.x.x --- Post-cutover / stabilization

Use:

    ./bin/release.sh patch "description"

to bump version, update changelog, and create release archive.

------------------------------------------------------------------------

## Documentation Standards

-   UTC timestamps: YYYYMMDDTHHMMZ\
-   Clear commit messages\
-   Evidence stored in /evidence/\
-   No secrets committed to repository\
-   Sensitive data stored in 1Password

------------------------------------------------------------------------

## Communication

-   Operational updates: Microsoft Teams\
-   Task tracking: Monday.com (Sprints board)\
-   Executive approvals: /docs/06-executive/

------------------------------------------------------------------------

## Project Leads

-   Dwayne Jamieson -- Technical Lead\
-   Brad Linnard -- Content Director\
-   Dan Trudeau -- Operations\
-   Richard Wand -- Programming

------------------------------------------------------------------------

This repository serves as the official change-control record for the
2026 ISP migration.
