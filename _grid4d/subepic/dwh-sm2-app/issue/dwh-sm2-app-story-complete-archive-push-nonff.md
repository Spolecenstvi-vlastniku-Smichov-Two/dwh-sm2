# story complete fails its final archive push when local main is behind origin

**Status:** open
**Found:** 2026-10-08 (DWH-SM2-APP-0004 completion)

## Problem

`story complete` in this epic can end with:

```
✗ push chore/archive-dwh-sm2-dwh-sm2-app-0004 to main failed - aborting before any further transition
 ! [rejected] chore/archive-d... -> main (non-fast-forward)
```

after every other phase already succeeded (story status completed, binding cleared, release `v0.0004.1.0004.00` tagged, GitHub release created, worktree and feature branch deleted). The visible symptom understates the state: the story commits ARE already on origin/main - only the archive commit (story set moved to `story/history/`) is missing from main.

Root cause chain:

1. origin/main moves independently of the local main tree - the Publish Public Dataset workflow bot-commits the datex parquet daily, and the complete run itself pushes the story commits to origin/main directly.
2. The CLI notices the stale local main at its merge step and prints a catch-up advice line, but proceeds anyway and builds the `chore/archive-*` branch on the stale local main base.
3. Pushing that branch to main is therefore non-fast-forward and the run aborts.
4. Trap: the complete process leaves the main checkout ON the chore branch - running recovery commands without `git checkout main` first makes every step misreport (ff "diverging", merge "already up to date", push "behind").

## Why It Matters

The failure lands exactly at the end of a long idempotent sequence: the release exists, but main lacks the archive state, the checkout sits on a half-integrated branch, and an operator who trusts the red error's "use git pull" hint can easily make it worse. In this epic it is not an edge case - main moves daily, so any complete that skips a preflight catch-up is exposed.

## Solution Direction

- **Preflight guard (operational, now):** before `story complete` in this epic, run `git -C ~/ahabase/dwh-sm2 fetch origin && git -C ~/ahabase/dwh-sm2 status -sb` and catch main up (`merge --ff-only origin/main`) if behind. Candidate runbook Operating Note.
- **Recovery (verified 2026-10-08):**
  1. `git -C ~/ahabase/dwh-sm2 checkout main`
  2. `git merge --ff-only origin/main` (main-tree drift in `analysis/` + ARCH docs survives - incoming commits do not touch those paths)
  3. `git merge --no-ff chore/archive-<story> -m "chore: integrate ... archive into main"` (preserves the original archive commit the tag may reference)
  4. `git push origin main`
  5. `git branch -d chore/archive-<story>`
- **Root fix (evolucean-side):** the complete sequence should catch main up (or abort before tagging) instead of printing advice and continuing on the stale base; it also should not leave the checkout on the chore branch. Mirror this as an evolucean `_grid4d/issue/` when a story opens there - it is a CLI sequencing gap, not a dwh-sm2 defect.

## Occurrences

- 2026-10-08, DWH-SM2-APP-0004 (`v0.0004.1.0004.00`): archive push rejected; recovery above executed clean (origin/main `8d003c3..a4167e9`), release untouched, drift preserved.

## Related

- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - operating context (daily bot commits)
- [dwh-sm2-app-readme-docs-drift](dwh-sm2-app-readme-docs-drift) - the story whose completion exposed this
