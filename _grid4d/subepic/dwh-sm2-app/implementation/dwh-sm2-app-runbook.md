# dwh-sm2-app Runbook

> How the SM2 temperature monitoring application actually runs, what can break where, and how to verify health. Grounded in the DWH-SM2-APP-0001 audit (2026-10-08); every claim below was measured against the repository.

## The Application in One Paragraph

Three GitHub Actions workflows run daily in sequence (Refresh 00:00 → InfluxImportNormalize 00:30 → Publish Public Dataset 01:30 UTC): raw sensor CSVs come from Google Drive (`sm2drive:` via rclone + service account), dbt/DuckDB builds fact tables, an ephemeral InfluxDB 2.7 container normalizes them into `sensor_data` (measurements `additive` = re-imported history, `nonadditive` = fresh daily), hourly aggregates flow back to Drive (`Normalized/`), and `build_public_dataset.py` publishes the CC BY 4.0 dataset (csv.gz + parquet) that the datex viewer (`docs/datex/`) renders in-browser. The expert analysis toolkit (`analysis/quasistationary_selection.py`) runs manually over the published parquet. Concepts: [dwh-sm2-app-application-blueprint](../ontology/dwh-sm2-app-application-blueprint), [dwh-sm2-app-pipeline-blueprint](../ontology/dwh-sm2-app-pipeline-blueprint).

## Component Inventory (audit-verified)

| Component | Location | Runs | Notes |
|-----------|----------|------|-------|
| refresh workflow | `.github/workflows/refresh.yml` | cron `0 0 * * *` + dispatch | inline csvkit ventilation merge; `indoor_merge_all_sensors.sh` v3.1 (GNU-only grep/date); dbt incremental-then-full build; bot commit `git add --all :/`; Drive archive step |
| InfluxImportNormalize | `.github/workflows/influx_import_workflow.yml` | cron `30 0 * * *` + dispatch | InfluxDB 2.7 service container (CI literals: `ci-user`/`ci-secret-token`); CLI 2.7.5 amd64 (step name says ARM64 - cosmetic); hard-fails |
| Publish Public Dataset | `.github/workflows/publish_public_dataset.yml` | cron `30 1 * * *` + dispatch | plain `git push` on checkout credentials; missing location_map only warns |
| prepare_annotated_csv.py | `scripts/` | workflow 2 | pandas; writes 7-col annotated CSV header (README shows stale 6-col); emits `months_to_process.json` |
| check_and_import_previous_exports.py | `scripts/` | workflow 2 | re-imports additive history; README claims `--skipRowOnError` + exit-1 semantics it does not have |
| export_aggregated_to_csv.py | `scripts/` | workflow 2 | hourly aggregateWindow → Drive `Normalized/`; literal CI token fallback in source |
| export_raw_by_month.py | `scripts/` | workflow 2 | monthly raw export → Drive `Influx/`; hard `os.environ[...]` on missing env |
| debug_influx_raw.py | `scripts/` | workflow 2 | diagnostic print only |
| indoor_merge_all_sensors.sh | `scripts/` | workflow 1 | v3.1; env-var configurable; README documents v2.2 |
| build_public_dataset.py | `scripts/` | workflow 3 | validates 6 columns, location remap, uploads 5 files to Drive `Public/`; parquet failure tolerated |
| dbt project | `dbt_project.yml`, `models/{ventilation,indoor}/` | workflow 1 | DuckDB `dwh_sm2.duckdb`, threads 24, external CSV materializations; 3 not_null tests total; dead config for non-existent `*_original` models; `dbt deps` is a no-op (no packages.yml) |
| seeds | `seeds/` (mapping, mapping_indoor, mapping_sources, location_map) | workflow 1 | sensor → location translations; `history` months per source drive the rolling window |
| InfluxDB | ephemeral per run | workflow 2 | bucket `sensor_data`; additive/nonadditive split |
| analysis toolkit | `analysis/quasistationary_selection.py` | manual (`--parquet --out`) | duckdb+pandas+matplotlib; ČSN 73 0540 window selection; outputs tracked in git |
| public dataset + datex | `public/`, `docs/datex/` | workflow 3 | parquet 3.1 MB tracked, daily bot-committed; Chart.js + hyparquet from CDN; cs/en configs; `config.js` defines `metrics` twice |

