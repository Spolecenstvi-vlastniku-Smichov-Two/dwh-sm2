# SM2 Data Warehouse - Refactoring & Growth Roadmap

**Status**: Strategic Implementation Plan  
**Horizon**: 24 months  
**Vision**: From single-building sensor warehouse to enterprise multi-model data platform

---

## Executive Summary

This document provides a **phase-by-phase refactoring roadmap** that:

1. **Respects current strength**: Your hybrid ephemeral architecture is correct and should be protected
2. **Addresses real pain points**: Targeted improvements to implementation details
3. **Enables future growth**: Structured path to Neo4j, Elasticsearch, multi-building support
4. **Maintains stability**: Each phase is independent, no breaking changes
5. **Controls cost**: Ephemeral infrastructure throughout

**Timeline**: 24 months, 6 phases, quarterly releases

---

## 1. Current State Analysis

### 1.1 What's Working Well ✅

| Component | Strength |
|-----------|----------|
| **Architecture** | Hybrid ephemeral multi-model design |
| **Cost** | 99% cheaper than persistent servers |
| **Data Flow** | Clear wide→narrow→aggregate transformation |
| **Reproducibility** | File-first approach enables replay |
| **Resilience** | Self-healing (2-month cache + monthly archive) |
| **Technology Choice** | DuckDB + InfluxDB perfectly matched to data shapes |

### 1.2 Pain Points to Address ⚠️

| Issue | Impact | Effort | Priority |
|-------|--------|--------|----------|
| **Silent format changes** | Data loss risk | 1-2 hours | P1 |
| **Complex new datasource** | Manual scripts required | 4-6 hours | P2 |
| **3 workflows + coordination** | Orchestration complexity | 2-3 hours | P2 |
| **Scattered data quality** | Hard to debug issues | 3-4 hours | P2 |
| **Limited monitoring** | Unknown pipeline health | 2 hours | P3 |
| **No hierarchy support** | Can't model building structure | Design phase | P4 |
| **Single building only** | No multi-tenant support | Major effort | P5 |

### 1.3 Technical Debt (Intentional)

**Items to NOT fix (by design)**:
- ✅ Keep 2-month InfluxDB window (intentional, correct)
- ✅ Keep ephemeral databases (intentional, cost-optimized)
- ✅ Keep file-first persistence (intentional, reproducible)

**Items to improve**:
- 🔧 Add explicit format validation
- 🔧 Simplify new datasource integration
- 🔧 Combine workflows 2+3
- 🔧 Centralize quality checks
- 🔧 Add operational monitoring

---

## 2. Phased Refactoring Roadmap

### Phase 1: Foundation (Q1 2025, Weeks 1-4)

**Goal**: Improve data quality visibility and format change detection

#### 1.1 Add Schema Validation

```python
# scripts/validate_schema.py (NEW)
import pandas as pd
from pathlib import Path

EXPECTED_SCHEMA = {
    'ventilation': {
        'columns': ['date', 'KOT1/Teplota venkovní', 'KOT1/Vlhkost venkovní'],
        'types': {'date': 'object', 'KOT1/Teplota venkovní': 'float64'}
    },
    'indoor': {
        'columns': ['Datetime', 'Location', 'Temperature_Celsius', 'Relative_Humidity(%)'],
        'types': {'Datetime': 'object', 'Temperature_Celsius': 'float64'}
    }
}

def validate_datasource(source_name, csv_file):
    """Fail explicitly if schema doesn't match expected."""
    df = pd.read_csv(csv_file)
    
    expected_cols = set(EXPECTED_SCHEMA[source_name]['columns'])
    actual_cols = set(df.columns)
    
    missing = expected_cols - actual_cols
    unexpected = actual_cols - expected_cols
    
    if missing:
        raise ValueError(
            f"❌ SCHEMA MISMATCH in {source_name}\n"
            f"Missing columns: {missing}\n"
            f"Expected: {expected_cols}\n"
            f"Actual: {actual_cols}\n"
            f"Action: Check if {csv_file} format changed"
        )
    
    if unexpected and source_name != 'new':
        print(f"⚠️ WARNING: Unexpected columns in {source_name}: {unexpected}")
    
    return True

# In workflow: Call before any processing
validate_datasource('ventilation', './gdrive/fact.csv')
validate_datasource('indoor', './gdrive/all_sensors_merged.csv')
```

