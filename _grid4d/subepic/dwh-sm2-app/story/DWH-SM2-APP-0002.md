# DWH-SM2-APP-0002: Refresh workflow falls back to full dbt build when the freshness selection is empty (content-only source changes are otherwise silently skipped)

> Refresh workflow falls back to full dbt build when the freshness selection is empty (content-only source changes are otherwise silently skipped)

**Type:** default
**Epic:** [DWH-SM2-APP](../DWH-SM2-APP)
**Status:** completed
**Blueprint:** [implementation-story-blueprint](implementation-story-blueprint)

## Goal

When the refresh workflow's selective dbt build selects no nodes (`source_status:fresher+` matches nothing), the run must still rebuild the fact tables and upload them to `sm2drive:Indoor/Model/`. Today that case exits 0, the `Full dbt build` fallback never fires, the fact upload step prints `not found, skipping upload`, and the workflow stays green while `Model/` keeps serving the previous sensor set to every downstream stage.

## Requirements

### R1: Empty freshness selection with uploaded rows triggers the full-build fallback

The `Run dbt build` step (`refresh.yml`) captures its own output and exits 1 when dbt reports that `source_status:fresher+` does not match any enabled nodes **and** the day's merge outputs contain data rows (`all_sensors_merged.csv` or `merged.csv` has more than the header). With the step's existing `continue-on-error: true`, outcome `failure` drives the already-present `Full dbt build` step (`if: steps.run_dbt_build.outcome != 'success'`), so the fact models materialize and the fact upload step finds `./fact_indoor_*.csv` at the repo root.

**Acceptance Criterion:** `.github/workflows/refresh.yml` contains the tee+grep guard keyed to `source_status:fresher+` (not to the benign `result:error+` warning that healthy runs also emit) AND the merge-rows condition, followed by `exit 1`, with `continue-on-error: true` preserved on the step.

### R2: The guard classifies all four day-types correctly

The guard must not change behavior on days where rebuilding would be waste or where the selective build already worked: (a) fresher-empty + uploaded rows → fallback (the incident case), (b) fresher-empty + header-only merges (no Upload that day) → skip, exactly as today - no daily reprocessing of unchanged facts, (c) healthy day (`result:error+` warning only, fresher matched) → skip, selective build already ran, (d) fresher-empty + ventilation rows only → fallback.

**Acceptance Criterion:** A locally executed rehearsal of the exact guard pipeline (ANSI-strip sed + grep + row counts) under `bash -e` classifies all four scenarios correctly, including the ANSI-colored warning line captured from run 37756665551 and the healthy-run line from 37735598512.

### R3: Incident captured as an issue

The root cause, evidence, and recovery are recorded in `issue/dwh-sm2-app-refresh-freshness-silent-skip.md` with the run IDs of the affected and contrast runs.

**Acceptance Criterion:** The issue file exists in this story's worktree, status open, Occurrences naming runs 37738331019 / 37756665551 (skipped) and 37735598512 (rebuilt).

### R4: Runbook health verification covers the silent-skip class

The runbook's Health Verification section gains a check for the fact upload actually having happened (`not found, skipping upload` absent for indoor facts; `::warning::` fallback annotation expected on content-only re-uploads).

**Acceptance Criterion:** `implementation/dwh-sm2-app-runbook.md` Health Verification contains the fact-upload check referencing the issue.

## Implementation Notes

- Minimal-diff choice: keep the selective path for the normal day (new readings → `fresher` matches → selective build runs) and extend what counts as "step failure" to include the empty selection. The simpler alternative - always running the full build (3 models, ~2 s in run logs) - was rejected after the Human's review question: it would rebuild and re-upload ~105 MB of unchanged facts every Upload-empty day. It stays documented in the issue's Solution Direction as a legitimate simplification if this step is ever revisited.
- The grep is deliberately keyed to `source_status:fresher+`: `result:error+ does not match` appears on healthy days too (run 37735598512) and must not trigger the fallback.
- The merge-rows gate (`wc -l` of `all_sensors_merged.csv` / `merged.csv` > 1) is the discriminator between "nothing arrived" (keep today's skip; the union would reproduce identical facts anyway) and "something arrived but freshness cannot see it" (rebuild). It answers the Human's daily-reprocessing concern: an Upload-empty day behaves exactly as before the fix.
- `sed 's/\x1b\[[0-9;]*m//g'` strips ANSI color codes before the grep; the captured incident lines carry `[33mWARNING[0m`-style sequences.
- Verification of the guard against captured lines from the real runs under `bash -e` (Actions' default shell for `run:` on Linux) is R2; live end-to-end proof (fallback fires in Actions, facts upload, datex recovers) is the recovery sequence in Notes and will be appended to the issue Occurrences after the Human-confirmed merge.

## Notes

- Found live on 2026-10-08: Human re-uploaded the complete 26-sensor export set after a partial first upload; datex kept showing the partial sensor set. Diagnosis in-session from Actions logs of runs 37756665551 / 37738331019 / 37735598512 (contrast), see the issue file.
- Recovery blocked on this fix: Human has no sensor access right now, so no reading newer than the recorded max can be produced - the freshness criterion cannot be advanced by data alone. The fix is the unblock: after merge, re-uploading the same all-sensor files dispatches refresh → fallback full build → facts rebuilt (union distinct with previous `Model/` facts, so the partial set is superseded) → upload → Influx → Publish → datex complete.
- Post-merge sequence: re-upload all-sensor exports to `sm2drive:Indoor/Latest/Upload` → dispatch refresh → verify the upload step shows no `not found, skipping upload` (and the `::warning::` fallback annotation) → dispatch InfluxImportNormalize → dispatch Publish Public Dataset → verify datex.

Created: 2026-10-08
