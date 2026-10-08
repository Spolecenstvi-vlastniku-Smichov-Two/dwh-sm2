# DWH-SM2-APP

> Temperature monitoring application SubEpic - owns the SM2 monitoring application end to end: the complete GitHub workflow and every component it orchestrates.

**Type:** SubEpic
**Inherits:** dwh-sm2
**StoryPrefix:** DWH-SM2-APP-

## Overview

Recursive variation of [Epic](ontology-epic-blueprint) instantiated at application scope inside the DWH-SM2 repository, per [ontology-subepic-blueprint](ontology-subepic-blueprint). The application is the complete GitHub Actions workflow and every component it orchestrates: source ingest (Google Drive annotated CSVs), InfluxDB 2.7 storage and hourly aggregation, dbt + DuckDB transformation (location mapping, fact tables), public dataset publication (CSV.gz + Parquet, CC BY 4.0) in a strict orchestration sequence (Refresh → InfluxImportNormalize → Publish Public Dataset), the analysis toolkit (`analysis/quasistationary_selection.py`, decisive-window graphs), and the datex viewer (`docs/datex/`) rendering the published dataset. datex is a viewer component of the application, not the application itself.

## Vision

The SM2 temperature monitoring application stays functional, sustainable, and continuously improved: every workflow component runs unattended and either succeeds or reports failure visibly; every component has current documentation (ontology concept plus implementation knowledge); improvements land as regular SubEpic stories rather than ad-hoc fixes.

Goals:

- keep the pipeline operational through the overheating seasons - the complaint case needs continuous evidence
- keep the application maintainable by someone other than its author: documented, reproducible, testable
- grow the application through measured improvements (audit findings, usage-driven proposals)

Non-goals:

- evidence interpretation (window selection, ČSN 730540-2 argumentation, expert replies) - owned by the parent Epic
- publication policy and licensing decisions - owned by the parent Epic

First direction (Human-set, 2026-10-08): a full audit of the whole application and its documentation, ontology and implementation, as the first SubEpic story (DWH-SM2-APP-0001).

## Scope

Application machinery of the SM2 monitoring pipeline: GitHub Actions workflows and their orchestration sequence, ingest and maintenance scripts (`scripts/`), the dbt project (`models/`, `dbt_project.yml`, `seeds/`), InfluxDB organization and bucket layout, the analysis toolkit (`analysis/`), public dataset publication, and the datex viewer (`docs/datex/`). Structural and operational concerns of the application - not the evidentiary content of the complaint case.

## Structure

| Folder | Content |
|--------|---------|
| `story/` | Stories under the `DWH-SM2-APP-` prefix; this file is the index |
| `implementation/` | Application implementation knowledge (audit findings, runbooks) |
| `ontology/` | Application concepts (pipeline stages, components) |
| `_generated/` | CLI-generated exports |

One story active: DWH-SM2-APP-0001 (full application audit, the Human-set first story).

## Related

- [DWH-SM2](DWH-SM2) - Parent Epic
- [ontology-subepic-blueprint](ontology-subepic-blueprint) - SubEpic concept definition
- [DWH-SM2-SubEpics](DWH-SM2-SubEpics) - Generated SubEpic overview
