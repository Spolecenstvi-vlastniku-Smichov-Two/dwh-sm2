#!/usr/bin/env python3
"""Quasi-stationary heat period selection from the SM2 public dataset.

DWH-SM2-0002. Answers the expert request (M. Zalesak, email 2026-09-21):
select periods of quasi-stationary thermal conditions - outdoor conditions
similar to (or slightly below) the normative design day of CSN 73 0540-3,
lasting at least 3 days - and evaluate the indoor temperatures against the
CSN 73 0540-2 limit theta_o,max,RQ = 27.0 degC operative temperature
(30 degC air temperature if the mean surface temperature is ~24 degC).

Method:
  1. Outdoor reference = Atrea temp_ambient, location sm2_01 (the only
     section with continuous ambient data after 2024-11; cross-section
     spread is <= 0.1 degC, the sensors are effectively identical).
  2. Frozen-day flag: a day whose ambient hourly std < 0.1 degC carries a
     stale carried-over value (mostly weekends - the Atrea unit only
     records while polled). Frozen days are excluded from window counting.
  3. Day classes vs the normative design day (peak 30.0 degC at 15:00,
     minimum 16.0 degC at night). A day is a quasi-stationary candidate
     only when it is WARM - similar to (or slightly below) the design day,
     not merely below its peak: tmax >= 26 and tmin >= 13.
       A  tmax <= 30.0   at or below normative peak (Human-confirmed window
                         criterion: outdoor maxima stay <= 30 degC for
                         >= 3 consecutive days)
       B  30.0 < tmax <= 33.0   slightly above (breaks a window)
       C  tmax > 33.0   well above (breaks a window)
     Quasi-stationary window = >= 3 consecutive WARM class-A days with
     >= 3 real (non-frozen) days. Indoor evidence is evaluated against
     both limits: 27 degC operative and 30 degC air temperature.
  4. Indoor evidence (two sources, Human-confirmed interpretation):
     ThermoPro sensors sit on the floor CORRIDORS (floors 1NP/5NP) -
     real measured temperatures with practically no internal gains
     (people/appliances), so corridor overheating is structural/solar;
     flats with internal gains are expected hotter. The 5th floor (5NP)
     is the focus. Atrea temp_indoor per section (sm2_01..09) is the
     AVERAGE temperature of air extracted from all flats of the section,
     not individual flats: a section average above the limit is a LOWER
     BOUND - the critical flats were hotter. Metrics: daily min/mean/max,
     share of hours above 27/30 degC, and the night minimum (00-05h).
     Windows from 2025-08 on also get a separate graph
     (window_thermopro_*.png) plotting the measured 5NP corridors against
     the outdoor air.
  5. Candidate evidence table (candidates.csv): every location whose
     indoor max exceeds the 30 degC air limit inside a selected window -
     measured 5NP corridor sensors (ThermoPro) and section averages
     (Atrea).

Usage:
  python quasistationary_selection.py --parquet <sm2_public_dataset.parquet> \
      --out <output-dir>
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# CSN 73 0540-3 design outdoor air temperature, summer period (hour -> degC).
# Source: expert attachment "Letni obdobi" (zalesak.pdf), page 2.
DESIGN_DAY = {
    1: 16.9, 2: 16.2, 3: 16.0, 4: 16.2, 5: 16.9, 6: 18.1, 7: 19.5, 8: 21.2,
    9: 23.0, 10: 24.8, 11: 26.5, 12: 27.9, 13: 29.1, 14: 29.8, 15: 30.0,
    16: 29.8, 17: 29.1, 18: 28.0, 19: 26.5, 20: 24.8, 21: 23.0, 22: 21.2,
    23: 19.5, 24: 16.1,
}
LIMIT_OP = 27.0  # CSN 73 0540-2 Table 9, theta_o,max,RQ
LIMIT_AIR_ALT = 30.0  # air temperature limit if mean surface temp ~ 24 degC
PRAGUE = "Europe/Prague"

SECTIONS = [f"sm2_{i:02d}" for i in range(1, 10)]


def read_hourly(parquet: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (atrea_hourly, thermopro_hourly) with local-time columns."""
    con = duckdb.connect()
    atrea = con.execute(
        f"""
        SELECT time, location, data_key, data_value
        FROM read_parquet('{parquet}')
        WHERE source = 'Atrea' AND data_key IN
              ('temp_ambient', 'temp_indoor', 'temp_intake')
        """
    ).fetchdf()
    thermo = con.execute(
        f"""
        SELECT time, location, data_key, data_value
        FROM read_parquet('{parquet}')
        WHERE source = 'ThermoPro' AND data_key = 'temp_indoor'
          AND location LIKE '%NP-%'
        """
    ).fetchdf()
    con.close()
    for df in (atrea, thermo):
        df["time"] = pd.to_datetime(df["time"], utc=True).dt.tz_convert(PRAGUE)
        df["day"] = df["time"].dt.date
        df["hour"] = df["time"].dt.hour
    return atrea, thermo


