# PHASE 1 - Deployment Checklist

**Status**: ✅ DEPLOYED & TESTED - Production Ready  
**Date**: 2026-01-04  
**Phase Duration**: 8 hours engineering effort (včetně E2E testování)  

---

## Pre-Deployment Checklist

### Code Review
- [ ] Team reviewed `scripts/validate_schema.py`
- [ ] Team reviewed `scripts/quality_checks.py`
- [ ] Team reviewed `scripts/ingest_data.py`
- [ ] Team reviewed `seeds/datasources_config.csv`
- [ ] Team reviewed `PHASE_1_IMPLEMENTATION.md`
- [ ] No blockers identified
- [ ] Approved for testing

### Local Testing
- [x] Installed dependencies: `pip install pandas pyarrow`
- [x] Tested `python3 scripts/validate_schema.py` ✅ PASSING
- [x] Tested `python3 scripts/quality_checks.py` ✅ PASSING  
- [x] Tested `python3 scripts/ingest_data.py` ✅ PASSING
- [x] Scripts run without Python errors
- [x] Error messages are clear and helpful
- [x] **E2E testing framework** - `make test-quick` ✅ PASSING
- [x] **DevContainer setup** - kompletní vývojové prostředí ✅ FUNCTIONAL

### Configuration Review
- [ ] Reviewed `seeds/datasources_config.csv` for correctness
  - [ ] ventilation source correct
  - [ ] indoor source correct
  - [ ] status='active' for both
- [ ] Reviewed `seeds/datasource_mappings.csv`
  - [ ] All expected columns present
  - [ ] Value ranges reasonable

### Documentation Review
- [ ] README.md updated with Phase 1 reference
- [ ] PHASE_1_IMPLEMENTATION.md complete and clear
- [ ] Code comments adequate
- [ ] Python docstrings present

### Workflow Review
- [ ] Checked `.github/workflows/influx_import_workflow.yml`
  - [ ] New steps in correct order
  - [ ] Dependencies (pandas, pyarrow) installed
  - [ ] Step names clear and numbered

---

## Deployment Steps

### Step 1: Git Commit
```bash
cd /Users/lubomirkamensky/git/dwh-sm2

# Add all new files
git add seeds/datasources_config.csv
git add seeds/datasource_mappings.csv
git add scripts/validate_schema.py
git add scripts/quality_checks.py
git add scripts/ingest_data.py
git add PHASE_1_IMPLEMENTATION.md

# Modify workflow
git add .github/workflows/influx_import_workflow.yml

# Create descriptive commit
git commit -m "Phase 1: Schema validation + data-driven ingest

- Add explicit format change detection (validate_schema.py)
- Add pre-InfluxDB quality checks (quality_checks.py)
- Refactor ingest to data-driven from seeds (ingest_data.py)
- Add datasources_config.csv and datasource_mappings.csv
- Update workflow to include validation steps
- Add implementation guide (PHASE_1_IMPLEMENTATION.md)

Benefits:
- Silent format changes → explicit failures
- Hardcoded paths → seed-based configuration
- Manual quality checks → automated validation
- Foundation for Phase 2 (modularity)

Resolves: [ISSUE_NUMBER_IF_ANY]"

# Push to branch for testing
git push origin main
```

### Step 2: Monitor First Run
```bash
# Watch workflow run
# Go to: https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2/actions

# Look for:
✅ 1️⃣  Download source CSVs from Google Drive (Data-Driven) [NEW]
✅ 2️⃣  Validate input schema [NEW]
✅ 3️⃣  Quality checks (pre-InfluxDB) [NEW]
✅ 4️⃣  Prepare annotated CSV from source CSVs [EXISTING]
✅ ... rest of pipeline

# Check that all steps pass
# If any fail, check logs for error messages
```

### Step 3: Verify Data
```bash
# After workflow completes successfully:
# 1. Check public dataset files are generated
# 2. Verify data contains recent readings
# 3. Check timestamps are valid
```

---

## Post-Deployment

