# Issue: macOS BSD awk locale-dependent decimal conversion

**Type:** environment quirk · **Status:** solved (workaround in place) · **Found:** 2026-09-23 (DWH-SM2-0002 tests)

## Symptom

macOS `awk version 20200816` (BSD awk, `/usr/bin/awk`) converts numeric strings **locale-dependently**.
Under `LC_NUMERIC` with a decimal comma (e.g. `cs_CZ`):

- `"31.09999999999997"+0` → `31` (conversion stops at the dot)
- `sprintf("%.1f", 31.0)` → `31,0` (comma output)
- but a **raw numeric comparison of the field itself works**: `$4>31` → true (correct internal parse)

Result: awk asserts written as `$field+0>limit` silently fail for non-integer limits, while the
same comparison without `+0` works. Plain-integer data (`"5.0"+0 > 0`) can pass by accident and
mask the bug.

## Repro

```sh
awk 'BEGIN{v="31.09999999999997"; print v+0, v>31}'   # 31   1   <- +0 truncates, raw compare fine
LC_ALL=cs_CZ.UTF-8 awk 'BEGIN{printf "%.1f\n", 31}'    # 31,0
```

## Rule for ahabase test suites and one-liners

- Never cast CSV fields with `+0`/`*1` before comparing; compare the raw field (`$4>31`) — awk's
  strnum-to-number comparison parses the value correctly regardless of locale.
- Never `sprintf("%.Nf")` numbers for further parsing — output carries the locale decimal comma.
- Prefer thresholds with a margin so plain-integer string forms cannot pass accidentally.
- Fixed for good in `DWH-SM2-0002-tests.md` (R2/R3); first found there.
