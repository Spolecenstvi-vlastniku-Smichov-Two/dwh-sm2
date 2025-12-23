# SM2 Data Warehouse - Architecture Refinement (Not Full Refactoring)

**Status**: Revised based on feedback about floating window strategy  
**Date**: 2025-12-23

---

## Executive Summary

Your current architecture with **floating 2-month InfluxDB window** is fundamentally sound and should be kept. Instead of full refactoring, this document proposes **targeted improvements** that increase robustness without changing core design.

**Key insight**: You've solved the hardest problem - how to keep complete historical archive while maintaining constant InfluxDB performance. The improvements are about:
1. Making format changes explicit (not silent)
2. Simplifying new datasource integration
3. Reducing orchestration complexity

---

## 1. Why Your Floating Window Strategy Is Correct

### 1.1 The Genius of 2-Month InfluxDB Window

```
┌─ TIME HIERARCHY ────────────────────────────────────────────┐
│                                                              │
│ Oldest Data (2+ years)  → Parquet Archive (Google Drive)   │
│                            ↑                                 │
│                            └─ Query for historical analysis  │
│                                                              │
│ Recent Data (0-2 months) → InfluxDB (Hot Storage)          │
│                            ↑                                 │
│                            ├─ Real-time aggregation        │
│                            ├─ Quality checks               │
│                            └─ Constant O(1) performance    │
│                                                              │
│ Future (monthly exports) → Normalized CSVs → Parquet      │
│                            Cumulative archive in time        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Why This Avoids All Major Problems

**Problem**: Full history in database = O(n) query latency
**Your Solution**: 2-month window = O(1) queries
**Result**: Performance is constant regardless of total historical data

**Problem**: How to archive history without losing it?
**Your Solution**: Monthly Parquet exports (immutable in Google Drive)
**Result**: Full history available for analysis, InfluxDB stays fast

**Problem**: What if InfluxDB data corrupts or is lost?
**Your Solution**: Previous month's export provides recovery point
**Result**: Self-healing, automatic recovery capability

### 1.3 Self-Healing Properties

Your current system has excellent failure resilience:

```
Scenario: Raw sensor data corrupted in Google Drive

Timeline:
├─ T-60 days: Last month's data exported to Parquet (safe)
├─ T-30 days: Data exported again (safe)
├─ T-Today: Current data corrupted
│
Recovery:
├─ Step 1: Re-download last known good from archive
├─ Step 2: Feed into InfluxDB (overwrite with valid)
├─ Step 3: Re-aggregate and export
├─ Result: Data restored without losing history
```

This is production-grade disaster recovery, built-in.

---

## 2. Actual Problem Areas (Not Full Architecture)

After reviewing your code, real opportunities for improvement:

### 2.1 Problem: Adding New Data Sources Is Complex

**Current State**:
- Sensor data from Atrea (ventilation) → fact.csv
- Sensor data from ThermoPro (indoor) → fact_indoor_*.csv
- Each has custom merge/import logic
- Adding weather API = new custom scripts

**Why Complex**:
```
New datasource workflow:

1. New data format arrives
2. Write custom merge script (or adapt existing)
   └─ indoor_merge_all_sensors.sh: 736 lines of AWK!
3. Integrate with InfluxDB Flux queries
4. Update public dataset generation (build_public_dataset.py)
5. Update dbt mapping (mapping.csv + models)
```

**Simplified Approach**:
```
New datasource workflow (simplified):

1. Create seed: seeds/datasources_config.csv (1 row)
2. Create landing: models/0_landing/landing_{source}_raw.sql (5 lines)
3. Create staging: models/1_staging/stg_{source}.sql (20 lines)
4. Add to fact: Update union in fct_sensor_readings (10 lines)
5. Done!

InfluxDB import + aggregation scripts work automatically
```

**Implementation**: See Section 4.

### 2.2 Problem: Format Changes Are Silent

**Current Risk**:
```
Atrea changes format:
├─ Old: [date, KOT1/Teplota, KOT1/Vlhkost, ...]
└─ New: [timestamp, sensor_id, temp, humidity, ...]

What happens:
├─ prepare_annotated_csv.py runs
├─ New columns don't match expected
├─ Code silently skips them (or crashes)
├─ No explicit "schema mismatch" error
└─ Data loss or corruption (hard to detect)
```

**Better Approach**:
```
Add explicit schema validation:

