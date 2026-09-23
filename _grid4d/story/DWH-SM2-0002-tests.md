# DWH-SM2-0002-tests

> Test definition for DWH-SM2-0002 with one test per requirement.

## Design

Verify the committed analysis deliverables rather than re-running against the parquet: the
selection outputs are deterministic products of `analysis/quasistationary_selection.py` over the
published dataset, and the parquet lives outside the Epic (environment-dependent re-runs would
break on any other machine). Tests are epic-root relative (run from the story worktree) and use
POSIX sh with awk field positions from the CSV headers. awk comparisons use the raw field
(`$4>31`), never `$4+0`: the macOS BSD awk (20200816) converts numbers locale-dependently, so
under a decimal-comma LC_NUMERIC the `+0` cast truncates "31.099..." to 31 (see
`_grid4d/issue/macos-awk-locale-decimal-conversion.md`).

## Definition

```yaml
tests:
  - name: R1_window_selection_outputs
    description: summary lists exactly 8 windows including the two decisive section-level and room-level cases
    command: |
      test -f analysis/window_summary.csv &&
      test "$(tail -n +2 analysis/window_summary.csv | grep -c .)" -eq 8 &&
      grep -qF '2024-08-02..2024-08-04' analysis/window_summary.csv &&
      grep -qF '2026-07-08..2026-07-11' analysis/window_summary.csv
    expect:
      exit_code: 0
  - name: R2_frozen_flag_and_real_days
    description: daily classification carries the frozen flag and every window keeps at least 3 real days
    command: |
      head -1 analysis/outdoor_daily_classification.csv | grep -q ',frozen' &&
      grep -q ',True' analysis/outdoor_daily_classification.csv &&
      awk -F, 'NR>1 && $3<3 {exit 1}' analysis/window_summary.csv
    expect:
      exit_code: 0
  - name: R3_decisive_windows_indoor_gt30
    description: three sections exceeded 30 degC in Aug 2024 and room 5NP-S3 exceeded it in both ThermoPro windows
    command: |
      awk -F, 'NR>1 && $7>0 {n++} END {exit n==3?0:1}' analysis/indoor_sections_2024-08-02_2024-08-04.csv &&
      awk -F, '$1=="5NP-S3" && $4>31 {f=1} END {exit f?0:1}' analysis/thermopro_rooms_2026-07-08_2026-07-11.csv &&
      awk -F, '$1=="5NP-S3" && $4>30.5 {f=1} END {exit f?0:1}' analysis/thermopro_rooms_2025-08-19_2025-08-21.csv
    expect:
      exit_code: 0
  - name: R4_report_documents_deliverables
    description: report documents the decisive windows and caveats and the frozen-weekend issue is logged
    command: |
      test -f analysis/DWH-SM2-0002-report.md &&
      grep -qF '2026-07-08..11' analysis/DWH-SM2-0002-report.md &&
      grep -q 'Frozen weekends' analysis/DWH-SM2-0002-report.md &&
      test -f _grid4d/issue/atrea-weekend-frozen-readings.md
    expect:
      exit_code: 0
  - name: R5_candidate_evidence_table
    description: candidates.csv lists 3 Atrea section averages for Aug 2024 and measured corridor sensor 5NP-S3 for both ThermoPro windows
    command: |
      test -f analysis/candidates.csv &&
      test "$(grep -cF '2024-08-02..2024-08-04,atrea_section_average' analysis/candidates.csv)" -eq 3 &&
      grep -qF '2025-08-19..2025-08-21,thermopro_measured_corridor_5np,5NP-S3,30.9' analysis/candidates.csv &&
      grep -qF '2026-07-08..2026-07-11,thermopro_measured_corridor_5np,5NP-S3,31.1' analysis/candidates.csv
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_window_selection_outputs | ✅ | 2026-09-23 |
| R2_frozen_flag_and_real_days | ✅ | 2026-09-23 |
| R3_decisive_windows_indoor_gt30 | ✅ | 2026-09-23 |
| R4_report_documents_deliverables | ✅ | 2026-09-23 |
| R5_candidate_evidence_table | ✅ | 2026-09-23 |

## Related

- [DWH-SM2-0002](DWH-SM2-0002) - Parent story

---
## _behavior

validation:
  required_sections: [Design, Definition, Execution]
  definition_format: yaml_code_block
