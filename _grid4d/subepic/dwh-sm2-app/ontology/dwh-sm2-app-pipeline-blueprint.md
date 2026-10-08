# dwh-sm2-app Pipeline Blueprint

> The daily evidence pipeline: three stages from Drive raw CSVs to the published public dataset, sequenced by cron stagger.

**Ontology:** application layer of the DWH-SM2 Epic
**Owner:** [dwh-sm2-app](../story/DWH-SM2-APP) SubEpic

## Overview

**Pipeline** = the ordered daily transformation chain Refresh → InfluxImportNormalize → Publish Public Dataset. Each stage consumes the previous stage's outputs and produces the next stage's inputs; the order is critical (a stage reading not-yet-refreshed data publishes stale evidence). Measured baseline: DWH-SM2-APP-0001 audit (2026-10-08).

## Rules

1. **Order is Refresh → Influx → Publish** - later stages must never read data the previous stage has not yet produced.
2. **Sequencing is currently implicit** - the only enforcement is cron stagger (00:00 / 00:30 / 01:30 UTC); a stage that overruns its 30-minute slot silently overlaps with the next (see issue [dwh-sm2-app-pipeline-unsequenced](../issue/dwh-sm2-app-pipeline-unsequenced)).
3. **Every stage is resumable by `workflow_dispatch`** - manual re-run is the recovery path; no stage requires state from a previous run beyond its Drive inputs.
4. **Failure visibility is the pipeline's open wound** - no stage notifies anyone on failure; detecting a dead pipeline is a Human act (GitHub Actions badge or inbox).

## Structure

| Stage | Cron (UTC) | Inputs | Outputs | Failure behavior |
|-------|------------|--------|---------|------------------|
| 1. Refresh (`refresh`) | 00:00 daily + dispatch | Drive `sm2drive:{Vzduchotechnika,Indoor}/{Model,Latest}` CSVs | `merged.csv`, `all_sensors_merged.csv`, dbt fact CSVs (uploaded back to Drive `Model/`), dbt docs committed to repo, Drive `Latest/Upload` archived | incremental dbt build and bot commit/push are `continue-on-error`; dbt fallback to full build; failures elsewhere fail the job silently |
| 2. InfluxImportNormalize (`InfluxImportNormalize`) | 00:30 daily + dispatch | fact CSVs from Drive `Model/`, historical annotated exports from Drive `Influx/` | ephemeral InfluxDB `sensor_data` (additive + nonadditive measurements), hourly aggregate CSVs → Drive `Normalized/`, per-month raw annotated CSVs → Drive `Influx/` | hard-fail on any error; missing `months_to_process.json` aborts |
| 3. Publish Public Dataset (`Publish Public Dataset`) | 01:30 daily + dispatch | Drive `Normalized/*_????-??.hourly.csv` | `public/sm2_public_dataset.{csv.gz,parquet}`, upload to Drive `Public/`, parquet copied to `docs/datex/` + bot commit and push | hard-fail on push error; missing `location_map.csv` only warns |

## Template

Stage inventory row:

```markdown
| <n>. <Stage name> (<workflow name>) | <cron> | <inputs> | <outputs> | <failure behavior> |
```

## Example

Stage 2 as the canonical entry:

```markdown
| 2. InfluxImportNormalize (InfluxImportNormalize) | 30 0 * * * + dispatch | Drive Model/ fact CSVs, Drive Influx/ history | InfluxDB sensor_data, Drive Normalized/ hourly, Drive Influx/ monthly raw | hard-fail; missing months_to_process.json aborts |
```

## Related

- [dwh-sm2-app-application-blueprint](dwh-sm2-app-application-blueprint) - the application this pipeline drives
- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - operating the pipeline
- [dwh-sm2-app-pipeline-unsequenced](../issue/dwh-sm2-app-pipeline-unsequenced) - the sequencing gap
