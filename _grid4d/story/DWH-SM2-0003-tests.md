# DWH-SM2-0003-tests

> Test definition for DWH-SM2-0003 with one test per requirement.

## Design

Verify the committed analysis deliverables rather than re-running against the parquet: the
separate ThermoPro PNGs are deterministic products of `analysis/quasistationary_selection.py`
over the published dataset, and the parquet lives outside the Epic. PNG pixel content cannot
be asserted from POSIX sh, so R2 checks the generator integration (function defined and
invoked, series labels present in the source) — re-running the script is the reproducibility
guarantee. Tests are epic-root relative (run from the story worktree), POSIX sh.

## Definition

```yaml
tests:
  - name: R1_thermopro_window_pngs
    description: all four separate ThermoPro window PNGs exist, including both decisive windows
    command: |
      test -f analysis/window_thermopro_2025-08-10_2025-08-12.png &&
      test -f analysis/window_thermopro_2025-08-19_2025-08-21.png &&
      test -f analysis/window_thermopro_2026-07-08_2026-07-11.png &&
      test -f analysis/window_thermopro_2026-08-19_2026-08-21.png &&
      test "$(ls analysis/window_thermopro_*.png | grep -c .)" -eq 4
    expect:
      exit_code: 0
  - name: R2_generator_integration
    description: quasistationary_selection.py defines and calls plot_window_thermopro drawing outdoor, 5NP band, 5NP-S3 and both limits
    command: |
      grep -q 'def plot_window_thermopro' analysis/quasistationary_selection.py &&
      grep -q 'window_thermopro_' analysis/quasistationary_selection.py &&
      grep -q '5NP corridors min-max band' analysis/quasistationary_selection.py &&
      grep -q 'measured 5NP-S3 corridor' analysis/quasistationary_selection.py &&
      grep -q 'outdoor vs measured 5NP corridors' analysis/quasistationary_selection.py
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_thermopro_window_pngs | ✅ | 2026-09-23 |
| R2_generator_integration | ✅ | 2026-09-23 |

## Related

- [DWH-SM2-0003](DWH-SM2-0003) - Parent story
- [DWH-SM2-0002](DWH-SM2-0002) - Window selection and combined graphs

---
## _behavior

validation:
  required_sections: [Design, Definition, Execution]
  definition_format: yaml_code_block
