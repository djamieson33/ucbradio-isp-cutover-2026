# ChatGPT Prompt Reference

*UCB ISP Changeover Repository*

------------------------------------------------------------------------

## 1️⃣ Generate Files / Folders (Reliable Way)

When creating structured YAML or multiple files:

    Give me the most reliable and idempotent way to generate these files on macOS.
    Use bash + python if needed.
    Avoid fragile sed tricks.
    Make it safe to re-run.

------------------------------------------------------------------------

## 2️⃣ Modify Existing YAML Safely

    Give me a robust script (python preferred) to modify this YAML safely.
    Preserve formatting where possible.
    Do not rely on sed.
    Make it idempotent.

------------------------------------------------------------------------

## 3️⃣ Repo-Wide Refactor

    Generate a deterministic repo-wide refactor script.
    Use canonical site.id as source of truth.
    Make it dry-run capable.
    Output summary statistics at the end.

------------------------------------------------------------------------

## 4️⃣ Add New Audit (Namespace Model)

    Create a new audit under bin/audit/checks/<name>/.
    Follow the namespace-per-script model.
    Include:
    - __main__.py
    - summary output
    - non-zero exit on issues
    Make it consistent with existing audits.

------------------------------------------------------------------------

## 5️⃣ Validate Architecture / Data Model

    Review this file as if it were infrastructure metadata.
    Point out structural inconsistencies or future risks.
    Recommend schema improvements.

------------------------------------------------------------------------

## 6️⃣ Scaffold New Site or Device

    Generate a scaffold for a new site using canonical lowercase id.
    Include:
    - inventory/sites.yaml entry
    - inventory/sites/<id>.yaml dossier
    - placeholder device blocks
    Keep consistent with current repo structure.

------------------------------------------------------------------------

## 7️⃣ Firewall / Export Workflow Review

    Review this firewall export workflow step.
    Explain:
    - what is happening
    - what is missing
    - what should be validated next
    Assume we are in controlled production migration.

------------------------------------------------------------------------

## 8️⃣ Enforce Naming Conventions

    Generate an audit that enforces:
    - lowercase site.id
    - uppercase site_code
    - filename matches site.id
    - metadata consistency
    Exit non-zero on violations.

------------------------------------------------------------------------

## 9️⃣ Create Drop-In Files

    Give me a complete drop-in file.
    No placeholders.
    No commentary.
    Ready to paste.

------------------------------------------------------------------------

## 🔟 Engineering Mode

If something sounds hacky:

    Do not optimize for cleverness.
    Optimize for reliability and future-proofing.

------------------------------------------------------------------------

# Quick Decision Matrix

  If Task Involves      Best Tool
  --------------------- --------------------------
  Structured YAML       Python
  Multiple files        Bash loop or Python
  One-liner text edit   sed
  Audit logic           Namespaced Python module
  Schema validation     Audit + exit codes
  Production safety     Idempotent + dry-run

------------------------------------------------------------------------

# Canonical Repo Rules

-   `site.id` = lowercase = authoritative identity
-   `site_code` = uppercase = vendor/display alias
-   Filenames = lowercase site.id
-   Devices reference `site.id`
-   Audits enforce integrity
-   Scripts must be idempotent
-   Scripts should support dry-run where appropriate

------------------------------------------------------------------------

# Ultra-Short Fast Prompt

When in a hurry:

    Give me the safest, most reliable, idempotent way to do this in our ISP repo.

------------------------------------------------------------------------

Generated: 2026-02-27 18:38:05 UTC
