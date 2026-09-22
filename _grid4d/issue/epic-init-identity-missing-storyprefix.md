# Epic Init Identity Missing StoryPrefix

> `epic init` scaffolds the identity document without the canonical **StoryPrefix:** declaration

**Status:** open
**Stories:** DWH-SM2-0001

## Problem

`epic init` writes the identity document without a `**StoryPrefix:**` field, so `doctor` warns immediately after bootstrap:

```
dwh-sm2: definition document DWH-SM2.md carries no StoryPrefix
- primary prefix comes from yaml ∅, registry ['DWH-SM2-'], or convention DWH-SM2-
```

The definition document is the canonical declaration home (see [evolucean-story-identity-pattern](evolucean-story-identity-pattern)); the bootstrap already knows the convention-derived prefix — it maps it in ahabase.yaml in the same run.

## Root Cause

The identity template in `bootstrap.py` (`epic_identity`) omits the `StoryPrefix` field although the same function writes the prefix mapping into the registry.

## Solution Requirements

| Req | Requirement                                                                                  | Story | Status |
| --- | -------------------------------------------------------------------------------------------- | ----- | ------ |
| R1  | `epic init` writes `**StoryPrefix:** <PREFIX>-` into the identity document; the dry-run plan shows it | - | open |
| R2  | The "Next:" hint mentions verifying prefix resolution with `doctor`                           | -     | open  |

## Occurrences

| Occurred   | Story                 | Manifestation                                                                                                     |
| ---------- | --------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 2026-09-22 | DWH-SM2-0001 founding | Init mapped `DWH-SM2-` in the registry but left the identity without the declaration; warning appeared on first `doctor`; declaration added manually in the founding story worktree. |
