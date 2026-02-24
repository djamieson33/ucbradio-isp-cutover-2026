# Inventory YAML Schema (v1)

This schema is intentionally lightweight and human-friendly.

## Required (recommended) keys
- schema_version: 1
- id
- name
- type (firewall | switch | modem | server | encoder | nas | workstation | other)
- site
- role

## Common optional sections
- network: mgmt_ip, mgmt_port, interfaces[]
- access: mgmt_url, auth_ref (1Password item name), notes
- ownership: primary, escalation
- dependencies: upstream[], downstream[]
- cutover: criticality, prechecks[], rollback[]
- evidence: pre_change_dir, post_change_dir

## Rules
- Never store secrets (passwords, private keys, VPN pre-shared keys) in this repo.
- Use `auth_ref` to point to a 1Password shared vault item by name.
