# dwh-sm2-app Application Blueprint

> The SM2 temperature monitoring application: the complete GitHub workflow and every component it orchestrates. datex is a viewer component, not the application.

**Ontology:** application layer of the DWH-SM2 Epic
**Owner:** [dwh-sm2-app](../story/DWH-SM2-APP) SubEpic

## Overview

**Application** = the union of the three GitHub Actions workflows, the scripts and dbt project they execute, the InfluxDB organization they populate, the Google Drive remotes they read and write, and the public dataset with its datex viewer. The application keeps the SM2 evidence base alive unattended: every overheating season produces continuous, reproducible measurements without manual intervention. Measured baseline: the DWH-SM2-APP-0001 audit (2026-10-08).

## Rules

1. **Unattended daily operation** - the application runs as cron-scheduled workflows; the only manual component is the expert analysis toolkit (`analysis/`), which never blocks the pipeline.
2. **datex is a viewer** - the application is the whole workflow; the Data Explorer only renders the published dataset.
3. **Evidence flows one way** - Drive raw CSVs → InfluxDB → hourly exports → public dataset → datex; no component writes back into an earlier stage (Drive archives are the only upstream writes, as part of ingest housekeeping).
4. **The knowledge layer mirrors the machinery** - every component belongs to a concept here and to a runbook entry in [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook); a component without both is a finding, not an exception.

## Structure

| Component | Location | Role |
|-----------|----------|------|
| refresh workflow | `.github/workflows/refresh.yml` | Daily 00:00 UTC. rclone-pulls Drive CSVs, merges ventilation (inline csvkit) and indoor (`scripts/indoor_merge_all_sensors.sh`) data, runs dbt seed/build into DuckDB, uploads fact CSVs back to Drive, commits dbt docs, archives processed Drive uploads |
| InfluxImportNormalize workflow | `.github/workflows/influx_import_workflow.yml` | Daily 00:30 UTC. Ephemeral InfluxDB 2.7 service container; `prepare_annotated_csv.py` converts fact CSVs to annotated CSV, re-imports additive history, writes nonadditive, exports hourly aggregates and per-month raw back to Drive |
| Publish Public Dataset workflow | `.github/workflows/publish_public_dataset.yml` | Daily 01:30 UTC. `build_public_dataset.py` builds `sm2_public_dataset.{csv.gz,parquet}` from hourly exports, copies the parquet into `docs/datex/`, bot-commits and pushes |
| ingest & transform scripts | `scripts/` (7 files) | merge, prepare, import, export, debug helpers - all workflow-invoked |
| dbt project | `dbt_project.yml`, `models/{ventilation,indoor}/`, `seeds/` (4 mapping seeds) | fact models over Drive CSVs via DuckDB external tables; 3 not_null tests total |
| InfluxDB layout | workflow-ephemeral org `ci-org`, bucket `sensor_data` | measurements `additive` (re-imported history) and `nonadditive` (fresh daily) |
| analysis toolkit | `analysis/quasistationary_selection.py` + outputs | manual expert analysis (ČSN 73 0540 window selection, limit evaluation); not workflow-invoked |
| public dataset | `public/` outputs → Drive `sm2drive:Public/`, `docs/datex/sm2_public_dataset.parquet` | CC BY 4.0 csv.gz + parquet |
| datex viewer | `docs/datex/` | static SPA: Chart.js + hyparquet reading the parquet in-browser, cs/en configs |
| knowledge plugin | `_grid4d/` | this SubEpic's ontology/implementation/issue layers + parent Epic stories/issues |

## Template

Component inventory row (what every component entry must carry):

```markdown
| <component> | <path> | <cron/trigger or manual> | <inputs> → <outputs> | <invoked-by> | <audit state> |
```

## Example

The refresh workflow as the canonical inventory entry:

```markdown
| refresh workflow | .github/workflows/refresh.yml | cron 0 0 * * * + dispatch | Drive Model/Latest CSVs → merged.csv, all_sensors_merged.csv, fact*.csv, docs/ | GitHub Actions | verified 2026-10-08, sequencing by cron stagger only |
```

## Key Facts (audit-verified)

- Sequencing between the three workflows exists only as cron stagger (00:00 / 00:30 / 01:30 UTC); there is no `workflow_run` chaining, no `concurrency` guard, no `timeout-minutes`, no failure notification anywhere.
- Secrets: `RCLONE_CONFIG`, `SERVICE_ACCOUNT_FILE` (rclone/Drive), `GITHUB_TOKEN` (bot push). Influx credentials are CI-ephemeral literals, not real secrets.
- The application has no dependency manifest: no requirements.txt / pyproject.toml; dependencies are ad-hoc unpinned `pip install` lines inside workflows.

## Related

- [dwh-sm2-app-pipeline-blueprint](dwh-sm2-app-pipeline-blueprint) - the stage sequence concept
- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - how to operate and verify it
- [DWH-SM2-APP-0001](../story/DWH-SM2-APP-0001) - the audit that measured all of this
