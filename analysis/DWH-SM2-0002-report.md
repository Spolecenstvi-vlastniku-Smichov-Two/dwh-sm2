# DWH-SM2-0002 — Quasi-stationary heat-period selection (expert request)

Analysis date: 2026-09-22 · Dataset: `sm2_public_dataset.parquet` (wiki "Live Files", 2026-09 export, 1 474 476 hourly rows, 2023-11 → 2026-09) · Script: `quasistationary_selection.py`

## 1. Request

Expert M. Zálešák (email 2026-09-21, see `_inbox/dwh-sm2/teploty SM2.eml`, attachment `zalesak.pdf`) asks for a selection of **quasi-stationary thermal periods** — outdoor conditions similar to (or slightly below) the normative design day of ČSN 73 0540-3 — lasting **at least 3 days**, and an evaluation of indoor temperatures against the ČSN 73 0540-2 limit **θ_o,max,RQ = 27.0 °C operative temperature** (clause 8.2.4, Table 9). The alternative reading of the same limit is **30.0 °C air temperature** when the mean room-surface temperature is ≈ 24 °C.

**Confirmed selection criterion (Human, 2026-09-22):** periods of **≥ 3 consecutive days whose daily outdoor temperature maxima do not exceed 30 °C** (the design-day peak, 15:00 h, from the expert's attachment), and the indoor evaluation checks whether **indoor maxima exceed 30 °C** (air limit) as well as the share of hours above the 27 °C operative limit.

## 2. Data and reference sensors

| Role | Source | Notes |
|---|---|---|
| Outdoor reference | Atrea `temp_ambient`, location `sm2_01` | Only continuous ambient series after 2024-11; cross-section spread ≤ 0.1 °C (sensors effectively identical) |
| Indoor, section level | Atrea `temp_indoor`, `sm2_01..09` | **Average** air temperature extracted from **all flats of the section** (1–9), not individual flats — a section average above the limit is a lower bound: the critical flats were necessarily hotter |
| Indoor, corridor level | ThermoPro `temp_indoor`, `1NP-S1..S9`, `5NP-S1..S9` | **Real measured temperatures on the floor corridors** — spaces with practically no internal gains (no people/appliances), so corridor overheating is structural/solar and flats with internal gains are expected hotter; the top floor (5NP) is the focus. Installed summer 2025; ground-floor sensor set also includes `*PP-*` garage locations (excluded here) |

All series are hourly, Europe/Prague local time. **Data-quality caveat — frozen weekends:** the Atrea unit only transmits while polled; on Saturday+Sunday pairs the same value is carried over (day std < 0.1 °C with ≥ 12 readings). Such *frozen* days are flagged per day and excluded from window day-counting; they are shaded orange in the window graphs and marked in `outdoor_daily_classification.csv` (column `frozen`). Logged as a data-quality issue: `_grid4d/issue/atrea-weekend-frozen-readings.md`.

## 3. Selection method

1. Daily outdoor statistics from the `sm2_01` ambient series.
2. A day is a **quasi-stationary warm candidate** only when it is warm — similar to or slightly below the design day, not merely below its peak: `tmax ≥ 26 °C` and `tmin ≥ 13 °C` (keeps winter/shoulder days out; design-day night minimum is 16.0 °C).
3. Day classes by daily maximum: **A** `tmax ≤ 30.0` (at/below normative peak — the criterion), **B** `30–33`, **C** `> 33`.
4. **Window = ≥ 3 consecutive class-A days containing ≥ 3 real (non-frozen) days.**
5. Indoor evaluation per window: per-section and per-room daily min/mean/max, share of hours above 27 / 30 °C, number of days whose indoor daily max exceeds 30 °C, and the night minimum (00–05 h) — the building's ability to cool down overnight.
6. **Candidate evidence table** (`candidates.csv`): every location whose indoor maximum exceeds the 30 °C air limit inside a selected window — measured 5NP rooms (ThermoPro, real room measurements) and section averages (Atrea, lower bound for the flats).

## 4. Results

Eight windows satisfy the outdoor criterion (full per-window tables in `window_summary.csv`, `indoor_sections_*.csv`, `thermopro_rooms_*.csv`; graphs `window_*.png`, hourly exports `hourly_*.csv`):

| Window | Days (real) | Outdoor daily max | Indoor maxima while outdoor ≤ 30 °C | Indoor > 30 °C? |
|---|---|---|---|---|
| 2024-06-28..07-02 | 5 (3; 2 frozen) | 26.3–30.0 | sections ≤ 29.8, sm2_03 mean 29.1 | no |
| **2024-08-02..04** | 3 (3) | **26.3–28.4** | **section averages: sm2_01 30.3 · sm2_08 30.2 · sm2_04 30.1** (sm2_03 = 30.0) | **yes — 3/9 sections** |
| 2025-06-01..03 | 3 (3) | 26.0–28.1 | sections ≤ 27.0 (early summer) | no |
| 2025-07-21..27 | 7 (7) | 26.6–29.8 | sections ≤ 28.3; sm2_03 95 % of hours > 27 | no |
| 2025-08-10..12 | 3 (3) | 27.1–29.7 | sensors: max 29.9, 2/3 > 27 | no |
| **2025-08-19..21** | 3 (3) | 27.2–29.2 | **corridor 5NP-S3 measured max 30.9** (100 % h > 27) | **yes — measured** |
| **2026-07-08..11** | 4 (4) | **26.8–28.3** | **corridor 5NP-S3 measured max 31.1**, mean 29.0, 100 % h > 27; 16/18 sensors > 27 | **yes — measured** |
| 2026-08-19..21 | 3 (3) | 28.8–29.5 | sensors max 28.5; 15/18 > 27 | no |

### 4.1 The three decisive windows (outdoor ≤ 30 °C, indoor > 30 °C)

Candidate locations — indoor maxima above the 30 °C air limit while the outdoor criterion held (`candidates.csv`; all with 100 % of hours above 27 °C):

| Window | Source | Location | Indoor max | Note |
|---|---|---|---|---|
| 2024-08-02..04 | Atrea, section average | `sm2_01` | **30.3 °C** | average over all flats of section 1 — flats were hotter |
| 2024-08-02..04 | Atrea, section average | `sm2_08` | **30.2 °C** | average over section 8 (`sm2_04` 30.1 °C, `sm2_03` exactly 30.0 °C) |
| 2025-08-19..21 | ThermoPro, measured corridor | `5NP-S3` | **30.9 °C** | top floor, section 3 — real measurement on the floor corridor |
| 2026-07-08..11 | ThermoPro, measured corridor | `5NP-S3` | **31.1 °C** | top floor, section 3 — real measurement on the floor corridor |

- **2024-08-02..04** — outdoor peaked at just **28.4 °C** (design day: 30.0). Section-extracted air: `sm2_01` 30.3 °C (5 h above 30), `sm2_08` 30.2 °C, `sm2_04` 30.1 °C; **all nine sections spent 93–100 % of hours above 27 °C**, night minima 27.3–28.8 °C. ThermoPro corridor sensors did not exist yet (installed summer 2025). See `window_2024-08-02_2024-08-04.png`, `indoor_sections_2024-08-02_2024-08-04.csv`.
- **2025-08-19..21** — outdoor 27.2/29.2/27.4 °C. Measured corridor sensor **5NP-S3 (top floor, section 3) reached 30.9 °C**; 7/9 monitored locations above 27 °C, `5NP-S3`/`5NP-S7` 100 % of hours above 27 °C.
- **2026-07-08..11** — the strongest case: outdoor maxima only **26.8–28.3 °C** (≈ 2 K *below* the design-day peak all four days), yet measured **5NP-S3 reached 31.1 °C** (four-day mean 29.0 °C, 100 % of hours above 27 °C) and **16 of 18 sensors exceeded 27 °C**. See `window_2026-07-08_2026-07-11.png`, `thermopro_rooms_2026-07-08_2026-07-11.csv`.

### 4.2 Supporting evidence for the 27 °C operative limit

In every mid-summer window the section-extracted air stays above 27 °C for **95–100 % of hours, nights included** (night minima 27.1–28.8 °C) — the building does not cool down overnight even when outdoor air drops to 16–20 °C. During the true heat waves (outdoor above the design day, e.g. 2024-07-16..26 with outdoor up to 32.2 °C, or 2026-07-07..20 up to 32.5 °C) section air reached 30.2 °C with **100 % of hours above 27 °C** — kept in the outputs (`window_2024-07-16_2024-07-26.png` etc.) as context, although those windows contain days above 30 °C outdoor and therefore do not meet the strict criterion.

### 4.3 Interpretation for the expert's question

Even under outdoor conditions **not worse than the normative design day** (in the decisive windows: up to 2 K milder), measured indoor air temperatures exceed both the 27.0 °C operative limit and, at the hot spots, the alternative 30.0 °C air limit — without any cooling of supply air. In 2024 the > 30 °C evidence comes from **section averages** — by definition a lower bound, so individual flats were hotter still; in 2025/2026 the > 30 °C evidence comes from **real measurements on the 5th-floor corridors** (5NP-S3, up to 31.1 °C) — spaces with practically no internal gains, so overheated flats with their own gains are expected hotter. This supports the conclusion that **cooling of supply air is necessary** to keep the flats within ČSN 73 0540-2 requirements.

## 5. Caveats

- **Atrea `temp_indoor` is the average extracted air across ALL flats of a section (1–9)** — not individual flats; a section average above the limit implies the critical flats were hotter. Room-level ThermoPro measurements show higher values than the section aggregate (5NP-S3 vs section sm2_03).
- **Air vs operative temperature:** limits compared against measured air temperature. With warm surfaces the operative temperature is ≥ air temperature, so air > 27 °C implies operative > 27 °C; the 30 °C air limit applies only when mean surface ≈ 24 °C.
- **Frozen weekends** (Atrea polled only on weekdays): frozen days excluded from day-counting; 2024-06-28..07-02 window contains two such days (hence 3 real of 5).
- **ThermoPro sensors sit on the floor corridors** (1NP/5NP), not inside flats. Corridors have practically no internal heat gains (no people, no appliances), so their overheating is structural/solar — flats with ordinary internal gains are expected to be hotter. Whether a floor corridor can itself be treated as an evaluated "critical room" under ČSN 73 0540-2 is for the expert to qualify; the data show the exceedance regardless.
- **ThermoPro coverage starts 2025-08** and only floors 1NP/5NP are monitored — locations between floors and mid-summer 2024/2025 indoor maxima are not observed.
- **Location 5NP-S3 is a single persistent hot spot** (top floor corridor, section 3) — consistent with the expert's focus on section 3; it should ideally be backed by a second instrumented flat.

## 6. Reproduction

```bash
# analysis venv: /Users/lubomirkamensky/ahabase/_temp/dwh-sm2-analysis-venv
#                (Python 3.9; pandas, duckdb, matplotlib)
python analysis/quasistationary_selection.py \
    --parquet _inbox/dwh-sm2/sm2_public_dataset.parquet --out analysis
```

Output inventory: `outdoor_daily_classification.csv` (per-day class + frozen flag), `window_summary.csv`, `candidates.csv` (locations with indoor max > 30 °C per window), `indoor_sections_<window>.csv` ×8, `thermopro_rooms_<window>.csv` ×4, `hourly_<window>.csv` ×8, `window_<window>.png` ×8, `overview_2024/2025/2026.png`.
