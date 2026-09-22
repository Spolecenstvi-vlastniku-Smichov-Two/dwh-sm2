# Epic Init Inherits Root Default

> `epic init` scaffolds every new Epic as `**Inherits:** none (root)` although new Epics inherit from the namespace root

**Status:** open
**Stories:** DWH-SM2-0001

## Problem

The `epic init` identity template hardcodes `**Inherits:** none (root)` (bootstrap.py:92). Per the namespace model, EVOLUCEAN is the root Epic and **all other Epics inherit from it directly or indirectly** - config resolution already works that way (`lookup_epic_config`, EVOLUCEAN-0131: EVOLUCEAN.md supplies root defaults for every epic != evolucean, overridden by the epic's own definition). A freshly initialized Epic therefore declares a falsehood and misses the declarative pointer to the patterns it actually consumes (story, knowledge-map, tests patterns resolve from the root chain).

## Root Cause

The template predates or ignores the inheritance convention; only `init-subepic` writes the real parent (`**Inherits:** {epic}`).

## Solution Requirements

| Req | Requirement                                                                                          | Story | Status |
| --- | ----------------------------------------------------------------------------------------------------- | ----- | ------ |
| R1  | `epic init` writes `**Inherits:** <root-epic>` (the primary/root Epic) instead of `none (root)`      | -     | open   |
| R2  | A deliberately standalone root Epic stays possible via an explicit option (e.g. `--root`)            | -     | open   |
| R3  | **Declared vs. effective consistency** - doctor flags divergence: `lookup()` / `lookup_epic_config()` apply the hardcoded evolucean root chain regardless of the declared `**Inherits:**`, so a doc declaring `none (root)` still consumes evolucean patterns and defaults | - | open |

## Occurrences

| Occurred   | Story                 | Manifestation                                                                                              |
| ---------- | --------------------- | ---------------------------------------------------------------------------------------------------------- |
| 2026-09-22 | DWH-SM2-0001 founding | DWH-SM2 identity scaffolded as `none (root)`; Human caught it during review; corrected to `EVOLUCEAN` in the founding story worktree. |
