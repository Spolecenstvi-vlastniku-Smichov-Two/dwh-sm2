# Multidash Prefix Epic Resolution

> `get_epic_for_story` truncates multi-dash prefixes and cannot resolve a story whose prefix declaration lives only on its story branch

**Status:** open
**Stories:** DWH-SM2-0001

## Problem

`story complete DWH-SM2-0001` failed at step 1: the epic resolved to **evolucean** (primary) instead of dwh-sm2, so the story file was searched in the wrong repo. Three stacked causes in `config.py`:

1. **Prefix truncation** (line ~1313): `story_prefix = story_id.split("-")[0] + "-"` turns `DWH-SM2-0001` into `DWH-`. Multi-dash prefixes (`DWH-SM2-`, and by extension `EVOLUCEAN-DATA-`, `EVOLUCEAN-COLLAB-`, ...) never survive this derivation intact.
2. **Canonical-tree blindness**: the def-doc scan reads the canonical tree only. A founding story declares `**StoryPrefix:**` in its worktree identity document; before the merge the declaration is invisible, so the scan yields nothing. (The lenient `prefix.startswith(truncated)` condition would otherwise rescue case 1.)
3. **yaml fallback truncation**: `re.match(r'^([A-Z]+)', story_id)` stops at the first dash, extracting `DWH`; the registry map key is `DWH-SM2` - unreachable for any multi-dash prefix. Falls through to `get_primary_epic()`.

## Root Cause

`get_epic_for_story` predates the unified resolver: it re-derives prefixes locally instead of consuming `story_prefixes_for` (the "one resolver for all consumers" rule of [evolucean-story-identity-pattern](evolucean-story-identity-pattern), EVOLUCEAN-0320).

## Solution Requirements

| Req | Requirement                                                                                                          | Story | Status |
| --- | --------------------------------------------------------------------------------------------------------------------- | ----- | ------ |
| R1  | `get_epic_for_story` consumes the unified resolver (`story_prefixes_for`) - full-prefix match against all declared prefixes | -  | open   |
| R2  | Prefix classification works for stories whose declaration is still on the story branch (consult the calling tree/worktree, or the counters claim) | - | open |
| R3  | The yaml fallback regex handles multi-segment prefix keys (match the longest key of the `prefixes:` map, not `^([A-Z]+)`)  | -  | open   |

## Occurrences

| Occurred   | Story                 | Manifestation                                                                                                                         |
| ---------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-09-22 | DWH-SM2-0001 founding | `story complete DWH-SM2-0001 --confirm` failed at "Locating story file" with the evolucean path; reproduced live: `get_epic_for_story('DWH-SM2-0001')` returns `evolucean`. Workaround: ff-merge the story branch to main first (declaration reaches the canonical tree), then complete. |

## Notes

Related: [story-prefix-mismatch](../../../evolucean/_grid4d/issue/story-prefix-mismatch.md) (same family, different consumer), [story-create-cross-epic-mint-proceeds](story-create-cross-epic-mint-proceeds) (same primary-epic fallback shape). The fix belongs to an evolucean CLI story; this founding story completes via the documented workaround.
