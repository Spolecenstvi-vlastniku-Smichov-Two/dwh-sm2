# Issue: Atrea weekend frozen readings

**Type:** data-quality (entropy) · **Status:** mitigated downstream, upstream open · **Found:** 2026-09-22 (DWH-SM2-0002)

## Symptom

Atrea VZT units (sections `sm2_01..09`) only transmit values while polled. On Saturday+Sunday pairs the same value is carried over for the whole weekend: a day whose hourly series has **std < 0.1 °C with ≥ 12 readings** is a stale repeated value, not a measurement. Affects all Atrea data keys — observed on `temp_ambient` and `temp_indoor`; weekend outdoor "maxima" are frozen plateaus (e.g. 2024-07-20/21 flat at ~30.4 °C, 2024-07-13/14 at ~25.5 °C).

## Impact

- Weekly/period aggregates computed naively (means, min/max, windows of "consecutive days") silently include non-measurements.
- For the expert evidence (DWH-SM2-0002) a frozen day cannot testify that outdoor maxima stayed ≤ 30 °C — the value is stale.
- Indoor freeze also flattens weekend room aggregates per section.

## Mitigation in place

`analysis/quasistationary_selection.py` flags such days (`frozen = std < 0.1 and n >= 12`, see `analysis/outdoor_daily_classification.csv`) and:
- excludes them from quasi-stationary window day-counting (windows must contain ≥ 3 real days),
- shades them orange in `analysis/window_*.png`,
- keeps them visible in the daily classification for auditability.

## Open

- Upstream fix: poll the Atrea units (or cache-and-mark) on weekends so carried-over values are distinguishable from real flat profiles — belongs to the dwh-sm2 pipeline (`refresh.yml` path), not to consumers.
- Near-frozen days (std slightly above 0.1) may still hide partial freezes; threshold is conservative by design.
