# Subepic Identity File Stale

> DWH-SM2-APP.md correctly declares the canonical StoryPrefix, but its Structure table and active-story line drifted from reality during stories 0002-0006.

**Status:** open
**Found in:** DWH-SM2-APP-0006 (2026-10-08, identity-file completeness check)

## Problem

The identity file `_grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP.md` is the canonical declaration (`**StoryPrefix:** DWH-SM2-APP-`, `**Inherits:** dwh-sm2`, `**Type:** SubEpic`) and story placement is consistent with it. But its content went stale:

- Structure table lists only `story/`, `implementation/`, `ontology/`, `_generated/` - the now-existing `metric/`, `issue/`, `idea/` folders are missing (metric/ gained three definitions and issue/ two issues in this story alone);
- "One story active: DWH-SM2-APP-0001" - stale since 0002: five stories completed, DWH-SM2-APP-0006 active at time of writing;
- Related section omits `implementation-subepic-blueprint` and `evolucean-story-identity-pattern`, which the subepic pattern lists as the contract documents for identity resolution.

Nothing re-syncs these prose sections when folders appear or stories complete, so drift is structural, not a one-off.

## Solution Direction

Story-side fix: refresh Structure (add metric/, issue/, idea/), drop the always-stale "One story active" line in favour of a pointer to `status` / the story folder, and add the two pattern Related links. Systemic fix candidate (EVOLUCEAN side): identity-file Structure sections should either be generated or verified against the filesystem - see idea `dwh-sm2-app-doctor-subepic-coverage` for the doctor hook this could hang on.

## Occurrences

| Date | Story | Signature |
|------|-------|-----------|
| 2026-10-08 | DWH-SM2-APP-0006 | Structure table missing 3 folders; "One story active: DWH-SM2-APP-0001" while 0006 active; pattern Related links absent |