#### 1.2 Create Datasources Configuration Seed

```csv
# seeds/datasources_config.csv
datasource_id,name,source_type,location,file_pattern,required_columns,data_type,retention_months,status
1,ventilation,csv,sm2drive:Vzduchotechnika/Latest/Upload,Graph*.csv,date;KOT1/Teplota;KOT1/Vlhkost,temperature;humidity,2,active
2,indoor,csv,sm2drive:Indoor/Latest/Upload,ThermoProSensor_export*.csv,Datetime;Location;Temperature_Celsius;Relative_Humidity,temperature;humidity,2,active
3,weather,api,https://api.openweathermap.org,weather_*.json,timestamp;location;temperature_k;humidity,temperature;humidity,1,planned
4,air_quality,csv,sm2drive:AirQuality/Latest,air_quality*.csv,time;location;pm25;co2,pollution,1,planned
```

#### 1.3 Update Ingest Script (Data-Driven)

```python
# scripts/ingest_data.py (REFACTORED)
import pandas as pd
import subprocess
from pathlib import Path

# Load datasources config
config = pd.read_csv('seeds/datasources_config.csv')

for _, row in config.iterrows():
    if row['status'] != 'active':
        print(f"⏭️ Skipping {row['name']} (status: {row['status']})")
        continue
    
    datasource = row['name']
    location = row['location']
    file_pattern = row['file_pattern']
    
    print(f"📥 Downloading {datasource}...")
    
    if row['source_type'] == 'csv':
        # Download from Google Drive
        Path(f'./raw/{datasource}').mkdir(parents=True, exist_ok=True)
        subprocess.run([
            'rclone', 'copy',
            f"{location}",
            f"./raw/{datasource}/",
            '--include', file_pattern,
            '-v'
        ])
    elif row['source_type'] == 'api':
        # Download from API
        download_from_api(row['location'], f"./raw/{datasource}/")
    
    # Validate schema
    csv_files = list(Path(f"./raw/{datasource}").glob(file_pattern))
    if not csv_files:
        raise FileNotFoundError(f"No files found for {datasource}")
    
    for csv_file in csv_files:
        validate_schema(datasource, csv_file, row['required_columns'])
    
    print(f"✅ {datasource}: {len(csv_files)} files validated")
```

#### 1.4 Add Quality Check Script

```python
# scripts/quality_checks.py (NEW)
import pandas as pd
from pathlib import Path

QUALITY_THRESHOLDS = {
    'ventilation': {
        'null_pct': 0.05,        # Fail if > 5% nulls
        'row_count_min': 100,    # At least 100 rows
        'row_count_max': 100000  # At most 100k rows
    },
    'indoor': {
        'null_pct': 0.02,
        'row_count_min': 50,
        'row_count_max': 50000
    }
}

def check_data_quality(source_name, csv_file):
    """Run quality checks before importing to InfluxDB."""
    df = pd.read_csv(csv_file)
    
    thresholds = QUALITY_THRESHOLDS.get(source_name, {})
    issues = []
    
    # Check null percentage
    null_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
    if null_pct > thresholds.get('null_pct', 0.1):
        issues.append(f"Null %: {null_pct:.1%} (threshold: {thresholds.get('null_pct', 0.1):.1%})")
    
    # Check row count
    row_count = len(df)
    if row_count < thresholds.get('row_count_min', 10):
        issues.append(f"Too few rows: {row_count} (min: {thresholds.get('row_count_min', 10)})")
    if row_count > thresholds.get('row_count_max', 1000000):
        issues.append(f"Too many rows: {row_count} (max: {thresholds.get('row_count_max', 1000000)})")
    
    # Check for unexpected future dates
    if 'date' in df.columns or 'Datetime' in df.columns:
        date_col = 'date' if 'date' in df.columns else 'Datetime'
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        future_count = (df[date_col] > pd.Timestamp.now()).sum()
        if future_count > 0:
            issues.append(f"Future dates detected: {future_count} rows")
    
    if issues:
        raise ValueError(f"❌ Quality checks failed for {source_name}:\n" + "\n".join(issues))
    
    print(f"✅ Quality checks passed for {source_name}: {row_count} rows, {null_pct:.1%} nulls")
    return True
```

