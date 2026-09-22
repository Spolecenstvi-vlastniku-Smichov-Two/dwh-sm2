# DWH-SM2

> SM2 building data warehouse - sensor evidence base for the overheating complaint of the apartment building (ČSN 730540-2)

**Type:** Epic
**Inherits:** none (root)
**Remote:** https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2.git
**Branch:** main
**Merge:** true
**Release:** true
**GitOperations:** true
**SnapshotOnComplete:** true
**StoryHistoryKeep:** 2
**StoryPattern:** story-pattern-default
**GitHubAccount:** Spolecenstvi-vlastniku-Smichov-Two
**StoryPrefix:** DWH-SM2-

## Overview

This Epic owns the SM2 Data Warehouse: the automated ETL pipeline turning raw building sensor data into evidence-grade datasets. Pipeline stages: Google Drive annotated CSVs → InfluxDB 2.7 (ingest, hourly aggregation) → dbt + DuckDB transformation (location mapping, fact tables for ventilation, indoor temperature, indoor humidity) → public dataset publication (CSV.gz + Parquet, CC BY 4.0). Orchestration runs on GitHub Actions in a strict three-step sequence (Refresh → InfluxImportNormalize → Publish Public Dataset). The Epic also owns the knowledge plugin (`_grid4d/`) covering the measurement, evidence and complaint-tracking knowledge of the SM2 overheating case.

## Vision

Achieve a successful formal complaint (reklamace) regarding the chronic overheating of the SM2 apartment building (Smíchov Two, Prague, developer Sekyra Group), by making the defect objectively measurable and publicly verifiable.

Background: the building was designed with mechanical cooling for all apartments; at final approval the design changed — cooling units were relocated to the basement and cooling limited to top-floor apartments, and the compensating redesign of shading and ventilation was never done. Roughly 180 apartments (floors 2–5) regularly exceed the 27 °C limit of ČSN 730540-2 for rooms without mechanical cooling; the developer has not acknowledged overheating as a defect and has no thermal-stability calculation.

The Epic serves that goal through three evidentiary functions: (1) documenting the extent of overheating objectively via continuous measurements (heat-recovery system data since Nov 2023, dedicated hallway and basement sensors since 2025), (2) providing transparent, reproducible data for technical audits and negotiations (public dataset, independent analyses), (3) supporting residents' technical proposals for remediation.

External references: [blog Horko v SM2](https://horkovsm2.blogspot.com/), [project wiki](https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2/wiki), [public data explorer](https://spolecenstvi-vlastniku-smichov-two.github.io/dwh-sm2/datex/).

## Related

- [ontology-epic-blueprint](ontology-epic-blueprint) - Epic concept definition

---