def daily_outdoor(atrea: pd.DataFrame) -> pd.DataFrame:
    """Daily stats of the outdoor reference plus the frozen-day flag."""
    amb = atrea[(atrea["location"] == "sm2_01") & (atrea["data_key"] == "temp_ambient")]
    g = amb.groupby("day")["data_value"]
    daily = pd.DataFrame({
        "n": g.count(),
        "tmin": g.min(),
        "tmean": g.mean(),
        "tmax": g.max(),
        "sd": g.std(),
    })
    daily["frozen"] = (daily["sd"] < 0.1) & (daily["n"] >= 12)
    # warm candidate: similar to (or slightly below) the summer design day,
    # not just any day below its peak - this keeps winter/shoulder days out
    warm = (daily["tmax"] >= 26.0) & (daily["tmin"] >= 13.0)
    # class A = outdoor tmax at/below the design-day peak (30.0 degC) - the
    # window criterion; B and C only annotate hotter days and break windows
    daily["class"] = pd.cut(
        daily["tmax"], bins=[-float("inf"), LIMIT_AIR_ALT, 33.0, float("inf")],
        labels=["A", "B", "C"],
    ).astype(str)
    daily.loc[~warm, "class"] = "-"
    return daily


def find_windows(daily: pd.DataFrame, min_len: int = 3, min_real: int = 3) -> list[tuple]:
    """Consecutive-day runs of class A (outdoor tmax <= 30 degC)."""
    days = daily[daily["class"] == "A"].index
    windows: list[tuple] = []
    run: list = []
    all_days = set(daily.index)
    for d in sorted(all_days):
        if d in set(days):
            run.append(d)
        else:
            if len(run) >= min_len:
                windows.append((run[0], run[-1]))
            run = []
    if len(run) >= min_len:
        windows.append((run[0], run[-1]))
    real = [w for w in windows
            if int((~daily.loc[w[0]:w[1], "frozen"]).sum()) >= min_real]
    return real


def window_indoor_stats(atrea: pd.DataFrame, start, end) -> pd.DataFrame:
    """Per-section indoor stats inside the window."""
    m = (atrea["data_key"] == "temp_indoor") & (atrea["day"] >= start) & (atrea["day"] <= end)
    w = atrea[m]
    g = w.groupby("location")["data_value"]
    stats = pd.DataFrame({
        "tmin": g.min(), "tmean": g.mean().round(1), "tmax": g.max(),
        "hours": g.count(),
        "h_gt27": w[w["data_value"] > LIMIT_OP].groupby("location").size(),
        "h_gt30": w[w["data_value"] > LIMIT_AIR_ALT].groupby("location").size(),
    }).reindex(SECTIONS)
    stats["pct_gt27"] = (100 * stats["h_gt27"] / stats["hours"]).round(0)
    stats["pct_gt30"] = (100 * stats["h_gt30"] / stats["hours"]).round(0)
    # days inside the window whose daily indoor maximum exceeds the 30 degC air limit
    dmax = w.groupby(["location", "day"])["data_value"].max()
    stats["days_tmax_gt30"] = (dmax > LIMIT_AIR_ALT).groupby("location").sum()
    night = w[w["hour"] < 6].groupby("location")["data_value"].min()
    stats["night_min"] = night
    return stats


