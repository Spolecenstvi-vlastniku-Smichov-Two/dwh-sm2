# DWH-SM2-APP-0005: Capture lessons learned from the DWH-SM2-APP-0004 documentation story

> Capture lessons learned from the DWH-SM2-APP-0004 documentation story

**Type:** default
**Epic:** [DWH-SM2-APP](../DWH-SM2-APP)
**Status:** in_progress
**Blueprint:** [implementation-story-blueprint](implementation-story-blueprint)

## Goal

Capture lessons learned from the DWH-SM2-APP-0004 documentation story

## Requirements

### R1: Capture the story-complete archive-push issue ✅

Capture [dwh-sm2-app-story-complete-archive-push-nonff](../issue/dwh-sm2-app-story-complete-archive-push-nonff): `story complete` succeeded through release/tag/archive but its final `chore/archive-*` push to main was rejected (non-fast-forward) because the archive branch was built on the stale local main while origin/main had moved (daily publish-bot parquet commits + the complete run's own story-commit push). Include the verified recovery recipe and the checkout-on-chore-branch trap; note the root cause is a knowledge-usage-cli sequencing gap to be mirrored as an evolucean-side issue when a story opens there.

**Acceptance Criterion:** Issue file exists with Problem / Why It Matters / Solution Direction (preflight guard + recovery recipe) / Occurrence (2026-10-08, v0.0004.1.0004.00) and the cross-epic note.

### R2: Capture the README-facts generation idea ✅

Capture [dwh-sm2-app-readme-facts-generated](../idea/dwh-sm2-app-readme-facts-generated): generate the README's operational excerpts (cron schedules, triggers, script versions) from the workflow files themselves (docs-as-code), eliminating the readme-docs-drift class at the source instead of only pinning it with grep tests (DWH-SM2-APP-0004 R4).

**Acceptance Criterion:** Idea file exists with Context / Proposal / Value and links to the resolved drift issue and the 0004 test suite.

### R3: Record the procedural lessons in the story Notes ✅

The 0004 run's smaller procedural lessons live here, not as separate documents: requirement headings need the done-marker for the stop hook to see progress; `story complete` takes no `--epic` (epic derives from the story worktree); both already captured in the ahabase session memory for reuse across epics.

**Acceptance Criterion:** Notes section lists the three lessons with pointers.

## Notes

Created: 2026-10-08

Lessons behind this journal (from the 0004 execution and completion):

1. **Requirement done-markers:** the stop hook reads completion from the requirement heading marker (`### RN: ... ✅`); an executed-but-unmarked story shows `0/4 done` and the hook nags about R1. Mark requirements as they complete.
2. **`story complete` flag surface:** no `--epic` option exists on complete (unlike create); the epic derives from the story worktree, and the command must run from the worktree root with the evolucean venv on PATH.
3. **Completion-time main hygiene:** see the issue captured in R1 — the practical rule is: before running complete in this epic, fetch and check that local main is not behind origin/main (the publish bot moves main daily).

Out of scope here (evolucean-side, mirror when a story opens there): the CLI sequencing gap itself (complete notices the stale main, prints catch-up advice, then builds the archive branch on the stale base anyway and leaves the checkout on the chore branch).
