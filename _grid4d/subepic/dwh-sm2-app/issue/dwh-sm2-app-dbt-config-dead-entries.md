# dbt project carries dead config and contradicted tool settings

**Status:** open
**Found:** 2026-10-08 (DWH-SM2-APP-0001 audit)

## Problem

1. **Dead model configs**: `dbt_project.yml:33-37` sets `+location` for models `fact_indoor_temperature_original` and `fact_indoor_humidity_original` - no models with those names exist (actual: `fact_indoor_temperature` / `fact_indoor_humidity`). The models land on default external paths that happen to match what the workflow uploads - working by coincidence, not by configuration.
2. **No-op `dbt deps`**: refresh.yml:87 runs `dbt deps` but no `packages.yml` exists and `dbt_packages/` is empty (local log: "Warning: No packages were found").
3. **sqlfluff dialect contradiction**: `.sqlfluff` declares `dialect = ansi`; the workflow lints with `--dialect duckdb` (refresh.yml:90-93). CLI flag wins, so the config file is dead and misleading.
4. **`sqlfluff fix` in CI on every daily run**, with a commented-out "lint only modified models" block (refresh.yml:95-97) as dead code - `fix` can silently rewrite model SQL that the bot's `git add --all :/` then commits.
5. **analysis-paths collision**: `dbt_project.yml:11` points dbt's `analysis-paths` at `analysis/`, which holds a Python analytics script and PNG/CSV outputs, not dbt `.sql` analyses.
6. **Declared-but-missing paths**: `tests/` and `macros/` directories do not exist (tolerated by dbt); source tables carry empty `freshness:` keys (null overrides).

## Solution Direction

Delete the `*_original` config blocks (or rename to the real models so the paths are intentional), drop the `dbt deps` step or add a real `packages.yml`, set `.sqlfluff` to `duckdb` and let the workflow drop the flag, decide fix-vs-lint policy for CI (fix belongs in a Human-reviewed change, not a nightly bot commit), and repoint `analysis-paths` to an empty `analyses/` directory or remove it.

## Related

- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - operating notes flag the local/CI dbt divergence
- [dwh-sm2-app-readme-docs-drift](dwh-sm2-app-readme-docs-drift) - README side of the same stale-docs theme