## Documentation Coverage Map

| Component | Documented where | Current? |
|-----------|------------------|----------|
| Whole pipeline | `README.md` (1163 lines) | ❌ false trigger claims ("on push"), wrong publish cadence (weekly vs daily), attributes ventilation merge to the indoor script, stale script semantics |
| Architecture | `ARCHITECTURE_HYBRID_PLATFORM.md` (root) | 🟡 strategy doc 2025-12-23, describes an unimplemented future platform |
| Architecture (deleted in drift) | `ARCHITECTURE_REFACTORING_PROPOSAL.md` (Czech), `ARCHITECTURE_REFINEMENT.md`, `REFACTORING_ROADMAP.md` | ❌ pending deletion in the uncommitted main-tree drift; proposal-grade, superseded |
| dbt docs | `docs/` (current, dbt 1.12.5) | ✅ auto-committed by refresh |
| dbt docs (stale) | `docs/dwh-sm2/`, `docs/tmp_docs/dwh-sm2/` (dbt 1.9.1, 2025-01) | ❌ describe a model lineage that no longer exists |
| datex viewer | none (self-contained) | 🟡 no README of its own; config duplication |
| analysis toolkit | `analysis/DWH-SM2-0002-report.md`, story docs 0002/0003 | ✅ |
| Application ontology | this SubEpic `ontology/` | ✅ founded by this story |
| Runbook | this document | ✅ founded by this story |
| Wiki | `_grid4d/wiki.yml` (name only) | ❌ knowledge not published anywhere outside the repo |

## Known Failure Modes (find and their issues)

| Symptom | Cause | Where captured |
|---------|-------|----------------|
| Silent overlap of stages | cron-stagger-only sequencing, no chaining/concurrency/timeout | [dwh-sm2-app-pipeline-unsequenced](../issue/dwh-sm2-app-pipeline-unsequenced) |
| Nobody notices a dead pipeline | no failure notification in any workflow | same issue |
| Stale evidence published | README cadence/trigger lies; operators reason from wrong docs | [dwh-sm2-app-readme-docs-drift](../issue/dwh-sm2-app-readme-docs-drift) |
| Repo bloat / confusing docs | 3 dbt-docs generations, datex.old, tmp_docs, .gitignore `!docs/**` leak | [dwh-sm2-app-stale-artifacts-tracked](../issue/dwh-sm2-app-stale-artifacts-tracked) |
| dbt behavior surprises | dead `*_original` configs, no-op `dbt deps`, sqlfluff dialect mismatch, analysis-paths collision | [dwh-sm2-app-dbt-config-dead-entries](../issue/dwh-sm2-app-dbt-config-dead-entries) |
| Environment drift | no dependency manifest; local dbt 1.7 vs CI 1.12.5 vs docs 1.9.1 | [dwh-sm2-app-dependencies-unpinned](../issue/dwh-sm2-app-dependencies-unpinned) |
| Lint gate kills the data pipeline | unpinned `sqlfluff fix` exits 1 on unfixable violations; dbt build + data commit skipped (live 2026-10-03 → 10-08, six consecutive failures; mitigated 2026-10-08: lint step pins `sqlfluff==4.3.0`) | [dwh-sm2-app-dependencies-unpinned](../issue/dwh-sm2-app-dependencies-unpinned) |
| Uncommitted work at risk | main-tree drift: Czech-labels feature + arch-doc deletion | [dwh-sm2-app-main-tree-drift](../issue/dwh-sm2-app-main-tree-drift) |

## Data Guarantees (additivity - verified in code, DWH-SM2-APP-0002)

The pipeline is append-only. No stage deletes or overwrites a reading:

- Fact models are `union distinct` of the new merge rows and the previous facts read back from Drive `Model/` (sources `fact_indoor_temperature_original` / `fact_indoor_humidity_original`); the only row filter is `source.datetime is not null`.
- The merge script drops rows where **both** temperature and humidity are empty (per-location "Location X nemeri" warning) but passes rows with **one** empty value; non-numeric values abort the merge (exit 6).
- The Influx import skips rows whose double field is empty (`--skipRowOnError`).

