# Pipeline Run Outcomes

> Last-N conclusions per monitored workflow - failure visibility without log forensics.

**Status:** active
**Category:** Pipeline
**Sensor:** `scripts/pipeline_health.py` (epic-owned, DWH-SM2-APP-0006)
**Projection:** none — `run_outcomes` in the reading JSON; `non_success_runs_in_window` in the `--status` line
**Threshold:** informational per run; `non_success_runs_in_window > 0` in a healthy steady-state window warrants a look (no automatic gate)

## Definition

What counts: the last 5 `[created_at, conclusion]` pairs per monitored workflow — `publish` (publish_public_dataset.yml), `refresh` (refresh.yml), `influx` (influx_import_workflow.yml) — plus the count of non-success conclusions across the whole collected window (live default: latest 30 runs each; historical windows: `--since/--until`).

Where it renders: the `run_outcomes` and `non_success_runs_in_window` fields of the reading JSON.

**Deferred sub-signal — guard fired:** whether a run emitted the content-only fallback `::warning::` (v0.0004.1.0002.00) requires the jobs/annotations API wiring; reading carries `guard_fired: null` until the nervous-system story adds it. Tracked there, not here.

**Historical evidence (DWH-SM2-APP-0006, window 2026-09-20..10-06):** refresh shows 4 consecutive `failure` conclusions before recovery — previously visible only by opening the Actions UI; now a reading (`sensor_readings/pipeline-health/dead-period-2026-09-20_10-06.json`).
