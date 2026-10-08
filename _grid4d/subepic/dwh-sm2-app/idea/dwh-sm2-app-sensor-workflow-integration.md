# Sensor Workflow Integration

> Let the publish workflow append the daily pipeline-health reading itself - automated measurement without notification (still Sensor, not nervous system).

**Status:** candidate
**Origin:** DWH-SM2-APP-0006 (2026-10-08)

## Proposal

Today `scripts/pipeline_health.py` runs on demand (activity-aligned by design). The natural next step inside the **Sensor** scope: a small step in `publish_public_dataset.yml` (after the bot commit) runs the sensor with `--json sensor_readings/pipeline-health/latest.json` and commits it with the same bot commit. Readings become daily, automatic, and public - still zero notification, zero chaining.

**Why it belongs to the Sensor principle:** it only automates the existing measurement; no thresholds trip actions. The nervous-system story later decides what (if anything) reacts to the readings.

## Considerations

- The reading's `action_freshness` will read ~0 h measured inside the run itself - fine (it measures the run's own success); the data axis (parquet commit just made) is the interesting half.
- Requires the workflow job to have `gh` or unauthenticated API access (public repo - unauth works, but CI runners' IP pool shares the 60/h limit; `gh` with the checkout token is safer).
- Alternative if the evolucean pluggable-sensor path lands first (see issue `dwh-sm2-app-epic-sensor-readings-path-missing`): point the same step at the shared store instead of a committed file.
