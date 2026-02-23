# UCB Radio – ISP Change Project (2026)


**Version:** 0.1.0  
**Last updated:** 2026-02-05

---

## Versioning & Changelog
- Discovery phase: 0.x.x (no production changes)
- Cutover/active changes: 1.x.x
- Post-cutover/maintenance: 2.x.x and above
- See CHANGELOG.md for details
- Use ./bin/bump_version.sh <new_version> to automate version and changelog updates

---

## Project Overview
- Change ISP from Cogeco to Bell for speed/reliability
- Deadline: Feb 28, 2026
- Goal: No downtime for radio/online feeds
- Sites: Belleville (NMC), remote towers
- Key systems: DNS (DigitalOcean), SonicWall firewall, Windows servers (Aquira, Zetta, etc.)

## Team & Roles
- Dwayne Jamieson (Digital Manager, "DJ"): Tech lead, project manager
- Brad Linnard (Content Director, "BL"): On-air content, station direction
- Dan Trudeau (Operations Manager, "DT"): Station operations
- Richard Wand (Program Director, "RW"): Audio, scheduling

## AI Assistant
- Used by tech lead for defensive planning, roll-backs, debugging, and automation
- Documents progress and assists with evidence
- All critical decisions/approvals: human only

## Documentation & Evidence
- Document all progress, changes, and decisions in project folders
- Use UTC timestamps in filenames: YYYYMMDDTHHMMZ
- Clear, descriptive commit messages
- Store validation evidence in evidence/ directory
- Folder structure changes: require tech lead approval

## Communication & Project Management
- Use Microsoft Teams for all project communication
- Post major updates, questions, and blockers in Teams group chat
- Track tasks/milestones in Monday.com

## Sensitive Data
- Store all passwords and sensitive info in 1Password shared vaults
- Never commit secrets to git or share via chat/email
- Reference sensitive items by 1Password vault entry name only

## Onboarding & Discovery
- Take initial snapshot:
	- List all public IPs/subnets
	- Export DNS (dns/current-records.yaml)
	- Export firewall (SonicWall) NAT/access rules
	- List all Windows servers/roles
	- List remote sites/towers
	- Note critical dependencies/integrations
- Team Discovery Questions:
  1. Which systems or services must never go offline during the ISP cutover?
  2. Are there any scheduled events, broadcasts, or deadlines that could be impacted by the transition?
  3. Are there any undocumented connections, dependencies, or integrations we should know about?
  4. Who should be contacted immediately if something fails during the cutover?
  5. Is there anything you’re specifically concerned about with this change?

## Standards & Glossary
- Use clear, consistent naming for files/folders/docs
- Place all scripts in the bin/ directory
- Maintain glossary of agreed terms (see below)
- Focus: smooth, interruption-free transition
- Security improvements (secure connections) = future goal

### Glossary
- NMC: National Media Centre (Belleville head office)
- BL: Brad Linnard (Content Director)
- DT: Dan Trudeau (Operations Manager)
- RW: Richard Wand (Program Director)

## Questions & Blockers
- Post all questions, blockers, and help requests in Teams group chat
- This may be updated as team needs change

---
## Raising Questions & Blockers

All questions, blockers, and requests for help should be posted in the designated Microsoft Teams group chat for this project. This may be updated as the team’s needs evolve.
## Standards & Glossary

- Use clear, consistent naming for files, folders, and documentation
- Maintain a glossary of agreed terms (see below)
- Prioritize a smooth, interruption-free transition for all systems
- Security improvements (e.g., enforcing secure connections) are a future goal—do not change existing connectivity during the initial cutover

### Project Glossary (add terms as needed)
- NMC: National Media Centre (Belleville head office)
- BL: Brad Linnard (Content Director)
- DT: Dan Trudeau (Operations Manager)
- RW: Richard Wand (Program Director)
## (Section removed: duplicate onboarding & discovery)
## Sensitive Data Handling

All passwords and sensitive information (e.g., VPN keys, private certificates, exports) must be stored in 1Password using shared vaults. Sensitive data must never be committed to the repository or shared via email or chat. Reference sensitive items in documentation by their 1Password vault entry name only.
## Communication & Project Management

Project communication is primarily conducted via Microsoft Teams. All major updates, questions, and decisions should be shared in the relevant Teams channels.

Monday.com is used as the project management system for tracking tasks, milestones, and assignments. Contributors should ensure that progress and blockers are updated in Monday.com as part of their workflow.
## Documentation Standards & Evidence

All contributors (human and AI) must:
- Document progress, changes, and decisions in the appropriate folders and files
- Use UTC timestamps in filenames (format: YYYYMMDDTHHMMZ) for traceability
- Provide clear, descriptive commit messages
- Store evidence of pre- and post-change validation in the evidence/ directory
- Record all folder structure changes for approval by the project tech lead

AI is responsible for assisting with documentation and ensuring all progress is logged. All folder structure decisions require approval from the tech lead before implementation.

## Key Collaborators & Roles

- **Dwayne Jamieson (Digital Manager, Full-Stack Programmer)** – Project tech lead and manager
- **Brad Linnard (Content Director, "BL")** – Oversees all on-air content and station direction
- **Dan Trudeau (Operations Manager, "DT")** – Responsible for station operations
- **Richard Wand (Program Director, "RW")** – Manages audio recordings and content scheduling


## AI Assistant Responsibilities

AI will be used by the project tech lead to:
- Ensure defensive planning and roll-back strategies for the ISP change
- Assist in debugging issues during the migration
- Investigate and execute operational automations where possible

All critical decisions and final approvals remain with human collaborators, with AI acting as a support and automation tool.

# UCB Radio – ISP Change Project (2026)

Documentation + evidence for the ISP migration:
- DNS (DigitalOcean)
- SonicWall NAT + access rules
- Windows servers (Aquira, Zetta, etc.)
- Pre/post validation evidence

## Project Mission & Overview

UCB (UCB Radio, UCB Media) is transitioning its internet service provider from Cogeco to Bell to achieve significant improvements in speed and reliability. This project covers the complete migration process, ensuring that all critical equipment and software remain operational with minimal interruption. The transition deadline is February 28, 2026.

Key responsibilities include:
- Maintain uninterrupted radio and online feeds during the ISP changeover 
- Coordinating changes for the SonicWall firewall
- Managing Windows servers at the Belleville head office (NMC) and remote radio tower sites
- Ensuring all critical systems and connections are updated and validated

The goal is to complete the transition smoothly, with thorough documentation and evidence, so that UCB Radio remains on the air throughout the process.

Rules:
- UTC timestamps in filenames: YYYYMMDDTHHMMZ
- Do NOT commit secrets (passwords, VPN keys, private certs)
