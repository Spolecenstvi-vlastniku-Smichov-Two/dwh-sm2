# Refresh dbt selection by source freshness silently skips content-only changes

**Status:** open
**Found:** 2026-10-08 (live diagnosis, missing-sensors incident)

## Problem

The refresh workflow's incremental build step (`refresh.yml`, step "Run dbt build"):

```
dbt build --select result:error+ source_status:fresher+ --defer --state docs
```

treats a source as changed only when its `max(loaded_at)` timestamp advances (`models/indoor/sources.yml` sets `loaded_at_field: cast(Datetime as timestamp)` on `all_sensors_merged.csv`). A source whose *content* changed without its max timestamp advancing — new sensors added, a sensor backfilled with history that ends inside the already-recorded window — matches no nodes, so the fact models are not rebuilt and the fact upload step prints `fact_indoor_*.csv not found, skipping upload`. Because an empty selection exits 0, the `Full dbt build` fallback (`if: steps.run_dbt_build.outcome != 'success'`) never fires. The run stays green: the upload of fact tables to `sm2drive:Indoor/Model/` is silently skipped, and every downstream stage (InfluxImportNormalize reads `Model/`, Publish reads `Normalized/` built from it, datex reads the published dataset) keeps serving the stale sensor set.

## Symptoms

- Re-uploading sensor exports whose latest reading timestamp does not exceed the state manifest's recorded max leaves `Model/` untouched while the refresh workflow reports success.
- The only visible trace is the upload step's `not found, skipping upload` lines (rclone prints nothing on success, so a real upload shows as a ~10 s gap in the log instead).
- Downstream stages cannot detect the gap: they read `Model/` and happily republish stale data.

## Solution Direction

Fail the selective build (or branch to the full build) when the selection is empty — e.g. detect `does not match any enabled nodes` for `source_status:fresher+` in the step output and fall back to `dbt build`. Given the project size (3 models, full build ≈ 2 s in run logs), running the full build unconditionally is a legitimate simplification. Alternatively/additionally, gate on source *fingerprint* (row count or file hash) rather than max timestamp. Keep the runbook's Health Verification section in sync (verify `Model/` fact mtimes advanced, not just green conclusions).

## Occurrences

- **2026-10-08 (live, missing-sensors incident)**: Human uploaded a partial sensor set, then re-uploaded the complete set after noticing gaps in datex. Runs 37738331019 (06:34) and 37756665551 (09:26) both merged all 26 sensor files (`all_sensors_merged.csv` = 26,634,057 B) yet both logged `source_status:fresher+ does not match any enabled nodes` → no fact rebuild → all three fact uploads skipped → `Model/` stayed at the 06:05 state written by run 37735598512 (which had rebuilt because the state manifest was a week stale after the lint outage). Influx 37738529816 / Publish 37739094359 consequently republished the partial dataset. Recovery: re-export with readings newer than the recorded max (advances `loaded_at`), or fix per Solution Direction.

## Related

- [dwh-sm2-app-pipeline-unsequenced](dwh-sm2-app-pipeline-unsequenced) - same evidence pipeline, failure-invisibility class
- [dwh-sm2-app-dependencies-unpinned](dwh-sm2-app-dependencies-unpinned) - root cause of the week-stale state that made the 06:04 rebuild fire at all
- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - Health Verification must cover this