#### 1.5 Update Workflow

```yaml
# .github/workflows/influx_import_workflow.yml (UPDATED)
jobs:
  import:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: 1. Validate input schema
        run: python scripts/validate_schema.py
        # NEW: Fails if format changed
      
      - name: 2. Download data
        run: python scripts/ingest_data.py
        # UPDATED: Data-driven from seeds/datasources_config.csv
      
      - name: 3. Quality checks
        run: python scripts/quality_checks.py
        # NEW: Fails before InfluxDB if issues detected
      
      - name: 4. InfluxDB aggregation
        run: python scripts/influx_aggregate.py
      
      - name: 5. Export public datasets
        run: python scripts/generate_public_datasets.py
```

#### Deliverable: Phase 1
- [x] Schema validation (explicit failure on format change)
- [x] Data-driven ingest (from seeds/datasources_config.csv)
- [x] Quality checks (pre-InfluxDB)
- [x] Updated workflows
- **Result**: Format changes detected, data quality explicit

---

### Phase 2: Modularity (Q1-Q2 2025, Weeks 5-8)

**Goal**: Enable new datasources without custom scripts

#### 2.1 Create dbt Templates

```sql
-- templates/0_landing_template.sql
-- Use this template for every new datasource

{{ config(materialized='table') }}

-- Load raw data from source
-- NO transformations, just SELECT *
-- Preserves exact input state for audit trail

SELECT * FROM {{ source('raw', '{{ datasource_name }}') }}
```

```sql
-- templates/1_staging_template.sql
-- Standardize to common schema

WITH raw AS (
    SELECT * FROM {{ ref('landing_{{ datasource_name }}_raw') }}
)
,cleaned AS (
    SELECT
        CAST({{ timestamp_column }} AS TIMESTAMP) AS timestamp,
        CAST({{ location_column }} AS VARCHAR) AS location,
        CAST({{ measurement_column }} AS VARCHAR) AS measurement,
        CAST({{ value_column }} AS FLOAT) AS value,
        '{{ source_name }}' AS source,
        CURRENT_TIMESTAMP AS ingested_at
    FROM raw
    WHERE
        {{ timestamp_column }} IS NOT NULL
        AND {{ measurement_column }} IS NOT NULL
        AND {{ value_column }} IS NOT NULL
)
SELECT *
FROM cleaned
WHERE
    -- Data quality: value must be in expected range
    value BETWEEN {{ value_min }} AND {{ value_max }}
    -- No future dates
    AND timestamp <= CURRENT_TIMESTAMP
    -- Recent data only (rolling 2-month window)
    AND timestamp >= CURRENT_DATE - INTERVAL {{ retention_months }} MONTH
```

#### 2.2 Create Datasource Mapping Seed

```csv
# seeds/datasource_mappings.csv
datasource_id,timestamp_column,location_column,measurement_column,value_column,source_name,value_min,value_max,retention_months
1,date,,"KOT1/Teplota venkovní",data_value,Atrea,-50,60,2
2,Datetime,Location,Temperature_Celsius,data_value,ThermoPro,-10,50,2
3,timestamp,location,temperature_k,temp_k,OpenWeather,200,350,1
4,time,location,pm25,pm25_value,AirQuality,0,500,1
```

#### 2.3 Document "Add New Datasource" Process

**Quick Start Guide**:

```
To add Weather API data (< 10 minutes):

1. Add row to seeds/datasources_config.csv:
   weather,Weather,api,https://api.openweathermap.org,weather_*.json,timestamp;location;temp;humidity,temperature;humidity,1,planned

2. Add row to seeds/datasource_mappings.csv:
   3,timestamp,location,temperature_k,temperature,OpenWeather,200,350,1

3. Create landing model: models/0_landing/landing_weather_raw.sql
   {{ config(materialized='table') }}
   SELECT * FROM {{ source('raw', 'weather') }}

4. Create staging model: models/1_staging/stg_weather.sql
   (Use template, fill in Jinja variables)

5. Update fact table: models/2_marts/fct_sensor_readings.sql
   Add to union:
   SELECT timestamp, location, measurement, value, source
   FROM {{ ref('stg_weather') }}

6. Run dbt + tests
   dbt seed
   dbt run
   dbt test

Done! New datasource is integrated.
```

