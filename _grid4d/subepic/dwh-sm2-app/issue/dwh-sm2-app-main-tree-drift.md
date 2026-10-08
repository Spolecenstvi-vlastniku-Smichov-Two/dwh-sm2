# Main tree carries uncommitted functional work and pending deletions

**Status:** open
**Found:** 2026-10-08 (DWH-SM2-APP-0001 audit); Human decision 2026-10-08: defer resolution to a story

## Problem

The dwh-sm2 main tree holds uncommitted drift (survived the DWH-SM2-0004 ff-merge only because the paths did not overlap):

1. **Uncommitted feature**: `analysis/quasistationary_selection.py` +167 lines - a `--labels cs` localization feature (Czech graph labels via `set_labels`, Czech date-range titles via `fmt_range_cs`) for the expert package, with all analysis PNGs/CSVs regenerated under it. Real functional work with no story and no commit.
2. **Pending deletions**: `ARCHITECTURE_REFACTORING_PROPOSAL.md` (Czech-language, violates the English-only documentation rule), `ARCHITECTURE_REFINEMENT.md`, `REFACTORING_ROADMAP.md` deleted in the working tree, uncommitted. `ARCHITECTURE_HYBRID_PLATFORM.md` survives.
3. **Touched knowledge file**: `_grid4d/story/DWH-SM2-0003-knowledge-map.md` modified (hook-attributed post-completion touch).

## Why It Matters

Uncommitted work in the main tree is one careless `git checkout .` away from loss, blocks clean merges (the next story completion must ff past it or stash), and the Czech labels feature is exactly the kind of change the SubEpic now exists to land properly: story, tests (labels rendered in outputs), commit.

## Solution Direction

One cleanup story: (a) land the Czech-labels feature - run the script with `--labels cs`, verify outputs, commit with its story; (b) commit the three architecture-doc deletions (their surviving content worth keeping should move into the knowledge system - see [dwh-sm2-app-readme-docs-drift](dwh-sm2-app-readme-docs-drift) for the README side); (c) leave the KM touch to the hook.

## Related

- [dwh-sm2-app-stale-artifacts-tracked](dwh-sm2-app-stale-artifacts-tracked) - the same cleanup-theme, git side
- [DWH-SM2-APP-0001](../story/DWH-SM2-APP-0001) - the audit that recorded the drift state
