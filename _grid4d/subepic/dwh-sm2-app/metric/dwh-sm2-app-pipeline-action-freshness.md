# Pipeline Action Freshness

> Hours since the last successful publish workflow run - the heartbeat of the daily pipeline.

**Status:** active
**Category:** Pipeline
**Sensor:** `scripts/pipeline_health.py` (epic-owned, DWH-SM2-APP-0006; transport `gh api` with unauthenticated fallback)
**Projection:** none — one-step read-back via `python3 scripts/pipeline_health.py --status`; readings committed under `sensor_readings/pipeline-health/`
**Threshold:** ok ≤ 48 h (one missed daily `30 1 * * *` run tolerated), warning ≤ 72 h, critical > 72 h

## Definition

What counts: age, in hours, of the most recent `publish_public_dataset.yml` run with conclusion `success`, measured at reading time. The publish workflow is the pipeline heartbeat — it runs daily and is the only stage that writes the public parquet.

Where it renders: the `action_freshness_h` / `action_state` fields of the reading JSON and the first segment of the `--status` line.

**Known blind spot (why [data freshness](dwh-sm2-app-pipeline-data-freshness) exists):** a green run is not a productive run. During the dead period 2026-09-18 → 2026-10-05 publish succeeded daily while the `source_status:fresher+` guard selected nothing and no dataset commit happened — the action axis read `ok` the whole time. Action freshness alone cannot detect silent no-op success; the data-freshness cross-check is the load-bearing signal.