#### Deliverable: Phase 2
- [x] dbt templates for landing/staging models
- [x] Datasource mapping seed
- [x] Documentation for new datasource integration
- **Result**: Any engineer can add new datasource in < 10 minutes

---

### Phase 3: Orchestration Simplification (Q2 2025, Weeks 9-12)

**Goal**: Reduce 3 workflows to 2 with clearer dependency

#### 3.1 Combine Workflows 2+3

**Current** (3 workflows):
```
Refresh → InfluxImportNormalize → PublishPublicDataset
```

**Refined** (2 workflows):
```
Refresh → Aggregate & Publish (auto-triggered when Refresh succeeds)
```

#### 3.2 New Unified Workflow

```yaml
# .github/workflows/aggregate-and-publish.yml (NEW)
name: Aggregate & Publish Dataset

on:
  workflow_run:
    workflows: ["Refresh"]
    types: [completed]
    branches: [main]

jobs:
  aggregate-publish:
    runs-on: ubuntu-latest
    if: github.event.workflow_run.conclusion == 'success'
    
    services:
      influxdb:
        image: influxdb:2.7
        env:
          INFLUX_DB_BUCKET: sensor_data
          INFLUX_DB_RETENTION: 2160h  # 90 days (2+ months)
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      
      - name: Setup Rclone
        env:
          RCLONE_CONFIG: ${{ secrets.RCLONE_CONFIG }}
        run: |
          echo "$RCLONE_CONFIG" > ~/.config/rclone/rclone.conf
          chmod 600 ~/.config/rclone/rclone.conf
      
      - name: 1. Download fact tables from Refresh
        run: |
          rclone copy sm2drive:Vzduchotechnika/Model/fact.csv ./gdrive/
          rclone copy sm2drive:Indoor/Model/fact_indoor_*.csv ./gdrive/
      
      - name: 2. Validate & quality checks
        run: python scripts/quality_checks.py
      
      - name: 3. Wait for InfluxDB startup
        run: |
          for i in {1..30}; do
            curl -s http://localhost:8086/health && echo "InfluxDB ready" && break
            echo "Waiting for InfluxDB... ($i/30)"
            sleep 2
          done
      
      - name: 4. Import to InfluxDB
        run: python scripts/influx_import.py
        env:
          INFLUX_URL: http://localhost:8086
          INFLUX_TOKEN: ci-secret-token
          INFLUX_ORG: ci-org
      
      - name: 5. Aggregate (hourly, daily, weekly)
        run: python scripts/influx_aggregate.py
      
      - name: 6. Generate public datasets
        run: python scripts/generate_public_datasets.py
      
      - name: 7. Upload to Google Drive
        run: |
          rclone copy ./public_datasets/ sm2drive:Public/ --delete
      
      - name: 8. Upload to cloud (optional)
        run: python scripts/upload_to_cloud.py
        env:
          CLOUD_TARGET: ${{ secrets.CLOUD_TARGET }}
```

#### 3.3 Archive Old Workflow

```yaml
# .github/workflows/influx_import_workflow.yml (DEPRECATED)
# This workflow is being replaced by aggregate-and-publish.yml
# Keeping for reference only - DO NOT USE
```

#### Deliverable: Phase 3
- [x] Single combined workflow (aggregate-and-publish.yml)
- [x] Removed old separate workflows
- [x] Clearer dependency (auto-trigger on Refresh success)
- **Result**: Simpler orchestration (2 vs 3 workflows)

---

### Phase 4: Monitoring & Observability (Q2-Q3 2025, Weeks 13-16)

**Goal**: Understand pipeline health and data quality in real-time

#### 4.1 Add Operational Metrics