1. Load datasources_config.csv (expected schema per source)
2. When loading CSV, validate columns match
3. If mismatch → FAIL with clear error message
4. Engineer reviews, updates config, redeploys
```

**Implementation**: Add to `scripts/ingest_data.py`

### 2.3 Problem: Orchestration Could Be Simpler

**Current (3 workflows)**:
```
Refresh (mandatory)
  ├─ Download sensor data
  ├─ dbt transformations
  └─ Output: fact.csv

InfluxImportNormalize (depends on Refresh)
  ├─ Download fact.csv
  ├─ Import to InfluxDB
  ├─ Aggregate to hourly
  └─ Output: {additive,nonadditive}_YYYY-MM.hourly.csv

PublishPublicDataset (depends on InfluxImportNormalize)
  ├─ Download hourly CSVs
  ├─ Generate Parquet + schema
  └─ Output: public_dataset.parquet
```

**Observation**:
- InfluxImportNormalize and PublishPublicDataset both depend on Refresh
- They process different stages of same data
- Could be combined (both are "archive and publish" phase)

**Simplified (2 workflows)**:
```
Refresh (mandatory)
  └─ Output: fact.csv

Archive & Publish (depends on Refresh)
  ├─ Import to InfluxDB
  ├─ Aggregate to hourly
  ├─ Generate Parquet + schema
  └─ Output: public_dataset.parquet
```

**Benefit**:
- Clearer dependency graph (2 vs 3)
- Both succeed or fail together (no partial states)
- Easier to debug (same workflow logs)

---

## 3. Recommended Improvements (In Order of Priority)

### Priority 1: Format Change Detection (Easy, High Value)

**Effort**: 1-2 hours  
**Value**: Prevents silent data loss  
**Risk**: None (additive only)

```python
# scripts/ingest_data.py - Add validation

import pandas as pd
from pathlib import Path

EXPECTED_SCHEMA = {
    'ventilation': ['date', 'KOT1/Teplota venkovní (°C)', 'KOT1/Vlhkost venkovní (%)'],
    'indoor': ['Datetime', 'Temperature_Celsius', 'Relative_Humidity(%)', 'Location']
}

def validate_schema(source_name, csv_file):
    """Fail if CSV columns don't match expected schema."""
    df = pd.read_csv(csv_file)
    actual = set(df.columns)
    expected = set(EXPECTED_SCHEMA[source_name])
    
    missing = expected - actual
    extra = actual - expected
    
    if missing:
        raise ValueError(f"Missing columns in {source_name}: {missing}")
    if extra and source_name != 'other':  # Allow extra columns for new sources
        raise ValueError(f"Unexpected columns in {source_name}: {extra}")
    
    return True

# In main ingest loop:
for source_name, csv_file in sources:
    validate_schema(source_name, csv_file)
    # ... proceed with import
```

**Benefits**:
- ✅ Catches format changes immediately
- ✅ Clear error message for engineer
- ✅ Automatic detection (no manual monitoring)
- ✅ Fail-fast: prevents bad data propagation

---

### Priority 2: Simplify Adding New Datasources (Medium, High Value)

**Effort**: 4-6 hours (once, reusable after)  
**Value**: Makes extending system easy  
**Risk**: Low (configuration-driven)

#### Step 1: Create datasources_config.csv Seed

```csv
# seeds/datasources_config.csv
datasource_id,name,type,location,file_pattern,required_columns,data_type
ventilation,Atrea,csv,sm2drive:Vzduchotechnika/Latest/Upload,Graph*,date;KOT1/Teplota venkovní;KOT1/Vlhkost venkovní,temperature;humidity
indoor,ThermoPro,csv,sm2drive:Indoor/Latest/Upload,ThermoProSensor_export*,Datetime;Temperature_Celsius;Relative_Humidity;Location,temperature;humidity
weather,OpenWeather,api,https://api.openweathermap.org,weather_*.json,timestamp;location;temp_k;humidity,temperature;humidity
```

#### Step 2: Update ingest_data.py (Data Download)

```python
import pandas as pd
from pathlib import Path

# Load config
config = pd.read_csv('seeds/datasources_config.csv')

