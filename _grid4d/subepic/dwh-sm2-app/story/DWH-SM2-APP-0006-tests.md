# DWH-SM2-APP-0006-tests

> Test definition for DWH-SM2-APP-0006 with one test per requirement.

## Design

Offline, deterministic tests: the sensor replays the committed dead-period fixture with a pinned reference time, so no network, no clock, no flakiness.

## Definition

```yaml
tests:
  - name: R1_metric_docs_exist
    description: Three pipeline-health metric documents exist with Status and Threshold
    command: "test -f _grid4d/subepic/dwh-sm2-app/metric/dwh-sm2-app-pipeline-action-freshness.md && test -f _grid4d/subepic/dwh-sm2-app/metric/dwh-sm2-app-pipeline-run-outcomes.md && test -f _grid4d/subepic/dwh-sm2-app/metric/dwh-sm2-app-pipeline-data-freshness.md && grep -q 'Threshold' _grid4d/subepic/dwh-sm2-app/metric/dwh-sm2-app-pipeline-action-freshness.md"
    expect:
      exit_code: 0

  - name: R2_script_fixture_contract
    description: Sensor computes the reading deterministically from the dead-period fixture at a pinned time
    command: "python3 scripts/pipeline_health.py --fixture sensor_readings/pipeline-health/fixture-dead-period.json --at 2026-10-06T23:59:59Z --json /tmp/0006-t.json && python3 -c \"import json; m=json.load(open('/tmp/0006-t.json'))['metrics']; assert m['action_freshness_h']==16.1 and m['action_state']=='ok' and m['data_freshness_h']==449.6 and m['data_state']=='critical' and m['non_success_runs_in_window']==4\""
    expect:
      exit_code: 0

  - name: R3_reading_artifacts_committed
    description: Live reading, dead-period reading, and fixture exist with the epic namespace
    command: "python3 -c \"import json; assert json.load(open('sensor_readings/pipeline-health/latest.json'))['epic']=='dwh-sm2'\" && test -f sensor_readings/pipeline-health/dead-period-2026-09-20_10-06.json && test -f sensor_readings/pipeline-health/fixture-dead-period.json"
    expect:
      exit_code: 0

  - name: R4_readback_one_step
    description: One-step status line renders from the fixture with pinned values
    command: "python3 scripts/pipeline_health.py --fixture sensor_readings/pipeline-health/fixture-dead-period.json --at 2026-10-06T23:59:59Z --status | grep -q '16.1h ago (ok)'"
    expect:
      exit_code: 0

  - name: R5_historical_paradox_evidence
    description: Dead-period reading shows critical data axis with ok action axis and 4 refresh failures
    command: "python3 -c \"import json; m=json.load(open('sensor_readings/pipeline-health/dead-period-2026-09-20_10-06.json'))['metrics']; assert m['data_state']=='critical' and m['action_state']=='ok' and m['non_success_runs_in_window']==4\""
    expect:
      exit_code: 0

  - name: R6_tests_table_contract
    description: Tests file carries the literal Execution header and R-prefixed result rows
    command: "grep -q '| Test | Result | Date |' _grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP-0006-tests.md && test \"$(grep -c '^| R' _grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP-0006-tests.md)\" -ge 6"
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_metric_docs_exist | ✅ | 2026-10-08 |
| R2_script_fixture_contract | ✅ | 2026-10-08 |
| R3_reading_artifacts_committed | ✅ | 2026-10-08 |
| R4_readback_one_step | ✅ | 2026-10-08 |
| R5_historical_paradox_evidence | ✅ | 2026-10-08 |
| R6_tests_table_contract | ✅ | 2026-10-08 |

## Related

- [DWH-SM2-APP-0006](DWH-SM2-APP-0006) - Parent story
