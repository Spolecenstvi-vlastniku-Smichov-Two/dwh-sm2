# SM2 Data Warehouse - Architecture Refactoring Proposal

**Cíl:** Zjednodušit, zrobustnit a zpřístupnit pipeline pro dlouhodobý růst.

**Motivace:**
- Maximální jednoduchost implementace
- Robustnost a odolnost vůči problémům s datovou kvalitou
- Snadné přidávání nových datasources (< 10 minut)
- Dlouhodobá scalabilita bez dopadu historie na performance
- Snadné detekování změn formátu vstupních dat

---

## 1. Analýza Aktuální Architektury

### Zdrojové Komponenty

```
Current Pipeline (3 workflows, 7 scripts):

[CSV Downloads] → [Refresh WF] → fact.csv (Google Drive)
                                    ↓
                  [InfluxImportNormalize WF] → InfluxDB → [7 Python scripts]
                                    ↓
                  [PublishPublicDataset WF] → Parquet (Google Drive)
```

### Problémy

#### 1.1 Redundance (4+ místa pro stejná data)
- **Google Drive**: Raw CSV files
- **DuckDB**: Fact tables (fact.csv imports)
- **InfluxDB**: Time-series store (bottleneck)
- **Google Drive Normalized/**: Hourly aggregations
- **Public/**: Final Parquet export

**Impact**: 
- Synchronizační problémy
- Disk space waste
- Komplexní debugging (které verze je "správná"?)

#### 1.2 Komplexnost Orchestrace
- 3 nezávislé workflows
- Ruční koordinace sekvencí (InfluxDB je bottleneck)
- 7 custom skriptů = 7 bodů selhání
- Těžké vidět data lineage

**Impact**:
- Při přidání nového datasource = nový custom script
- Chyby v jednom skriptu = kaskádovitá selhání

#### 1.3 Datová Kvalita - Rozptýlená
- Validace v AWK (indoor_merge_all_sensors.sh)
- Validace v Python (export_aggregated_to_csv.py)
- Validace v dbt (tests)
- Žádný centrální schéma

**Impact**:
- Chyby v datech jsou tiché (bez explicitního selhání)
- Obtížné pochopit, jaké hodnoty jsou "správné"

#### 1.4 Skalabilita - Dlouhodobě Omezená
- InfluxDB pro archiv = **zvýšené query latency** s rostoucím objemem
- Historická data = zvýšená InfluxDB DB size
- Přidání nového datasource = nový ETL process

**Impact**:
- Za rok: 10x data → 10x delší agregace
- Za 3 roky: neudržitelné

---

## 2. Navrhovaná Zjednodušená Architektura

### 2.1 Principy

1. **Single Source of Truth**: Jedna primární reprezentace (DuckDB fact table)
2. **Schema-First**: Definuj schéma DŘÍV než přijmu data
3. **Landing → Staging → Mart**: Jasné transformační vrstvy
4. **Modular Datasources**: Nový datasource = seed + 3 SQL soubory
5. **Immutable History**: Append-only raw, SCD2 dims

### 2.2 Data Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│                        SIMPLIFIED PIPELINE                  │
└─────────────────────────────────────────────────────────────┘

┌─ INGESTION LAYER ─────────────────────────────────────────┐
│ Raw CSV Download (configurable from seed)                │
│  ├─ Ventilation (Vzduchotechnika/Latest/)               │
│  ├─ Indoor Sensors (Indoor/Latest/)                      │
│  └─ [NEW] Easy to add more sources                       │
└───────────────────────────────────────────────────────────┘
                         ↓ python scripts/ingest_data.py
┌─ LANDING ZONE (DuckDB) ───────────────────────────────────┐
│ Exact raw data (SELECT * only)                           │
│  ├─ landing_ventilation_raw                             │
│  ├─ landing_indoor_raw                                  │
│  └─ _landing_metadata (ingestion_time, row_count, etc.) │
│                                                          │
│ Data Quality Checks:                                     │
│  ├─ Row count anomaly detection (±50%)                  │
│  ├─ Null percentage thresholds (configurable)           │
│  ├─ Date format validation                              │
│  └─ Duplicate timestamp detection                       │
└───────────────────────────────────────────────────────────┘
                         ↓ dbt stg_*.sql
┌─ STAGING LAYER (dbt) ─────────────────────────────────────┐
│ Standard schema + cleansing                              │
│  ├─ stg_ventilation                                     │
│  │   ├─ Rename to standard names (time, location, etc.)│
│  │   ├─ Cast to correct types (TIMESTAMP, FLOAT, etc.)│
│  │   ├─ Normalize dates (RFC3339)                      │
│  │   └─ Handle nulls explicitly                        │
│  └─ stg_indoor (same pattern)                          │
│                                                          │
│ Data Quality Tests:                                      │
│  ├─ Not null checks                                     │
│  ├─ Value range validation (schema.yml)                │
│  ├─ Unique timestamp checks                            │
│  └─ No future dates                                    │
└───────────────────────────────────────────────────────────┘
                         ↓ dbt fct_*.sql
┌─ FACT/DIM LAYER (dbt) ────────────────────────────────────┐
│ Star schema with surrogate keys                         │
│  ├─ dim_locations (SCD Type 2)                         │
│  │   └─ effective_from, effective_to                   │
│  ├─ dim_measurements (LKP)                             │
│  ├─ dim_sensors (LKP)                                  │
│  └─ fct_sensor_readings (FACT)                         │
│      ├─ timestamp (UTC)                                │
│      ├─ location_id (FK)                               │
│      ├─ measurement_id (FK)                            │
│      ├─ sensor_id (FK)                                 │
│      ├─ value (FLOAT)                                  │
│      ├─ data_quality_flags (BITMASK)                   │
│      └─ Partitioned by DATE (for archival)            │
└───────────────────────────────────────────────────────────┘
                         ↓ dbt agg_*.sql (optional)
┌─ AGGREGATIONS (dbt, materialized) ─────────────────────────┐
│ Time-series summaries (computed on-demand)              │
│  ├─ agg_hourly (timestamp_hour, location, measurement) │
│  ├─ agg_daily (timestamp_date, location, measurement)  │
│  └─ agg_monthly (same)                                 │
└───────────────────────────────────────────────────────────┘
                         ↓ python scripts/generate_public_datasets.py
┌─ PUBLIC DATASETS (Parquet) ───────────────────────────────┐
│ Analysis-ready exports                                  │
│  ├─ public_dataset_raw.parquet                         │
│  │   └─ Flattened fct_sensor_readings + dimensions     │
│  ├─ public_dataset_hourly.parquet                      │
│  │   └─ Pre-aggregated for quick viz                   │
│  ├─ public_dataset_schema.json                         │
│  │   └─ Column definitions (auto-generated from dbt)   │
│  ├─ public_dataset_lineage.json                        │
│  │   └─ Data provenance + transformation history       │
│  └─ public_dataset_README.md                           │
│      └─ Data dictionary + usage examples               │
└───────────────────────────────────────────────────────────┘
```

### 2.3 dbt Model Organization

```
models/
├─ 0_landing/
│  ├─ landing_ventilation_raw.sql      (SELECT * from CSV)
│  ├─ landing_indoor_raw.sql           (SELECT * from CSV)
│  ├─ _landing_metadata.sql            (Ingestion tracking)
│  └─ sources.yml                      (Source definitions)
│
├─ 1_staging/
│  ├─ stg_ventilation.sql              (Standardize)
│  ├─ stg_indoor.sql                   (Standardize)
│  ├─ schema.yml                       (Column definitions + tests)
│  └─ tests/
│     ├─ test_stg_ventilation.sql
│     └─ test_stg_indoor.sql
│
├─ 2_marts/
│  ├─ dim_locations.sql                (LKP)
│  ├─ dim_measurements.sql             (LKP)
│  ├─ dim_sensors.sql                  (LKP)
│  ├─ fct_sensor_readings.sql          (FACT - union all stages)
│  ├─ schema.yml                       (Document all fields)
│  └─ tests/
│     ├─ test_fct_uniqueness.sql
│     └─ test_fct_no_future_dates.sql
│
├─ 3_aggregations/
│  ├─ agg_hourly.sql
│  ├─ agg_daily.sql
│  └─ agg_monthly.sql
│
├─ 4_public/
│  ├─ public_dataset.sql               (Flattened for Parquet)
│  └─ schema.yml
│
├─ 5_metrics/
│  ├─ metric_data_quality.sql          (Daily QA)
│  ├─ metric_freshness.sql             (Data staleness checks)
│  └─ metric_ingestion_time.sql        (Pipeline runtime)
│
└─ _shared/
   ├─ macros/
   │  ├─ generate_schema_yml.sql       (Auto-document)
   │  └─ data_quality_utils.sql
   └─ vars.yml                         (Configurable thresholds)
```

### 2.4 Single Unified Workflow

```yaml
name: unified-data-pipeline
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 1 * * *'    # Daily at 01:00 UTC
  workflow_dispatch:

jobs:
  pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      
      - name: Install dependencies
        run: |
          pip install dbt-duckdb pandas pyarrow
          dbt deps
      
      - name: Setup Rclone
        run: # Setup from secrets
      
      - name: 1. Ingest raw data
        run: python scripts/ingest_data.py
        # Reads datasources_config.csv
        # Downloads all configured sources
        # Validates file existence
      
      - name: 2. Load landing zone
        run: python scripts/load_landing.py
        # Load CSVs into DuckDB landing tables
        # Track metadata (ingestion_time, row_count)
      
      - name: 3. dbt run
        run: dbt run
        # Runs landing → staging → marts
        # All data transformations
      
      - name: 4. dbt test (FAIL FAST)
        run: dbt test --fail-fast
        # Data quality checks
        # If tests fail, pipeline stops (prevents bad data)
      
      - name: 5. Generate public datasets
        run: python scripts/generate_public_datasets.py
        # Export to Parquet
        # Generate schema.json
        # Generate lineage.json
      
      - name: 6. Upload to Google Drive
        run: rclone copy ./public_datasets/ sm2drive:Public/
      
      - name: 7. Commit documentation (optional)
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add dbt_docs/
          git commit -m "Update dbt documentation" || true
          git push
```

---

## 3. Comparison: Current vs Proposed

### Execution Simplicity

| Aspekt | Current | Proposed |
|--------|---------|----------|
| Workflows | 3 sequential | 1 unified |
| Scripts | 7 custom | 2 generic |
| Orchestration Complexity | High | Low |
| Failure Isolation | Cascading | Clear |

### Adding New Datasource

**Current (30+ minutes):**
1. Download data
2. Create custom merge script (e.g., indoor_merge_all_sensors.sh)
3. Create aggregation script
4. Create export script
5. Add to workflow
6. Test

**Proposed (< 10 minutes):**
1. Add row to `seeds/datasources_config.csv`
2. Create `models/0_landing/landing_{source}_raw.sql` (SELECT *)
3. Create `models/1_staging/stg_{source}.sql` (Standardize)
4. Create `models/2_marts/fct_{source}.sql` (or add to union)
5. Done - workflow runs automatically

### Data Quality

| Aspect | Current | Proposed |
|--------|---------|----------|
| Quality Definition | Per-script | Centralized (schema.yml) |
| Format Detection | No explicit check | Test fails explicitly |
| Quality Monitoring | Post-pipeline | Pre-fact loading |
| Anomaly Response | Silent or partial failure | Stop pipeline + alert |

### Performance & Scalability

| Aspect | Current | Proposed |
|--------|---------|----------|
| Bottleneck | InfluxDB (import/aggregation) | None (local DuckDB) |
| Historical Data | In InfluxDB (slow queries) | Partitioned + archived |
| Query Performance | Degrades with history | Stable (indexes + partitions) |
| Disk Space | Multiple copies | Single source + exports |

### Long-term Growth

| Aspect | Current | Proposed |
|--------|---------|----------|
| 1 year, 10x data | InfluxDB gets 10x slower | No impact (DuckDB scales) |
| Adding new sensors | Modify script | Add to mapping seed |
| Adding new metrics | New custom script | New staging SQL |
| Schema evolution | Silent data issues | Explicit test failures |

---

## 4. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Create new dbt model structure (0_landing through 5_metrics)
- [ ] Create seeds for datasources_config, mappings
- [ ] Migrate existing data to landing zone
- [ ] Create staging models (stg_ventilation, stg_indoor)
- [ ] Write data quality tests

**Deliverable:** Landing + Staging layers working, tests passing

### Phase 2: Star Schema (Week 2-3)
- [ ] Create dimension tables (dim_locations, dim_measurements, dim_sensors)
- [ ] Create fact table (fct_sensor_readings)
- [ ] Add SCD Type 2 for slowly changing dims
- [ ] Write comprehensive schema.yml documentation

**Deliverable:** Unified fact table (union of all sources)

### Phase 3: Unified Workflow (Week 3-4)
- [ ] Consolidate 3 workflows into 1
- [ ] Simplify Python scripts (ingest + public export only)
- [ ] Remove InfluxDB dependency
- [ ] Remove intermediate CSV exports

**Deliverable:** Single workflow that produces Parquet output

### Phase 4: Modularity (Week 4)
- [ ] Document "add new datasource" process
- [ ] Create reusable templates (landing, staging, fact)
- [ ] Add example: Weather API as new datasource
- [ ] Create automated tests

**Deliverable:** Documented templates for rapid datasource addition

### Phase 5: Monitoring & Polish (Week 5+)
- [ ] Data quality dashboard (metric_data_quality.sql)
- [ ] Freshness monitoring (metric_freshness.sql)
- [ ] Auto-generated documentation
- [ ] Schema evolution alerts

**Deliverable:** Production-ready, monitored pipeline

---

## 5. Key Technical Decisions

### 5.1 Why DuckDB + dbt (not InfluxDB)

**InfluxDB Issues:**
- Designed for real-time streaming, not historical archiving
- Query latency increases with data volume
- Not ACID compliant (data integrity risks)
- Aggregation is complex (custom Flux queries)

**DuckDB Advantages:**
- Local disk-based (unlimited history without performance penalty)
- Full SQL support (complex joins, window functions)
- Parquet-native (direct export to public format)
- ACID transactions (data integrity guaranteed)
- Partitioning support (automatic archival strategy)

### 5.2 Why Star Schema (not Flat)

**Flat (Current):**
```sql
SELECT time, location, data_key, data_value FROM fact.csv
```
- Repeats location names 1M times
- No type safety (string location, string measurement)
- Hard to change location names (update all rows)

**Star (Proposed):**
```sql
SELECT 
    f.timestamp, d.location_name, m.measurement_name, f.value
FROM fct_sensor_readings f
JOIN dim_locations d ON f.location_id = d.location_id
JOIN dim_measurements m ON f.measurement_id = m.measurement_id
```
- Normalized (no data repetition)
- Type-safe (location_id is integer FK)
- Easy to update (change 1 row in dim_locations)
- Slow Changing Dimensions (track location changes over time)

### 5.3 Why Landing → Staging → Mart

**Landing (Raw Copy)**
- Preserve exact ingestion state
- No business logic
- Simple SELECT * queries
- Traceable audit trail

**Staging (Standardize)**
- Rename to standard columns
- Type casting
- Null handling
- Data quality tests

**Mart (Analysis-ready)**
- Add surrogate keys
- Join dimensions
- Quality flags
- Partition for performance

**Benefit:** Clear separation of concerns, easy debugging

### 5.4 Incremental Strategy

```sql
-- Current incremental logic in Refresh workflow:
SELECT * FROM fact.csv 
WHERE time >= (SELECT MAX(start_ts) FROM params)

-- Proposed: Simpler
SELECT * FROM fct_sensor_readings 
WHERE DATE(timestamp) >= CURRENT_DATE - INTERVAL 2 MONTHS
```

**Why:** 
- Append-only landing zone (never delete)
- dbt `incremental` materialization for fact tables
- Configurable retention period (seeds/vars.yml)

---

## 6. Data Quality Strategy

### 6.1 Multi-Layer Validation

```
Layer 1 - Ingestion (Python):
  ├─ File exists and not empty
  ├─ Row count matches expectation (configurable tolerance)
  └─ File format valid (CSV/JSON/etc.)

Layer 2 - Landing (dbt test):
  ├─ Row count matches source
  ├─ No unexpected columns dropped
  └─ Metadata tracked correctly

Layer 3 - Staging (dbt test):
  ├─ Not null on required columns
  ├─ Value ranges (temperature -10 to +50)
  ├─ No duplicate timestamps per sensor
  └─ No future dates

Layer 4 - Fact (dbt test):
  ├─ Referential integrity (FK constraints)
  ├─ No duplicate composite keys
  ├─ Quality flags correctly populated
  └─ Data complete (no gaps > N hours)
```

### 6.2 Anomaly Detection

```sql
-- Daily quality metrics
SELECT
    DATE(timestamp) AS date,
    datasource,
    COUNT(*) AS row_count,
    COUNT(*) FILTER (WHERE value IS NULL) AS null_count,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    STDDEV(value) AS std_dev,
    COUNT(DISTINCT sensor_id) AS active_sensors
FROM fct_sensor_readings
WHERE DATE(timestamp) = CURRENT_DATE
GROUP BY 1, 2
HAVING row_count < expected_count * 0.5  -- Alert on 50% drop
```

### 6.3 Format Change Detection

```yaml
# dbt_project.yml
on-run-end:
  - "{{ log_if_schema_changed() }}"
  - "{{ alert_if_new_columns_detected() }}"
```

When source file format changes:
1. New columns appear in landing table
2. dbt test fails (unexpected columns)
3. Engineer reviews and updates staging model
4. Deploy with explicit migration

---

## 7. Example: Adding New Datasource (Weather API)

### Step 1: Update Configuration
```csv
# seeds/datasources_config.csv (add row)
weather,Weather,api,https://api.openweathermap.org,weather_*.json,90,temperature;humidity;pressure
```

### Step 2: Create Landing Model
```sql
-- models/0_landing/landing_weather_raw.sql
{{ config(materialized='table') }}

SELECT
    timestamp,
    location,
    temperature_kelvin,
    humidity_pct,
    pressure_hpa,
    _ingestion_timestamp,
    _source_file
FROM {{ source('raw', 'weather') }}
```

### Step 3: Create Staging Model
```sql
-- models/1_staging/stg_weather.sql
WITH raw AS (
    SELECT * FROM {{ ref('landing_weather_raw') }}
),
cleaned AS (
    SELECT
        CAST(timestamp AS TIMESTAMP) AS timestamp,
        CAST(location AS VARCHAR) AS location,
        CAST(temperature_kelvin - 273.15 AS FLOAT) AS temperature_celsius,
        CAST(humidity_pct AS FLOAT) AS humidity_pct,
        CAST(pressure_hpa AS FLOAT) AS pressure_hpa,
        'openweather' AS source_system,
        _ingestion_timestamp
    FROM raw
)
SELECT *
FROM cleaned
WHERE
    timestamp IS NOT NULL
    AND location IS NOT NULL
    AND temperature_celsius BETWEEN -50 AND 60
    AND humidity_pct BETWEEN 0 AND 100
```

### Step 4: Add to Fact Table
```sql
-- models/2_marts/fct_sensor_readings.sql
-- Add to union:

SELECT
    timestamp,
    location,
    'temperature' AS measurement_type,
    temperature_celsius AS value,
    sensor_id,
    'openweather' AS source,
    _ingestion_timestamp
FROM {{ ref('stg_weather') }}

UNION ALL

SELECT
    timestamp,
    location,
    'humidity' AS measurement_type,
    humidity_pct AS value,
    sensor_id,
    'openweather' AS source,
    _ingestion_timestamp
FROM {{ ref('stg_weather') }}
```

### Step 5: Add Tests
```yaml
# models/1_staging/schema.yml (add section)
- name: stg_weather
  tests:
    - dbt_expectations.expect_column_count_to_equal: { value: 5 }
  columns:
    - name: temperature_celsius
      tests:
        - not_null
        - dbt_expectations.expect_column_values_to_be_between:
            min_value: -50
            max_value: 60
    - name: humidity_pct
      tests:
        - not_null
        - dbt_expectations.expect_column_values_to_be_between:
            min_value: 0
            max_value: 100
```

**Done!** New datasource integrated with no custom scripts.

---

## 8. Public Dataset Changes

### Current
```
fact.csv (CSV)
→ [manual cleanup] →
public_dataset.csv.gz (CSV)
```

### Proposed
```
fct_sensor_readings (DuckDB)
↓
public_dataset_raw.parquet (Raw detail)
public_dataset_hourly.parquet (Pre-aggregated)
public_dataset_monthly.parquet (Monthly summary)
↓
public_dataset_schema.json (Column definitions)
public_dataset_lineage.json (Data provenance)
public_dataset_README.md (Usage guide)
```

**Benefits:**
- Parquet is more efficient than CSV (10x compression)
- Multiple aggregations for different use cases
- Automatic schema generation (from dbt models)
- Data lineage tracking (which column comes from where)

---

## 9. Migration Path

### Phase 1: Parallel Run (1 week)
- Keep current 3-workflow pipeline active
- Run new unified pipeline in parallel
- Compare outputs (should be identical)
- Validate correctness

### Phase 2: Cutover (1 day)
- Switch public dataset production to new pipeline
- Monitor for issues
- Keep old workflow for fallback (disabled)

### Phase 3: Cleanup (1 week)
- Archive old InfluxDB
- Remove old scripts (but keep in git history)
- Remove old workflows
- Update documentation

---

## 10. Summary: Why This Refactoring

| Goal | Current | Proposed | Benefit |
|------|---------|----------|---------|
| Simplicity | 3 WF + 7 scripts | 1 WF + 2 scripts | -80% complexity |
| New Datasource | 30 min + custom code | < 10 min + seed | Easy scaling |
| Data Quality | Silent failures | Explicit tests | Safe deployments |
| Performance | InfluxDB bottleneck | DuckDB + indexes | Unlimited history |
| History | Lost after archival | Partitioned tables | Full audit trail |
| Schema Changes | Silent breaking | Explicit test failure | Easy detection |
| Team Onboarding | Complex WF logic | dbt best practices | Industry standard |

---

## 11. Questions & Risks

### Q: Why remove InfluxDB?
**A:** It's designed for real-time streaming, not historical archiving. DuckDB + Parquet exports is simpler and more performant.

### Q: How do I query the data?
**A:**
```sql
SELECT 
    timestamp, location, measurement_type, value
FROM fct_sensor_readings
WHERE DATE(timestamp) >= CURRENT_DATE - INTERVAL 30 DAYS
ORDER BY timestamp DESC
```

### Q: Can I still do time-series aggregation?
**A:** Yes! Use dbt materialized views (agg_hourly, agg_daily, agg_monthly). Or compute on-the-fly with DuckDB window functions.

### Risk: What if data source format changes?
**A:** dbt test will fail with clear error. Engineer updates schema, runs test, confirms, deploys.

### Risk: What about very large historical datasets?
**A:** DuckDB partitions by date. Old months are archived to Parquet in S3/GCS. Queries on recent data are fast.

---

## Appendix: Quick Reference

### New Developer Onboarding
1. Read dbt_project.yml (understand structure)
2. Read models/0_landing/sources.yml (data sources)
3. Read models/1_staging/schema.yml (expected schema)
4. Read models/2_marts/fct_sensor_readings.sql (fact table logic)
5. Done!

### Adding New Datasource
1. Seed entry in seeds/datasources_config.csv
2. Create landing_{source}_raw.sql
3. Create stg_{source}.sql
4. Add to fct_sensor_readings union
5. Test

### Debugging Data Issues
1. Check landing table (raw input): `SELECT * FROM landing_{source}_raw LIMIT 10`
2. Check staging table (standardized): `SELECT * FROM stg_{source} LIMIT 10`
3. Check fact table (enriched): `SELECT * FROM fct_sensor_readings WHERE source = '...' LIMIT 10`
4. Check test results: `dbt test --select stg_{source}`

### Running Pipeline
```bash
# Local development
dbt run
dbt test
python scripts/generate_public_datasets.py

# On GitHub (automatic)
git push origin main
# Workflow runs, generates Parquet, uploads to Google Drive
```

---

**Status**: Proposal for Review  
**Author**: Refactoring Recommendation  
**Date**: 2025-12-23
