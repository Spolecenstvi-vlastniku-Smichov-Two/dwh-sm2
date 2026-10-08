# DWH-SM2-APP-0003-tests

> Test definition for DWH-SM2-APP-0003 with one test per requirement.

## Design

Structural verification of a capture story: every requirement pins a knowledge file
into the tree and asserts the content that makes the capture useful (status lines,
section headings, key facts, cross-links). R1 checks the resolved status and the
live-verification occurrence of the silent-skip issue. R2 and R6 check the two new
issues (echo pollution, Atrea export lag) for their full section sets and decisive
content. R3 and R7 check the two ideas. R4 asserts the no-duplicate rule as a
cross-reference from the plug-and-play idea to the pre-existing pipeline-unsequenced
issue. R5 asserts the promotion of transient story-0002 knowledge into the runbook
and pipeline blueprint. Tests are worktree-root relative, POSIX sh.

## Definition

```yaml
tests:
  - name: R1_issue_resolved_with_live_verification
    description: silent-skip issue marked resolved with the live-verification occurrence and run IDs
    command: |
      f=_grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-refresh-freshness-silent-skip.md
      test -f "$f" &&
      grep -qF '**Status:** resolved (v0.0004.1.0002.00' "$f" &&
      grep -q 'fix verified live' "$f" &&
      grep -q '37761728956' "$f" &&
      grep -q '37762967460' "$f" &&
      grep -q '10:22:42' "$f"
    expect:
      exit_code: 0
  - name: R2_echo_pollution_issue_captured
    description: actions-log echo-pollution issue exists with full section set and mechanism
    command: |
      f=_grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-actions-log-echo-pollution.md
      test -f "$f" &&
      grep -q '## Problem' "$f" &&
      grep -q '## Symptoms' "$f" &&
      grep -q '## Solution Direction' "$f" &&
      grep -q '## Occurrences' "$f" &&
      grep -q 'rclone' "$f" &&
      grep -q 'stats-one-line' "$f"
    expect:
      exit_code: 0
  - name: R3_fallback_annotation_ux_idea_captured
    description: fallback-annotation UX idea exists with context, proposal and value
    command: |
      f=_grid4d/subepic/dwh-sm2-app/idea/dwh-sm2-app-fallback-annotation-ux.md
      test -f "$f" &&
      grep -q '## Context' "$f" &&
      grep -q '## Proposal' "$f" &&
      grep -q '## Value' "$f" &&
      grep -q 'id: detect' "$f"
    expect:
      exit_code: 0
  - name: R4_no_duplicate_captures
    description: plug-and-play idea cross-references the pre-existing pipeline-unsequenced issue instead of duplicating it
    command: |
      grep -q 'dwh-sm2-app-pipeline-unsequenced' _grid4d/subepic/dwh-sm2-app/idea/dwh-sm2-app-plug-and-play-evolucean-integration.md &&
      test -f _grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-pipeline-unsequenced.md
    expect:
      exit_code: 0
  - name: R5_transient_knowledge_promoted
    description: runbook carries Data Guarantees and the worked recovery sequence; blueprint carries additivity and windowing rules
    command: |
      r=_grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md
      b=_grid4d/subepic/dwh-sm2-app/ontology/dwh-sm2-app-pipeline-blueprint.md
      grep -q '## Data Guarantees' "$r" &&
      grep -q 'append-only' "$r" &&
      grep -q '139023652' "$r" &&
      grep -q '177614384' "$r" &&
      grep -q '184554441' "$r" &&
      grep -q 'append-only' "$b" &&
      grep -q 'mapping_sources.csv' "$b" &&
      grep -q 'windowing is config-driven' "$b"
    expect:
      exit_code: 0
  - name: R6_atrea_export_lag_captured
    description: Atrea export-lag issue exists with location names, wall-time symptom and backfill recovery path
    command: |
      f=_grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-atrea-export-lag.md
      test -f "$f" &&
      grep -q 'sm2_01' "$f" &&
      grep -q '3PP-S7' "$f" &&
      grep -q 'months_to_process.json' "$f" &&
      grep -q 'v0.0004.1.0002.00' "$f" &&
      grep -q 'diagnostic trap' "$f"
    expect:
      exit_code: 0
  - name: R7_plug_and_play_idea_captured
    description: plug-and-play idea exists with gap table, unauthored-blueprint finding and phased proposal
    command: |
      f=_grid4d/subepic/dwh-sm2-app/idea/dwh-sm2-app-plug-and-play-evolucean-integration.md
      test -f "$f" &&
      grep -q 'plug-and-play-epic-integration' "$f" &&
      grep -q 'does not exist' "$f" &&
      grep -q 'Audit/documentation phase' "$f" &&
      grep -q 'Nervous system' "$f"
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_issue_resolved_with_live_verification | ✅ | 2026-10-08 |
| R2_echo_pollution_issue_captured | ✅ | 2026-10-08 |
| R3_fallback_annotation_ux_idea_captured | ✅ | 2026-10-08 |
| R4_no_duplicate_captures | ✅ | 2026-10-08 |
| R5_transient_knowledge_promoted | ✅ | 2026-10-08 |
| R6_atrea_export_lag_captured | ✅ | 2026-10-08 |
| R7_plug_and_play_idea_captured | ✅ | 2026-10-08 |

## Related

- [DWH-SM2-APP-0003](DWH-SM2-APP-0003) - Parent story

---
## _behavior

validation:
  required_sections: [Design, Definition, Execution]
  definition_format: yaml_code_block
