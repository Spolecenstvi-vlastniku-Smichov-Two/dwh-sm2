# DWH-SM2-APP-0004-tests

> Test definition for DWH-SM2-APP-0004 with one test per requirement.

## Design

README-facts pinning: R1 pins the runbook baseline refresh (content-only guard row),
R2 pins every repaired README claim plus the resolved drift issue, R3 pins the datex
documentation deliverables, R4 pins cross-file drift guards (workflow files carry no
push trigger; seed values match the README text). All commands are instant greps over
the worktree.

## Definition

```yaml
tests:
  - name: R1_runbook_refresh_guard
    description: Runbook refresh inventory row mentions the content-only upload guard with full-build fallback
    command: grep -q 'content-only upload guard' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md
    expect:
      exit_code: 0
  - name: R2_readme_daily_publish_cron
    description: README carries the real daily publish cron 30 1 * * *
    command: test "$(grep -c '30 1 \* \* \*' README.md)" -ge 1
    expect:
      exit_code: 0
  - name: R2_readme_no_weekly_cron
    description: weekly cron drift string 10 2 * * 6 is gone from README
    command: test -z "$(grep '10 2 \* \* 6' README.md)"
    expect:
      exit_code: 0
  - name: R2_readme_no_push_trigger_claims
    description: no workflow trigger block in README claims a push trigger
    command: test -z "$(grep '^- Push to .main. branch' README.md)"
    expect:
      exit_code: 0
  - name: R2_readme_no_v22_label
    description: indoor merge script is not labeled v2.2 anymore
    command: test -z "$(grep '(v2.2)' README.md)"
    expect:
      exit_code: 0
  - name: R2_readme_ventilation_attribution
    description: ventilation merge is attributed to inline csvkit in refresh.yml
    command: grep -q 'inline csvkit bash' README.md
    expect:
      exit_code: 0
  - name: R2_readme_single_refresh_section
    description: README documents the Refresh workflow exactly once
    command: test "$(grep -c '^### Refresh Workflow' README.md)" -eq 1
    expect:
      exit_code: 0
  - name: R2_readme_runbook_pointer
    description: README points to the runbook as operational source of truth
    command: grep -q 'dwh-sm2-app-runbook.md' README.md
    expect:
      exit_code: 0
  - name: R2_issue_resolved
    description: readme-docs-drift issue flipped to resolved
    command: grep -qF '**Status:** resolved' _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-readme-docs-drift.md
    expect:
      exit_code: 0
  - name: R3_datex_readme_exists
    description: docs/datex/README.md exists
    command: test -f docs/datex/README.md
    expect:
      exit_code: 0
  - name: R3_datex_issue_exists
    description: the config metrics duplication issue file exists
    command: test -f _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-datex-config-metrics-duplicated.md
    expect:
      exit_code: 0
  - name: R3_runbook_datex_coverage
    description: runbook coverage map links the new datex issue
    command: grep -q 'dwh-sm2-app-datex-config-metrics-duplicated' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md
    expect:
      exit_code: 0
  - name: R4_no_push_triggers_in_workflows
    description: no workflow file declares a push trigger (README must never re-claim one)
    command: test -z "$(grep -r 'push:' .github/workflows/)"
    expect:
      exit_code: 0
  - name: R4_readme_seed_history
    description: README seed example carries the real ThermoPro history value 2
    command: grep -qF 'fact_indoor_humidity.csv,ThermoPro,2' README.md
    expect:
      exit_code: 0
```

## Execution

| Test | Result |
|------|--------|
| R1_runbook_refresh_guard | PASS |
| R2_readme_daily_publish_cron | PASS |
| R2_readme_no_weekly_cron | PASS |
| R2_readme_no_push_trigger_claims | PASS |
| R2_readme_no_v22_label | PASS |
| R2_readme_ventilation_attribution | PASS |
| R2_readme_single_refresh_section | PASS |
| R2_readme_runbook_pointer | PASS |
| R2_issue_resolved | PASS |
| R3_datex_readme_exists | PASS |
| R3_datex_issue_exists | PASS |
| R3_runbook_datex_coverage | PASS |
| R4_no_push_triggers_in_workflows | PASS |
| R4_readme_seed_history | PASS |
