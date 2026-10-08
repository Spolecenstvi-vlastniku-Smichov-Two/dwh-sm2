# DWH-SM2-APP-0001-tests

> Test definition for DWH-SM2-APP-0001 with one test per requirement.

## Design

Structural verification of the audit deliverables: the knowledge documents the story
founds (ontology blueprints, runbook, issue documents) are checked for existence and
required content. The audit facts themselves (cron expressions, dead config lines) are
carried in the documents; the tests pin the documents, not the audited repository - a
fact test belongs to the fix story that changes the fact. Tests are worktree-root
relative, POSIX sh.

## Definition

```yaml
tests:
  - name: R1_component_inventory_persists
    description: runbook carries the audit component inventory covering all three workflows and the scripts
    command: |
      test -f _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md &&
      grep -q 'refresh.yml' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md &&
      grep -q 'influx_import_workflow.yml' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md &&
      grep -q 'publish_public_dataset.yml' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md &&
      grep -q 'build_public_dataset.py' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md
    expect:
      exit_code: 0
  - name: R2_pipeline_stages_documented
    description: pipeline blueprint documents the three stages with triggers and failure behavior
    command: |
      test -f _grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-pipeline-blueprint.md &&
      grep -q 'Refresh' _grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-pipeline-blueprint.md &&
      grep -q 'InfluxImportNormalize' _grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-pipeline-blueprint.md &&
      grep -q 'Publish Public Dataset' _grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-pipeline-blueprint.md &&
      grep -q 'cron stagger' _grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-pipeline-blueprint.md
    expect:
      exit_code: 0
  - name: R3_docs_coverage_map_exists
    description: runbook maps documentation to components including the drift finding
    command: |
      grep -q 'Documentation Coverage Map' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md &&
      grep -q 'ARCHITECTURE_HYBRID_PLATFORM.md' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md &&
      grep -q 'README.md' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md
    expect:
      exit_code: 0
  - name: R4_ontology_blueprints_founded
    description: both application ontology blueprints exist with the required sections
    command: |
      test -f _grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-application-blueprint.md &&
      grep -q '^## Overview' _grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-application-blueprint.md &&
      grep -q '^## Rules' _grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-application-blueprint.md &&
      grep -q '^## Structure' _grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-application-blueprint.md &&
      grep -q '^## Example' _grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-application-blueprint.md
    expect:
      exit_code: 0
  - name: R5_runbook_founded
    description: runbook exists with failure modes and health verification grounded in the audit
    command: |
      grep -q '^## Health Verification' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md &&
      grep -q '^## Known Failure Modes' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md &&
      grep -q 'workflow_dispatch' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md
    expect:
      exit_code: 0
  - name: R6_findings_persist_as_issues
    description: all six audit findings persist as open issue documents in the subepic issue folder
    command: |
      test -f _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-pipeline-unsequenced.md &&
      test -f _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-readme-docs-drift.md &&
      test -f _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-stale-artifacts-tracked.md &&
      test -f _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-dbt-config-dead-entries.md &&
      test -f _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-dependencies-unpinned.md &&
      test -f _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-main-tree-drift.md &&
      grep -rlF '**Status:** open' _grid4d/subepic/dwh-sm2-app/issue/ | wc -l | grep -q '^ *6$'
    expect:
      exit_code: 0
  - name: R7_live_failure_analyzed
    description: live GitHub failure analysis is folded into issue documents and runbook with run identifiers
    command: |
      grep -qF '37723784092' _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-dependencies-unpinned.md &&
      grep -q '37091726016' _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-pipeline-unsequenced.md &&
      grep -q 'sqlfluff fix' _grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_component_inventory_persists | ✅ | 2026-10-08 |
| R2_pipeline_stages_documented | ✅ | 2026-10-08 |
| R3_docs_coverage_map_exists | ✅ | 2026-10-08 |
| R4_ontology_blueprints_founded | ✅ | 2026-10-08 |
| R5_runbook_founded | ✅ | 2026-10-08 |
| R6_findings_persist_as_issues | ✅ | 2026-10-08 |
| R7_live_failure_analyzed | ✅ | 2026-10-08 |

## Related

- [DWH-SM2-APP-0001](DWH-SM2-APP-0001) - Parent story

---
## _behavior

validation:
  required_sections: [Design, Definition, Execution]
  definition_format: yaml_code_block
