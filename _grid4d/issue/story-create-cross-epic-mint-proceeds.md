# Story Create Cross-Epic Mint Proceeds

> `story create` warns on epic-vs-calling-tree mismatch but still mints into the primary epic

**Status:** open
**Stories:** DWH-SM2-0001

## Problem

`story create` without `--epic` resolves the target epic to the **primary epic** (evolucean), even when the calling tree belongs to another registered epic. The EVOLUCEAN-0312 mint-time warning prints, and then the mint **proceeds**: counter consumed, worktree + story branch created, baseline snapshot tagged, pool entry and active-story binding set — all in the wrong epic. During the dwh-sm2 epic founding this produced ghost story EVOLUCEAN-0397 (manually cleaned; counter slot wasted).

## Root Cause

The 0312 guard stops at a warning; the default epic remains `primary_epic` regardless of the calling tree. A warning scrolls past in scripted and LLM-driven runs — and rare operations (founding a new Epic, minting its first story) are exactly where the operator's attention is on the new epic, not on the default.

## Solution Requirements

| Req | Requirement                                                                                          | Story | Status |
| --- | ---------------------------------------------------------------------------------------------------- | ----- | ------ |
| R1  | **Calling-tree default** - when the calling tree belongs to a known epic, that epic is the default `--epic`; no warning needed in that case | - | open |
| R2  | **Deliberate cross-epic mint stays possible** via explicit `--epic` naming a different epic          | -     | open  |

## Occurrences

| Occurred   | Story               | Manifestation                                                                                                                                                                                                                                    |
| ---------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2026-09-22 | DWH-SM2-0001 founding | `story create` from the dwh-sm2 root minted EVOLUCEAN-0397 into evolucean: counter claimed on counters branch, worktree + branch created, baseline tagged, pool + active set. Manual cleanup applied (see [no-cli-cleanup-for-wrong-mint](no-cli-cleanup-for-wrong-mint)). Same ghost shape as EVOLUCEAN-0281 in [story-prefix-mismatch](story-prefix-mismatch). |

## Notes

Third occurrence of the ghost-mint shape (0281, 0397). The warn-then-proceed design fits interactive use but not autonomous runs; per the competence boundary, what can be validated by software MUST be validated by software.