for _, row in config.iterrows():
    datasource = row['name']
    location = row['location']
    file_pattern = row['file_pattern']
    
    print(f"📥 Downloading {datasource}...")
    
    if row['type'] == 'csv':
        # Download from Google Drive or local
        subprocess.run([
            'rclone', 'copy',
            f"{location}",
            f"./raw/{datasource}/",
            '--include', file_pattern
        ])
    elif row['type'] == 'api':
        # Download from API
        download_from_api(location, f"./raw/{datasource}/")
    
    # Validate schema
    validate_schema(datasource, row['required_columns'])
    print(f"✓ {datasource} validated")
```

#### Step 3: dbt Models Stay Modular

```sql
-- models/0_landing/landing_weather_raw.sql (if added Weather API)
{{ config(materialized='table') }}
SELECT * FROM {{ source('raw', 'weather') }}

-- models/1_staging/stg_weather.sql
WITH raw AS (SELECT * FROM {{ ref('landing_weather_raw') }})
SELECT
    CAST(timestamp AS TIMESTAMP) AS timestamp,
    CAST(location AS VARCHAR) AS location,
    CAST(temp_k - 273.15 AS FLOAT) AS temperature_celsius,
    CAST(humidity AS FLOAT) AS humidity_pct,
    'openweather' AS source,
    CURRENT_TIMESTAMP AS ingested_at
FROM raw
WHERE timestamp IS NOT NULL

-- In models/2_marts/fct_sensor_readings.sql, just add to union:
SELECT
    timestamp,
    location,
    'temperature' AS measurement,
    temperature_celsius AS value,
    'weather' AS source
FROM {{ ref('stg_weather') }}
```

**Result**: New datasource integrated in < 10 minutes without custom scripts.

---

### Priority 3: Combine Workflows 2+3 (Medium, Medium Value)

**Effort**: 2-3 hours  
**Value**: Simpler orchestration  
**Risk**: Low (both succeed/fail together anyway)

```yaml
# New: .github/workflows/aggregate-and-publish.yml
name: Aggregate & Publish Dataset

on:
  workflow_run:
    workflows: ["Refresh"]
    types: [completed]

jobs:
  aggregate-publish:
    runs-on: ubuntu-latest
    if: github.event.workflow_run.conclusion == 'success'
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - name: Setup services (InfluxDB, Rclone)
      - name: Download fact.csv from Google Drive
      - name: Import to InfluxDB + Aggregate
        run: python scripts/influx_aggregate.py
      - name: Generate public datasets (Parquet)
        run: python scripts/generate_public_datasets.py
      - name: Upload to Google Drive
        run: rclone copy ./public_datasets/ sm2drive:Public/
```

**Workflow Trigger**:
- `Refresh` workflow completes successfully
- This workflow runs automatically (depends on previous success)
- Orchestration is explicit (GitHub Actions dependency)

**Benefits**:
- ✅ Clearer mental model (2 workflows: compute, then archive)
- ✅ Automatic failure handling (both succeed/fail)
- ✅ GitHub Actions handles dependencies (no manual coordination)

---

### Priority 4: Add Data Quality Checks in InfluxDB Import

**Effort**: 3-4 hours  
**Value**: Prevents bad data propagation  
**Risk**: Low (tests are optional)

```python
# scripts/influx_quality_checks.py

import subprocess
import pandas as pd
from pathlib import Path

def check_data_quality(fact_csv):
    """Run quality checks before InfluxDB import."""
    df = pd.read_csv(fact_csv)
    
    checks = {
        'row_count': len(df),
        'null_pct': df.isnull().sum().sum() / (len(df) * len(df.columns)),
        'duplicate_timestamps': df.duplicated(subset=['time', 'location']).sum(),
        'future_dates': (df['time'] > pd.Timestamp.now()).sum(),
    }
    
    # Configurable thresholds
    THRESHOLDS = {
        'null_pct': 0.05,  # Fail if > 5% nulls
        'future_dates': 0,  # Fail if any future dates
        'duplicate_timestamps': 0,  # Fail if duplicates
    }
    
    failures = []
    for check, threshold in THRESHOLDS.items():
        if checks[check] > threshold:
            failures.append(f"{check}: {checks[check]} (threshold: {threshold})")
    
    if failures:
        raise ValueError("Quality checks failed:\n" + "\n".join(failures))
    
    print(f"✓ Quality checks passed: {checks}")
    return True

