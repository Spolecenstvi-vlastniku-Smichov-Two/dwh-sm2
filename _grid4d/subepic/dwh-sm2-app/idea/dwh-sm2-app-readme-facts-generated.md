# Generate README operational facts from the workflow files

**Status:** open (idea)
**Proposed:** 2026-10-08 (DWH-SM2-APP-0005, from the 0004 experience)

## Context

The 1163-line README drifted into documenting an application that does not exist (weekly publish cadence, push triggers, wrong script attribution, stale script versions) - resolved by hand in DWH-SM2-APP-0004 and pinned by a 14-test README-facts suite. But the suite only detects the next drift; it does not prevent it. The true source of operational facts (cron expressions, triggers, script names/versions, CSV schemas) is the workflow YAML and the scripts themselves.

## Proposal

Docs-as-code for the operational layer: a small generator (workflow step or pre-commit check) that extracts the facts from `.github/workflows/*.yml` and the script headers and renders the README's operational excerpts (per-workflow trigger blocks, schedule lines, script version lines) from them - either as committed generated blocks with markers, or as a drift check that rewrites/fails when the README disagrees with the source files.

## Value

Eliminates the readme-docs-drift failure class at its source instead of detecting it after the fact; the README-facts suite then only needs to pin the generator's presence, not every fact. Fits the plug-and-play audit phase: documentation that cannot lie because it is derived.

## Related

- [dwh-sm2-app-readme-docs-drift](../issue/dwh-sm2-app-readme-docs-drift) - the drift class this idea removes (resolved by hand in 0004)
- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - current operational source of truth
- DWH-SM2-APP-0004 tests - the detection layer this idea would simplify