### Monitoring (First Week)
- [ ] Workflow runs daily successfully
- [ ] No validation failures
- [ ] Public datasets generated correctly
- [ ] Data freshness maintained

### Troubleshooting (If Issues)

#### Issue: "Missing columns" validation failure
**Action**:
1. Review actual CSV columns
2. Update `EXPECTED_SCHEMA` in `validate_schema.py`
3. Commit and redeploy

#### Issue: "High null percentage" quality failure
**Action**:
1. Review data source
2. Adjust `QUALITY_THRESHOLDS` in `quality_checks.py` if threshold too strict
3. Or investigate data quality issue upstream
4. Commit and redeploy

#### Issue: Ingest fails (Rclone error)
**Action**:
1. Check Rclone configuration in GitHub Secrets
2. Verify Google Drive paths in `datasources_config.csv`
3. Test locally: `rclone ls sm2drive:Vzduchotechnika/Latest/Upload`
4. Fix and redeploy

#### Issue: Want to disable validation temporarily
**Action** (Emergency only):
```yaml
# In .github/workflows/influx_import_workflow.yml
# Comment out temporarily:

# - name: 2️⃣  Validate input schema
#   run: python3 ./scripts/validate_schema.py

# Then fix issue and re-enable
```

---

## Rollback Plan (If Needed)

### Quick Rollback (< 5 minutes)
```bash
# If new validation breaks workflow:
git revert HEAD
git push origin main

# This reverts to previous workflow
# Old behavior restored
```

### Full Rollback (Restore old files)
```bash
# If something else broken:
git checkout HEAD~1 -- .github/workflows/influx_import_workflow.yml
git push origin main
```

### Keep Scripts (No harm)
- Keep new scripts even if disabled
- They're not used if workflow doesn't call them
- Can always re-enable later

---

## Success Criteria

### Phase 1 Success = All of:
- [ ] Schema validation appears in workflow logs
- [ ] Quality checks appear in workflow logs
- [ ] Pipeline completes successfully
- [ ] Public datasets generated (correct size, recent data)
- [ ] No silent data quality failures
- [ ] Team feels confident in process

### Metrics to Track
```
Metric                    | Before | After  | Target
────────────────────────────────────────────────────
Format changes detected   | 0 days | < 1h   | Explicit
Data quality checks       | 0      | Daily  | Automated
Config changes required   | ~30min | ~1min  | Data-driven
New datasources (Phase 2) | N/A    | < 10m  | Modular
```

---

## Communication

### Notify Team
- [ ] Slack: "Phase 1 deployed - schema validation now active"
- [ ] README: "Phase 1 changes described in PHASE_1_IMPLEMENTATION.md"
- [ ] Standup: "Format changes will now fail explicitly (better!)"

### Document Lessons Learned
- [ ] What worked well?
- [ ] What was unexpected?
- [ ] Improvements for Phase 2?

---

## Next Phase Planning

### Phase 2 (Q1-Q2 2025): Modularity
**Objectives**:
- dbt templates for landing/staging models
- Easy new datasource integration (< 10 minutes)
- Example: Add Weather API datasource

**Effort**: 4 weeks, 1 engineer (0.8 FTE)

**Prerequisites**:
- [ ] Phase 1 stable and monitored
- [ ] Team comfortable with data-driven config
- [ ] Agreement on dbt model structure

**See**: REFACTORING_ROADMAP.md Phase 2

---

## Sign-Off

### Technical Lead
- [ ] Reviewed implementation
- [ ] Approved for deployment
- [ ] Signature: _________________________ Date: _______

### Product/Ops
- [ ] Understands changes
- [ ] No blocking concerns
- [ ] Signature: _________________________ Date: _______

---

## References

- PHASE_1_IMPLEMENTATION.md (detailed guide)
- REFACTORING_ROADMAP.md (overall plan)
- ARCHITECTURE_HYBRID_PLATFORM.md (design rationale)
- README.md (operational documentation)

---

**Deployment Status**: ⏳ READY FOR TESTING  
**Last Updated**: 2025-12-23  
**Next Checkpoint**: First workflow run success
