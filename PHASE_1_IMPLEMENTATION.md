# PHASE 1 Implementation Guide

**Status**: Complete  
**Components**: Schema Validation, Data-Driven Ingest, Quality Checks  
**Files Added/Modified**: 7  

---

## Overview

Phase 1 implements explicit format change detection and data-driven datasource configuration, replacing hardcoded paths with seed-based configuration.

**Benefits**:
- Format changes detected immediately (not silent)
- New datasources easily added via CSV config
- Quality issues flagged before InfluxDB import
- Clearer data flow (config → download → validate → check → process)

---

## Files Created

### 1. `seeds/datasources_config.csv`

Central configuration for all datasources. Easy to extend for new sources.

```csv
datasource_id,name,source_type,location,file_pattern,required_columns,data_type,retention_months,status,description
1,ventilation,csv,sm2drive:Vzduchotechnika/Latest/Upload,Graph*.csv,...,temperature;humidity,2,active,...
2,indoor,csv,sm2drive:Indoor/Latest/Upload,ThermoProSensor_export*.csv,...,temperature;humidity,2,active,...
```

**To add new datasource**:
1. Add row to this CSV
2. Mark status='active' when ready
3. Ingest script automatically picks it up

### 2. `seeds/datasource_mappings.csv`

Column mapping for each datasource. Used in Phase 2 (dbt templates).

```csv
datasource_id,timestamp_column,location_column,measurement_column,value_column,...
```

### 3. `scripts/ingest_data.py` (NEW)

Replaces hardcoded rclone commands. Now reads from `datasources_config.csv`.

**Features**:
- Data-driven configuration (reads CSV)
- Supports CSV and API sources (API not yet implemented)
- Skip inactive datasources automatically
- Validates files downloaded

**Usage**:
```bash
python3 scripts/ingest_data.py
```

**Output**:
```
DATA INGEST (DATA-DRIVEN)

Loading datasources configuration...
✅ Loaded 2 datasources

Processing: ventilation (csv)
  Downloading ventilation...
  From: sm2drive:Vzduchotechnika/Latest/Upload
  Pattern: Graph*.csv
  To: ./raw/ventilation
  ✅ Downloaded 1 file(s)

Processing: indoor (csv)
  ...
  ✅ Downloaded 1 file(s)

INGEST SUMMARY
Total files downloaded: 2
✅ All 2 datasource(s) downloaded successfully
```

### 4. `scripts/validate_schema.py` (NEW)

Explicitly validates CSV schema. Fails if format changed.

**Features**:
- Compares actual columns vs expected
- Detects missing columns (FAIL)
- Warns about unexpected columns
- Type checking (lenient, warning only)

**Usage**:
```bash
python3 scripts/validate_schema.py
```

**Output if schema matches**:
```
SCHEMA VALIDATION

✅ Schema validation passed: ventilation
   File: ./gdrive/fact.csv
   Rows: 365, Columns: 150

✅ Schema validation passed: indoor
   File: ./gdrive/all_sensors_merged.csv
   Rows: 1000, Columns: 4

ALL VALIDATIONS PASSED
```

**Output if schema mismatches**:
```
❌ SCHEMA MISMATCH: ventilation
   File: ./gdrive/fact.csv
   Missing columns: {'KOT1/Teplota venkovní'}
   Expected columns: {'date', 'KOT1/Teplota venkovní', 'KOT1/Vlhkost venkovní'}
   Actual columns: {'date', 'KOT1/Teplotavnější', 'KOT1/Vlhkost venkovní'}

   ACTION: Check if ventilation data format changed!

VALIDATION FAILED
```

### 5. `scripts/quality_checks.py` (NEW)

Validates data quality before InfluxDB import.

**Features**:
- Null percentage check
- Row count bounds
- Date/timestamp validation
- Future date detection
- Duplicate timestamp warning

**Usage**:
```bash
python3 scripts/quality_checks.py
```

**Output**:
```
DATA QUALITY CHECKS

Checking: ventilation
File: ./gdrive/fact.csv
------
✅ Null check: 0.05% (OK, threshold: 5.00%)
✅ Row count check: 365 rows (OK, min: 100)
✅ Row count check: 365 rows (OK, max: 100000)
✅ Date format check: All timestamps valid
✅ Future date check: No future dates
✅ Date range: 2024-01-01 to 2024-12-31 (365 days)

ALL QUALITY CHECKS PASSED: ventilation

...

ALL QUALITY CHECKS PASSED
```

---

## Files Modified

### 6. `.github/workflows/influx_import_workflow.yml`

**Changes**:
- Replaced hardcoded rclone commands with `scripts/ingest_data.py`
- Added validation steps before InfluxDB import
- Added dependencies to pyarrow (for quality checks)

**New step sequence**:
```
1️⃣  Download source CSVs from Google Drive (Data-Driven) [NEW]
2️⃣  Validate input schema [NEW]
3️⃣  Quality checks (pre-InfluxDB) [NEW]
4️⃣  Prepare annotated CSV from source CSVs [EXISTING]
5️⃣  ... rest of pipeline (unchanged)
```

**Behavior**:
- If validation fails → workflow stops (explicit error)
- No silent failures
- Clear error messages for engineer debugging

---

## How to Use Phase 1

### 1. Local Testing (Before Deploying)

