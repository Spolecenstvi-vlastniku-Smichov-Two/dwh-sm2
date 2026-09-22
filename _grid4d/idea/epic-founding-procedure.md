# Epic Founding Procedure

> Written end-to-end procedure for founding a new ahabase Epic - founding is rare, the knowledge must not live only in session memory

**Status:** captured (candidate for an evolucean shaping story)
**Origin:** DWH-SM2-0001 founding session, 2026-09-22, Human request

## Motivation

Founding a new Epic happens rarely and the procedure existed only as tribal memory. The dwh-sm2 founding hit three avoidable issues ([story-create-cross-epic-mint-proceeds](../issue/story-create-cross-epic-mint-proceeds), [epic-init-identity-missing-storyprefix](../issue/epic-init-identity-missing-storyprefix), [no-cli-cleanup-for-wrong-mint](../issue/no-cli-cleanup-for-wrong-mint)) that a written procedure prevents.

## Procedure as executed (DWH-SM2, 2026-09-22)

1. **Prepare the clone** at `~/ahabase/<name>` with an origin remote (a PAT may live in the remote URL; only the clean URL is stored anywhere).
2. **Dry-run**: `knowledge-usage epic init <name> --dry-run --description "..."` - review the plan: knowledge folders, identity document, wiki.yml, registry entry, prefix map.
3. **Real init**: `knowledge-usage epic init <name> --description "..."`.
4. **Commit the scaffold** in the epic main tree (empty folders are not tracked; only the identity document and wiki.yml land).
5. **Mint the founding story with explicit `--epic`**: `knowledge-usage story create --epic <name> "Bootstrap <EPIC> epic: identity, StoryPrefix declaration, founding knowledge"`.
6. **Fill the identity in the story worktree**: Overview + Vision (Human supplies the vision - it is the epic's reason to exist, never a TODO), declare `**StoryPrefix:** <PREFIX>-`, set `**Inherits:** <root-epic>` (the scaffold's `none (root)` is false for a new Epic), write story requirements.
7. **Verify**: `knowledge-usage doctor` - the StoryPrefix warning clears once the story merges (doctor reads the canonical tree).
8. **Complete the story** (merge brings vision + prefix to main), then push.

## How pattern inheritance actually works (verified in code, 2026-09-22)

Three separate mechanisms - only one reads the `**Inherits:**` field:

1. **Pattern document resolution** - `pattern_resolver.lookup()` (Chain of Responsibility, first match wins): subepic pattern folder → `<epic>/_grid4d/pattern/<epic>-<name>.md` → **hardcoded root fallback** `evolucean/_grid4d/pattern/evolucean-<name>.md`. A new Epic gets the evolucean story/knowledge-map/tests pattern documents automatically; an own variant just drops `<epic>-<name>.md` into the epic pattern folder and wins the chain.
2. **Epic config inheritance** - `pattern_resolver.lookup_epic_config()` (EVOLUCEAN-0131): EVOLUCEAN.md supplies root defaults for every epic != evolucean, the epic's own definition overlays it, subepic overlays further. Consumed by `get_story_pattern()`, `get_epic_merge()`, `get_epic_git_operations()`, `get_epic_snapshot_on_complete()`, `get_epic_story_history_keep()`.
3. **`**Inherits:**` field** - read only by the Inheritance projection (EPIC-Inheritance.md / fishbone tree rendering). It displays the hierarchy; it drives no resolution.

Consequence: declared inheritance (`**Inherits:**`) and effective inheritance (hardcoded evolucean fallbacks) can diverge silently - a doc declaring `none (root)` still consumes the evolucean fallbacks. See [epic-init-inherits-root-default](../issue/epic-init-inherits-root-default) R3 for the consistency check.

## Lessons

- The founding story must exist **before** any identity edit - the STORY REQUIRED hook has no exceptions.
- Always pass `--epic` on the first story: the epic is brand new, and the default target is the primary epic.
- Inheritance from the root Epic (EVOLUCEAN) is what supplies the story/knowledge-map/tests patterns; the resolution chain is automatic (EVOLUCEAN.md root defaults → epic definition), but the identity's `**Inherits:**` field must state the truth.
- The registry entry (ahabase.yaml) is written by `epic init` itself; no manual `_config` editing - pattern-driven configuration applies.

## Destination

The procedure belongs in **evolucean** knowledge - as a pattern or an extension of the epic bootstrap blueprint - minted via an evolucean shaping story; the founding issues above are its inputs. Until then this document in dwh-sm2 is the single written source.
