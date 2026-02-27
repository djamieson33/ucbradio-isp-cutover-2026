## [0.7.0] - 2026-02-27
- 🚀 v0.7.0 — Governance & Identity Model Formalization

This release formalizes the architectural and governance foundation of the ISP Changeover repository.

🔐 Canonical Identity Model
	•	Established site.id (lowercase) as the authoritative system key
	•	Defined site_code (uppercase) as vendor/display alias only
	•	Standardized filename conventions to match site.id
	•	Locked identity usage across audits and tooling

⸻

📘 Documentation Overhaul

Introduced a structured governance documentation set:
	•	ARCHITECTURE.md — metadata-driven system model and identity contract
	•	REPO_GOVERNANCE.md — enforcement rules and naming conventions
	•	AUDIT_FRAMEWORK.md — audit namespace structure and validation standards
	•	CONTRIBUTING.md — engineering and idempotency standards
	•	DOCS_INDEX.md — documentation hierarchy reference

This establishes a long-term maintainable schema evolution path.

⸻

🌍 Sites Registry Expansion

Updated inventory/sites.yaml:
	•	Added Western Canada sites:
	•	REGI-100
	•	SASK-100
	•	FMAC-100
	•	MHAT-100
	•	Standardized ipsec.enabled across all sites
	•	Normalized status field formatting
	•	Clarified Windsor IPSec state
	•	Confirmed identity alignment with canonical model

⸻

🛡 Audit Integrity
	•	Governance model now explicitly enforced via audit framework
	•	Identity consistency validated through canonical site linkage

⸻

🔄 Impact

No functional changes to firewall export or seeding workflows.
This release strengthens structural integrity and future-proofing.

⸻

If you’d like, I can also generate:
	•	The exact bin/release.sh command you should run
	•	A CHANGELOG entry formatted to match your existing style
	•	Or a semantic tag summary formatted for GitHub release UI

This is a clean architectural milestone.

## [0.6.0] - 2026-02-27
- v0.6.0 – Per-Firewall Seeding & Scoped Overrides

This release introduces a major structural improvement to the SonicWall seeding workflow: device-scoped seeding and override resolution.

Seeding is now explicitly tied to the exporting firewall, eliminating cross-firewall ambiguity and enabling clean multi-site management.

## [0.5.0] - 2026-02-26
- BROC-100 Bell path validated; inventory normalized
### Added
- Canonical cutover-status.yaml tracker
- BROC-100 Bell path validation record

### Changed
- Standardized device_key to match filename stems
- Normalized server filenames with site codes
- Moved Peplink devices into firewalls category
- Updated deprecated headers to valid schema format
- Refined lint rules to align with nested site schema

### Verified
- BROC-100 successfully renegotiated IPsec over Bell (207.236.163.98)
- Tunnel restored cleanly to Cogeco
- No sustained audio interruption observed
- Failover monitoring and probes confirmed operational

## [0.4.1] - 2026-02-26
- docs: formalize ISP cutover governance and validation framework

## [0.4.0] - 2026-02-25
- feat: add site env resolver + nettest suite (ping/tcp/curl/ssh/public_ip + run_all)

## [0.3.0] - 2026-02-25
- refactor(tooling): introduce namespaced bin architecture

- release/ tool with lib/ (git, semver, archive, checksum, github)
- archive/ tool with lib/
- validate/ tool with modular check registry
- Wrapper scripts maintained for compatibility

Standardizes internal tooling architecture ahead of Bell WAN pilot.

## [0.2.0] - 2026-02-25
- Stage Bell WAN + BROC dual-gateway prep; add evidence artifacts and topology normalization

## [0.1.4] - 2026-02-25
- Bell WAN staged; BROC dual gateway configured

## [0.1.3] - 2026-02-24
- Firewall configuration has effectively been converted into structured infrastructure data.

## [0.1.2] - 2026-02-24
- adding intentory files

## [0.1.1] - 2026-02-05
- Patch release: Improved release automation and versioning process.
	- Added VERSION file for consistent version tracking
	- Updated zipproject script to read version from VERSION file
	- Ensured zip filenames match project version
	- Automated changelog and release steps
	- No content changes to project files, only process improvements

## [0.1.0] - 2026-02-05
- Release: Updated project version and created new zip archive for distribution.
	- Updated VERSION file to v0.1.0
	- Added new release entry to CHANGELOG
	- Created zip archive for v0.1.0
	- See evidence/ for supporting documentation
	- See dns/, firewall/, and scripts/ for updated configs

## [0.0.2] - 2026-02-05
- Test release automation

# Changelog

All notable changes to this project will be documented in this file.

## [0.0.1] - 2026-02-05
- Project discovery phase started.
- Initial structure, onboarding, standards, and team documentation.
