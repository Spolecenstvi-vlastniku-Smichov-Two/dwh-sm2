# SM2 Hybrid Data Platform Architecture

**Design Philosophy**: Ephemeral, Cost-Optimized, Multi-Model Data Processing

**Status**: Architecture Definition Document  
**Date**: 2025-12-23  
**Author**: Team SM2

---

## Executive Summary

The SM2 data platform is a **hybrid, ephemeral data processing architecture** designed to:

1. **Transform "wide" data** (many columns, relational) → **"narrow" data** (few columns, time-series)
2. **Use specialized databases** for their intended purposes (not one-size-fits-all)
3. **Run platforms on-demand** during pipeline execution (no persistent DB servers)
4. **Persist data as files** (CSV/Parquet) for cost efficiency and portability

This is a **serverless data architecture** - you only pay for computation, not persistent storage of databases.

---

## 1. Core Architecture

### 1.1 Data Transformation Stages

```
Stage 1: RAW SENSOR DATA (Files)
┌─────────────────────────────────────────────────────────────┐
│ CSV files from sensors (Google Drive)                       │
│ ├─ Ventilation: Graph*.csv (Wide)                          │
│ └─ Indoor: ThermoProSensor_export_*.csv (Wide)             │
└─────────────────────────────────────────────────────────────┘
              ↓
Stage 2: RELATIONAL PROCESSING (DuckDB - Ephemeral)
┌─────────────────────────────────────────────────────────────┐
│ DuckDB (spawned only during pipeline run)                   │
│ ├─ Merge Atrea: csvcut / csvjoin (Workflow)                │
│ ├─ Merge Indoor: scripts/indoor_merge_all_sensors.sh       │
│ ├─ Unpivot: Wide → Narrow transformation (dbt)             │
│ ├─ Apply dbt transformations                               │
│ └─ Output: Narrow, normalized CSV (fact.csv)               │
└─────────────────────────────────────────────────────────────┘
              ↓
Stage 3: TIME-SERIES PROCESSING (InfluxDB - Ephemeral)
┌─────────────────────────────────────────────────────────────┐
│ InfluxDB (spawned in GitHub Actions, 2-month retention)     │
│ ├─ Ingestion: scripts/prepare_annotated_csv.py             │
│ ├─ Retention policy: 2 months (floating window)            │
│ ├─ Aggregation: scripts/export_aggregated_to_csv.py        │
│ └─ Output: Aggregated CSV files                            │
└─────────────────────────────────────────────────────────────┘
              ↓
Stage 4: PUBLIC DATASETS (Parquet Files)
┌─────────────────────────────────────────────────────────────┐
│ Script: scripts/build_public_dataset.py                    │
│ ├─ Merge monthly hourly CSVs                               │
│ ├─ Apply location mapping (seeds/location_map.csv)         │
│ └─ Output: Parquet + CSV.gz + Metadata                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Current Implementation Details

### 2.1 Relational Layer (DuckDB + dbt)
Využívá DuckDB jako efemérní analytický engine. 
- **Atrea**: Slučování probíhá pomocí `csvkit` přímo v GitHub Actions workflow `refresh.yml`.
- **ThermoPro**: Slučování probíhá pomocí robustního bash/awk skriptu `indoor_merge_all_sensors.sh`.
- **dbt**: Provádí unpivot širokých tabulek na dlouhý formát a zajišťuje `union distinct` s historickými daty (`fact_original`).

### 2.2 Time-Series Layer (InfluxDB)
InfluxDB běží jako Docker service v CI/CD.
- **Plovoucí okno**: Udržuje pouze posledních 60 dní dat pro maximální výkon agregací.
- **Agregace**: Flux dotazy počítají hodinové průměry (non-additive) a sumy (additive).

### 2.3 Persistence Layer (Google Drive)
Google Drive slouží jako "Cold Storage" pro:
- Raw data (Archiv)
- Mezivýsledky (Fact tables)
- Agregované měsíční soubory (Normalized)
- Veřejné datasety (Public)

---

## 3. Why This Design Is Optimal
- **Cost Efficiency**: $0 za běžící servery.
- **Operational Simplicity**: Žádná správa DB (backupy, upgrady).
- **Reproducibility**: Celý dataset lze přegenerovat ze zdrojových souborů.

---

**Document Status**: Architecture Definition ✅  
**Review Date**: 2025-12-23