Operator consequences: re-uploading an **older** file than previously processed can never remove or overwrite already-valid readings; a file with **empty values for later dates** cannot blank out earlier valid values. Conversely, **deliberate** data removal (bad sensor, correction) has no pipeline path - it requires a manual `Model/` + rebuild operation; treat any such need as a story.

## Health Verification (how to know it works)

1. **Pipeline liveness**: GitHub → Actions → all three workflows show a successful run within the last 24 h. (There is no notification; checking is manual today.) Live proof this check matters: refresh failed six consecutive days (2026-10-03 → 10-08) unnoticed - [dwh-sm2-app-dependencies-unpinned](../issue/dwh-sm2-app-dependencies-unpinned).
2. **Freshness end-to-end**: `docs/datex/sm2_public_dataset.parquet` last bot-commit is ≤ 2 days old (commit "chore: update sm2_public_dataset.parquet for Data Explorer").
3. **Evidence freshness**: datex viewer (github.io) shows the most recent days for any section; frozen weekend readings are a known data-quality pattern (parent Epic issue `atrea-weekend-frozen-readings`).
4. **Drive hygiene**: `sm2drive:{Vzduchotechnika,Indoor}/Latest/Upload` should stay near-empty (the refresh archive step purges it); accumulation means refresh is failing before its archive step.
5. **Fact upload really happened**: a green refresh conclusion is not proof the data moved. In the run log, the fact upload step must NOT print `fact_indoor_temperature.csv not found, skipping upload` (rclone prints nothing on success, so a real transfer shows as a ~10 s gap instead). A skip means `Model/` was not updated and every downstream stage republishes stale data - [dwh-sm2-app-refresh-freshness-silent-skip](../issue/dwh-sm2-app-refresh-freshness-silent-skip). After re-uploading sensor exports whose latest reading does not advance the recorded max, expect the `::warning::source_status:fresher+ selected no nodes - falling back to full dbt build` annotation (the fix turning this case into a full rebuild).
6. **Manual recovery**: every workflow has `workflow_dispatch` - re-run the failed stage from the Actions UI after fixing the cause; stages are independent beyond their Drive inputs. Worked full-pipeline recovery from stale `Model/` (verified live 2026-10-08, after the silent-skip fix): (1) re-upload the **complete** sensor export set - not a partial one - to `sm2drive:{Vzduchotechnika,Indoor}/Latest/Upload`; (2) dispatch refresh (`gh api repos/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2/actions/workflows/139023652/dispatches -f ref=main`) - on a content-only re-upload expect the `::warning::...falling back to full dbt build` annotation and a red-but-green selective step (by design, v0.0004.1.0002.00); (3) verify the fact upload per item 5; (4) dispatch InfluxImportNormalize (workflow id 177614384); (5) dispatch Publish Public Dataset (workflow id 184554441); (6) confirm the datex bot commit (item 2) is newer than the dispatch timestamp.

## Operating Notes

- Local dbt runs need the venv with `dbt-duckdb` (CI runs 1.12.5; local tree shows 1.7.19 artifacts) - expect dialect differences until [dwh-sm2-app-dependencies-unpinned](../issue/dwh-sm2-app-dependencies-unpinned) is resolved.
- `analysis/quasistationary_selection.py` takes `--parquet docs/datex/sm2_public_dataset.parquet --out <dir>`; its committed outputs in `analysis/` are story deliverables, not pipeline products.
- Never edit `docs/dwh-sm2/` or `docs/tmp_docs/` - they are stale snapshots pending removal.

## Related

- [dwh-sm2-app-application-blueprint](../ontology/dwh-sm2-app-application-blueprint) - what the application is
- [dwh-sm2-app-pipeline-blueprint](../ontology/dwh-sm2-app-pipeline-blueprint) - stage sequence
- [DWH-SM2-APP-0001](../story/DWH-SM2-APP-0001) - the audit story
