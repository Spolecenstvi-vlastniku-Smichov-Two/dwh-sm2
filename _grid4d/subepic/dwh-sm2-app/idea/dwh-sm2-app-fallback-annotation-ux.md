# Make the deliberate full-build fallback visually distinct from real errors

**Created:** 2026-10-08 (DWH-SM2-APP-0003, from the DWH-SM2-APP-0002 recovery experience)

## Context

The refresh freshness guard (v0.0004.1.0002.00) detects content-only uploads by failing the selective build step on purpose (`exit 1` under `continue-on-error: true`) so the existing `Full dbt build` fallback fires. Functionally correct — but in the Actions UI the healthy recovery path renders as a red `##[error]Process completed with exit code 1.` annotation plus a red X on the step, with only the accompanying `::warning::` line explaining it. During the live verification the Human's first question about the healthy run was whether that error is expected — exactly the misread the pipeline should not invite on a legal-evidence pipeline where red must mean broken.

## Proposal

Split detection from execution so the deliberate branch never needs a failing step:

- A dedicated detection step (`id: detect`) runs the selective build, writes `outputs.fallback` (`true`/`false`), and never fails.
- The full-build fallback step keys on `steps.detect.outputs.fallback == 'true'` instead of `steps.run_dbt_build.outcome != 'success'` (real dbt errors still fail the detection step directly and keep their genuine red).
- Optionally rename the steps so the UI reads as intent: "Run dbt build (selective)", "Run dbt build (full fallback on content-only change)".

## Value

Red in the Actions tab means broken, nothing else. Removes the "is this error OK?" question from every future content-only re-upload day; keeps genuine dbt failures loud.

## Related

- [dwh-sm2-app-refresh-freshness-silent-skip](../issue/dwh-sm2-app-refresh-freshness-silent-skip) - resolved incident this UX wart belongs to
- [dwh-sm2-app-actions-log-echo-pollution](../issue/dwh-sm2-app-actions-log-echo-pollution) - same verification-clarity theme