# In workflow:
# 1. Import to InfluxDB
# 2. Run quality checks (FAIL FAST if issues)
# 3. Proceed with aggregation only if checks pass
```

---

## 4. Implementation Roadmap (Incremental)

### Phase 1: Format Change Detection (Week 1)
- [ ] Add schema validation to `scripts/ingest_data.py`
- [ ] Create `seeds/datasources_config.csv` with expected schemas
- [ ] Test with existing datasources
- [ ] Update README with schema definition

**Deliverable**: Pipeline fails explicitly if format changes

### Phase 2: Simplify New Datasources (Week 2)
- [ ] Extract datasource config to seed (from hardcoded paths)
- [ ] Make `scripts/ingest_data.py` data-driven (reads seed)
- [ ] Document "add new datasource" process
- [ ] Create example: add Weather API

**Deliverable**: New datasource can be added in < 10 minutes

### Phase 3: Combine Workflows 2+3 (Week 3)
- [ ] Create `aggregate-and-publish.yml` workflow
- [ ] Remove `publish_public_dataset.yml` (legacy)
- [ ] Update README with new workflow diagram
- [ ] Test parallel run (old + new)

**Deliverable**: Simplified 2-workflow orchestration

### Phase 4: Quality Checks (Week 4)
- [ ] Add quality check script
- [ ] Integrate into InfluxDB workflow
- [ ] Define thresholds per datasource
- [ ] Add monitoring dashboard

**Deliverable**: Data quality issues detected automatically

---

## 5. What NOT To Change (Keep These)

### Keep: 2-Month InfluxDB Window
✅ **Reason**: Solves O(n) performance problem perfectly  
✅ **Benefit**: Constant performance regardless of history  
✅ **Risk of change**: Reintroduces bottleneck

### Keep: Monthly Parquet Archive
✅ **Reason**: Complete historical archive outside InfluxDB  
✅ **Benefit**: Self-healing, recoverable  
✅ **Risk of change**: Lose disaster recovery capability

### Keep: Star Schema in Public Dataset
✅ **Reason**: Better than flat CSVs (not null, type-safe)  
✅ **Benefit**: Easy to add new dimensions  
✅ **Risk of change**: None (Parquet → flat is downgrade)

### Keep: dbt for Transformations
✅ **Reason**: Industry-standard, testable, documented  
✅ **Benefit**: Easy to understand, modify, extend  
✅ **Risk of change**: Lose best practices

---

## 6. Visual: Current vs Refined Architecture

### Current (3 Workflows)

```
┌─────────────────────────────────────────────┐
│ 1. Refresh Workflow                         │
│    ├─ Download sensor data                  │
│    ├─ dbt transformations                   │
│    └─ Output: fact.csv                      │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 2. InfluxImportNormalize Workflow           │
│    ├─ Download fact.csv                     │
│    ├─ Import to InfluxDB                    │
│    ├─ Aggregate to hourly CSVs              │
│    └─ Output: *_hourly.csv                  │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 3. PublishPublicDataset Workflow            │
│    ├─ Download hourly CSVs                  │
│    ├─ Generate Parquet + schema             │
│    └─ Output: public_dataset.parquet        │
└─────────────────────────────────────────────┘
```

### Refined (2 Workflows + Improvements)

```
┌─────────────────────────────────────────────┐
│ Refresh Workflow (mandatory)                │
│ ├─ Download sensor data                     │
│ ├─ [NEW] Validate schema (fail if wrong)    │
│ ├─ dbt transformations                      │
│ └─ Output: fact.csv                         │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ Aggregate & Publish Workflow (auto-trigger) │
│ ├─ Download fact.csv                        │
│ ├─ [NEW] Quality checks (fail if bad)       │
│ ├─ Import to InfluxDB (2-month window)      │
│ ├─ Aggregate to hourly CSVs                 │
│ ├─ [NEW] Data-driven import (from seed)     │
│ ├─ Generate Parquet + schema                │
│ └─ Output: public_dataset.parquet           │
└─────────────────────────────────────────────┘
```

---

## 7. Implementation Examples

### Example 1: Add Weather API Data (10 minutes)

```
Step 1: Add to seed
$ echo "weather,OpenWeather,api,https://api.openweathermap.org,weather_*.json,timestamp;location;temp;humidity" >> seeds/datasources_config.csv

Step 2: Create landing model
$ cat > models/0_landing/landing_weather_raw.sql << 'SQL'
{{ config(materialized='table') }}
SELECT * FROM {{ source('raw', 'weather') }}
SQL

