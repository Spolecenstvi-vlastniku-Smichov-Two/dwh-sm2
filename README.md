# SM2 Data Warehouse

Automated data warehouse pipeline for building sensor data collection, processing, and public dataset publication. This repository manages the complete ETL lifecycle for environmental (ventilation) and indoor climate monitoring sensors.

**Repository:** [dwh-sm2](https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2)  
**Organization:** [Společenství vlastníků Smíchov Two](https://github.com/Spolecenstvi-vlastniku-Smichov-Two)  
**License:** MIT (source code) + CC BY 4.0 (public dataset)

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Workflows](#workflows)
  - [Workflow Execution Order (Critical)](#workflow-execution-order-critical)
  - [Refresh Workflow (First)](#refresh-workflow)
  - [InfluxImportNormalize Workflow (Second)](#influximportnormalize-workflow)
  - [Publish Public Dataset Workflow (Third)](#publish-public-dataset-workflow)
- [Support Scripts](#support-scripts)
- [dbt Models](#dbt-models)
- [Data Sources & Mappings](#data-sources--mappings)
- [Storage & Cloud Integration](#storage--cloud-integration)
- [Setup & Configuration](#setup--configuration)
- [Development](#development)

---

## Architecture Overview

The system operates as a multi-stage data pipeline:

```
Raw Sensor Data (Google Drive)
    ↓
[InfluxDB 2.7] ← Annotated CSVs
    ↓
    ├─→ [Hourly Aggregation] → Normalized CSVs (Google Drive)
    ├─→ [Raw Export] → Monthly Annotated CSVs (Google Drive/Influx)
    └─→ [dbt + DuckDB]
         ↓
         [Location Mapping]
         ↓
         [Fact Tables]
         ↓
    ┌────────────────────────────────────────┐
    ├─ fact.csv (Ventilation)               │
    ├─ fact_indoor_temperature.csv          │
    ├─ fact_indoor_humidity.csv             │
    └─ Public Dataset (CSV.gz + Parquet)    │
         ↓
    [Google Drive: Public]
```

### Key Technologies

- **InfluxDB 2.7** — Time-series database for raw sensor ingestion and query
- **dbt** (data build tool) — SQL-based data transformation & testing
- **DuckDB** — Embedded analytical database for dbt transformation layer
- **Python 3.12** — ETL orchestration & data processing
- **Rclone** — Cloud storage sync (Google Drive)
- **GitHub Actions** — Workflow automation & scheduling

---

## Workflows

### Workflow Execution Order (Critical)

**⚠️ CRITICAL: Workflows must run SEQUENTIALLY in this order:**

```
┌─────────────────────────────────────────────────────────────────┐
│                 WORKFLOW EXECUTION SEQUENCE                      │
└─────────────────────────────────────────────────────────────────┘

1️⃣  Refresh Workflow
    • Reads: Latest sensor data from Google Drive
    • Does: dbt transform + fact table generation
    • Outputs: fact.csv, fact_indoor_temperature.csv, fact_indoor_humidity.csv
    • Uploads to: sm2drive:Vzduchotechnika/Model/ & sm2drive:Indoor/Model/
    ↓ MUST SUCCEED before step 2
    ⏱️ Daily: 00:00 UTC

2️⃣  InfluxImportNormalize Workflow
    • Reads: Fact tables from Google Drive (output of Refresh)
    • Does: InfluxDB import → hourly aggregation
    • Outputs: additive_YYYY-MM.hourly.csv, nonadditive_YYYY-MM.hourly.csv
    • Uploads to: sm2drive:Normalized/
    ↓ MUST SUCCEED before step 3
    ⏱️ Daily: 00:30 UTC

3️⃣  Publish Public Dataset Workflow
    • Reads: Hourly aggregated CSVs (output of InfluxImportNormalize)
    • Does: Public dataset build + schema/README generation
    • Outputs: sm2_public_dataset.csv.gz, sm2_public_dataset.parquet
    • Uploads to: sm2drive:Public/
    ✅ Final public dataset ready
    ⏱️ Weekly: Saturday 02:10 UTC
```

**Data Flow Dependency:**

```
Refresh          InfluxImportNormalize      Publish Public Dataset
──────           ──────────────────────      ──────────────────────
Fact tables  →   Hourly aggregation    →    Public CSV.gz
(CSV)            (Normalized CSVs)         (Schema + README)
                                            (CC BY 4.0)
```

Each workflow **MUST complete successfully before the next one starts**. They are interdependent:
- **Refresh** generates fact tables (fact.csv, fact_indoor_*.csv) → uploaded to Google Drive
- **InfluxImportNormalize** reads these fact tables, processes them via InfluxDB, exports hourly aggregated CSVs
- **Publish Public Dataset** reads aggregated CSVs from InfluxImportNormalize, builds final public dataset

All workflows are defined in `.github/workflows/` and can be triggered via:
- Push to `main` branch
- Scheduled cron triggers (see individual workflows)
- Manual dispatch (`workflow_dispatch`)

**⚠️ Important:** When triggering manually, always maintain the sequential order. Do NOT start InfluxImportNormalize before Refresh completes, and do NOT start Publish Public Dataset before InfluxImportNormalize completes.

### Refresh Workflow

**File:** `.github/workflows/refresh.yml`  
**Triggers:**
- Push to `main` branch
- Daily schedule: `0 0 * * *` (00:00 UTC)
- Manual: `workflow_dispatch`

**⚠️ Execution Order: FIRST (1️⃣)**

**Purpose:**
Merge latest sensor data, transform via dbt, generate fact tables, run tests, export to Google Drive.

**Why it runs first:**
- Prepares fresh fact tables (fact.csv, fact_indoor_temperature.csv, fact_indoor_humidity.csv)
- These are required inputs for the subsequent InfluxImportNormalize workflow
- Updates source data that feeds the entire pipeline

**Steps:**

1. **Setup**
   - Checkout code
   - Setup Rclone + Google Drive credentials
   - Setup Python 3.12

2. **Data Download**
   ```bash
   rclone copy sm2drive:Vzduchotechnika/Model/ ./gdrive/
   rclone copy sm2drive:Indoor/Model/ ./gdrive/
   rclone copy sm2drive:Vzduchotechnika/Latest/Upload ./latest/
   rclone copy sm2drive:Indoor/Latest/Upload ./latest/
   ```

3. **Ventilation Data Merge** (`scripts/indoor_merge_all_sensors.sh`)
   - Read Graph CSV exports (semicolon-delimited, UTF-8)
   - Auto-detect date format: MDY (`MM/DD/YYYY`) vs DMY (`DD/MM/YYYY`)
   - Heuristics:
     - Last date matches today? → That format
     - Last date in last week? → That format
     - Unique value counts (p1 vs p2 vary) → That format
     - Fallback: hint count (values > 12 in p1 → DMY)
   - Handle null tokens: empty string, `-`, `NA`, `NULL` → skip or mark
   - Output: `./gdrive/merged.csv` (Date, KOT1/Teplota venkovní (°C), ...)

4. **Indoor Data Merge** (`scripts/indoor_merge_all_sensors.sh`)
   - Process ThermoPro CSV exports
   - Same date format detection logic
   - Output: `./gdrive/all_sensors_merged.csv` (Datetime, Temperature_Celsius, Relative_Humidity(%), Location)
   - Validation: Month ≤ 12 check; fail on invalid dates

5. **Install dbt Dependencies**
   ```bash
   pip install dbt-duckdb duckdb
   dbt deps
   ```
   - Profile: `dwh_sm2` → DuckDB backend (`dwh_sm2.duckdb`)
   - Threads: 24

6. **SQL Linting**
   ```bash
   sqlfluff fix --dialect duckdb -v models/
   sqlfluff lint --dialect duckdb -v models/
   ```
   - Dialect: DuckDB
   - Auto-fix + lint report

7. **dbt Freshness Check**
   ```bash
   dbt source freshness
   ```
   - Validates CSV sources are recent

8. **dbt Seed**
   ```bash
   dbt seed
   ```
   - Loads mapping CSVs into DuckDB tables:
     - `mapping.csv` (data_key_original → location, data_key)
     - `mapping_indoor.csv` (sensor → location)
     - `mapping_sources.csv` (file_nm, source_nm, history)
     - `location_map.csv` (public location names)

9. **dbt Build (Incremental Strategy)**
   ```bash
   dbt build --select result:error+ source_status:fresher+ --defer --state docs
   ```
   - Selects only failed models + fresher sources + defer to prior state
   - If successful → done
   - If failed → run full `dbt build` (all models)
   - **Outputs: fact.csv, fact_indoor_temperature.csv, fact_indoor_humidity.csv**

10. **Generate Documentation**
    ```bash
    dbt docs generate
    ```
    - Creates `target/manifest.json`, `target/catalog.json`, `target/index.html`
    - Copy to `docs/` directory

11. **Upload Fact Tables to Google Drive** ⭐ CRITICAL OUTPUT
    ```bash
    rclone copy fact.csv sm2drive:Vzduchotechnika/Model/
    rclone copy fact_indoor_temperature.csv sm2drive:Indoor/Model/
    rclone copy fact_indoor_humidity.csv sm2drive:Indoor/Model/
    ```
    - These files are consumed by InfluxImportNormalize workflow
    - Must complete successfully before next workflow runs

12. **Archive Old Data**
    - Move `Vzduchotechnika/Latest/Upload/*` → `Vzduchotechnika/Archiv/{TIMESTAMP}/`
    - Move `Indoor/Latest/Upload/*` → `Indoor/Archiv/{TIMESTAMP}/`
    - Timestamp format: `YYYY-MM-DD_HH-MM-SS`

13. **Commit & Push**
    - Add all files: `git add --all :/`
    - Commit: `"Add docs"`
    - Push to branch: `ad-m/github-push-action`

**Output Files for Next Workflow:**
- ✅ `fact.csv` (uploaded to sm2drive:Vzduchotechnika/Model/)
- ✅ `fact_indoor_temperature.csv` (uploaded to sm2drive:Indoor/Model/)
- ✅ `fact_indoor_humidity.csv` (uploaded to sm2drive:Indoor/Model/)
- ✅ Generated dbt documentation

---

### InfluxImportNormalize Workflow

**File:** `.github/workflows/influx_import_workflow.yml`  
**Triggers:**
- Push to `main` branch
- Daily schedule: `30 0 * * *` (00:30 UTC)
- Manual: `workflow_dispatch`

**⚠️ Execution Order: SECOND (2️⃣)**

**Purpose:**
Read fact tables from Google Drive (output of Refresh workflow), import into InfluxDB, aggregate to hourly, export aggregated & raw data back to Google Drive.

**Why it runs second:**
- Depends on fact.csv, fact_indoor_temperature.csv, fact_indoor_humidity.csv from Refresh workflow
- Reads these CSV files from Google Drive
- Processes them through InfluxDB time-series system
- Creates hourly aggregated CSVs (additive=sum, nonadditive=mean)
- These aggregated CSVs are required inputs for Publish Public Dataset workflow

**Prerequisite:**
✅ Refresh workflow must complete successfully

**Steps:**

1. **Checkout & Environment Setup**
   - Clone repository
   - Setup Python 3.12 + pip

2. **InfluxDB Service**
   - Start InfluxDB 2.7 container (localhost:8086)
   - Initialize with test org/bucket/token
   - Health check enabled

3. **Rclone Configuration**
   - Setup Rclone from GitHub Secrets
   - Load Google Drive service account credentials

4. **Data Download**
   ```bash
   rclone copy sm2drive:Vzduchotechnika/Model/ ./gdrive/
   rclone copy sm2drive:Indoor/Model/ ./gdrive/
   ```

5. **Prepare Annotated CSV** (`scripts/prepare_annotated_csv.py`)
   - Read mappings from `seeds/mapping_sources.csv`
   - Load source CSVs (Atrea ventilation, ThermoPro indoor)
   - Rename columns: `time` → `_time`, `data_key` → `quantity`, `data_value` → `_value`
   - Add `_measurement: nonadditive` tag
   - Format timestamps to RFC3339: `YYYY-MM-DDTHH:MM:SSZ`
   - Output: `nonadditive_combined.annotated.csv`

6. **Floating Month Processing**
   - Read `months_to_process.json` (user-configured list)
   - Download only `additive_*` and `nonadditive_*` CSVs for those months
   - Purpose: Allows incremental re-processing of recent months

7. **Previous Exports Check** (`scripts/check_and_import_previous_exports.py`)
   - Scan `./gdrive/Influx/*.csv` for previously exported raw data
   - Re-import into InfluxDB (idempotent via `skipRowOnError`)

8. **InfluxDB Write**
   ```bash
   influx write --bucket sensor_data --format csv --file nonadditive_combined.annotated.csv
   ```

9. **Verify & Debug**
   - List buckets: `influx bucket list`
   - Query sample: `from(bucket:"sensor_data") |> range(start: -1y) |> limit(n:5)`
   - Run debug script: `scripts/debug_influx_raw.py` (validates schema)

10. **Aggregation & Export**
    - **Aggregated (hourly):** `scripts/export_aggregated_to_csv.py`
      - Flux queries: `additive` → `sum()`, `nonadditive` → `mean()` over 1h windows
      - Output: `additive_YYYY-MM.hourly.csv`, `nonadditive_YYYY-MM.hourly.csv`
      - Upload to `sm2drive:Normalized/`
    
    - **Raw (monthly):** `scripts/export_raw_by_month.py`
      - Export annotated CSVs per month per measurement
      - Output: `{additive,nonadditive}_YYYY-MM.annotated.csv`
      - Upload to `sm2drive:Influx/`

**Environment Variables (GitHub Secrets):**
- `RCLONE_CONFIG` — Full rclone config (TOML format)
- `SERVICE_ACCOUNT_FILE` — Google Cloud service account JSON
- Runtime env:
  - `INFLUX_TOKEN: ci-secret-token`
  - `INFLUX_ORG: ci-org`
  - `INFLUX_URL: http://localhost:8086`

---

### Refresh Workflow

**File:** `.github/workflows/refresh.yml`  
**Triggers:**
- Push to `main` branch
- Daily schedule: `0 0 * * *` (00:00 UTC)
- Manual: `workflow_dispatch`

**Purpose:**
End-to-end dbt refresh: download latest sensor exports, merge indoor data, transform via dbt, run tests, generate docs, export fact tables.

**Steps:**

1. **Setup**
   - Checkout code
   - Setup Rclone + Google Drive credentials
   - Setup Python 3.12

2. **Data Download**
   ```bash
   rclone copy sm2drive:Vzduchotechnika/Model/ ./gdrive/
   rclone copy sm2drive:Indoor/Model/ ./gdrive/
   rclone copy sm2drive:Vzduchotechnika/Latest/Upload ./latest/
   rclone copy sm2drive:Indoor/Latest/Upload ./latest/
   ```

3. **Ventilation Data Merge** (`scripts/indoor_merge_all_sensors.sh`)
   - Read Graph CSV exports (semicolon-delimited, UTF-8)
   - Auto-detect date format: MDY (`MM/DD/YYYY`) vs DMY (`DD/MM/YYYY`)
   - Heuristics:
     - Last date matches today? → That format
     - Last date in last week? → That format
     - Unique value counts (p1 vs p2 vary) → That format
     - Fallback: hint count (values > 12 in p1 → DMY)
   - Handle null tokens: empty string, `-`, `NA`, `NULL` → skip or mark
   - Output: `./gdrive/merged.csv` (Date, KOT1/Teplota venkovní (°C), ...)

4. **Indoor Data Merge** (`scripts/indoor_merge_all_sensors.sh`)
   - Process ThermoPro CSV exports
   - Same date format detection logic
   - Output: `./gdrive/all_sensors_merged.csv` (Datetime, Temperature_Celsius, Relative_Humidity(%), Location)
   - Validation: Month ≤ 12 check; fail on invalid dates

5. **Install dbt Dependencies**
   ```bash
   pip install dbt-duckdb duckdb
   dbt deps
   ```
   - Profile: `dwh_sm2` → DuckDB backend (`dwh_sm2.duckdb`)
   - Threads: 24

6. **SQL Linting**
   ```bash
   sqlfluff fix --dialect duckdb -v models/
   sqlfluff lint --dialect duckdb -v models/
   ```
   - Dialect: DuckDB
   - Auto-fix + lint report

7. **dbt Freshness Check**
   ```bash
   dbt source freshness
   ```
   - Validates CSV sources are recent

8. **dbt Seed**
   ```bash
   dbt seed
   ```
   - Loads mapping CSVs into DuckDB tables:
     - `mapping.csv` (data_key_original → location, data_key)
     - `mapping_indoor.csv` (sensor → location)
     - `mapping_sources.csv` (file_nm, source_nm, history)
     - `location_map.csv` (public location names)

9. **dbt Build (Incremental Strategy)**
   ```bash
   dbt build --select result:error+ source_status:fresher+ --defer --state docs
   ```
   - Selects only failed models + fresher sources + defer to prior state
   - If successful → done
   - If failed → run full `dbt build` (all models)

10. **Generate Documentation**
    ```bash
    dbt docs generate
    ```
    - Creates `target/manifest.json`, `target/catalog.json`, `target/index.html`
    - Copy to `docs/` directory

11. **Upload Fact Tables**
    ```bash
    rclone copy fact.csv sm2drive:Vzduchotechnika/Model/
    rclone copy fact_indoor_temperature.csv sm2drive:Indoor/Model/
    rclone copy fact_indoor_humidity.csv sm2drive:Indoor/Model/
    ```

12. **Archive Old Data**
    - Move `Vzduchotechnika/Latest/Upload/*` → `Vzduchotechnika/Archiv/{TIMESTAMP}/`
    - Move `Indoor/Latest/Upload/*` → `Indoor/Archiv/{TIMESTAMP}/`
    - Timestamp format: `YYYY-MM-DD_HH-MM-SS`

13. **Commit & Push**
    - Add all files: `git add --all :/`
    - Commit: `"Add docs"`
    - Push to branch: `ad-m/github-push-action`

**Output Files for Next Workflow:** ⭐ CRITICAL OUTPUT
- ✅ `additive_YYYY-MM.hourly.csv` (uploaded to sm2drive:Normalized/)
- ✅ `nonadditive_YYYY-MM.hourly.csv` (uploaded to sm2drive:Normalized/)
- ✅ `additive_YYYY-MM.annotated.csv` (raw data, uploaded to sm2drive:Influx/)
- ✅ `nonadditive_YYYY-MM.annotated.csv` (raw data, uploaded to sm2drive:Influx/)
- These hourly aggregated CSVs are consumed by Publish Public Dataset workflow

---

### Publish Public Dataset Workflow

**File:** `.github/workflows/publish_public_dataset.yml`  
**Triggers:**
- Push to `main` branch
- Weekly schedule: `10 2 * * 6` (Saturday 02:10 UTC = Sun 03:10 CET)
- Manual: `workflow_dispatch`

**⚠️ Execution Order: THIRD (3️⃣)**

**Purpose:**
Aggregate hourly sensor data into a public CC BY 4.0 dataset with schema & documentation.

**Why it runs third:**
- Depends on aggregated hourly CSVs from InfluxImportNormalize workflow
- Reads `{additive,nonadditive}_YYYY-MM.hourly.csv` from sm2drive:Normalized/
- Merges all monthly CSVs, applies location mapping
- Creates final public dataset for external consumption

**Prerequisite:**
✅ InfluxImportNormalize workflow must complete successfully

**Steps:**

1. **Setup**
   - Checkout code
   - Setup Rclone + credentials
   - Setup Python 3.12 + pip

2. **Download Aggregated Hourly CSVs**
   ```bash
   rclone copy --include "*_????-??.hourly.csv" sm2drive:Normalized ./gdrive/
   ```
   - Pattern: `{additive,nonadditive}_YYYY-MM.hourly.csv`
   - ⭐ These are outputs from InfluxImportNormalize workflow

3. **Validate Location Map Seed**
   ```bash
   test -f ./seeds/location_map.csv
   ```

4. **Build Public Dataset** (`scripts/build_public_dataset.py`)
   - Load all monthly hourly CSVs
   - Columns required: `time`, `location`, `source`, `measurement`, `data_key`, `data_value`
   - Apply location mapping: `SM2_01_L1_01` → `1NP-S1`
   - Sort by (time, location, data_key, source)
   - Output:
     - **CSV.gz:** `public/sm2_public_dataset.csv.gz`
     - **Parquet:** `public/sm2_public_dataset.parquet`
     - **README.md:** Data description, schema, counts
     - **schema.json:** Column types, primary key, metrics
     - **LICENSE:** CC BY 4.0 text
   - Upload all to `sm2drive:Public/`

**Public Dataset Schema:**
```json
{
  "columns": [
    {"name": "time", "type": "datetime", "timezone": "UTC"},
    {"name": "data_value", "type": "number"},
    {"name": "measurement", "type": "string", "enum": ["additive","nonadditive"]},
    {"name": "location", "type": "string"},
    {"name": "data_key", "type": "string"},
    {"name": "source", "type": "string"}
  ],
  "primary_key": ["time","measurement","location","data_key","source"]
}
```

---

## Support Scripts

### `scripts/prepare_annotated_csv.py`

**Purpose:** Convert raw CSVs to InfluxDB line-protocol-compatible annotated CSV.

**Logic:**
1. Read `seeds/mapping_sources.csv` (file_nm, source_nm)
2. For each source CSV:
   - Load from `./gdrive/{file_nm}`
   - Add `source` column = source_nm
   - Concat all sources
3. Rename columns to InfluxDB convention:
   - `time` → `_time`
   - `data_key` → `quantity`
   - `data_value` → `_value`
4. Convert `_time` to RFC3339 format
5. Add `_measurement: nonadditive` tag
6. Write with CSV headers (InfluxDB annotated format):
   ```csv
   #datatype,dateTime:RFC3339,string,string,string,string,double
   #group,false,true,true,true,true,false
   #default,,,,,
   _time,_measurement,location,quantity,source,_value
   ```

**Output:** `nonadditive_combined.annotated.csv`

---

### `scripts/check_and_import_previous_exports.py`

**Purpose:** Re-import previously exported monthly raw CSVs for idempotent data recovery.

**Logic:**
1. Scan `./gdrive/Influx/*.csv` recursively
2. For each CSV with size > 0:
   ```bash
   influx write --bucket sensor_data --format csv --file {csv}
   ```
3. Use `--skipRowOnError` for duplicate-safe writes

**Exit Code:** 0 (success), 1 (InfluxDB error)

---

### `scripts/debug_influx_raw.py`

**Purpose:** Validate InfluxDB data schema and inspect first 10 rows.

**Logic:**
1. Run simple Flux query: `from(bucket) |> range(-100y) |> limit(10)`
2. Strip InfluxDB header lines (#group, #datatype, #default)
3. Parse with Pandas
4. Display columns and sample data
5. Verify `_time` column existence

**Exit Code:** 0 (success), 1 (no data/error)

---

### `scripts/export_aggregated_to_csv.py`

**Purpose:** Aggregate InfluxDB sensor data hourly and export to clean CSVs per month.

**Logic:**
1. For each measurement (`additive`, `nonadditive`):
   - Find min/max `_time` in bucket
2. For each month in range:
   - Flux query with aggregation:
     - `additive` → `sum()` (hourly)
     - `nonadditive` → `mean()` (hourly)
   - Apply `aggregateWindow(every: 1h, fn: {fn}, createEmpty: false)`
   - Select columns: `_time`, `_value`, `_measurement`, `location`, `quantity`, `source`
3. Parse InfluxDB annotated CSV output
4. Rename columns: `_time` → `time`, `_value` → `data_value`, `quantity` → `data_key`
5. Split by month: `{measurement}_YYYY-MM.hourly.csv`
6. Upload to `sm2drive:Normalized/{filename}`

**Files Produced:**
- `additive_2024-12.hourly.csv` (ventilation sums)
- `nonadditive_2024-12.hourly.csv` (indoor means)

---

### `scripts/export_raw_by_month.py`

**Purpose:** Export raw InfluxDB data as annotated CSVs per month (for data backup & re-import).

**Logic:**
1. For each measurement (`additive`, `nonadditive`):
   - Find min/max time
2. For each month in range:
   - Raw Flux query (no aggregation): `range(start, stop) |> filter(_measurement == ...)`
3. Export with InfluxDB line-protocol annotation headers
4. Output: `{measurement}_YYYY-MM.annotated.csv`
5. Upload to `sm2drive:Influx/{filename}`

---

### `scripts/indoor_merge_all_sensors.sh` (v2.2)

**Purpose:** Robust merging of ThermoPro sensor exports with automatic date format detection.

**Language:** Bash/AWK (36 KB)

**Features:**

- **Date Format Auto-Detection (DMY vs MDY):**
  - Heuristics:
    1. Last date = today? → That format
    2. Last date in last 7 days? → That format
    3. Unique value count > 12 in position → That format (e.g., many months in p1 → DMY)
    4. Chronological breaks (backwards time)? → That format (fewest breaks)
    5. Fallback: hint count (values > 12 → DMY)
    6. Ultimate fallback: `FORCE_FMT` env or fail with `STRICT=1`

- **Null Token Handling:**
  - Empty string, `-`, `NA`, `N/A`, `NULL` → treated as null
  - Two nulls (temp + RH both null) → skip row (sensor not operating)
  - One null → keep with empty field
  - Debug sampling: first 5 (or `SAMPLE_N`) nulls logged

- **Validation:**
  - Non-numeric temp/RH → exit 6
  - Month > 12 in output → exit 4 (format detection failure)
  - Multiple files → merge with concatenation

**Environment Variables:**
```bash
INPUT_GLOB="./latest/ThermoProSensor_export_*.csv"
OUTPUT="./gdrive/all_sensors_merged.csv"
SAMPLE_N=5                      # null token samples to show
TZ="Europe/Prague"              # timezone for today detection
TODAY="$(date +%Y-%m-%d)"
STRICT=1                        # fail on ambiguous format
FMT_DEFAULT="DMY"               # fallback if STRICT=0
NULL_TOKEN_SAMPLE_N=25          # max nulls to log
NULL_TOKEN_DUMP=0               # log all nulls if =1
FORCE_FMT=""                    # override format (DMY or MDY)
```

**Output Schema:**
```csv
Datetime,Temperature_Celsius,Relative_Humidity(%),Location
2024-12-21 14:30:00,22.5,45.2,S1
```

---

### `scripts/build_public_dataset.py`

**Purpose:** Create public-ready dataset with schema & documentation.

**Logic:**
1. Find all `*_????-??.hourly.csv` in `./gdrive/`
2. Load & validate columns: `time`, `location`, `source`, `measurement`, `data_key`, `data_value`
3. Load `seeds/location_map.csv` (from → to mapping)
4. Apply location mapping
5. Concatenate, sort by (time, location, data_key, source)
6. Output formats:
   - **CSV.gz:** Compressed CSV
   - **Parquet:** Columnar format (optional)
   - **schema.json:** Column definitions, primary key, row counts
   - **README.md:** Description, schema, statistics
   - **LICENSE:** CC BY 4.0 text
7. Upload all to `sm2drive:Public/`

**Generated README includes:**
- Created timestamp (UTC)
- Row count & time range
- Measurement types & data_key distribution
- Attribution & citation instructions
- License text link

---

## dbt Models

**Backend:** DuckDB (embedded)  
**Configuration:** `dbt_project.yml` + `profiles.yml`  
**Model Paths:** `models/ventilation/`, `models/indoor/`

### Directory Structure

```
models/
├─ ventilation/
│  ├─ fact.sql              # Main ventilation fact table
│  ├─ schema.yml            # Tests & descriptions
│  └─ sources.yml           # Source definitions
├─ indoor/
│  ├─ fact_indoor_temperature.sql
│  ├─ fact_indoor_humidity.sql
│  ├─ schema.yml
│  └─ sources.yml
seeds/
├─ mapping.csv              # data_key_original → (location, data_key)
├─ mapping_indoor.csv       # sensor → location
├─ mapping_sources.csv      # file_nm, source_nm, history
└─ location_map.csv         # internal → public location names
```

### Model: `ventilation/fact.sql`

**Purpose:** Transform ventilation sensor data with location & metric mapping.

**Logic:**

1. **source CTE:**
   - Read from `source('csv_google', 'merged')` (merged.csv from Atrea)
   - Cast all columns to VARCHAR
   - Purpose: handle dynamic/unknown column schema

2. **unpivoted CTE:**
   - Unpivot on all columns except `date`
   - Output: (data_key_original, data_value)
   - Purpose: convert wide format to long (tidy data)

3. **mapped CTE:**
   - INNER JOIN with `ref('mapping')` (seed)
   - Map: `data_key_original` → (location, data_key)
   - Filter: `date IS NOT NULL`

4. **params CTE:**
   - Calculate `start_ts = date_trunc('month', now()) - (history - 1) month`
   - From `ref('mapping_sources')` where `file_nm = 'fact.csv'`
   - Purpose: retain only recent months (history=2 → last 2 months)

5. **final CTE:**
   - UNION DISTINCT with `source('csv_google', 'fact_original')` (previous exports)
   - Ensures incremental updates don't duplicate

6. **SELECT:**
   - Filter: `time >= start_ts`
   - Output: (time, location, data_key, data_value)

**Materialization:** `external` (CSV file at `./fact.csv`)

---

### Model: `indoor/fact_indoor_temperature.sql`

**Purpose:** Transform indoor temperature sensor data.

**Sources:**
- `source('csv_google_indoor', 'merged_indoor')` (all_sensors_merged.csv from ThermoPro)
- `source('csv_google_indoor', 'fact_indoor_temperature_original')`

**Logic:**
1. Select from merged_indoor
2. Map sensor name → location via `ref('mapping_indoor')`
3. Hardcode `data_key = 'temp_indoor'`
4. Use column `temperature_celsius` as `data_value`
5. UNION DISTINCT with original exports
6. Apply history filter (2 months)

**Materialization:** `external` (CSV at `./fact_indoor_temperature.csv`)

---

### Model: `indoor/fact_indoor_humidity.sql`

**Purpose:** Transform indoor humidity sensor data.

**Similar to temperature:**
- Hardcode `data_key = 'humidity_indoor'`
- Use column `"Relative_Humidity(%)"` as `data_value`
- Materialization: `external` (CSV at `./fact_indoor_humidity.csv`)

---

## Data Sources & Mappings

### Seeds

#### `mapping.csv`
**Purpose:** Ventilation sensor → (location, metric key)

Example:
```csv
data_key_original,location,data_key
KOT1/Teplota venkovní (°C),1NP-S1,temp_outdoor
KOT1/Vlhkost venkovní (%),1NP-S1,humidity_outdoor
...
```

#### `mapping_indoor.csv`
**Purpose:** ThermoPro sensor ID → location

Example:
```csv
sensor,location
SM2_01_L1_01,1NP-S1
SM2_02_L1_01,1NP-S2
...
```

#### `mapping_sources.csv`
**Purpose:** Source file → source name & history window

```csv
file_nm,source_nm,history
fact.csv,Atrea,2
fact_indoor_humidity.csv,ThermoPro,2
fact_indoor_temperature.csv,ThermoPro,2
```

- `file_nm` — Name of exported fact table
- `source_nm` — Display name (used in InfluxDB source tag)
- `history` — Number of months to retain (rolling window)

#### `location_map.csv`
**Purpose:** Internal sensor location ID → public-friendly display name

```csv
from,to
SM2_01_L1_01,1NP-S1
SM2_01_L5/L6_01,5NP-S1
...
```

- Used by `build_public_dataset.py` to normalize location names in public dataset

### Sources (YAML)

#### `ventilation/sources.yml`

```yaml
sources:
  - name: csv_google
    database: csv_google
    tables:
      - name: merged              # ./gdrive/merged.csv
      - name: fact_original       # Previous ./fact.csv export
```

#### `indoor/sources.yml`

```yaml
sources:
  - name: csv_google_indoor
    database: csv_google_indoor
    tables:
      - name: merged_indoor                      # ./gdrive/all_sensors_merged.csv
      - name: fact_indoor_temperature_original   # Previous export
      - name: fact_indoor_humidity_original      # Previous export
```

---

## Storage & Cloud Integration

### Google Drive Structure

```
sm2drive:/
├─ Vzduchotechnika/
│  ├─ Model/
│  │  └─ fact.csv (latest full export)
│  ├─ Latest/Upload/          (incoming sensor files from ThermoProSensor_export_*.csv)
│  ├─ Archiv/
│  │  └─ {TIMESTAMP}/         (archived monthly)
│  └─ Normalized/             (aggregated hourly CSVs)
├─ Indoor/
│  ├─ Model/
│  │  ├─ fact_indoor_temperature.csv
│  │  └─ fact_indoor_humidity.csv
│  ├─ Latest/Upload/          (incoming Graph*.csv)
│  ├─ Archiv/
│  │  └─ {TIMESTAMP}/
│  └─ Normalized/
├─ Influx/
│  ├─ additive_2024-12.annotated.csv       (raw monthly exports)
│  ├─ nonadditive_2024-12.annotated.csv
│  └─ ...
└─ Public/
   ├─ sm2_public_dataset.csv.gz
   ├─ sm2_public_dataset.parquet
   ├─ README.md
   ├─ schema.json
   └─ LICENSE
```

### Rclone Configuration

**Required:** GitHub Secret `RCLONE_CONFIG` (full TOML configuration)

```toml
[sm2drive]
type = drive
client_id = {GCP_CLIENT_ID}
client_secret = {GCP_CLIENT_SECRET}
token = {OAUTH_TOKEN_JSON}
...
```

**Required:** GitHub Secret `SERVICE_ACCOUNT_FILE` (JSON service account key)

### Local Directories (Gitignored)

- `./gdrive/` — Downloaded CSVs & aggregated hourly
- `./latest/` — Latest sensor uploads
- `./target/` — dbt build artifacts
- `./public/` — Public dataset output

---

## Setup & Configuration

### Prerequisites

- Python 3.12+
- dbt-duckdb
- InfluxDB 2.7 (for local development, or use GitHub Actions)
- Rclone (with Google Drive credentials)
- Bash/AWK (for sensor merge)

### Local Development

1. **Clone Repository**
   ```bash
   git clone https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2
   cd dwh-sm2
   ```

2. **Create Virtual Environment**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   ```

3. **Install Dependencies**
   ```bash
   pip install dbt-duckdb sqlfluff pandas pyarrow
   dbt deps
   ```

4. **Configure Rclone** (for Google Drive access)
   ```bash
   rclone config
   # Add remote: sm2drive (type: drive)
   ```

5. **Set dbt Profile**
   - Edit `profiles.yml`:
     ```yaml
     dwh_sm2:
       target: dev
       outputs:
         dev:
           type: duckdb
           path: 'dwh_sm2.duckdb'
           threads: 24
     ```
   - Set env: `export DBT_PROFILES_DIR=./`

6. **Download Source Data** (manual)
   ```bash
   rclone copy sm2drive:Vzduchotechnika/Model/ ./gdrive/
   rclone copy sm2drive:Indoor/Model/ ./gdrive/
   ```

7. **Run dbt**
   ```bash
   dbt seed                    # Load mapping CSVs
   dbt run                     # Generate fact tables
   dbt test                    # Run tests from schema.yml
   dbt docs generate           # Build documentation
   dbt docs serve              # Local server at localhost:8000
   ```

### GitHub Actions Secrets

- `RCLONE_CONFIG` — Full rclone configuration (TOML)
- `SERVICE_ACCOUNT_FILE` — Google Cloud service account JSON key

---

## Development

### Testing

**dbt Tests:**
```bash
dbt test
```

Defined in `models/ventilation/schema.yml` and `models/indoor/schema.yml`.

**SQL Linting:**
```bash
sqlfluff lint --dialect duckdb models/
sqlfluff fix --dialect duckdb models/
```

### Adding New Sensors

1. **Map New Sensor:**
   - Add row to `seeds/mapping.csv` (ventilation) or `seeds/mapping_indoor.csv` (indoor)
   - Columns: source_name → (location, metric_key)

2. **Update Source Config:**
   - Edit `models/ventilation/sources.yml` or `models/indoor/sources.yml`
   - Add data freshness tests if applicable

3. **Adjust Models:**
   - Modify `fact.sql` unpivot logic if schema changes
   - Update tests in schema.yml

4. **Commit & Push:**
   - Workflows auto-trigger on push to main
   - Validate via GitHub Actions logs

### Metrics & Monitoring

**Check Workflow Runs:**
```
https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2/actions
```

**View Generated Docs:**
- Automatically uploaded to `sm2drive:Public/`
- Can serve locally: `dbt docs serve`

**Monitor Data Freshness:**
```bash
dbt source freshness
```

### Troubleshooting

**InfluxDB Import Fails:**
- Check `debug_influx_raw.py` output for schema validation
- Verify CSV headers match InfluxDB annotated format
- Use `--skipRowOnError` in workflows for robustness

**Date Format Detection Fails:**
- Set `FORCE_FMT=DMY` or `FORCE_FMT=MDY` in `indoor_merge_all_sensors.sh`
- Check `STRICT=1` (default) vs `STRICT=0` for fallback behavior

**dbt Build Fails:**
- Run `dbt debug` to verify profile
- Check DuckDB file permissions: `ls -la dwh_sm2.duckdb*`
- Validate sources exist: `dbt source freshness`

**Rclone Authentication:**
- Regenerate `rclone config` locally: `rclone config`
- Update GitHub Secrets: `RCLONE_CONFIG` + `SERVICE_ACCOUNT_FILE`

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes (update models, add scripts, etc.)
4. Test locally: `dbt test && sqlfluff lint`
5. Commit with clear messages
6. Push & create Pull Request

---

## License

**Source Code:** MIT License (see LICENSE file)

**Public Dataset:** CC BY 4.0 (see `public/LICENSE`)

Attribution: Společenství vlastníků Smíchov Two, [horkovsm2.blogspot.com](https://horkovsm2.blogspot.com/), [GitHub](https://github.com/Spolecenstvi-vlastniku-Smichov-Two)

---

## Support

For issues, questions, or feature requests, open an issue on GitHub:  
[Issues](https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2/issues)

Website: [horkovsm2.blogspot.com](https://horkovsm2.blogspot.com/)
