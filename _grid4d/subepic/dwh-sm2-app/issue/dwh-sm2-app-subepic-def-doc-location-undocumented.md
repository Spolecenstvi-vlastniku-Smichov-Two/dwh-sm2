# Subepic Def-Doc Location Undocumented

> The subepic identity file's location convention exists only in code - no pattern or blueprint states the path, so the identity-file transition is incomplete for anyone following the knowledge.

**Status:** open (fix belongs to EVOLUCEAN)
**Found in:** DWH-SM2-APP-0006 (2026-10-08, Human-directed identity-concept review)

## Problem

The subepic def-doc lives at `_grid4d/subepic/<name>/story/<SUBEPIC>.md` (mirroring the epic def-doc at `_grid4d/story/<EPIC>.md`) - but no knowledge document says so:

- [ontology-identity-system-blueprint](ontology-identity-system-blueprint): "its identity file (def-doc: `Type`, `Inherits`, `StoryPrefix`)" - fields, no path;
- [evolucean-story-identity-pattern](evolucean-story-identity-pattern): "the epic / subepic identity file" - no path;
- [evolucean-subepic](evolucean-subepic) pattern template - no path;
- CLAUDE.md: "subepic index with its `StoryPrefix:` field" - no path.

Measured cost in this story: the consistency analysis searched `_grid4d/subepic/dwh-sm2-app/` root, found no identity file, and nearly logged a false "registration missing" issue; the file was in `story/` one level down. The convention is enforced only implicitly by the CLI's def-doc scan - an agent, a new installation, or a Human reader cannot derive it from the knowledge that is supposed to be the declaration home.

## Solution Direction (EVOLUCEAN side)

Add the path convention to the subepic pattern and the identity-system blueprint (epic def-doc path + subepic def-doc path), one line each. Pairs with issue `dwh-sm2-app-identity-declaration-vs-tooling-divergence`: once doctor scans the filesystem for def-docs, the location becomes a validated contract instead of tribal knowledge.

## Occurrences

| Date | Story | Signature |
|------|-------|-----------|
| 2026-10-08 | DWH-SM2-APP-0006 | subepic-root search found no def-doc; actual location `subepic/dwh-sm2-app/story/DWH-SM2-APP.md`; no path stated in pattern/blueprint/CLAUDE.md |