```sql
-- models/5_metrics/metric_daily_summary.sql
SELECT
    CURRENT_DATE AS date,
    datasource,
    measurement,
    COUNT(*) AS row_count,
    COUNT(DISTINCT timestamp) AS unique_timestamps,
    COUNT(*) FILTER (WHERE value IS NULL) AS null_count,
    ROUND(COUNT(*) FILTER (WHERE value IS NULL)::FLOAT / COUNT(*) * 100, 2) AS null_pct,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    ROUND(AVG(value), 2) AS avg_value,
    ROUND(STDDEV(value), 2) AS std_dev,
    COUNT(DISTINCT location) AS locations_active
FROM {{ ref('fct_sensor_readings') }}
WHERE DATE(timestamp) = CURRENT_DATE
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 2, 3
```

#### 4.2 Add Anomaly Detection

```python
# scripts/detect_anomalies.py (NEW)
import pandas as pd
import duckdb

def detect_anomalies(df_metrics):
    """Detect data quality anomalies."""
    anomalies = []
    
    # Check 1: Sudden drop in row count
    if len(df_metrics) > 1:
        prev_row_count = df_metrics.iloc[-2]['row_count']
        curr_row_count = df_metrics.iloc[-1]['row_count']
        if curr_row_count < prev_row_count * 0.5:  # 50% drop
            anomalies.append(
                f"⚠️ Row count dropped 50%: "
                f"from {prev_row_count} to {curr_row_count}"
            )
    
    # Check 2: High null percentage
    for _, row in df_metrics.iterrows():
        if row['null_pct'] > 10:
            anomalies.append(
                f"⚠️ High null %: {row['datasource']} "
                f"{row['measurement']} = {row['null_pct']:.1f}%"
            )
    
    # Check 3: Unusual value ranges
    for _, row in df_metrics.iterrows():
        if row['std_dev'] > row['avg_value'] * 2:
            anomalies.append(
                f"⚠️ High variance: {row['datasource']} "
                f"std_dev ({row['std_dev']:.2f}) > 2x avg ({row['avg_value']:.2f})"
            )
    
    return anomalies

# In workflow:
# 1. Generate metrics
# 2. Detect anomalies
# 3. Log warnings (don't fail)
# 4. Email if critical
```

#### 4.3 Add GitHub Issue Auto-Reporting

```python
# scripts/report_issues.py (NEW)
import github
import os

def create_issue_if_anomalies(anomalies):
    """Create GitHub issue if anomalies detected."""
    if not anomalies:
        print("✅ No anomalies detected")
        return
    
    gh = github.Github(os.getenv('GITHUB_TOKEN'))
    repo = gh.get_repo('Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2')
    
    issue_title = f"⚠️ Data Quality Alert - {pd.Timestamp.now().strftime('%Y-%m-%d')}"
    issue_body = "## Detected Anomalies\n\n"
    issue_body += "\n".join(f"- {a}" for a in anomalies)
    
    repo.create_issue(
        title=issue_title,
        body=issue_body,
        labels=['data-quality', 'automated']
    )
    print(f"📋 Created issue: {issue_title}")
```

#### Deliverable: Phase 4
- [x] Daily metrics SQL models
- [x] Anomaly detection script
- [x] GitHub issue auto-reporting
- **Result**: Automatic alerting on data issues

---

### Phase 5: Graph Database Integration (Q3-Q4 2025, Weeks 17-24)

**Goal**: Support hierarchical data and relationships

#### 5.1 Design Hierarchy Model

```
Building SM2
├─ Floor 1 (NP)
│  ├─ Zone 1 (1NP-S1)
│  │  ├─ Sensor: Thermometer
│  │  └─ Sensor: Humidity Sensor
│  └─ Zone 2 (1NP-S2)
├─ Floor 5 (5NP)
│  ├─ Zone 1 (5NP-S1)
│  └─ Zone 2 (5NP-S2)
└─ Basement (PP)
   └─ Zone 1 (1PP-S1)
```

#### 5.2 Create Neo4j Initialization

