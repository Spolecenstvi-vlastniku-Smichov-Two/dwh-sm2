# Application dependencies unpinned, three dbt generations in one tree

**Status:** open
**Found:** 2026-10-08 (DWH-SM2-APP-0001 audit)

## Problem

The application has no dependency manifest: no `requirements.txt` (gitignored, .gitignore:30), no `pyproject.toml`, no `packages.yml`. Dependencies exist only as ad-hoc unpinned `pip install` lines inside the workflows (`pandas`, `csvkit`, `dbt-duckdb`, `duckdb`, `sqlfluff`, `pyarrow`) and a README local-dev list. Measured version drift: local dbt 1.7.19 (logs/target artifacts), CI dbt 1.12.5 (docs/manifest.json), docs snapshots dbt 1.9.1 - three generations of the core transform tool in one tree, none pinned anywhere.

The datex viewer compounds this at the browser layer: Chart.js and hyparquet/apache-arrow load from jsdelivr CDN with no version-pinned local copies, so the viewer's behavior can change under a redeployed CDN artifact.

Also noted: `scripts/export_aggregated_to_csv.py:10` carries a literal CI token fallback (`ci-secret-token`) and `influx_import_workflow.yml` holds CI credentials inline - ephemeral CI-only values today, but a pattern that would leak the moment the container is pointed at a real Influx instance.

## Why It Matters

An evidence pipeline must be reproducible: "same inputs, same outputs" is the whole point of the complaint case. Unpinned daily-resolving dependencies mean a breaking upstream release silently changes the transformation stack mid-season, and local analysis cannot be guaranteed to match CI behavior.

## Solution Direction

Add a pinned dependency manifest (requirements.txt with exact versions, or pyproject + lock) consumed by the workflows; pin the datex CDN assets to exact versions (they already carry versions in URL, verify and freeze) or vendor them; replace the literal CI token fallback with a required env var. Choose one dbt version (CI's 1.12.5 unless there is a reason not to) and pin it everywhere.

## Occurrences

- **2026-10-03 → 2026-10-08 (live, diagnosed via `gh api` in DWH-SM2-APP-0001)**: the unpinned `pip install sqlfluff` in refresh resolved 4.3.0 → 4.4.0 overnight (last success 2026-10-02, run 36959260448, sqlfluff 4.3.0 clean; first failure 2026-10-03, run 37091726016, sqlfluff 4.4.0). The new version reports 3 unfixable violations across the 3 dbt models; `sqlfluff fix` exits 1 on unfixable violations, failing the "Lint with sqlfluff" step (verified in job 113137197577 / run 37723784092) and skipping dbt build, docs generate, and the bot data commit. Six consecutive daily refresh failures; the repo-side data/docs outputs froze at 2026-10-02. Mitigated in-story (DWH-SM2-APP-0001, Human-directed, 2026-10-08): the refresh lint step now pins `sqlfluff==4.3.0` exact, verified locally (fix + lint exit 0, zero violations over `models/`). The issue stays open: there is still no dependency manifest (dbt, pandas, csvkit, pyarrow, CDN assets all unpinned), and adopting sqlfluff 4.4.0 (3 unfixable violations in the models) is deferred to the fix story.

## Related

- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - operating notes flag local-vs-CI dbt behavior differences
- [dwh-sm2-app-dbt-config-dead-entries](dwh-sm2-app-dbt-config-dead-entries) - the dbt-project side of the same drift
