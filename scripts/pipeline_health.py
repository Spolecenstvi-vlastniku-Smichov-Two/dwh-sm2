#!/usr/bin/env python3
"""Pipeline health sensor for the DWH-SM2 epic.

Play principle 1 (Sensor) of plug-and-play epic integration: measure the
pipeline deterministically, store a reading, never notify (that is the
nervous-system story). Epic-owned per the isolation rule — evolucean
provides no pluggable readings path for external epics (see issue
dwh-sm2-app-epic-sensor-readings-path-missing), so the reading lives in
this repository.

Metrics (definitions: _grid4d/subepic/dwh-sm2-app/metric/):
  - action_freshness   hours since the last successful publish run
  - run_outcomes       last-N conclusions per monitored workflow
  - data_freshness     hours since the last commit touching the public
                       parquet (bot heartbeat proxy for dataset age)

Transport: `gh api` when available (authenticated, higher rate limit);
unauthenticated urllib otherwise. `--fixture` runs fully offline against
a saved snapshot; `--at` pins the reference time for deterministic runs.

Usage:
  python3 scripts/pipeline_health.py --status            # one-step read-back
  python3 scripts/pipeline_health.py --json sensor_readings/pipeline-health/latest.json
  python3 scripts/pipeline_health.py --fixture <snap.json> --at 2026-10-08T12:00:00Z --status
  python3 scripts/pipeline_health.py --since 2026-10-01 --until 2026-10-06 --status
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import urllib.parse
import urllib.request

REPO = "Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2"
WORKFLOWS = {  # file name -> short label
    "publish_public_dataset.yml": "publish",
    "refresh.yml": "refresh",
    "influx_import_workflow.yml": "influx",
}
PARQUET_PATH = "docs/datex/sm2_public_dataset.parquet"
N_OUTCOMES = 5

# Thresholds (metric docs are authoritative; mirrored here for the probe)
FRESH_OK_H = 48.0
FRESH_WARN_H = 72.0


def _api(path: str) -> dict:
    """One GitHub API call, via gh when available, else unauth urllib."""
    try:
        out = subprocess.run(
            ["gh", "api", path], capture_output=True, text=True, timeout=30
        )
        if out.returncode == 0:
            return json.loads(out.stdout)
    except FileNotFoundError:
        pass
    with urllib.request.urlopen(
        f"https://api.github.com/{path}", timeout=30
    ) as resp:
        return json.loads(resp.read().decode())


def _hours_between(a: str, b: dt.datetime) -> float:
    t = dt.datetime.fromisoformat(a.replace("Z", "+00:00"))
    return round((b - t).total_seconds() / 3600.0, 1)


def _collect_live(since: str | None, until: str | None) -> dict:
    snap: dict = {"workflows": {}, "parquet_last_commit": None}
    parts = ["per_page=30"]
    if since and until:
        parts.append("created=" + urllib.parse.quote(f"{since}..{until}"))
    elif since:
        parts.append("created=" + urllib.parse.quote(f">={since}"))
    elif until:
        parts.append("created=" + urllib.parse.quote(f"<={until}"))
    q = "?" + "&".join(parts)
    for fname, label in WORKFLOWS.items():
        data = _api(f"repos/{REPO}/actions/workflows/{fname}/runs{q}")
        snap["workflows"][label] = [
            [r["created_at"], r["conclusion"] or r["status"]]
            for r in data.get("workflow_runs", [])
        ]
    cq = f"?path={PARQUET_PATH}&per_page=1"
    if until:
        cq += "&until=" + urllib.parse.quote(until + ("T23:59:59Z" if len(until) == 10 else ""))
    commits = _api(f"repos/{REPO}/commits{cq}")
    if commits:
        snap["parquet_last_commit"] = commits[0]["commit"]["committer"]["date"]
    return snap


def measure(snap: dict, at: dt.datetime) -> dict:
    """Compute the reading from a snapshot (live-collected or fixture)."""
    wf = snap.get("workflows", {})
    runs = wf.get("publish", [])
    last_success = next((c for c, concl in runs if concl == "success"), None)
    action_freshness = (
        _hours_between(last_success, at) if last_success else None
    )
    if action_freshness is None:
        action_state = "unknown"
    elif action_freshness <= FRESH_OK_H:
        action_state = "ok"
    elif action_freshness <= FRESH_WARN_H:
        action_state = "warning"
    else:
        action_state = "critical"

    plc = snap.get("parquet_last_commit")
    data_freshness = _hours_between(plc, at) if plc else None
    data_state = (
        "ok" if data_freshness is not None and data_freshness <= FRESH_OK_H
        else ("critical" if data_freshness is not None else "unknown")
    )

    outcomes = {
        label: [[c, concl] for c, concl in runs[:N_OUTCOMES]]
        for label, runs in wf.items()
    }
    failures = sum(
        1 for label, runs in wf.items() for _, concl in runs if concl != "success"
    )
    return {
        "epic": "dwh-sm2",
        "measured_at": at.isoformat(),
        "metrics": {
            "action_freshness_h": action_freshness,
            "action_state": action_state,
            "data_freshness_h": data_freshness,
            "data_state": data_state,
            "run_outcomes": outcomes,
            "non_success_runs_in_window": failures,
            "guard_fired": None,  # deferred: annotations wiring lands with the nervous-system story
        },
        "source": snap,
    }


def status_line(reading: dict) -> str:
    m = reading["metrics"]
    af = m["action_freshness_h"]
    df = m["data_freshness_h"]
    return (
        f"publish last success: {af}h ago ({m['action_state']}) | "
        f"parquet last commit: {df}h ago ({m['data_state']}) | "
        f"non-success runs in window: {m['non_success_runs_in_window']}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--status", action="store_true", help="print one-step summary")
    ap.add_argument("--json", metavar="PATH", help="write reading JSON to PATH")
    ap.add_argument("--fixture", metavar="PATH", help="offline snapshot input")
    ap.add_argument("--at", metavar="ISO", help="reference time (default: now)")
    ap.add_argument("--since", metavar="DATE", help="window start (live mode)")
    ap.add_argument("--until", metavar="DATE", help="window end (live mode)")
    args = ap.parse_args()

    at = (
        dt.datetime.fromisoformat(args.at.replace("Z", "+00:00"))
        if args.at
        else dt.datetime.now(dt.timezone.utc)
    )
    if args.fixture:
        with open(args.fixture) as fh:
            snap = json.load(fh)
    else:
        snap = _collect_live(args.since, args.until)

    reading = measure(snap, at)
    if args.status:
        print(status_line(reading))
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(reading, fh, indent=2)
            fh.write("\n")
        print(f"reading written: {args.json}")
    if not (args.status or args.json):
        json.dump(reading, sys.stdout, indent=2)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
