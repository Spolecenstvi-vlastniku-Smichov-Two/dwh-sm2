# Atrea ventilation exports lag months behind - location gaps that look like an incident

**Status:** open (expected source behavior, documented as a diagnostic trap)
**Found:** 2026-10-08 (post-recovery data completeness check)

## Problem

The Atrea ventilation export (locations `sm2_01`..`sm2_09`, `SM2_03_L5_355_IN`, `SM2_03_L5_355_OUT`, `3PP-S7` = 12 of the ~38 published locations) arrives months after the fact. Until it is delivered and uploaded, the published dataset shows those locations ending mid-month (September 2026: present through Sep 14, gone from Sep 15; 26 locations instead of 38) while indoor sensors continue. To an operator checking coverage this looks exactly like a data-loss incident - it is not; it is source lag.

## Symptoms

- Month coverage query (`count(distinct location)` per month over the published parquet) shows a 38 → 26 location drop at 2026-09-15; the same 12 names are absent through the dataset tail.
- InfluxImportNormalize wall time varies with the month set (`months_to_process.json` = months present in `Model/` facts): a run covering 4 months (Jul..Oct, 2026-10-08 10:17, ~3.5 min) is markedly faster than one covering 6 months (May..Oct, 06:38, ~6 min). Faster-than-usual Influx runs are a symptom of a narrower month set, never of data loss - months outside the set ride through untouched from the Drive `Influx/` monthly archive and `Normalized/` per-month files.

## Solution Direction

None needed for the lag itself (source reality). What to keep:

1. Before alarming on location gaps, check whether the missing names are the Atrea set above and whether the gap start aligns with an export boundary - if yes, wait for the Atrea export.
2. When the Atrea export arrives: upload it, run the standard recovery sequence (runbook Health Verification item 6). Its readings are older than the recorded max, so max(loaded_at) will NOT advance - this is precisely the content-only change the freshness guard (v0.0004.1.0002.00) exists to catch; expect the `::warning::...falling back` annotation and a full rebuild, after which `months_to_process.json` gains the backfilled months and Influx re-exports them.

## Occurrences

- **2026-10-08**: post-recovery completeness check on the freshly published parquet (bot commit 10:22:42 UTC) found Sep at 26 locations / Oct at 6 days. Human confirmed: Atrea September data has not arrived yet ("za září ještě nemáme Atrea data, ty teprve přijdou"); indoor sensor files end 2026-10-05/06 (no newer data obtainable). Full history 2023-11..2026-10 otherwise present.

## Related

- [atrea-weekend-frozen-readings](../../../issue/atrea-weekend-frozen-readings) - the other known Atrea data-quality pattern (parent Epic issue)
- [dwh-sm2-app-refresh-freshness-silent-skip](dwh-sm2-app-refresh-freshness-silent-skip) - the guard that will make the future Atrea backfill land
- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - recovery sequence (Health Verification item 6)