Step 3: Create staging model
$ cat > models/1_staging/stg_weather.sql << 'SQL'
SELECT
    CAST(timestamp AS TIMESTAMP) AS timestamp,
    CAST(location AS VARCHAR) AS location,
    CAST(temp - 273.15 AS FLOAT) AS temperature,
    CAST(humidity AS FLOAT) AS humidity,
    'openweather' AS source
FROM {{ ref('landing_weather_raw') }}
WHERE timestamp IS NOT NULL
SQL

Step 4: Update fact table
$ # Add to union in models/2_marts/fct_sensor_readings.sql
SELECT timestamp, location, 'temperature' AS measurement, temperature AS value, source
FROM {{ ref('stg_weather') }}

Step 5: Done!
✓ New datasource integrated, workflow picks it up automatically
```

### Example 2: Detect Format Change (Automatic)

```
Scenario: Atrea changes column name

Old: [date, KOT1/Teplota venkovní (°C), ...]
New: [timestamp, temperature_celsius, ...]

Timeline:
├─ Workflow downloads new file
├─ Schema validation runs: expected [date, KOT1/...] actual [timestamp, ...]
├─ Validation FAILS with clear error
├─ Email alert sent: "Schema mismatch in Atrea data"
├─ Engineer reviews, updates seeds/datasources_config.csv
├─ Engineer updates models/1_staging/stg_ventilation.sql
└─ Redeploy, workflow runs successfully

Result: Format change detected in < 1 hour, not silent data loss
```

---

## 8. FAQ

### Q: Why not remove InfluxDB entirely?
**A**: InfluxDB is perfect for your use case:
- Designed for time-series data
- Built-in retention policies (2-month window)
- Fast aggregation queries (Flux language)
- No bottleneck because you never query full history

If you removed InfluxDB:
- Would need alternative aggregation layer
- DuckDB is great for analytics, not real-time time-series
- Would duplicate functionality (dbt already does transformations)

### Q: Why 2-month window specifically?
**A**: You've chosen wisely. Trade-off:
- **Too short (1 month)**: Limited for debugging, harder to detect anomalies
- **Too long (6 months)**: Performance degrades, InfluxDB size grows
- **2 months**: Covers recent data + previous month for comparisons

Configurable in InfluxDB retention policy.

### Q: What about very old data queries?
**A**: That's why you have Parquet archive:
```python
# For research (old data):
import pandas as pd
df = pd.read_parquet('sm2_public_dataset.parquet')
df.query('timestamp >= "2023-01-01" & timestamp < "2023-02-01"')

# For monitoring (recent data):
# Query InfluxDB (fast)
```

### Q: How do I add a new aggregation level?
**A**: Add a Flux query:
```python
# scripts/influx_aggregate.py
# Add this alongside hourly, daily aggregations:

def aggregate_weekly():
    flux = '''
    from(bucket:"sensor_data")
      |> range(start: -30d)
      |> filter(fn: (r) => r._measurement == "nonadditive")
      |> aggregateWindow(every: 1w, fn: mean, createEmpty: false)
    '''
    # Export to weekly_*.csv
```

**Or** in dbt:
```sql
-- models/3_aggregations/agg_weekly.sql
SELECT
    DATE_TRUNC('week', timestamp) AS week,
    location,
    measurement,
    AVG(value) AS avg_value
FROM {{ ref('fct_sensor_readings') }}
GROUP BY 1, 2, 3
```

---

## 9. Success Metrics

After implementing these improvements:

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Time to add datasource | 30+ min | < 10 min | ✅ |
| Format change detection | Silent | Explicit | ✅ |
| New engineer onboarding | Complex | Straightforward | ✅ |
| Pipeline orchestration | 3 workflows | 2 workflows | ✅ |
| Data quality visibility | Limited | Comprehensive | ✅ |

---

## 10. Summary

Your current architecture is **fundamentally correct**. The floating 2-month InfluxDB window with monthly Parquet archives is an elegant solution to a hard problem.

**This refinement proposal focuses on**:
1. Making format changes explicit (not silent)
2. Simplifying new datasource integration
3. Reducing orchestration complexity

**All changes are additive** (no breaking changes). You keep the core robust design while gaining better visibility and extensibility.

**Next Step**: Pick 1-2 improvements from Section 3 and implement incrementally.

EOF
cat /Users/lubomirkamensky/git/dwh-sm2/ARCHITECTURE_REFINEMENT.md | head -100
