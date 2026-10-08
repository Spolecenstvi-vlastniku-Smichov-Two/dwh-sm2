# DWH-SM2-APP-0003: Capture operational issues and ideas from the DWH-SM2-APP-0002 incident recovery

> Capture operational issues and ideas from the DWH-SM2-APP-0002 incident recovery

**Type:** default
**Epic:** [DWH-SM2-APP](../DWH-SM2-APP)
**Status:** completed
**Blueprint:** [implementation-story-blueprint](implementation-story-blueprint)

## Goal

Capture operational issues and ideas from the DWH-SM2-APP-0002 incident recovery

## Requirements

### R1: Mark the refresh freshness silent-skip issue resolved with live verification evidence

Update [dwh-sm2-app-refresh-freshness-silent-skip](../issue/dwh-sm2-app-refresh-freshness-silent-skip) from open to resolved (v0.0004.1.0002.00) and append the live-verification occurrence: run 37761728956 (guard fired → full-build fallback PASS=10 → all three fact uploads to Model/ → GDrive confirmed), plus the green downstream chain (Influx 37762493326, Publish 37762967460, datex bot commit 10:22:42 UTC).

**Acceptance Criterion:** Issue file shows `Status: resolved (v0.0004.1.0002.00)` and an Occurrence entry dated 2026-10-08 10:22 UTC with the run IDs above.

### R2: Capture the raw-log echo-pollution issue

Capture [dwh-sm2-app-actions-log-echo-pollution](../issue/dwh-sm2-app-actions-log-echo-pollution): raw Actions job logs echo the run script (grep counts conflate echo and output), step names are absent from log text, and silent-on-success tools (rclone) leave only timestamp gaps. Solution direction: self-evident scripts (`--stats-one-line` + explicit uploaded-bytes echo) and structure-aware verification until then.

**Acceptance Criterion:** Issue file exists with Problem / Symptoms / Solution Direction / Occurrences and links to the silent-skip incident and the runbook.

### R3: Capture the fallback-annotation UX idea

Capture [dwh-sm2-app-fallback-annotation-ux](../idea/dwh-sm2-app-fallback-annotation-ux): the deliberate exit-1 fallback renders as a red error on healthy content-only re-upload days; propose a detection-step with output instead of outcome-keyed failure, so red always means broken.

**Acceptance Criterion:** Idea file exists with Context / Proposal / Value and links to the resolved silent-skip issue.

### R4: No duplicate captures

Do not re-capture what existing knowledge already covers: pipeline chaining and failure notification are already [dwh-sm2-app-pipeline-unsequenced](../issue/dwh-sm2-app-pipeline-unsequenced).

**Acceptance Criterion:** The three captures above are the only new knowledge files; each neighbouring overlap is referenced, not duplicated.

### R5: Promote transient story-0002 knowledge into permanent knowledge files

The knowledge-audit (2026-10-08, Human question "what have we learned that is not yet documented") found four items living only in DWH-SM2-APP-0002 story notes and session memory: (a) the append-only/additive data guarantee, (b) the worked full-pipeline recovery sequence with dispatch commands, (c) fact windowing driven by `seeds/mapping_sources.csv`, (d) the deliberate-removal-has-no-path consequence. Promote them: Data Guarantees section + expanded recovery item 6 in [dwh-sm2-app-runbook](../implementation/dwh-sm2-app-runbook); Rules 5-6 in [dwh-sm2-app-pipeline-blueprint](../ontology/dwh-sm2-app-pipeline-blueprint).

**Acceptance Criterion:** Runbook carries a Data Guarantees section and the six-step recovery sequence with workflow ids; blueprint Rules cover additivity and config-driven windowing; neither duplicates the other (runbook = operator consequences, blueprint = invariant).

### R6: Capture the Atrea export-lag diagnostic trap

The post-recovery completeness check found September 2026 at 26 locations instead of 38 — the 12 Atrea ventilation locations whose exports lag months behind (Human confirmed the September export has not arrived). Capture [dwh-sm2-app-atrea-export-lag](../issue/dwh-sm2-app-atrea-export-lag) so the pattern is not mistaken for an incident: location names, the months_to_process wall-time connection, and the recovery path via the freshness guard when the backfill lands.

**Acceptance Criterion:** Issue file exists with the Atrea location names, the influx month-set wall-time symptom, and the content-only backfill recovery path.

### R7: Capture the plug-and-play evolucean integration idea

Capture [dwh-sm2-app-plug-and-play-evolucean-integration](../idea/dwh-sm2-app-plug-and-play-evolucean-integration): the Human direction to run dwh-sm2 as a plug-and-play evolucean Epic, the plugged-vs-play gap table (sensor, nervous system, shaping read-back, prune/sustain), the finding that `plug-and-play-epic-integration` is referenced in the shaping blueprint but unauthored, and the phased proposal (audit story first).

**Acceptance Criterion:** Idea file exists with the gap table, the unauthored-blueprint finding, and the phased proposal.

## Notes

Created: 2026-10-08

Scope ruling (Human, 2026-10-08): this story is an **issues-and-ideas journal only** — log captures here, do not grow it into audit or implementation work; those get their own stories. R5's runbook/blueprint promotion (committed before the ruling) stays as the one delivered exception. Complete when the capture batch is committed.

Language: English per ahabase convention.

