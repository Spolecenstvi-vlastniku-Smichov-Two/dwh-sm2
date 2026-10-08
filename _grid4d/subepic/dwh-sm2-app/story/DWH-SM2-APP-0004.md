# DWH-SM2-APP-0004: Functional inventory and documentation coverage of the dwh-sm2 repository

> Functional inventory and documentation coverage of the dwh-sm2 repository

**Type:** default
**Epic:** [DWH-SM2-APP](../DWH-SM2-APP)
**Status:** in_progress
**Blueprint:** [implementation-story-blueprint](implementation-story-blueprint)

## Goal

Functional inventory and documentation coverage of the dwh-sm2 repository

## Requirements

### R1: Refresh the audit baseline for the post-0002 state ✅

The DWH-SM2-APP-0001 component inventory (runbook) predates the refresh freshness guard (v0.0004.1.0002.00). Re-verify the inventory against the tree and update what changed: the refresh workflow row (content-only guard → full-build fallback), and the Documentation Coverage Map rows this story touches.

**Acceptance Criterion:** Runbook Component Inventory refresh row mentions the content-only upload guard; coverage map reflects this story's README and datex outcomes.

### R2: Repair the README operational sections (resolves readme-docs-drift) ✅

Fix every false claim listed in [dwh-sm2-app-readme-docs-drift](../issue/dwh-sm2-app-readme-docs-drift): publish cadence weekly→daily `30 1 * * *` (README 92-98, 449-461), push-trigger claims removed (116-119, 444-447, 1039), ventilation merge attributed to the inline csvkit step (not `indoor_merge_all_sensors.sh`), `indoor_merge_all_sensors.sh` documented as v3.1 (not v2.2), annotated-CSV header shows the `_field` column (7 columns), `check_and_import_previous_exports.py` documented with its real semantics (no `--skipRowOnError`, exits 0), seed history values 4/2/2 (Atrea/ThermoPro), and the duplicated/mislabeled workflow section around line 340 corrected. Add a pointer that the operational source of truth is the runbook.

**Acceptance Criterion:** Issue flips to resolved; a README-facts grep finds `30 1 * * *`/daily cadence and no `10 2 * * 6`, no push-trigger claim, no v2.2, correct script attribution.

### R3: Document the datex viewer and capture its config duplication ✅

The datex viewer has no documentation of its own (coverage map: none). Add `docs/datex/README.md` describing what it is, its files (index.html, config.js/config_en.js, styles.css, the parquet), how it renders (Chart.js + hyparquet from CDN), and its dependency on the publish bot commit. Capture the verified finding that `config.js` defines `metrics:` twice (lines ~120 and ~254; the second silently shadows the first) as an open issue - fixing the JS is next-phase implementation work, out of this story's documentation scope.

**Acceptance Criterion:** `docs/datex/README.md` exists with the component description; new issue `dwh-sm2-app-datex-config-metrics-duplicated` captures the duplication with line references and consequence.

### R4: Tests pin the repaired documentation ✅

README-facts test suite: cron/cadence claims, absence of drift strings (weekly cron, push trigger, v2.2), script-attribution correction, datex README existence, runbook coverage-map update.

**Acceptance Criterion:** Story tests pass; yaml parses before complete.

## Notes

Created: 2026-10-08

Audit finding shaping this story: the DWH-SM2-APP-0001 inventory already covers the functional sweep (Component Inventory + Documentation Coverage Map, both 2026-10-08); the genuine gap is the open documentation defects that map exposes - README drift (this story fixes), datex undocumented (this story documents), stale artifacts (separate issue backlog). Phase discipline per the plug-and-play direction: audit/documentation first, implementation (config.js fix, chaining, sensors) later.
