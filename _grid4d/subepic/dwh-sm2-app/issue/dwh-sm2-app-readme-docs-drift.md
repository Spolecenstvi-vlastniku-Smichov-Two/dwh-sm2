# README documents an application that does not exist

**Status:** open
**Found:** 2026-10-08 (DWH-SM2-APP-0001 audit)

## Problem

The 1163-line README makes operational claims that are false against the workflow files it claims to describe:

1. **Triggers**: README (116-119, 127-129, 444-447) says all three workflows trigger "on push to main" - no workflow file has a `push:` trigger (schedule + `workflow_dispatch` only).
2. **Publish cadence**: README (92-98, 449-452) says weekly Saturday 02:10 (`10 2 * * 6`); the actual cron is daily 01:30 (`30 1 * * *`).
3. **Wrong component attribution**: README step 3 credits `scripts/indoor_merge_all_sensors.sh` with the ventilation merge - that script merges only indoor ThermoPro files; the ventilation merge is inline csvkit bash in refresh.yml:55-73.
4. **Stale script semantics**: `check_and_import_previous_exports.py` is documented with `--skipRowOnError` and exit-1-on-error - it has neither (always exits 0, no flag passed); `indoor_merge_all_sensors.sh` is documented as v2.2, the file is v3.1; the annotated-CSV header example lacks the `_field` column the script writes.
5. **Seed values**: README "Historical Data Recovery" shows history 4/4/4; `mapping_sources.csv` holds 4/2/2.

## Why It Matters

The README is the first document a collaborator, auditor, or expert reads in an evidence-grade repository. Every false claim transfers into their mental model of how the evidence is produced - in a complaint case that trades on reproducibility.

## Solution Direction

Either regenerate the operational sections from the workflow files (single source of truth, possibly a checked-in generated excerpt per workflow), or trim the README to stable facts and link the runbook ([dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook)) for anything operational. A README-facts test in the story suite can pin cron expressions and script names against the files.

## Related

- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - the corrected operational picture
- [dwh-sm2-app-pipeline-unsequenced](dwh-sm2-app-pipeline-unsequenced) - the sequencing reality behind claims 1-2
