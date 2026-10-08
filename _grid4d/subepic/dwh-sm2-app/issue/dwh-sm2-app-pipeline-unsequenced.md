# Pipeline stages unsequenced: cron stagger only, no guards, no failure notification

**Status:** open
**Found:** 2026-10-08 (DWH-SM2-APP-0001 audit)

## Problem

The README calls the Refresh → InfluxImportNormalize → Publish order "CRITICAL" (README:67-121), but nothing enforces it. The three workflows run on cron stagger alone (00:00 / 00:30 / 01:30 UTC). No `workflow_run` or `repository_dispatch` chaining, no `concurrency:` guard, no `timeout-minutes:`, and no failure notification (`if: failure()`, Slack, e-mail, nothing) exists in any of the three workflow files. A stage that overruns its 30-minute slot overlaps with the next; a stage that fails dead stays dead - the pipeline is an evidence pipeline for an active legal complaint, and its death would be invisible until a Human opens the Actions tab.

## Symptoms

- Any workflow run exceeding its stagger window silently reads stale/absent inputs from the previous stage.
- A failing workflow produces no signal beyond the GitHub UI badge; consecutive daily failures accumulate unnoticed.
- A manual `workflow_dispatch` re-run of an early stage does not trigger the later stages - the operator must know to re-run all three in order.

## Solution Direction

Chain the stages explicitly (`workflow_run` on completion of the previous stage, keeping the cron on stage 1 only), add `concurrency` groups per workflow and `timeout-minutes`, and add a failure-notification step (GitHub issue creation or e-mail via a secret). Keep the runbook's Health Verification section in sync.

## Occurrences

- **2026-10-03 → 2026-10-08 (live, diagnosed via `gh api` in DWH-SM2-APP-0001)**: refresh failed six consecutive scheduled runs (37091726016 … 37723784092, all at the sqlfluff lint gate; root cause in [dwh-sm2-app-dependencies-unpinned](dwh-sm2-app-dependencies-unpinned)). InfluxImportNormalize and Publish Public Dataset stayed green throughout - no chaining exists, so the failure never propagated and nothing notified anyone. Measured blast radius: public dataset and datex freshness unaffected (Publish reads `sm2drive:Normalized` directly, not the repo); repo-side refresh outputs (dbt docs, fact CSVs) frozen at 2026-10-02. Also observed: GitHub scheduler delay of 3-4 h (cron `0 0 * * *` actually firing 03:00-03:39 UTC), further compressing the assumed 30-minute stagger.

## Related

- [dwh-sm2-app-pipeline-blueprint](../ontology/dwh-sm2-app-pipeline-blueprint) - the sequenced concept this violates
- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - manual checking procedure
