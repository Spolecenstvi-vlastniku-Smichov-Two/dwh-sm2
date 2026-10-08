# DWH-SM2-APP-0006: Measure pipeline health with a sensor feeding the knowledge system

> Measure pipeline health with a sensor feeding the knowledge system

**Type:** default
**Epic:** [DWH-SM2-APP](../DWH-SM2-APP)
**Status:** in_progress
**Blueprint:** [implementation-story-blueprint](implementation-story-blueprint)

## Goal

Measure pipeline health with a sensor feeding the knowledge system

First Play-phase story per [plug-and-play-epic-integration](evolucean:ontology-plug-and-play-epic-integration-blueprint) (cross-epic): the Plug is complete (audit closed at 0004/0005); this story starts the Play at principle 1 — Sensor. Today pipeline health is discoverable only by manual log forensics; a six-day-dead pipeline was invisible. After this story, pipeline health is measured deterministically and stored as readings in the knowledge system. **This story measures only — no notifications, no chaining, no self-heal** (that is the next story: nervous system).

## Requirements

### R1: Metric definitions in the Epic's own knowledge

Health metrics defined as knowledge documents in dwh-sm2 `_grid4d/` (own DNA, per the isolation rule): action freshness (hours since last successful publish run), last-N run outcomes per monitored workflow (publish/refresh, influx import), data freshness cross-check (latest `Date` in `sm2_public_dataset.parquet` vs today), guard signal (content-only fallback `::warning::` fired).

**Acceptance Criterion:** Metric documents exist in the Epic's `_grid4d/metric/` (or the epic's declared metric location) with semantics and thresholds; zero evolucean-side changes.

### R2: Deterministic measuring script as an Epic artifact

A script (e.g. `scripts/pipeline_health.py`) reads GitHub Actions workflow runs via API (public repo — unauthenticated read) and the parquet latest Date, and emits a small JSON reading per run.

**Acceptance Criterion:** Script runs locally on the personal machine, no secrets required, produces the defined readings deterministically.

### R3: Readings land in the evolucean sensor infrastructure

Readings are stored through the existing CLI sensor-reading path (namespaced `epic=dwh-sm2`), using existing instruments only — no evolucean core edits. If an instrument gap appears, log it as an issue for an EVOLUCEAN story and continue with what exists.

**Acceptance Criterion:** A stored reading is queryable via the CLI after running the sensor; no commits to evolucean made by this story.

### R4: Minimal read-back surface

The reading is visible without forensics — at least one queryable surface (CLI query / projection row) a Player can check in one step.

**Acceptance Criterion:** Demonstrated one-step read-back of the latest health reading.

### R5: Historical validation

Sensor validated against known history: the period when the pipeline was dead (last week, pre-v0.0004.1.0002.00 recovery) must show as stale/failed in a retrospective reading.

**Acceptance Criterion:** Retrospective reading for the dead period reflects staleness; documented in the story.

### R6: Story tests

`-tests.md` verifies the script output contract, the metric documents' existence, and the read-back path; all pass.

**Acceptance Criterion:** All tests PASS; yaml parses.

## Notes

Created: 2026-10-08. Design agreed with Human 2026-10-08 (Sensor before nervous system; activity-aligned — measurement on demand / at sync, no always-on daemon). Isolation rule (Human 2026-10-08): evolucean must stay stable without this epic — definitions and script are dwh-sm2 DNA, evolucean provides namespaced transport only; instrument gaps travel as issues, never as edits.

Parked after minting: executed after EVOLUCEAN-0474 (blueprint amendment) per Human's ordering choice.
