# Stale artifact generations tracked in git

**Status:** open
**Found:** 2026-10-08 (DWH-SM2-APP-0001 audit)

## Problem

The repository tracks multiple dead generations of generated artifacts:

1. **Three dbt docs sites**: `docs/` (current, dbt 1.12.5, 2026-10-02), `docs/dwh-sm2/` (dbt 1.9.1, 2025-01-24) and `docs/tmp_docs/dwh-sm2/` (dbt 1.9.1, 2025-01-25). The two older sets describe a model lineage that no longer exists (single `fact` model reading `./gdrive/sm2_0X.csv` per-section sources) - each carries a 1.7 MB index.html, manifest.json and graph.gpickle.
2. **`docs/datex.old/`**: the previous datex viewer with its own 1.8 MB stale parquet; nothing references it and its index.html imports the NEW config path, so even its local config is dead.
3. **`.gitignore` negation leak**: the trailing `!docs/**` exception (line 87) re-includes everything under docs/, defeating the `tmp_docs/` and `**/.DS_Store` rules - `git check-ignore` confirms `docs/.DS_Store`, `docs/tmp_docs/**` are not ignored, and they are tracked.
4. **3 `.gpickle` files** (pickled graph objects) tracked under docs/ - build artifacts of `dbt docs generate`.

Roughly 5+ MB of the repository is dead weight that misleads readers (an auditor opening `docs/dwh-sm2/` sees a wrong lineage) and bloats every clone.

## Solution Direction

Remove `docs/dwh-sm2/`, `docs/tmp_docs/`, `docs/datex.old/`, the stale gpickles and `docs/.DS_Store` in one cleanup story; fix the `.gitignore` negation to un-ignore only the intended docs subpaths (`!docs/index.html`, `!docs/datex/`, the tracked dbt-docs artifacts) instead of `!docs/**`.

## Related

- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - "never edit" list includes the stale copies
- [dwh-sm2-app-main-tree-drift](dwh-sm2-app-main-tree-drift) - the arch-doc deletions riding the same cleanup theme
