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

Each workflow **MUST complete successfully before the next one starts**. They are interdependent.

---

### Refresh Workflow

**File:** `.github/workflows/refresh.yml`  
**Triggers:** Daily `00:00 UTC`, Push to `main`, Manual.

**Purpose:**
Merge latest sensor data, transform via dbt, generate fact tables, run tests, export to Google Drive.

**Steps:**
1. **Data Download**: Syncs `Model` and `Latest/Upload` folders from GDrive.
2. **Ventilation Data Merge**: Uses `csvcut` and `csvjoin` (csvkit) directly in the workflow to merge `Graph*` files into `merged.csv`.
3. **Indoor Data Merge**: Uses `scripts/indoor_merge_all_sensors.sh` to merge `ThermoProSensor_export_*` files into `all_sensors_merged.csv`.
4. **dbt Build**: Runs `dbt seed` and `dbt build` (incremental strategy using `--defer --state docs`).
5. **Outputs**: Generates `fact.csv`, `fact_indoor_temperature.csv`, and `fact_indoor_humidity.csv`.
6. **Archive**: Moves processed files from `Latest/Upload` to `Archiv/{TIMESTAMP}`.

---

### InfluxImportNormalize Workflow

**File:** `.github/workflows/influx_import_workflow.yml`  
**Triggers:** Daily `00:30 UTC`, Push to `main`, Manual.

**Purpose:**
Import fact tables into InfluxDB, perform hourly aggregation, and export results.

**Steps:**
1. **InfluxDB Service**: Starts an ephemeral InfluxDB 2.7 Docker container.
2. **Prepare Data**: `scripts/prepare_annotated_csv.py` creates annotated CSVs for InfluxDB.
3. **Import**: Writes data to InfluxDB, including previous monthly exports for recovery via `scripts/check_and_import_previous_exports.py`.
4. **Aggregation**: `scripts/export_aggregated_to_csv.py` runs Flux queries to create hourly CSVs.
5. **Raw Export**: `scripts/export_raw_by_month.py` saves raw data as annotated CSVs for backup.

---

### Publish Public Dataset Workflow

**File:** `.github/workflows/publish_public_dataset.yml`  
**Triggers:** Weekly `Saturday 02:10 UTC`, Push to `main`, Manual.

**Purpose:**
Create the final public dataset with metadata and license.

**Steps:**
1. **Download**: Fetches all `*_YYYY-MM.hourly.csv` files from `sm2drive:Normalized`.
2. **Build**: `scripts/build_public_dataset.py` merges data, applies `location_map.csv`, and generates:
   - `sm2_public_dataset.csv.gz` & `.parquet`
   - `README.md`, `schema.json`, `LICENSE` (CC BY 4.0)
3. **Upload**: Publishes all artifacts to `sm2drive:Public/`.

---

## Support Scripts

- `scripts/indoor_merge_all_sensors.sh`: Robust merging of ThermoPro exports with date format detection.
- `scripts/prepare_annotated_csv.py`: Prepares data for InfluxDB ingestion.
- `scripts/export_aggregated_to_csv.py`: Performs hourly aggregation via Flux.
- `scripts/export_raw_by_month.py`: Monthly raw data backup.
- `scripts/build_public_dataset.py`: Final dataset assembly and metadata generation.
- `scripts/check_and_import_previous_exports.py`: Idempotent re-import of historical raw data.
- `scripts/debug_influx_raw.py`: Schema validation for InfluxDB data.

---

## dbt Models

- `models/ventilation/fact.sql`: Unpivots ventilation data and joins with history.
- `models/indoor/fact_indoor_temperature.sql`: Processes indoor temperature readings.
- `models/indoor/fact_indoor_humidity.sql`: Processes indoor humidity readings.

---

## Setup & Configuration

### Prerequisites
- Python 3.12+, dbt-duckdb, InfluxDB 2.7 (Docker), Rclone, csvkit.

### Local Development
1. Clone the repository.
2. Run `bash setup_dev.sh` to initialize the environment.
3. Configure `profiles.yml` (DuckDB path: `dwh_sm2.duckdb`).
4. Use `rclone` to sync source data to `./gdrive/`.
5. Run `dbt build`.

---

## License
**Source Code:** MIT  
**Public Dataset:** CC BY 4.0
