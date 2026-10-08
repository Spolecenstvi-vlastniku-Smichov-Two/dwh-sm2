# SM2 Data Explorer (datex)

> Static in-browser viewer over the public SM2 temperature dataset - no build step, no backend.

**Maintained by:** the Publish Public Dataset workflow (the parquet here is a pipeline output, not a hand-edited file)
**Documented:** 2026-10-08 (DWH-SM2-APP-0004)

## What this is

A single-page application that renders the published SM2 dataset (`sm2_public_dataset.parquet`) as filterable time-series charts. Everything runs client-side: the parquet is fetched and decoded in the browser, so the viewer is deployable as plain static hosting (GitHub Pages).

## Files

| File | Role |
|------|------|
| `index.html` | the whole SPA: filters, chart, state, URL param handling |
| `config.js` | Czech configuration (`DATASET_CONFIG`: sources, locations, metrics, granularity, i18n) |
| `config_en.js` | English configuration (same shape) |
| `styles.css` | layout and theming |
| `sm2_public_dataset.parquet` | the data (3.1 MB, CC BY 4.0) |

## How it renders

Dependencies come from the jsDelivr CDN at runtime - there is no bundler and no `node_modules`:

- **Chart.js** (`cdn.jsdelivr.net/npm/chart.js`) - chart rendering
- **hyparquet** 1.0.0 (`parquetRead`) - decodes the parquet in the browser
- **apache-arrow** 14.0.0 - column data plumbing

Language is selected by the `lang` URL parameter (`?lang=en` loads `config_en.js`, the default `cz` loads `config.js`); `changeLanguage()` rewrites the parameter and reloads.

## Data dependency (the part that matters operationally)

The parquet in this directory is refreshed **daily** by the `Publish Public Dataset` workflow (cron `30 1 * * *`): `build_public_dataset.py` rebuilds it from the hourly aggregates in `sm2drive:Normalized/` and the workflow bot-commits it here (`chore: update sm2_public_dataset.parquet for Data Explorer`). A stale last-bot-commit therefore means the whole upstream pipeline is stale - see Health Verification in the [runbook](../../_grid4d/subepic/dwh-sm2-app/implementation/dwh-sm2-app-runbook.md).

## Running locally

The SPA fetches the parquet over HTTP, so serve the repo root instead of opening `index.html` from `file://`:

```bash
python3 -m http.server
# then open http://localhost:8000/docs/datex/
```

## Known issue

`config.js` defines `metrics:` twice (identical blocks at lines 120 and 254; the second silently shadows the first) - [dwh-sm2-app-datex-config-metrics-duplicated](../../_grid4d/subepic/dwh-sm2-app/issue/dwh-sm2-app-datex-config-metrics-duplicated.md). Fixing the JS is next-phase implementation work.