```yaml
# .github/workflows/hierarchy-sync.yml (NEW, triggered manually or on-demand)
name: Sync Building Hierarchy

on:
  workflow_dispatch:
  schedule:
    - cron: '0 2 * * 6'  # Weekly Saturday

jobs:
  sync-hierarchy:
    runs-on: ubuntu-latest
    
    services:
      neo4j:
        image: neo4j:latest
        env:
          NEO4J_AUTH: none  # Disable auth for CI
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Load hierarchy from CSV
        run: |
          # Load seeds/building_hierarchy.csv into Neo4j
          python scripts/load_hierarchy.py
      
      - name: Run hierarchy queries
        run: |
          # Test: "Show all sensors in building"
          # Test: "Find adjacent zones"
          # Test: "Get temperature path"
          python scripts/test_hierarchy.py
      
      - name: Export hierarchy relationships
        run: |
          # Export as Parquet for public dataset
          python scripts/export_hierarchy.py
```

#### 5.3 Create Hierarchy Seed

```csv
# seeds/building_hierarchy.csv
id,parent_id,type,name,level,coordinates
B1,,Building,SM2,0,"50.0735 14.4079"
B1_F1,B1,Floor,Podlaží 1,1,
B1_F1_Z1,B1_F1,Zone,Zóna 1,2,
B1_F1_Z1_S1,B1_F1_Z1,Sensor,SM2_01_L1_01,3,
B1_F1_Z1_S2,B1_F1_Z1,Sensor,Thermometer_1,3,
B1_F1_Z2,B1_F1,Zone,Zóna 2,2,
```

#### 5.4 Cypher Queries

```cypher
// Create nodes
LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/building_hierarchy.csv' AS row
CREATE (n:Node {
    id: row.id,
    type: row.type,
    name: row.name,
    level: toInteger(row.level)
})

// Create relationships
MATCH (child:Node {parent_id: NOT NULL})
MATCH (parent:Node {id: child.parent_id})
CREATE (parent)-[:CONTAINS]->(child)

// Query: All sensors in Zone 1
MATCH (zone:Node {type: 'Zone', name: 'Zóna 1'})-[:CONTAINS*]->(sensor:Node {type: 'Sensor'})
RETURN sensor.name, sensor.id

// Query: Adjacent zones
MATCH (zone1:Node {type: 'Zone'})-[:CONTAINS]->(sensor1)
MATCH (zone2:Node {type: 'Zone'})-[:CONTAINS]->(sensor2)
WHERE zone1.parent_id = zone2.parent_id  // Same floor
AND zone1 <> zone2
RETURN zone1.name, zone2.name
```

#### Deliverable: Phase 5
- [x] Building hierarchy model (CSV seed)
- [x] Neo4j initialization workflow
- [x] Hierarchy queries (Cypher)
- [x] Hierarchy export as Parquet
- **Result**: Support for hierarchical data + relationship queries

---

### Phase 6: Multi-Building & Enterprise (Q4 2025+, Weeks 25+)

**Goal**: Scale to multiple buildings and enterprise integrations

#### 6.1 Multi-Tenant Architecture

```
buildings_config.csv:
├─ SM2 (Smíchov Two)
├─ Building_B (Prague)
├─ Building_C (Brno)
└─ Building_D (Ostrava)
```

#### 6.2 Cloud DWH Integration

```python
# scripts/upload_to_cloud.py (NEW)

def upload_to_bigquery(parquet_file):
    """Upload public dataset to BigQuery."""
    from google.cloud import bigquery
    
    client = bigquery.Client()
    dataset_id = 'sm2_data'
    table_id = 'sensor_readings'
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=True,
    )
    
    with open(parquet_file, 'rb') as source_file:
        job = client.load_table_from_file(
            source_file,
            f"{dataset_id}.{table_id}",
            job_config=job_config
        )
    
    job.result()  # Wait for job to complete

def upload_to_snowflake(parquet_file):
    """Upload to Snowflake."""
    # Similar pattern using snowflake-connector-python

def upload_to_redshift(parquet_file):
    """Upload to AWS Redshift."""
    # Similar pattern using redshift connector
```

#### Deliverable: Phase 6
- [x] Multi-building support
- [x] Cloud DWH integrations (BigQuery, Snowflake, Redshift)
- [x] Federated data platform
- **Result**: Enterprise data warehouse

---

## 3. Implementation Sequence

### Recommended Execution Order