```bash
# Install dependencies
pip install pandas pyarrow

# Test ingest (will fail if Rclone not configured, that's OK)
python3 scripts/ingest_data.py

# Test validation (will fail if files not present, that's OK)
python3 scripts/validate_schema.py

# Test quality checks (will fail if files not present, that's OK)
python3 scripts/quality_checks.py
```

### 2. Adding New Datasource

Example: Add Air Quality sensor data

```bash
# Step 1: Add to datasources_config.csv
echo "3,air_quality,csv,sm2drive:AirQuality/Latest,air_quality*.csv,time;location;pm25,pollution,1,planned,Air quality sensors" >> seeds/datasources_config.csv

# Step 2: Define mappings (optional, for Phase 2)
# ... add rows to datasources_mappings.csv

# Step 3: Change status to 'active' when ready
# ... update datasources_config.csv

# Step 4: Ingest picks it up automatically!
python3 scripts/ingest_data.py
```

### 3. Handling Format Changes

**If Atrea changes column names**:

1. Data is downloaded
2. Validation script FAILS with clear error:
   ```
   ❌ SCHEMA MISMATCH: ventilation
   Missing columns: {'KOT1/Teplota venkovní'}
   ```
3. Engineer reviews error
4. Engineer updates `EXPECTED_SCHEMA` in `validate_schema.py`
5. Engineer commits and redeploys
6. No silent data loss!

### 4. Quality Threshold Tuning

In `scripts/quality_checks.py`, adjust thresholds as needed:

```python
QUALITY_THRESHOLDS = {
    'ventilation': {
        'null_pct_max': 0.05,        # ← Adjust here (0.05 = 5%)
        'row_count_min': 100,         # ← Or here
        'row_count_max': 100000,
        ...
    },
    ...
}
```

If threshold too strict → loosen it and commit.

---

## Migration from Old to New

### Old Approach:
```bash
# Hardcoded in workflow
rclone copy sm2drive:Vzduchotechnika/Model/ ./gdrive/
rclone copy sm2drive:Indoor/Model/ ./gdrive/
```

### New Approach:
```bash
# Data-driven from seed
python3 scripts/ingest_data.py  # Reads datasources_config.csv
```

### Migration Steps:

1. ✅ Commit new files (done)
2. ✅ Update workflow (done)
3. Test in parallel (see Testing section)
4. Switch to new workflow (push to main)
5. Monitor for issues (look at workflow logs)
6. Keep old scripts as fallback (don't delete)

---

## Testing

### Dry-Run (No Changes)

```bash
# Test without touching Google Drive or InfluxDB
python3 scripts/ingest_data.py --dry-run

# Test validation only
python3 scripts/validate_schema.py --check-only
```

### Parallel Run

Run old + new workflow side-by-side:
1. Deploy new workflow to branch (not main)
2. Run old workflow on main
3. Compare outputs
4. When outputs match, merge to main

---

## Rollback

If issues detected:

### Option 1: Disable new validation (quick)
```yaml
# In workflow, comment out:
# - name: Validate input schema
#   run: python3 ./scripts/validate_schema.py
```

### Option 2: Revert to old approach (full)
```bash
# Revert workflow to previous version
git checkout HEAD~1 -- .github/workflows/influx_import_workflow.yml

# Keep scripts (no harm, they're not used)
```

---

## Monitoring

### Success Indicators

- ✅ Workflow logs show validation passing
- ✅ Schema validation output appears in logs
- ✅ Quality check output appears in logs
- ✅ Pipeline continues to import data
- ✅ Public datasets generated correctly

### Failure Investigation

If validation fails:

```bash
# Check logs
git log --oneline -5  # See recent changes

# Check schema
cat seeds/datasources_config.csv  # Verify columns

# Check thresholds
grep -n "null_pct_max" scripts/quality_checks.py  # Current threshold

# Manual test
python3 scripts/validate_schema.py
```

---

## Next Steps

### Immediate (This week)
- [ ] Test Phase 1 locally
- [ ] Review scripts with team
- [ ] Deploy to main branch
- [ ] Monitor first run

### Short-term (Next week)
- [ ] Verify all validations working
- [ ] Adjust thresholds if needed
- [ ] Document actual vs expected in README
- [ ] Plan Phase 2 (Modularity)

### Phase 2 (Following weeks)
- Add dbt templates
- Simplify new datasource integration
- See REFACTORING_ROADMAP.md

---

## FAQ

### Q: What if validation is too strict?
**A**: Adjust `QUALITY_THRESHOLDS` or `EXPECTED_SCHEMA`. It's a configuration, not hardcoded logic.

### Q: Can I still use old hardcoded approach?
**A**: Yes, keep old scripts. Just use new ones in workflow.

### Q: Does this break existing pipeline?
**A**: No, it's additive. If validation fails, you get clear error. Old behavior is preserved.

### Q: How do I debug validation failure?
**A**: Run script locally with same CSV:
```bash
python3 scripts/validate_schema.py
```
See exact error message.

### Q: Can I skip validation for one run?
**A**: Yes, comment out in workflow temporarily:
```yaml
# - name: Validate input schema
#   run: python3 ./scripts/validate_schema.py
```

Then commit fix and re-enable.

---

## References

- REFACTORING_ROADMAP.md (Phase 1 details)
- ARCHITECTURE_REFINEMENT.md (Improvement plan)
- README.md (Operational guide)

---

**Status**: Phase 1 Complete ✅  
**Next**: Phase 2 (Q1-Q2 2025) - Modularity & New Datasources  
**Questions**: See README.md or REFACTORING_ROADMAP.md
