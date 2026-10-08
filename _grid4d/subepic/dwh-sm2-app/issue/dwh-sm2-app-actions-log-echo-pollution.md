# Raw Actions job logs echo the run script, polluting grep-based verification

**Status:** open
**Found:** 2026-10-08 (live diagnosis, missing-sensors incident)

## Problem

Raw GitHub Actions job logs (downloaded zip, or `gh api .../logs`) reproduce the entire `run:` script inside the `##[group]Run <script>` header before the real output. Step *names* never appear as plain text. Any grep over a raw log therefore matches the echoed script as well as (or instead of) the actual command output, and tools that are silent on success (rclone without `-v`) leave nothing but a timestamp gap as evidence. Verification recipes built on string counts over raw logs silently produce wrong answers.

## Symptoms

- `grep -c 'not found, skipping upload'` returns 3 on a healthy run (the three `echo "..." not found, skipping upload"` lines of the echoed script only) but 6 on a genuine skip (3 echo + 3 plain timestamped outputs). Counting to 3 without splitting echo from output reads as "upload skipped" when the upload succeeded.
- Searching for a step name (`'Full dbt build'`) finds 0 matches and led to a false "fallback did not run" conclusion; step names exist only in the API `steps[]` array, not in raw log text.
- A real rclone transfer produces no log lines at all — the only trace is a ~10 s gap between the step's `##[endgroup]` and the next step's `##[group]`.

## Solution Direction

Two layers:

1. **Make the scripts self-evident.** rclone copy with `--stats-one-line` (or `-v`) plus an explicit `echo "uploaded <file> (<bytes> bytes)"` per file, so success is a one-grep check instead of time-gap forensics. This removes the whole class rather than documenting around it.
2. **Until then, verify against structure, not raw counts.** Distinguish group-echo lines (carry the ANSI `[36;1m` marker / sit inside the `##[group]` block) from plain timestamped output lines; prefer the Actions API `jobs[].steps[]` array (name + status + conclusion) over log text for "did step X run"; treat a timestamp gap as the rclone transfer signature.

The runbook's Health Verification item 5 (fact upload really happened) already documents the 3-vs-6 counts and the ~10 s gap; it should shrink to "grep the explicit uploaded-bytes line" once layer 1 lands.

## Occurrences

- **2026-10-08**: during the missing-sensors diagnosis and the fix verification, three consecutive log analyses hit this: the invalid `'Full dbt build' ×0` step-name check (runs 37738331019 / 37756665551 / 37761728956), and the ambiguous `not found, skipping upload` count on run 37761728956 that briefly read as a failed upload before the echo/plain split (3 = echoed script only = success) and the ~14 s gap confirmed the transfer.

## Related

- [dwh-sm2-app-refresh-freshness-silent-skip](dwh-sm2-app-refresh-freshness-silent-skip) - the incident whose diagnosis kept tripping over this
- [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook) - Health Verification item 5 carries the interim recipe