def thermopro_stats(thermo: pd.DataFrame, start, end) -> pd.DataFrame:
    """Room-sensor stats inside the window (floors 1NP/5NP only)."""
    m = (thermo["day"] >= start) & (thermo["day"] <= end)
    w = thermo[m]
    g = w.groupby("location")["data_value"]
    stats = pd.DataFrame({
        "tmin": g.min(), "tmean": g.mean().round(1), "tmax": g.max(),
        "hours": g.count(),
        "h_gt27": w[w["data_value"] > LIMIT_OP].groupby("location").size(),
    })
    stats["pct_gt27"] = (100 * stats["h_gt27"] / stats["hours"]).round(0)
    return stats.sort_index()


def plot_window(hourly_amb: pd.DataFrame, hourly_in03: pd.DataFrame,
                start, end, frozen_days: set, out: Path) -> None:
    """Hourly outdoor (with design day) and indoor sm2_03 for one window."""
    fig, ax = plt.subplots(figsize=(14, 5))
    design_x, design_y = [], []
    span = pd.date_range(start, end + pd.Timedelta(days=1), freq="D", tz=PRAGUE)
    for day0 in span[:-1]:
        for h, v in DESIGN_DAY.items():
            design_x.append(day0 + pd.Timedelta(hours=h))
            design_y.append(v)
    ax.plot(design_x, design_y, color="grey", ls="--", lw=1.0,
            label="CSN 73 0540-3 design day (peak 30.0)")
    ax.plot(hourly_amb["time"], hourly_amb["data_value"],
            color="green", lw=1.2, label="outdoor (Atrea temp_ambient sm2_01)")
    ax.plot(hourly_in03["time"], hourly_in03["data_value"],
            color="blue", lw=1.2, label="indoor flat air (Atrea temp_indoor sm2_03)")
    ax.axhline(LIMIT_OP, color="red", lw=1, ls=":", label="27.0 degC operative limit")
    ax.axhline(LIMIT_AIR_ALT, color="darkred", lw=1, ls="-.",
               label="30.0 degC air limit (surface ~24 degC)")
    for fd in sorted(frozen_days):
        ax.axvspan(pd.Timestamp(fd, tz=PRAGUE), pd.Timestamp(fd, tz=PRAGUE) + pd.Timedelta(days=1),
                   color="orange", alpha=0.12)
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.set_ylabel("temperature (degC)")
    ax.set_title(f"Quasi-stationary window {start} .. {end} (orange = frozen sensor day)")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def plot_window_thermopro(hourly_amb: pd.DataFrame, thermo5: pd.DataFrame,
                          start, end, frozen_days: set, out: Path) -> None:
    """Separate graph: outdoor air vs measured 5NP corridor sensors (ThermoPro).

    DWH-SM2-0003 deliverable — the real measurements deserve their own chart:
    min-max band of all 5NP corridors plus the 5NP-S3 line (the persistent
    hot spot, top floor section 3), against the design day and both limits.
    """
    fig, ax = plt.subplots(figsize=(14, 5))
    design_x, design_y = [], []
    span = pd.date_range(start, end + pd.Timedelta(days=1), freq="D", tz=PRAGUE)
    for day0 in span[:-1]:
        for h, v in DESIGN_DAY.items():
            design_x.append(day0 + pd.Timedelta(hours=h))
            design_y.append(v)
    ax.plot(design_x, design_y, color="grey", ls="--", lw=1.0,
            label="CSN 73 0540-3 design day (peak 30.0)")
    ax.plot(hourly_amb["time"], hourly_amb["data_value"],
            color="green", lw=1.2, label="outdoor (Atrea temp_ambient sm2_01)")
    wide = thermo5.pivot_table(index="time", columns="location",
                               values="data_value")
    ax.fill_between(wide.index, wide.min(axis=1), wide.max(axis=1),
                    color="purple", alpha=0.12,
                    label="5NP corridors min-max band (ThermoPro measured)")
    if "5NP-S3" in wide.columns:
        s3 = wide["5NP-S3"].dropna()
        ax.plot(s3.index, s3, color="purple", lw=1.4,
                label="measured 5NP-S3 corridor (top floor, section 3)")
    ax.axhline(LIMIT_OP, color="red", lw=1, ls=":", label="27.0 degC operative limit")
    ax.axhline(LIMIT_AIR_ALT, color="darkred", lw=1, ls="-.",
               label="30.0 degC air limit (surface ~24 degC)")
    for fd in sorted(frozen_days):
        ax.axvspan(pd.Timestamp(fd, tz=PRAGUE), pd.Timestamp(fd, tz=PRAGUE) + pd.Timedelta(days=1),
                   color="orange", alpha=0.12)
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.set_ylabel("temperature (degC)")
    ax.set_title(f"Quasi-stationary window {start} .. {end}: outdoor vs measured "
                 "5NP corridors (ThermoPro; orange = frozen sensor day)")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def plot_summer(hourly: pd.DataFrame, year: int, out: Path) -> None:
    """Whole-year overview: outdoor band + indoor sm2_03 min/mean/max."""
    fig, ax = plt.subplots(figsize=(16, 5))
    amb = hourly[(hourly["location"] == "sm2_01") & (hourly["data_key"] == "temp_ambient")]
    ind = hourly[(hourly["location"] == "sm2_03") & (hourly["data_key"] == "temp_indoor")]
    for src, color in ((amb, "green"), (ind, "blue")):
        d = src.groupby("day")["data_value"].agg(["min", "max", "mean"])
        d.index = pd.to_datetime(d.index)
        ax.fill_between(d.index, d["min"], d["max"], color=color, alpha=0.15)
        ax.plot(d.index, d["mean"], color=color, lw=1.1)
    ax.axhline(LIMIT_OP, color="red", lw=1, ls=":", label="27.0 degC operative limit")
    ax.axhline(LIMIT_AIR_ALT, color="darkred", lw=1, ls="-.", label="30.0 degC air limit")
    ax.set_xlim((pd.Timestamp(f"{year}-01-01", tz=PRAGUE),
                 pd.Timestamp(f"{year}-12-31", tz=PRAGUE)))
    ax.set_ylabel("temperature (degC)")
    ax.set_title(f"{year}: daily min-max band and mean - outdoor (green, sm2_01 ambient) "
                 "vs indoor flat air (blue, sm2_03)")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def export_window_hourly(atrea: pd.DataFrame, start, end, out: Path) -> None:
    """Wide hourly CSV for the window, ready to send to the expert."""
    m = (atrea["day"] >= start) & (atrea["day"] <= end)
    w = atrea[m]
    piv = w.pivot_table(index="time", columns=["data_key", "location"],
                        values="data_value")
    piv.columns = [f"{k}_{loc}" for k, loc in piv.columns]
    piv = piv.reset_index()
    piv.to_csv(out / f"hourly_{start}_{end}.csv", index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    atrea, thermo = read_hourly(args.parquet)
    daily = daily_outdoor(atrea)
    daily.to_csv(out / "outdoor_daily_classification.csv")

    windows = find_windows(daily)
    print("Quasi-stationary windows (>= 3 consecutive WARM days with outdoor "
          "tmax <= 30.0 degC, >= 3 real days):")
    summary_rows = []
    candidate_rows: list[dict] = []
    for start, end in windows:
        sub = daily.loc[start:end]
        n_real = int((~sub["frozen"]).sum())
        cls = ",".join(sub["class"].astype(str))
        tmaxes = "/".join(f"{v:.1f}" for v in sub["tmax"])
        print(f"  {start} .. {end}  ({(end - start).days + 1} days, {n_real} real)  "
              f"classes {cls}  tmax {tmaxes}")
        stats = window_indoor_stats(atrea, start, end)
        stats.to_csv(out / f"indoor_sections_{start}_{end}.csv")
        s03 = stats.loc["sm2_03"]
        summary_rows.append({
            "window": f"{start}..{end}", "days": (end - start).days + 1,
            "real_days": n_real,
            "outdoor_tmax_max": round(sub["tmax"].max(), 1),
            "outdoor_tmax_min": round(sub["tmax"].min(), 1),
            "sm2_03_indoor_min": s03["tmin"], "sm2_03_indoor_mean": s03["tmean"],
            "sm2_03_indoor_max": s03["tmax"],
            "sm2_03_pct_hours_gt27": s03["pct_gt27"],
            "sm2_03_pct_hours_gt30": s03["pct_gt30"],
            "sm2_03_night_min": s03["night_min"],
            "sm2_03_days_tmax_gt30": s03["days_tmax_gt30"],
            "all_sections_max_tmax": stats["tmax"].max(),
            "sections_with_hour_gt30": int((stats["h_gt30"] > 0).sum()),
        })
        print(f"    sm2_03 indoor max {s03['tmax']:.1f} degC, "
              f"days with indoor max >30: {s03['days_tmax_gt30']}, "
              f"sections with any hour >30: {summary_rows[-1]['sections_with_hour_gt30']}/9")
        # candidate evidence: section averages exceeding the 30 degC air limit
        # (a section average above the limit is a lower bound for the flats)
        for loc, r in stats[stats["tmax"] > LIMIT_AIR_ALT].iterrows():
            candidate_rows.append({
                "window": f"{start}..{end}", "source": "atrea_section_average",
                "location": loc, "tmax": round(float(r["tmax"]), 1),
                "pct_gt27": r["pct_gt27"],
            })
        amb_h = atrea[(atrea["location"] == "sm2_01") & (atrea["data_key"] == "temp_ambient")
                      & (atrea["day"] >= start) & (atrea["day"] <= end)]
        in03_h = atrea[(atrea["location"] == "sm2_03") & (atrea["data_key"] == "temp_indoor")
                       & (atrea["day"] >= start) & (atrea["day"] <= end)]
        frozen = {d for d in sub.index if sub.loc[d, "frozen"]}
        plot_window(amb_h, in03_h, pd.Timestamp(start), pd.Timestamp(end),
                    frozen, out / f"window_{start}_{end}.png")
        export_window_hourly(atrea, start, end, out)
        # room sensors only exist from 2025-08 on
        if str(start) >= "2025-08":
            ts = thermopro_stats(thermo, start, end)
            ts.to_csv(out / f"thermopro_rooms_{start}_{end}.csv")
            print(f"    ThermoPro rooms: max of room maxima {ts['tmax'].max():.1f} degC, "
                  f"rooms >27 degC: {(ts['pct_gt27'] > 0).sum()}/{len(ts)}, "
                  f"rooms with max >30: {int((ts['tmax'] > LIMIT_AIR_ALT).sum())}/{len(ts)}")
            summary_rows[-1]["thermopro_max"] = round(float(ts["tmax"].max()), 1)
            summary_rows[-1]["thermopro_rooms_max_gt30"] = int((ts["tmax"] > LIMIT_AIR_ALT).sum())
            # separate deliverable graph: outdoor vs measured 5NP corridors
            plot_window_thermopro(
                amb_h, thermo[thermo["location"].str.startswith("5NP-")],
                pd.Timestamp(start), pd.Timestamp(end), frozen,
                out / f"window_thermopro_{start}_{end}.png")
            # candidate evidence: measured 5NP (top floor) corridor sensors above the limit
            for loc, r in ts[ts.index.str.startswith("5NP-")
                             & (ts["tmax"] > LIMIT_AIR_ALT)].iterrows():
                candidate_rows.append({
                    "window": f"{start}..{end}",
                    "source": "thermopro_measured_corridor_5np",
                    "location": loc, "tmax": round(float(r["tmax"]), 1),
                    "pct_gt27": r["pct_gt27"],
                })
    pd.DataFrame(summary_rows).to_csv(out / "window_summary.csv", index=False)
    pd.DataFrame(
        candidate_rows,
        columns=["window", "source", "location", "tmax", "pct_gt27"],
    ).to_csv(out / "candidates.csv", index=False)

    for year in (2024, 2025, 2026):
        plot_summer(atrea, year, out / f"overview_{year}.png")

    print(f"\nOutputs written to {out}")


if __name__ == "__main__":
    main()
