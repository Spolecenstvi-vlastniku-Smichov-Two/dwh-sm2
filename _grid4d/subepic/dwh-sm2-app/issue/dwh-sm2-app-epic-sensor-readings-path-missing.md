# Epic Sensor Readings Path Missing

> External epics cannot feed the evolucean readings store without evolucean-side code — the isolation rule forces epic-side readings instead.

**Status:** open (cross-epic mirror — the fix belongs to EVOLUCEAN)
**Found in:** DWH-SM2-APP-0006 (2026-10-08)

## Problem

The Play principle 1 (Sensor) wants pipeline-health readings stored through the shared sensor infrastructure. The evolucean CLI offers two reading paths and both are evolucean DNA:

- `sensor read` — internal sensors are Python modules inside the CLI (`sensors_*.py`, registry per [implementation-cli-sensors-blueprint](evolucean:implementation-cli-sensors-blueprint));
- `external sense` — platform adapters are likewise CLI-side modules (Gmail/Drive/Classroom today).

An external epic cannot register either without writing into evolucean code — which the disconnection-stability rule (evolucean ontology `ontology-plug-and-play-epic-integration-blueprint`, Rule 7, EVOLUCEAN-0474) forbids: other installations run evolucean without this epic present.

## Consequence

dwh-sm2 readings live epic-side: `scripts/pipeline_health.py` emits JSON committed to `sensor_readings/pipeline-health/` in this repo, read back via `--status`. Divergence from the shared store: no gradient roll-ups, no karma integration, no `query sql` over these readings.

## Solution Direction

An EVOLUCEAN story adds an **epic-pluggable sensor path**: epic-owned adapters registered via epic configuration (not CLI code), writing namespaced readings (`epic=<name>`) into the shared DuckDB through a validated schema. Requirements: registration is declarative (config/identity-file declared, `doctor`-checked); absence of any epic's sensors degrades to zero readings (disconnection stability); the path shares the hardened capability-parser lessons (see evolucean-side issue `verify-code-capability-scanner-legacy-regex`, captured by the peer session in EVOLUCEAN-0473's aftermath — same family: config-declared things must be validated, not regex-scraped).

## Notes

- MQTT-topic ingest was considered and deferred: the data layer is activity-aligned (sleep = pause by design); a sleeping broker would drop on-demand readings.
- This mirror follows the dwh-sm2-app precedent of filing cross-epic defects here with the fix ownership named (see `dwh-sm2-app-story-complete-archive-push-nonff`).
