# Apply evolucean principles to dwh-sm2 as a plug-and-play Epic

**Created:** 2026-10-08 (DWH-SM2-APP-0003, Human direction)

## Context

Human direction: apply ahabase evolucean principles to dwh-sm2 as the next plug-and-play Epic. Phasing is fixed: first the audit/documentation phase (detailed functional understanding of the repo, all functionality documented), only then evolucean integration work. Notably, the concept `plug-and-play-epic-integration` is *referenced* in `ontology-shaping-blueprint` (Integration is bidirectional; the genetic model — ontology and implementation blueprints are own DNA, metabolism is remappable) but the blueprint file **does not exist yet**. dwh-sm2 would be its first real application, and authoring the blueprint grounded in this case follows the pattern-driven integration rule (concept → pattern → implementation).

## What is already plugged in (verified)

Epic identity + inheritance from EVOLUCEAN root, story lifecycle with worktrees and release flow (proven by DWH-SM2-0001..0004, APP-0001/0002), the `_grid4d` knowledge plugin (issues, ideas, implementation, ontology; auto-generated projections including body views Skeleton/Muscles/Immunity/Nervous-System), hooks (story-required writes, auto knowledge-map logging, tests gating), runbook discipline.

## What "play" still requires (principle → gap)

| Evolucean principle | dwh-sm2 gap |
|---------------------|-------------|
| **Sensor** (measure where we are) | Nothing measures the pipeline automatically — freshness, datex age, upload success are manual log forensics (the 2026-10-08 incident proved it) |
| **Nervous system / stimulus-response interval** | [dwh-sm2-app-pipeline-unsequenced](../issue/dwh-sm2-app-pipeline-unsequenced) — no chaining, no failure notification; a 6-day dead pipeline was invisible |
| **Shaping cycle read-back** | `DWH-SM2-Shaping` / Gradients projections generate but nobody reads them into story decisions; evolucean's idle-session playbook rhythm is not applied to dwh-sm2 sessions |
| **Prune/Sustain as first-class modes** | The prune backlog already exists as issues (stale-artifacts-tracked, readme-docs-drift, dbt-config-dead-entries, main-tree-drift) but is never scheduled as Sustain stories |

## Proposal

1. Audit/documentation phase first (separate story): full functional inventory of the repo vs runbook/blueprints, close the coverage gaps.
2. Evolucean-side story: author the missing `plug-and-play-epic-integration` blueprint, grounded in the dwh-sm2 case.
3. dwh-sm2 stories in principle order: a pipeline health **sensor** (deterministic measurement into the knowledge system), then the **nervous system** (chaining + failure notification — resolves pipeline-unsequenced), then Sustain/prune stories from the backlog.

## Value

Turns dwh-sm2 from "a repo with the evolucean plugin mounted" into an Epic that operates by evolucean rules: measured, self-reporting, shaped by gradient. Shrinks the stimulus-response interval that let both the lint outage (6 days) and the silent-skip incident (days of stale datex) go unnoticed.

## Related

- [dwh-sm2-app-pipeline-unsequenced](../issue/dwh-sm2-app-pipeline-unsequenced) - the nervous-system gap, already an open issue
- [dwh-sm2-app-actions-log-echo-pollution](../issue/dwh-sm2-app-actions-log-echo-pollution) - manual forensics the sensor principle would retire
- [dwh-sm2-app-fallback-annotation-ux](dwh-sm2-app-fallback-annotation-ux) - verification clarity, same theme
