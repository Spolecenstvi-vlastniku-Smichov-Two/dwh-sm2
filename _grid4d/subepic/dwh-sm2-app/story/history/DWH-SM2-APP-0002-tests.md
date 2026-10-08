# DWH-SM2-APP-0002-tests

> Test definition for DWH-SM2-APP-0002 with one test per requirement.

## Design

Structural verification of the workflow guard plus a behavioral rehearsal of the guard
logic itself. R1 pins the guard into `refresh.yml` (detection keyed to
`source_status:fresher+`, merge-rows gate, deliberate `exit 1`, `continue-on-error`
preserved, fallback step untouched). R2 rehearses the exact guard pipeline on synthetic
ANSI-colored warning lines cloned from the captured run logs (37756665551 incident,
37735598512 healthy) and asserts the four day-type outcomes. R3 and R4 pin the issue
document and the runbook health check. Tests are worktree-root relative, POSIX sh.

## Definition

```yaml
tests:
  - name: R1_guard_in_workflow
    description: refresh.yml carries the empty-selection guard with rows gate and preserved fallback wiring
    command: |
      grep -q 'dbt_selective_build.log' .github/workflows/refresh.yml &&
      grep -q 'source_status:fresher+.*does not match' .github/workflows/refresh.yml &&
      grep -q 'rows_indoor' .github/workflows/refresh.yml &&
      grep -q 'rows_vent' .github/workflows/refresh.yml &&
      grep -q 'exit 1' .github/workflows/refresh.yml &&
      grep -q 'continue-on-error: true' .github/workflows/refresh.yml &&
      grep -q 'result:error+ source_status:fresher+ --defer --state docs' .github/workflows/refresh.yml &&
      grep -q "steps.run_dbt_build.outcome != 'success'" .github/workflows/refresh.yml
    expect:
      exit_code: 0
  - name: R2_guard_day_type_matrix
    description: guard fires on incident and ventilation-only days, skips healthy and empty days
    command: |
      tmpd=$(mktemp -d)
      printf "06:27:44  \033[33mWARNING\033[0m]: The selection criterion 'source_status:fresher+' does not match any enabled nodes\n" > "$tmpd/incident.log"
      printf "06:05:01  \033[33mWARNING\033[0m]: The selection criterion 'result:error+' does not match any enabled nodes\n" > "$tmpd/healthy.log"
      guard() { sed 's/\x1b\[[0-9;]*m//g' "$1" | grep -q "source_status:fresher+.*does not match" && { [ "$2" -gt 1 ] || [ "$3" -gt 1 ]; }; }
      guard "$tmpd/incident.log" 500000 1 || { echo "incident day not caught"; exit 1; }
      guard "$tmpd/healthy.log" 500000 1 && { echo "healthy day false positive"; exit 1; }
      guard "$tmpd/incident.log" 1 1 && { echo "empty day not skipped"; exit 1; }
      guard "$tmpd/incident.log" 1 4000 || { echo "ventilation-only day not caught"; exit 1; }
      rm -rf "$tmpd"
    expect:
      exit_code: 0
  - name: R3_issue_captured
    description: silent-skip issue exists with affected and contrast run IDs
    command: |
      test -f _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-refresh-freshness-silent-skip.md &&
      grep -qF '**Status:** open' _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-refresh-freshness-silent-skip.md &&
      grep -q '37738331019' _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-refresh-freshness-silent-skip.md &&
      grep -q '37756665551' _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-refresh-freshness-silent-skip.md &&
      grep -q '37735598512' _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-refresh-freshness-silent-skip.md
    expect:
      exit_code: 0
  - name: R4_runbook_health_covers_silent_skip
    description: runbook health verification checks the fact upload actually happened and links the issue
    command: |
      grep -qF 'not found, skipping upload' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md &&
      grep -q 'dwh-sm2-app-refresh-freshness-silent-skip' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md &&
      grep -q 'falling back to full dbt build' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_guard_in_workflow | ✅ | 2026-10-08 |
| R2_guard_day_type_matrix | ✅ | 2026-10-08 |
| R3_issue_captured | ✅ | 2026-10-08 |
| R4_runbook_health_covers_silent_skip | ✅ | 2026-10-08 |

## Related

- [DWH-SM2-APP-0002](DWH-SM2-APP-0002) - Parent story

---
## _behavior

validation:
  required_sections: [Design, Definition, Execution]
  definition_format: yaml_code_block