```
PHASE 1: Foundation (4 weeks)
├─ Week 1: Schema validation
├─ Week 2: Ingest refactoring
├─ Week 3: Quality checks
└─ Week 4: Testing + Documentation

PHASE 2: Modularity (4 weeks)
├─ Week 5: dbt templates
├─ Week 6: Datasource seed
├─ Week 7: Documentation + example
└─ Week 8: Testing

PHASE 3: Orchestration (4 weeks)
├─ Week 9-10: Workflow consolidation
├─ Week 11: Testing parallel run
└─ Week 12: Cutover

PHASE 4: Monitoring (4 weeks)
├─ Week 13: Metrics models
├─ Week 14: Anomaly detection
├─ Week 15: Issue reporting
└─ Week 16: Dashboard

PHASE 5: Neo4j (8 weeks)
├─ Week 17-18: Design + seed
├─ Week 19-20: Neo4j integration
├─ Week 21-22: Queries + export
└─ Week 23-24: Testing

PHASE 6+: Enterprise (ongoing)
├─ Multi-building support
├─ Cloud DWH integrations
└─ Federated analytics
```

---

## 4. Resource Requirements

### Team Composition (Per Phase)

| Phase | Role | Weeks | FTE |
|-------|------|-------|-----|
| 1 | Backend Engineer | 4 | 1.0 |
| 2 | Backend Engineer | 4 | 0.8 |
| 3 | DevOps/Backend | 4 | 0.6 |
| 4 | Backend/DataEng | 4 | 0.5 |
| 5 | DataEng/Architect | 8 | 0.7 |
| 6+ | DataEng Lead | ongoing | 0.5 |

### Infrastructure Cost

| Component | Phase 1-3 | Phase 4-5 | Phase 6+ |
|-----------|-----------|-----------|----------|
| GitHub Actions | Free | Free | Free |
| DuckDB | $0 | $0 | $0 |
| InfluxDB ephemeral | $0 | $0 | $0 |
| Neo4j (Phase 5+) | $0 | $0 | $0 |
| Storage (Parquet) | $0-5 | $0-10 | $5-20 |
| Cloud DWH (Phase 6+) | - | - | $50-500 |
| **Total** | **$0-5** | **$0-10** | **$55-520** |

---

## 5. Success Metrics

### Phase 1 Success
- [ ] Format changes detected within 1 hour
- [ ] All ingestion failures explicit (not silent)
- [ ] Data quality metrics logged daily

### Phase 2 Success
- [ ] New datasource integrated in < 10 minutes
- [ ] No custom scripts needed for standard datasources
- [ ] 3/3 engineers can add new datasource independently

### Phase 3 Success
- [ ] Single workflow combines import + publish
- [ ] Automatic triggering on Refresh success
- [ ] Clearer mental model (2 workflows, not 3)

### Phase 4 Success
- [ ] Anomalies detected automatically
- [ ] GitHub issues created on data quality issues
- [ ] Zero silent data quality failures

### Phase 5 Success
- [ ] Hierarchical queries working (Cypher)
- [ ] Building structure modeled in Neo4j
- [ ] Hierarchy exported as Parquet

### Phase 6 Success
- [ ] Data available in BigQuery/Snowflake/Redshift
- [ ] Multiple buildings in same platform
- [ ] Federated queries across buildings

---

## 6. Risk Management

### Risk 1: Breaking Changes in Workflows

**Mitigation**:
- Parallel run Phase 3 (old + new workflows side-by-side)
- Validate outputs match before cutover
- Keep old workflows as fallback (disabled)

### Risk 2: InfluxDB Connection Issues

**Mitigation**:
- Pre-flight health checks before import
- Retry logic with exponential backoff
- Fallback to previous month's cache if import fails

### Risk 3: Data Quality Validation Too Strict

**Mitigation**:
- Start with loose thresholds (10% null, 50% row count variance)
- Tighten gradually based on actual data patterns
- Allow overrides (e.g., skip validation flag) for legitimate edge cases

### Risk 4: Neo4j Complexity

