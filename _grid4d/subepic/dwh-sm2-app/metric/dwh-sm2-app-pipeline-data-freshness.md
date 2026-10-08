# Pipeline Data Freshness

> Hours since the last commit touching the public parquet - the cross-check that catches green-but-dead pipelines.

**Status:** active
**Category:** Pipeline
**Sensor:** `scripts/pipeline_health.py` (epic-owned, DWH-SM2-APP-0006); source = GitHub commits API for `docs/datex/sm2_public_dataset.parquet` (bot heartbeat)
**Projection:** none — `data_freshness_h` / `data_state` in the reading JSON; second segment of the `--status` line
**Threshold:** ok ≤ 48 h, critical > 48 h (the dataset is committed daily; one missed day is the tolerance)

## Definition

What counts: age, in hours, of the most recent commit touching `docs/datex/sm2_public_dataset.parquet` (the daily `chore: update sm2_public_dataset.parquet for Data Explorer` bot commit). In historical windows (`--until`) the commits query is bounded to the window end so the reading reflects what was knowable then.

Where it renders: the `data_freshness_h` / `data_state` fields of the reading JSON.

**Why it is the load-bearing signal:** this is the only metric that caught the dead period. At 2026-10-06T23:59:59Z the reading shows `data_freshness_h: 449.6 (critical)` — no dataset commit since 2026-09-18 — while [action freshness](dwh-sm2-app-pipeline-action-freshness) read `ok` the whole time (publish ran green daily with an empty selection). Action axes verify the runner, not the product; the data axis verifies the product.

**Proxy note:** commit timestamp stands in for the parquet's latest `Date` value (would require local parquet read, e.g. pyarrow). The bot writes the parquet in the same run it commits it, so the proxy lags at most one run.
