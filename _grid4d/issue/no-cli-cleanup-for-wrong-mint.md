# No CLI Cleanup For Wrong Mint

> A wrongly minted story has no delete/abandon command; cleanup is manual git + state surgery

**Status:** open
**Stories:** DWH-SM2-0001

## Problem

`story create` has no counterpart for discarding a story minted by mistake (no `story delete` / `abandon` / `discard`). Manual cleanup has to touch every artifact the mint created:

1. worktree: `git worktree remove --force <worktree>`
2. story branch: `git branch -D <branch>`
3. `state.json`: clear `active_story`, remove the `story_pool` entry
4. snapshot store: baseline tag of the ghost story (no snapshot delete exists; during the founding the tag was left in place)
5. counters: the ID stays consumed (gap) - rewriting the counters branch was judged riskier than a gap

## Root Cause

No command surface for mint rollback; recovery knowledge exists only as tribal memory. Contrast: BODY-0008 has a written recovery recipe for a different failure class.

## Solution Requirements

| Req | Requirement                                                                                                             | Story | Status |
| --- | ----------------------------------------------------------------------------------------------------------------------- | ----- | ------ |
| R1  | `story discard <ID>` that removes worktree + branch + pool entry and refuses when the story has work beyond the mint (extra commits, merge) - or a documented recovery recipe in knowledge | -  | open   |
| R2  | Baseline tag cleanup (or snapshot GC) for discarded stories                                                              | -     | open   |

## Occurrences

| Occurred   | Story                 | Manifestation                                                                                                                        |
| ---------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 2026-09-22 | DWH-SM2-0001 founding | EVOLUCEAN-0397 ghost cleaned manually; stale tag `EVOLUCEAN-0397-baseline` left on the snapshot commit; counter gap 0397. Trigger: [story-create-cross-epic-mint-proceeds](story-create-cross-epic-mint-proceeds). |