**Mitigation**:
- Phase 5 is optional (start only when hierarchies critical)
- Keep Neo4j separate (doesn't affect phases 1-4)
- Use managed Neo4j (not self-hosted) if scaling needed

---

## 7. Rollback Strategy

If any phase introduces issues:

```
Phase 1: Rollback
├─ Remove schema validation scripts
├─ Revert ingest_data.py to hardcoded paths
└─ Keep quality checks (backward compatible)

Phase 2: Rollback
├─ Remove dbt templates
├─ Revert to hardcoded datasource models
└─ Keep seeds (useful regardless)

Phase 3: Rollback
├─ Disable aggregate-and-publish workflow
├─ Re-enable old 3-workflow setup
└─ Diff outputs between old and new before committing

Phase 4-6: Rollback
├─ Disable monitoring (no-op if not collecting)
├─ Disable Neo4j (separate workflow)
└─ All previous phases remain functional
```

---

## 8. Communication Plan

### Stakeholders

| Role | Communication | Frequency |
|------|---------------|-----------|
| **Data Scientists** | "New datasources easier to integrate" | Weekly |
| **Operations** | "Zero-touch database provisioning" | Monthly |
| **Business** | "Complete historical archive" | Quarterly |
| **Engineers** | Detailed technical docs | Per phase |

### Status Updates

```
Weekly:
├─ Team standup (15 min)
├─ Blockers discussion
└─ Code review

End of Phase:
├─ Demo to stakeholders
├─ Document lessons learned
└─ Plan next phase
```

---

## 9. Documentation Updates

### For Each Phase

```markdown
Phase X Completion:
├─ Update README.md (operational changes)
├─ Update architecture docs (design changes)
├─ Add implementation guide (how-to for new features)
├─ Add troubleshooting section (common issues)
└─ Record metrics (what improved)
```

---

## 10. Timeline & Milestones

```
Q1 2025 (Jan-Mar)
├─ Week 1-4: Phase 1 (Schema + Quality)
├─ Week 5-8: Phase 2 (Modularity)
├─ Milestone: "Silent failures prevented, new datasources simplified"

Q2 2025 (Apr-Jun)
├─ Week 9-12: Phase 3 (Orchestration)
├─ Week 13-16: Phase 4 (Monitoring)
├─ Milestone: "2-workflow pipeline, auto-alerting"

Q3-Q4 2025 (Jul-Dec)
├─ Week 17-24: Phase 5 (Neo4j Hierarchies)
├─ Milestone: "Support for hierarchical data"

2026+ (Year 2)
├─ Phase 6: Multi-building, cloud DWH
├─ Phase 7: Real-time streaming (if needed)
├─ Phase 8: ML/Predictions (if needed)
```

---

## 11. Why This Roadmap Is Right

### ✅ Respects Current Strengths
- Keeps 2-month InfluxDB window (cost-optimized)
- Keeps ephemeral databases (reproducible)
- Keeps file-first approach (portable)

### ✅ Addresses Real Pain Points
- Silent format changes → explicit validation
- Complex new datasources → templated dbt models
- Orchestration complexity → 2 workflows instead of 3
- Unknown data quality → automated anomaly detection

### ✅ Enables Future Growth
- Neo4j ready for hierarchies
- Cloud DWH integration path
- Multi-building support
- No breaking changes between phases

### ✅ Maintains Stability
- Each phase independent
- Rollback strategy for each
- Parallel run before cutover
- Old infrastructure stays as fallback

### ✅ Controls Cost
- All ephemeral (no persistent servers)
- Total cost: $0-10/month (not $600-2000)
- Cloud integrations are optional
- Start small, scale as needed

---

## 12. Conclusion

This roadmap transforms your SM2 Data Warehouse from a **robust single-building sensor platform** into an **enterprise-grade multi-model data platform**:

**Year 1 (2025)**:
- ✅ Explicit format change detection
- ✅ Simplified new datasource integration
- ✅ Automated quality monitoring
- ✅ Hierarchical data support

**Year 2 (2026)+**:
- ✅ Multi-building federation
- ✅ Cloud DWH integration
- ✅ Enterprise analytics capabilities
- ✅ Real-time features (if needed)

**Throughout**:
- ✅ Ephemeral infrastructure (cost-optimized)
- ✅ File-first persistence (reproducible)
- ✅ No breaking changes (evolutionary)
- ✅ Production-grade reliability

**Next Step**: Start Phase 1 (Week 1) with schema validation.

---

**Document Status**: Strategic Roadmap ✅  
**Review Date**: Ready for team approval  
**Next Action**: Assign Phase 1 lead engineer
