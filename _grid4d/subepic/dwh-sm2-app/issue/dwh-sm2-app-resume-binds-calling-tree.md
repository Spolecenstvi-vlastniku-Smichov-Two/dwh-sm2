# Resume Binds to the Calling Tree

> `resume` run outside the story worktree binds the session to the epic main tree - the stop-hook then reports "Story file not found" and the knowledge map never generates.

**Status:** open (fix belongs to EVOLUCEAN)
**Found in:** DWH-SM2-APP-0006 (2026-10-08)

## Problem

Story work must be anchored to a clear subepic identity and a well-defined story binding. In this story the anchoring broke silently:

1. `resume DWH-SM2-APP-0006` was run from `~/ahabase` (workspace root) instead of the story worktree;
2. the session bound to the **dwh-sm2 main tree** - `knowledge-usage sessions list` showed TREE = main checkout, not `_worktrees/dwh-sm2/dwh-sm2-app/DWH-SM2-APP-0006`;
3. symptoms: stop-hook "Story file not found in `<main-tree>/_grid4d`" on every turn, no knowledge-map auto-logging, yet `status` still showed the story active - active-ness and binding diverged;
4. re-running `resume` from the worktree root printed "rebound to the calling tree" and healed everything.

The failure is quiet: nothing refuses the wrong-tree bind even though the story's worktree exists and holds the branch. The operator learns only from downstream symptoms (missing KM), which look like unrelated failures.

## Solution Direction (EVOLUCEAN side)

`resume` knows the story ID; the story's worktree is discoverable (binding metadata from `story create`, or the `_worktrees/` layout convention). Either resolve the story's own worktree instead of the calling tree, or emit a warning when the calling tree is not the story worktree and a worktree exists. Interim mitigation (documented in memory): always `resume` from the story worktree root.

## Occurrences

| Date | Story | Signature |
|------|-------|-----------|
| 2026-10-08 | DWH-SM2-APP-0006 | resume from `~/ahabase` → TREE = dwh-sm2 main; stop-hook "Story file not found"; KM not generated; heal = re-resume from worktree |
