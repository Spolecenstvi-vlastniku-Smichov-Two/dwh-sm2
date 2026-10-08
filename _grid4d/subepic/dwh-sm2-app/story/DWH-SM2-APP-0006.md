# DWH-SM2-APP-0006: Measure pipeline health with a sensor feeding the knowledge system

> Measure pipeline health with a sensor feeding the knowledge system

**Type:** default
**Epic:** [DWH-SM2-APP](../DWH-SM2-APP)
**Status:** in_progress
**Blueprint:** [implementation-story-blueprint](implementation-story-blueprint)

## Goal

Measure pipeline health with a sensor feeding the knowledge system

First Play-phase story per [plug-and-play-epic-integration](evolucean:ontology-plug-and-play-epic-integration-blueprint) (cross-epic): the Plug is complete (audit closed at 0004/0005); this story starts the Play at principle 1 — Sensor. Today pipeline health is discoverable only by manual log forensics; a six-day-dead pipeline was invisible. After this story, pipeline health is measured deterministically and stored as readings. **This story measures only — no notifications, no chaining, no self-heal** (that is the next story: nervous system).

## Requirements

### R1: Metric definitions in the Epic's own knowledge ✅

Health metrics defined as knowledge documents in dwh-sm2 `_grid4d/` (own DNA, per the isolation rule): action freshness (hours since last successful publish run), last-N run outcomes per monitored workflow (publish/refresh, influx import), data freshness cross-check (latest parquet bot-commit vs now), guard signal (content-only fallback `::warning::` fired).

**Acceptance Criterion:** Metric documents exist in the Epic's `_grid4d/metric/` (or the epic's declared metric location) with semantics and thresholds; zero evolucean-side changes.

**Result:** three metric docs in `subepic/dwh-sm2-app/metric/` (action-freshness, run-outcomes incl. data cross-check rationale, data-freshness) with Status/Category/Sensor/Threshold. The guard sub-signal is explicitly **deferred** to the nervous-system story (needs jobs/annotations API wiring; reading carries `guard_fired: null`). Zero evolucean-side changes.

### R2: Deterministic measuring script as an Epic artifact ✅

A script (e.g. `scripts/pipeline_health.py`) reads GitHub Actions workflow runs via API (public repo — unauthenticated read) and the parquet latest Date, and emits a small JSON reading per run.

**Acceptance Criterion:** Script runs locally on the personal machine, no secrets required, produces the defined readings deterministically.

**Result:** `scripts/pipeline_health.py` (stdlib only): `gh api` transport with unauthenticated fallback (the shared IP exhausted the unauth 60/h limit during development — authenticated path is the default when `gh` is present; no secrets in code or output), `--status` / `--json` / `--since/--until` historical windows / `--fixture`+`--at` fully deterministic offline mode. Parquet freshness uses the bot-commit timestamp (proxy documented in the metric doc — same-run commit, ≤ 1 run lag).

### R3: Readings land in the evolucean sensor infrastructure ✅

Readings are stored through the existing CLI sensor-reading path (namespaced `epic=dwh-sm2`), using existing instruments only — no evolucean core edits. If an instrument gap appears, log it as an issue for an EVOLUCEAN story and continue with what exists.

**Acceptance Criterion:** A stored reading is queryable via the CLI after running the sensor; no commits to evolucean made by this story.

**Result:** the instrument gap branch fired: both CLI reading paths (`sensor read` modules, `external sense` adapters) are evolucean-side code, unreachable for an external epic under the disconnection-stability rule. Readings therefore live epic-side (`sensor_readings/pipeline-health/*.json`, committed) — logged as [dwh-sm2-app-epic-sensor-readings-path-missing](../issue/dwh-sm2-app-epic-sensor-readings-path-missing) with the EVOLUCEAN-side solution direction (declarative epic-pluggable sensor path). Zero commits to evolucean by this story.

### R4: Minimal read-back surface ✅

The reading is visible without forensics — at least one queryable surface (CLI query / projection row) a Player can check in one step.

**Acceptance Criterion:** Demonstrated one-step read-back of the latest health reading.

**Result:** `python3 scripts/pipeline_health.py --status` → `publish last success: 2.2h ago (ok) | parquet last commit: 2.2h ago (ok) | non-success runs in window: 6` (live, 2026-10-08). Runbook Health Verification item 1 now points at it; README documents usage.

### R5: Historical validation ✅

Sensor validated against known history: the period when the pipeline was dead (last week, pre-v0.0004.1.0002.00 recovery) must show as stale/failed in a retrospective reading.

**Acceptance Criterion:** Retrospective reading for the dead period reflects staleness; documented in the story.

**Result:** window 2026-09-20 → 10-06 (`--at 2026-10-06T23:59:59Z`, artifact `dead-period-2026-09-20_10-06.json`): **data_freshness 449.6 h (critical)** — no dataset commit since 2026-09-18 — while publish concluded `success` on every single run in the window and refresh shows 4 consecutive `failure`s before recovery. The reading surfaces exactly the previously-invisible condition, and demonstrates why the data axis (not the action axis) is load-bearing. Fixture `fixture-dead-period.json` replays the window deterministically.

### R6: Story tests ✅

`-tests.md` verifies the script output contract, the metric documents' existence, and the read-back path; all pass.

**Acceptance Criterion:** All tests PASS; yaml parses.

**Result:** six tests R1-R6, all PASS (fixture-based, deterministic, offline).

### R_docs: End-to-end documentation ✅

All changes documented from ontology to code docstrings.

**Acceptance Criterion:** Changes reflected in ontology, implementation blueprints, CLI blueprints, and code docstrings.

Metric docs + runbook (inventory row, Health Verification item) + README `scripts/pipeline_health.py` section + module docstring. The evolucean-side blueprint example already names this story (EVOLUCEAN-0474).

### R_issues: Log all issues and ideas ✅

All problems, bugs, and ideas encountered during story logged to `_grid4d/issue/`.

**Acceptance Criterion:** No silent failures - every issue either fixed or documented.

[dwh-sm2-app-epic-sensor-readings-path-missing](../issue/dwh-sm2-app-epic-sensor-readings-path-missing) (open, cross-epic). In-story bug fixed during development: historical-window query filter was not URL-encoded (GitHub ignored the raw `>=` range and returned current runs — caught by comparing window output to live output before accepting the reading).

## Acceptance Criteria

- [x] R1: metric definitions
- [x] R2: measuring script
- [x] R3: readings path (instrument-gap branch, issue logged)
- [x] R4: read-back surface
- [x] R5: historical validation
- [x] R6: tests pass
- [x] R_docs: Documentation complete
- [x] R_issues: Issues logged

## Notes

Created: 2026-10-08. Design agreed with Human 2026-10-08 (Sensor before nervous system; activity-aligned — measurement on demand / at sync, no always-on daemon). Isolation rule (Human 2026-10-08): evolucean must stay stable without this epic — definitions and script are dwh-sm2 DNA, evolucean provides namespaced transport only; instrument gaps travel as issues, never as edits.

Parked after minting: executed after EVOLUCEAN-0474 (blueprint amendment) per Human's ordering choice.

Next story (nervous system, per the blueprint's principle order): notification/chaining on top of these readings; also picks up the deferred guard sub-signal and, if the EVOLUCEAN pluggable-sensor path lands, migrates readings into the shared store.
