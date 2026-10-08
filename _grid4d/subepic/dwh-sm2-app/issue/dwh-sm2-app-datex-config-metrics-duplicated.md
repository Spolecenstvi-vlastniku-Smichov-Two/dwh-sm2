# config.js defines metrics twice - the second block silently shadows the first

**Status:** open
**Found:** 2026-10-08 (DWH-SM2-APP-0004 audit)

## Problem

`docs/datex/config.js` defines the `metrics` key twice inside the `DATASET_CONFIG` object literal:

- lines 120-147: `// Definice metrik - řídí filter UI a chování`
- lines 254-281: `// ===== METRIKY ===== ... oddělené od location hierarchie`

Both blocks are byte-identical today (542 chars, keys `temp_indoor`, `temp_ambient`, `temp_fresh`, `temp_intake`, `temp_waste`), so the duplication is currently harmless at runtime. `config_en.js` carries the identical duplication (also lines 120/254 - verified). But in a JavaScript object literal the **last** definition wins silently: any future edit to the first block (line 120) has no effect on the application, with no error and no warning.

## Why It Matters

The metrics block drives the filter UI and per-metric behavior (`global`, `aggregateLocation` flags). A maintainer tuning metric flags in the wrong (first) block will see zero effect and likely "fix" it by also editing the second block - or worse, diverge the blocks and lose track of which one is live. `config_en.js` has the same structure and must be checked when fixing.

## Solution Direction

Delete one of the two blocks (keep the later one with the clearer sectioning comment, or merge comments), then assert single-definition in a lightweight way - e.g. a test that counts `^  metrics: {$` occurrences in `config.js` and `config_en.js` (expect 1 each). Next-phase implementation story; this story documented the viewer and captured the trap only.

## Related

- `docs/datex/README.md` - the viewer documentation founded with this issue
- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - datex row in the coverage map
