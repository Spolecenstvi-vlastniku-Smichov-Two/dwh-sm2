# DWH-SM2-APP-0001: Full application audit - the whole application and its documentation, ontology and implementation

> Full application audit - the whole application and its documentation, ontology and implementation

**Type:** default
**Epic:** [DWH-SM2-APP](../DWH-SM2-APP)
**Status:** in_progress
**Blueprint:** [implementation-story-blueprint](implementation-story-blueprint)

## Goal

Establish a measured baseline for the SM2 temperature monitoring application (Human-set first story of [DWH-SM2-APP](../DWH-SM2-APP)): audit the whole application - the complete GitHub workflow and every component it orchestrates - and its documentation on both knowledge axes, ontology and implementation. The audit measures and documents; fixes belong to follow-up stories chosen from its findings.

## Requirements

### R1: Component inventory

Every component of the application is enumerated with its current state: GitHub Actions workflows and their orchestration sequence, ingest and maintenance scripts (`scripts/`), the dbt project (`models/`, `dbt_project.yml`, `profiles.yml`, `seeds/`), InfluxDB organization and buckets, the analysis toolkit (`analysis/`), public dataset publication, and the datex viewer (`docs/datex/`).

**Acceptance Criterion:** the inventory lists each component with location, purpose, and state (tracked/untracked, operational status, last relevant change); nothing in the repo that the workflow executes is missing from it.

### R2: Pipeline functionality audit

The orchestration chain (Refresh → InfluxImportNormalize → Publish Public Dataset) is verified against the actual workflow definitions: triggers, sequencing, dependencies, failure behavior, and secrets/tokens each stage needs.

**Acceptance Criterion:** each workflow stage is documented with its trigger, inputs, outputs, and known failure modes; sequencing violations or dead stages are reported as findings.

### R3: Documentation audit

Existing documentation (README, `docs/`, GitHub wiki, `_grid4d/` knowledge, the ARCHITECTURE drafts pending deletion in the main-tree drift) is mapped against the component inventory: what is documented, where, and how current it is.

**Acceptance Criterion:** a documentation-coverage mapping exists (component → docs); gaps, stale docs, and undocumented components are named; the main-tree drift state is recorded as a finding (documented, not fixed here).

### R4: Ontology layer founded

The SubEpic's `ontology/` folder opens with concepts for the application's structure: the application as a whole (workflow + components), the pipeline stages, and the component kinds.

**Acceptance Criterion:** `_grid4d/subepic/dwh-sm2-app/ontology/` contains blueprint-grade concept documents (`dwh-sm2-app-*` naming) covering application, pipeline, and components, following [ontology-epic-blueprint](ontology-epic-blueprint) conventions.

### R5: Implementation knowledge founded

The SubEpic's `implementation/` folder opens with a runbook capturing how the application actually runs: the operational sequence, what can break where, and how to verify health.

**Acceptance Criterion:** `_grid4d/subepic/dwh-sm2-app/implementation/` contains an application runbook grounded in the audit findings (not aspirational content).

### R6: Findings captured as issues

Every problem the audit surfaces (broken links, stale docs, drift, sequencing gaps, undocumented failure modes, knowledge-system quirks) is captured as an issue document in the parent Epic's `issue/` pool or the SubEpic's own `issue/` folder, per [ontology-issue-blueprint](ontology-issue-blueprint).

**Acceptance Criterion:** each audit finding is either fixed trivially in-story or persists as an issue document with symptoms and at least a sketch of root cause; no finding lives only in the story prose.

### R7: Live GitHub issue analysis

The audit's static findings are confronted with the live repository: current GitHub Actions runs and failures are pulled via `gh api` and diagnosed to root cause, and the analysis is folded back into the issue documents as dated occurrences with run identifiers.

**Acceptance Criterion:** at least one live failing run is diagnosed (failing step, why it fails, blast radius on downstream stages) from measured evidence, and the relevant issue documents and runbook carry the occurrence.

## Notes

Created: 2026-10-08. Human assignment (2026-10-08): "celkový audit celé aplikace a její dokumentace - ontologie i implementace". R7 added mid-story at Human request: analyze live GitHub Actions failures, not just the static tree. The application is the entire GitHub workflow including all its components (datex is only a viewer). The uncommitted main-tree drift (deleted ARCHITECTURE drafts, regenerated analysis outputs, touched DWH-SM2-0003 knowledge map) is Human-deferred to a later story - this audit documents its state as a finding.

## Related

- [DWH-SM2-APP](../DWH-SM2-APP) - SubEpic identity
- [DWH-SM2-0004](DWH-SM2-0004) - Founding story of this SubEpic
- [DWH-SM2](DWH-SM2) - Parent Epic
