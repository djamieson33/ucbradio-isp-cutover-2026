# SonicWall exports

This folder stores raw exports from SonicWall (CSV + config exports) used by repo automation.

## Folder layout

Store exports per-site:

firewall/sonicwall/exports/<site-slug>/

Examples:
- firewall/sonicwall/exports/bell-102/
- firewall/sonicwall/exports/broc-100/
- firewall/sonicwall/exports/wind-100/
- firewall/sonicwall/exports/tbay-100/

## Required exports for seed_inbound_services

`bin/seed_inbound_services/run.py` expects (within a site folder):

- nat-configurations-<UTCSTAMP>.csv
- security-policy-<UTCSTAMP>.csv

UTCSTAMP format:
- YYYYMMDDThhmmZ  (example: 20260226T2144Z)

Example filenames (inside firewall/sonicwall/exports/wind-100/):
- nat-configurations-20260226T2144Z.csv
- security-policy-20260226T2144Z.csv

Run example:
- python bin/seed_inbound_services/run.py --exports-dir firewall/sonicwall/exports/wind-100 --site wind-100

## Optional exports (recommended evidence)

Store additional artifacts alongside the required CSVs using the same UTCSTAMP pattern:

- access-rules-<UTCSTAMP>.csv
- route-configurations-<UTCSTAMP>.csv
- dns-<UTCSTAMP>.csv (if exported)
- config-export-<UTCSTAMP>.<ext> (use the native export extension)

## Notes

- Keep raw exports immutable once committed (treat them as evidence).
- Use bin/rename_export.sh to stamp files in-place with UTC timestamps.
