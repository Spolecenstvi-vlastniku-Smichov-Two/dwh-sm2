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
5. **Enable future multi-model analysis** with graph databases (Neo4j)

This is a **serverless data architecture** - you only pay for computation, not persistent storage of databases.

---

## 1. Core Architecture

### 1.1 Data Transformation Stages

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE                            │
└─────────────────────────────────────────────────────────────┘

Stage 1: RAW SENSOR DATA (Files)
┌─────────────────────────────────────────────────────────────┐
│ CSV files from sensors (Google Drive)                       │
│ ├─ Ventilation: Multiple columns per location              │
│ │  └─ [date, KOT1/Teplota, KOT1/Vlhkost, KOT2/..., ...]   │
│ ├─ Indoor: Multiple columns per sensor                     │
│ │  └─ [Datetime, Location, Temp, Humidity, Pressure, ...] │
│ └─ Format: Wide (many columns)                             │
└─────────────────────────────────────────────────────────────┘
              ↓
         (On-demand)
              ↓
Stage 2: RELATIONAL PROCESSING (DuckDB - Ephemeral)
┌─────────────────────────────────────────────────────────────┐
│ DuckDB (spawned only during pipeline run)                   │
│ ├─ Load CSV files                                           │
│ ├─ Unpivot: Wide → Narrow transformation                   │
│ │  └─ [date, KOT1/Teplota, KOT1/Vlhkost] → [time, metric] │
│ ├─ Apply dbt transformations                               │
│ ├─ Join with mapping tables (seeds)                        │
│ └─ Output: Narrow, normalized CSV/Parquet                  │
│                                                              │
│ Why DuckDB:                                                │
│  • OLAP optimized (analytical queries)                     │
│  • Ephemeral (no persistent server needed)                │
│  • Parquet-native (direct output)                         │
│  • Localhost-only (no network overhead)                   │
└─────────────────────────────────────────────────────────────┘
              ↓
         (On-demand)
              ↓
Stage 3: TIME-SERIES PROCESSING (InfluxDB - Ephemeral)
┌─────────────────────────────────────────────────────────────┐
│ InfluxDB (spawned in GitHub Actions, 2-month retention)     │
│ ├─ Narrow data format: [time, location, measurement, value]│
│ ├─ Append-only ingestion (immutable log)                    │
│ ├─ Retention policy: 2 months (floating window)            │
│ ├─ Aggregation (Flux queries)                              │
│ │  └─ hourly, daily, weekly, monthly summaries             │
│ └─ Output: Aggregated Parquet files                        │
│                                                              │
│ Why InfluxDB:                                              │
│  • Time-series optimized (designed for sensors)            │
│  • Fast aggregation (Flux language)                        │
│  • Built-in retention policies                            │
│  • Docker container (ephemeral)                           │
│  • 2-month window = constant performance                  │
└─────────────────────────────────────────────────────────────┘
              ↓
         (On-demand, future)
              ↓
Stage 4: HIERARCHY PROCESSING (Neo4j - Ephemeral, Future)
┌─────────────────────────────────────────────────────────────┐
│ Neo4j (spawned for hierarchy/relationship analysis)         │
│ ├─ Graph model: Building → Floors → Zones → Sensors       │
│ ├─ Relationships: Parent-child, dependencies               │
│ ├─ Queries: "All sensors in Zone 3", "Temperature path"   │
│ └─ Output: Hierarchical relationships as Parquet          │
│                                                              │
│ Why Neo4j (future):                                        │
│  • Graph optimized (relationships as first-class)         │
│  • Natural for building hierarchies                       │
│  • Cypher language (intuitive for hierarchies)            │
│  • Docker container (ephemeral)                          │
│  • Enables spatial + temporal analysis                    │
└─────────────────────────────────────────────────────────────┘
              ↓
         (Automatic)
              ↓
Stage 5: PUBLIC DATASETS (Parquet Files)
┌─────────────────────────────────────────────────────────────┐
│ Multiple Parquet exports for different audiences:           │
│ ├─ public_dataset_raw.parquet                              │
│ │  └─ Detailed sensor readings (time-series)              │
│ ├─ public_dataset_hourly.parquet                           │
│ │  └─ Aggregated hourly (reduced size, faster queries)    │
│ ├─ public_dataset_hierarchy.parquet (future)               │
│ │  └─ Sensor relationships + hierarchy info               │
│ └─ Metadata: schema.json, lineage.json, README.md         │
│                                                              │
│ Format: Apache Parquet                                     │
│  • Columnar (fast queries on subset of columns)           │
│  • Compressed (10x smaller than CSV)                      │
│  • Language-agnostic (Python, R, Go, Julia, ...)         │
│  • Distributed-ready (Pandas, DuckDB, Spark, ...)        │
└─────────────────────────────────────────────────────────────┘
              ↓
         (Distribution)
              ↓
Stage 6: DATA CONSUMERS
┌─────────────────────────────────────────────────────────────┐
│ Different distribution methods per audience:                │
│                                                              │
│ Data Scientists (Research)                                 │
│ ├─ Parquet files via Google Drive                          │
│ ├─ Load with Pandas, Polars, or DuckDB                    │
│ └─ Goal: Exploratory analysis, ML model training          │
│                                                              │
│ Business Users (Dashboards)                               │
│ ├─ Parquet files via BI Tool (Tableau, PowerBI)          │
│ ├─ Pre-aggregated (hourly) for performance                │
│ └─ Goal: Monitoring, alerting, KPI tracking              │
│                                                              │
│ Integrations (APIs)                                        │
│ ├─ Parquet → BigQuery (GCP)                               │
│ ├─ Parquet → S3 (AWS)                                     │
│ ├─ Parquet → Snowflake (cloud DWH)                        │
│ └─ Goal: Enterprise data lake                             │
│                                                              │
│ Web/Mobile Apps                                            │
│ ├─ Parquet → REST API (aggregated subset)                │
│ ├─ Or: Parquet → SQLite (on-device analytics)            │
│ └─ Goal: Real-time user experience                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Key Design Principles

#### Principle 1: "Wide → Narrow" Transformation
```
Wide Data (Relational):
┌──────────┬──────────────┬──────────────┬──────────────┐
│ Date     │ KOT1/Teplota │ KOT1/Vlhkost │ KOT2/Teplota │ ...
├──────────┼──────────────┼──────────────┼──────────────┤
│ 2025-01-01 │ 20.5       │ 45.2         │ 21.3         │
│ 2025-01-02 │ 20.8       │ 44.9         │ 21.1         │
└──────────────────────────────────────────────────────┘
  ↓ UNPIVOT (DuckDB)
Narrow Data (Time-Series):
┌──────────────┬──────────┬───────────┬──────────┐
│ Timestamp    │ Location │ Metric    │ Value    │
├──────────────┼──────────┼───────────┼──────────┤
│ 2025-01-01   │ KOT1     │ Temperature│ 20.5    │
│ 2025-01-01   │ KOT1     │ Humidity   │ 45.2    │
│ 2025-01-01   │ KOT2     │ Temperature│ 21.3    │
│ 2025-01-02   │ KOT1     │ Temperature│ 20.8    │
└──────────────────────────────────────────────────┘
```

**Why this transformation**:
- Wide data = relational (one row per time period, many columns)
- Narrow data = time-series (many rows, few columns)
- DuckDB excels at unpivot/transpose operations
- InfluxDB requires narrow format (time-series native)

#### Principle 2: Ephemeral Databases (Containers)
```
Traditional approach (Persistent):
  Production DuckDB Server ← Always running, costs $$$
  Production InfluxDB Server ← Always running, costs $$$
  Production Neo4j Server ← Always running, costs $$$
  Problem: 23 hours/day unused, 1 hour/day processing

SM2 approach (Ephemeral):
  GitHub Actions starts → Spawn DuckDB (seconds) → Process → Shutdown
  GitHub Actions starts → Spawn InfluxDB (seconds) → Process → Shutdown
  GitHub Actions starts → Spawn Neo4j (seconds, future) → Process → Shutdown
  Benefit: Pay only for what you use (1 hour/day = 4% cost)
```

**Docker Containers on Ephemeral Infrastructure**:
```yaml
services:
  influxdb:
    image: influxdb:2.7
    # Run only during this workflow, then destroy
    # Data persists as files, not in running server
```

#### Principle 3: Files as Single Source of Truth
```
Persistent:  ← CSV/Parquet files (git-tracked or archived)
             ↓ (only when pipeline runs)
Ephemeral:   ← DuckDB (in-memory + temp disk)
             ← InfluxDB (2-month window)
             ← Neo4j (relationship processing, future)
             ↓ (output)
Persistent:  ← Parquet files (Google Drive, S3, BigQuery, ...)
```

**Benefits**:
- Single source of truth is immutable (files)
- Databases are side effects (processing artifacts)
- Can replay entire pipeline from files (reproducible)
- No vendor lock-in (files are portable)
- Cost: 0 for storage (CSV/Parquet in cold storage)

#### Principle 4: Multi-Model for Different Data Shapes
```
Data Shape          │ Optimized DB  │ Use Case
────────────────────────────────────────────────────────
Wide (relational)   │ DuckDB (OLAP) │ Transform, join, pivot
Narrow (time-series)│ InfluxDB      │ Aggregate, window functions
Hierarchical (tree) │ Neo4j (graph) │ Relationships, paths, hierarchies
```

**Why not one database for everything**:
- DuckDB for time-series = slow (not optimized)
- InfluxDB for hierarchies = awkward (no relationship support)
- Neo4j for OLAP joins = slow (not optimized)

Each database does one thing well. Orchestration (dbt + Python scripts) ties them together.

---

## 2. Current Implementation (Stages 1-3)

### 2.1 Stage 1: Raw Sensor Data

**Format**: CSV files on Google Drive

```
Ventilation (Atrea):
  sm2drive:Vzduchotechnika/Model/fact.csv
  ├─ Columns: date, KOT1/Teplota, KOT1/Vlhkost, KOT2/Teplota, ...
  ├─ Format: Wide (150+ columns)
  └─ Source: Atrea system (building ventilation)

Indoor (ThermoPro):
  sm2drive:Indoor/Model/fact_indoor_temperature.csv
  sm2drive:Indoor/Model/fact_indoor_humidity.csv
  ├─ Columns: Datetime, Location, Sensor1_Temp, Sensor2_Temp, ...
  ├─ Format: Wide
  └─ Source: ThermoPro sensors (room-level monitoring)
```

### 2.2 Stage 2: DuckDB Transformation

**Process** (happens once per day during Refresh workflow):

```sql
-- models/0_landing/landing_ventilation_raw.sql
SELECT * FROM read_csv('sm2drive:Vzduchotechnika/Model/fact.csv')

-- models/1_staging/stg_ventilation.sql (Unpivot)
UNPIVOT (
    SELECT * FROM landing_ventilation_raw
)
ON COLUMNS (* EXCLUDE (date))
INTO
    NAME data_key_original
    VALUE data_value

-- models/2_marts/fct_sensor_readings.sql (Normalize + Join)
SELECT
    CAST(date AS TIMESTAMP) AS timestamp,
    mapping.location,
    mapping.data_key,
    CAST(data_value AS FLOAT) AS value
FROM unpivoted
INNER JOIN mapping ON unpivoted.data_key_original = mapping.data_key_original
WHERE date >= CURRENT_DATE - INTERVAL 2 MONTHS
```

**Output**: Narrow, normalized CSV
```
timestamp,location,data_key,value
2025-01-01T00:00:00Z,KOT1,temperature,20.5
2025-01-01T00:00:00Z,KOT1,humidity,45.2
2025-01-01T00:00:00Z,KOT2,temperature,21.3
```

### 2.3 Stage 3: InfluxDB Aggregation

**Process** (happens once per day during InfluxImportNormalize workflow):

```yaml
services:
  influxdb:
    image: influxdb:2.7
    # Spawned in GitHub Actions
    # Runs for ~15 minutes
    # Auto-destroys when workflow ends
```

**Steps**:
1. Load narrow CSV into InfluxDB bucket
2. Run Flux queries for hourly/daily/weekly aggregation
3. Export aggregated data to Parquet

```flux
from(bucket:"sensor_data")
  |> range(start: -2d)  # Only last 2 days (floating window)
  |> filter(fn: (r) => r._measurement == "temperature")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> yield(name: "hourly_avg")
```

**Output**: Pre-aggregated Parquet (optimized for analytics)
```
timestamp,location,measurement,value_mean,value_std,count
2025-01-01T00:00:00Z,KOT1,temperature,20.5,0.2,6
2025-01-01T01:00:00Z,KOT1,temperature,20.6,0.3,6
```

---

## 3. Future Implementation (Stage 4: Neo4j Hierarchies)

### 3.1 Problem: Current System Lacks Hierarchies

**Current limitation**:
- Sensor readings are isolated: (location, measurement, value)
- No relationship information: "Which zones share a wall?"
- No parent-child hierarchy: "Building → Floor → Zone → Room → Sensor"
- Difficult to query: "All sensors in Zone 3" requires manual joins

### 3.2 Solution: Neo4j for Graph Analysis

**When to add Neo4j**:
- When you need to ask questions about relationships
- When you need to model hierarchies
- When you need path analysis or spatial queries

**Example use cases**:
```
Query 1: "Show me all sensors and their parent building"
  MATCH (building:Building)-[:CONTAINS]->(floor:Floor)-[:CONTAINS]->(zone:Zone)-[:CONTAINS]->(sensor:Sensor)
  RETURN building.name, floor.level, zone.name, sensor.id

Query 2: "Find all sensors that measure the same thing in adjacent zones"
  MATCH (sensor1:Sensor)-[:MEASURES]->(metric:Metric)
  MATCH (sensor1)-[:IN]->(zone1:Zone)
  MATCH (zone2:Zone)-[:ADJACENT_TO]->(zone1)
  MATCH (sensor2:Sensor)-[:IN]->(zone2)
  MATCH (sensor2)-[:MEASURES]->(metric)
  RETURN sensor1.id, sensor2.id, zone1.name, zone2.name

Query 3: "Temperature propagation through building"
  MATCH path = (sensor1:Sensor)-[:IN*]->(room:Room)
         -[:IN*]->(floor:Floor)-[:IN*]->(building:Building)
  WHERE sensor1.id = 'SM2_01'
  RETURN path, length(path)
```

### 3.3 Implementation Pattern (Future)

```
┌─ Stage 4: Neo4j Hierarchy Processing ────────────────────┐
│ (Spawned on-demand, if hierarchy queries needed)         │
│                                                           │
│ Input: Sensor metadata                                   │
│  └─ CSV with: sensor_id, parent_zone, parent_floor      │
│                                                           │
│ Processing (Cypher):                                     │
│  ├─ Create nodes: Building, Floor, Zone, Sensor         │
│  ├─ Create relationships: CONTAINS, ADJACENT_TO, etc.   │
│  ├─ Run path queries, aggregations                      │
│  └─ Export results as Parquet                           │
│                                                           │
│ Output: Hierarchy + relationships as Parquet            │
│  └─ Can be joined with time-series data for analysis    │
│                                                           │
│ Docker:                                                  │
│   docker run --rm -e NEO4J_AUTH=none neo4j:latest       │
└────────────────────────────────────────────────────────┘
```

### 3.4 Why Later, Not Now

**Current state**: You have 2 sensor types + 1 building
- Hierarchy is simple (not worth Neo4j complexity)
- DuckDB joins are sufficient

**Trigger point**: When you need to:
- Model multiple buildings
- Track sensor movement (time-varying hierarchy)
- Analyze spatial propagation
- Query "path from sensor A to sensor B"

Then Neo4j becomes valuable.

---

## 4. Ephemeral Database Orchestration

### 4.1 Current Workflow Orchestration

```yaml
# .github/workflows/influx_import_workflow.yml
jobs:
  import-influx:
    runs-on: ubuntu-latest
    
    services:
      influxdb:
        image: influxdb:2.7
        # Automatically started when job begins
        # Automatically destroyed when job ends
        # No persistent database server required
```

**Cost Impact**:
- InfluxDB in production: $100-500/month (even if idle)
- InfluxDB ephemeral: $0 (runs inside CI/CD for free)
- Storage: Only Parquet files in Google Drive ($0-10/month)

### 4.2 Scaling Pattern

```
If you add Neo4j (future):

services:
  duckdb:
    # Implicit (file-based, no container)
    # Just use `import duckdb; import pandas`
  
  influxdb:
    image: influxdb:2.7
    # 15 minutes execution time
  
  neo4j:
    image: neo4j:latest
    # 5 minutes execution time (for hierarchy sync)
    # Only run if hierarchy has changed
```

**Total runtime**: ~25 minutes per day  
**Total cost**: Cost of GitHub Actions compute only (~$0.40/month for free tier, included in GitHub)

---

## 5. Data Flow: Current vs Future

### 5.1 Current Data Flow

```
CSV (Google Drive)
  ↓ dbt + DuckDB (Refresh)
Fact tables (CSV)
  ↓ InfluxDB (InfluxImportNormalize)
Normalized hourly CSVs
  ↓ Python (PublishPublicDataset)
Parquet files (Google Drive)
  ↓ Data Scientists, BI Tools
Analysis & Reports
```

### 5.2 Future Data Flow (with Neo4j)

```
CSV (Google Drive)
  ↓ dbt + DuckDB (Refresh)
Fact tables (CSV)
  ↓ InfluxDB (InfluxImportNormalize)
Normalized hourly CSVs
  ├─→ Python (PublishPublicDataset)
  │   ├─ Parquet (time-series raw)
  │   └─ Parquet (time-series hourly)
  │
  └─→ Neo4j (HierarchyProcessing, if needed)
      ├─ Load hierarchy from CSV
      ├─ Create graph relationships
      ├─ Run hierarchy queries
      └─ Export as Parquet (hierarchy + sensor metadata)
      
   ↓
Parquet files (Google Drive)
  ├─ public_dataset_raw.parquet
  ├─ public_dataset_hourly.parquet
  └─ public_dataset_hierarchy.parquet (future)
  
  ↓
Distribution (multiple channels):
  ├─ Data Scientists (Pandas + exploratory)
  ├─ BI Tools (Hourly + pre-aggregated)
  ├─ Cloud DWH (BigQuery, Snowflake)
  ├─ REST APIs (apps)
  └─ Integrations (other services)
```

---

## 6. Why This Design Is Optimal

### 6.1 Cost Efficiency

| Aspect | Traditional | SM2 Hybrid |
|--------|------------|-----------|
| **DuckDB** | $0 (local) | $0 (local) |
| **InfluxDB Server** | $200-500/month | $0 (ephemeral) |
| **Neo4j Server** (future) | $300-1000/month | $0 (ephemeral) |
| **Storage** | Expensive (hot DB) | Cheap (cold Parquet) |
| **Total/month** | $500-1500 | $0-10 |

### 6.2 Operational Simplicity

- **No database administration**: No backups, no patches, no recovery procedures
- **Reproducibility**: Replay any day from CSV + Parquet files
- **Disaster recovery**: Automatic (files are immutable)
- **Scaling**: Horizontal (add workflows, not infrastructure)

### 6.3 Technical Flexibility

- **Switch databases**: Don't like InfluxDB? → Use TimescaleDB (same workflow)
- **Add new models**: Hierarchy with Neo4j? → Just add stage to workflow
- **Change storage**: Move from Google Drive → S3/GCS → BigQuery
- **No lock-in**: All data lives in open formats (CSV/Parquet)

### 6.4 Future-Proof

```
Year 1: DuckDB + InfluxDB (current)
Year 2: Add Neo4j (hierarchies)
Year 3: Add Elasticsearch (full-text search, future)
Year 4: Add Presto (distributed SQL, if scaling)

All use same pattern:
├─ Input: Parquet files
├─ Process: Ephemeral container
└─ Output: Parquet files

No migration, no rewrite needed.
```

---

## 7. Implementation Checklist

### Current (Stages 1-3): ✅ Done

- [x] CSV → DuckDB transformation (Refresh workflow)
- [x] DuckDB → InfluxDB ingestion (InfluxImportNormalize workflow)
- [x] InfluxDB → Parquet export (PublishPublicDataset workflow)
- [x] Ephemeral InfluxDB in GitHub Actions
- [x] Floating 2-month retention policy
- [x] Public Parquet datasets

### Future (Stages 4+): Planning

- [ ] **Hierarchy mapping** (sensor parent-child relationships)
- [ ] **Neo4j integration** (when hierarchies become important)
- [ ] **Hierarchy Parquet export** (graph relationships as tables)
- [ ] **Multi-location support** (if expanding to other buildings)
- [ ] **Real-time API** (if apps need live data)
- [ ] **Full-text search** (Elasticsearch, if data exploration is bottleneck)

### To Extend (Adding New Datasources)

- [ ] Define datasource in `seeds/datasources_config.csv`
- [ ] Create landing SQL model
- [ ] Create staging SQL model
- [ ] Add to fact table union
- [ ] Done! Workflow picks it up automatically

---

## 8. Key Architectural Decisions & Rationale

### Decision 1: Ephemeral vs Persistent Databases

**Chosen**: Ephemeral (spawn during pipeline, destroy after)

**Why not persistent**:
- Cost: Server running 24/7 but used 1 hour/day
- Maintenance: Backups, patches, monitoring
- Scalability: Fixed resources (server capacity)
- Complexity: Database administration overhead

**Why ephemeral works**:
- Cost: Pay only for compute used
- Simplicity: No server to manage
- Reproducibility: Pipeline is deterministic
- Scalability: Infinite (just run more workflows)

### Decision 2: Wide → Narrow Transformation in DuckDB

**Chosen**: DuckDB UNPIVOT (relational database)

**Why not do in Python**:
- DuckDB is faster (columnar, optimized)
- DuckDB is cleaner (SQL vs pandas code)
- DuckDB handles skew (sensors with different columns)
- DuckDB is testable (dbt tests)

**Why not do in InfluxDB**:
- InfluxDB expects narrow input
- Flux language is for aggregation, not pivoting
- Would need custom script anyway

### Decision 3: InfluxDB for Time-Series Aggregation

**Chosen**: InfluxDB 2.7 with Flux queries

**Why not DuckDB**:
- DuckDB: OLAP (analytical), not optimized for time-series windowing
- InfluxDB: OLTS (operational time-series), designed for sensors

**Why not custom Python**:
- Less efficient (O(n) vs O(log n))
- Less readable (Flux is cleaner for time operations)
- Less maintainable (SQL/Flux vs imperative code)

### Decision 4: 2-Month Floating Window

**Chosen**: Keep last 2 months in InfluxDB, archive older to Parquet

**Why not full history in InfluxDB**:
- Performance: O(1) queries vs O(n)
- Storage: 60-day database vs multi-year
- Cost: Minimal InfluxDB footprint

**Why not 1 month**:
- Too short for debugging (can't see previous cycle)
- Too short for anomaly detection (need comparison period)

**Why not 6 months**:
- Performance degrades as data grows
- Query latency becomes noticeable
- Storage size becomes expensive

**2 months**:
- Long enough for meaningful analysis
- Short enough for constant performance
- Balanced cost/utility trade-off

### Decision 5: Parquet as Final Format

**Chosen**: Apache Parquet for all public datasets

**Why not CSV**:
- Parquet: 10x compression, faster queries
- Parquet: Columnar (only read columns you need)
- Parquet: Typed (schema-aware, no guessing)
- Parquet: Portable (all languages support it)

**Why not other formats**:
- HDF5: Scientific, not portable
- Feather/Arrow: Good for interchange, overkill for archive
- ORC: Big data only, not needed for this scale
- SQLite: Database, not a format
- JSON: Text, slow, large file size

---

## 9. Deployment Architecture

### 9.1 GitHub Actions as Orchestration

```
GitHub Actions = Workflow Engine (not a database)

├─ Refresh Workflow (daily 00:00 UTC)
│  ├─ Start: Pull code
│  ├─ Execute: dbt run (DuckDB transforms)
│  ├─ Output: Fact tables (CSV)
│  └─ End: Commit docs, push to repo
│
├─ InfluxImportNormalize Workflow (daily 00:30 UTC, after Refresh)
│  ├─ Start: Pull code + fact tables
│  ├─ Spawn: InfluxDB container (15 min)
│  ├─ Execute: Import + aggregate + export
│  ├─ Output: Parquet files
│  └─ End: Destroy InfluxDB, upload to Google Drive
│
└─ PublishPublicDataset Workflow (weekly, after InfluxImportNormalize)
   ├─ Start: Pull code + aggregated files
   ├─ Execute: Generate public datasets + metadata
   ├─ Output: Parquet + schema.json + README.md
   └─ End: Upload to Google Drive
```

**Why GitHub Actions**:
- Free tier included with repository
- Built-in secrets management
- Automatic logging + audit trail
- Easy to trigger (push, schedule, manual)
- Scales without additional infrastructure

**Alternative orchestration tools**:
- Apache Airflow (over-engineered for this pipeline)
- Prefect (similar to Airflow, unnecessary)
- Dagster (over-engineered, overkill)
- dbt Cloud (not needed, local dbt works)

---

## 10. Summary: The Three-Layer Stack

| Layer | Technology | Role | Ephemeral? |
|-------|-----------|------|-----------|
| **Input** | CSV files | Raw data storage | Persistent |
| **Transform (Wide)** | DuckDB | Relational processing | Ephemeral |
| **Transform (Narrow)** | InfluxDB | Time-series aggregation | Ephemeral |
| **Transform (Hierarchy)** | Neo4j | Graph relationships | Ephemeral (future) |
| **Output** | Parquet files | Public dataset | Persistent |

## 11. FAQ

### Q: Why use GitHub Actions and not a Kubernetes cluster?
**A**: GitHub Actions is simpler, cheaper, and sufficient. Kubernetes is for highly complex orchestration; this pipeline is straightforward (3 sequential jobs). When (if) you scale to 100+ jobs, then consider Kubernetes.

### Q: What if I need real-time monitoring (not batch daily)?
**A**: Decouple the pipeline:
- Real-time: Stream data from sensors → InfluxDB Cloud (persistent)
- Batch: Daily pipeline for aggregation + archival (as current)
- No conflicts, both work in parallel

### Q: How do I query the data without Parquet files?
**A**: 
```python
import pandas as pd
import duckdb

# Option 1: Local DuckDB
con = duckdb.connect(':memory:')
df = con.execute("SELECT * FROM 'public_dataset.parquet'").df()

# Option 2: Pandas
df = pd.read_parquet('public_dataset.parquet')

# Option 3: Cloud integration (BigQuery, Snowflake)
# Upload Parquet to cloud DWH, query there
```

### Q: When should I add Neo4j?
**A**: When you need to ask questions like:
- "Which sensors are in the same zone?"
- "What's the temperature path through the building?"
- "If zone A temperature drops, predict zone B?"
- "Optimize sensor placement based on adjacency?"

Until then, skip it (YAGNI principle).

### Q: Can I use a different time-series database (TimescaleDB, QuestDB)?
**A**: Yes! Just swap the Docker image:
```yaml
# Current
services:
  influxdb:
    image: influxdb:2.7

# Alternative
services:
  timescaledb:
    image: timescale/timescaledb:latest
```

Same pattern, different engine. Parquet output unchanged.

### Q: What if Google Drive hits storage limits?
**A**: Migrate to:
```
Option 1: S3 (AWS)
  rclone copy ./public_datasets/ s3:my-bucket/sm2/

Option 2: GCS (Google Cloud Storage)
  gsutil cp -R ./public_datasets/* gs://my-bucket/sm2/

Option 3: BigQuery (Google Cloud, SQL-native)
  bq load --source_format=PARQUET dataset.table public_dataset.parquet

Option 4: Snowflake
  snowsql -c my_connection -f upload.sql
```

No code changes needed (Parquet is portable).

---

## 12. Future Roadmap

### Phase 1 (Current): Time-Series Warehouse
- [x] CSV → Parquet (sensor data)
- [x] Real-time aggregation (InfluxDB)
- [x] Public dataset distribution

### Phase 2: Add Hierarchies (when needed)
- [ ] Model building structure (Graph data model)
- [ ] Neo4j for relationships
- [ ] Spatial analysis queries

### Phase 3: Add Real-Time Features (if needed)
- [ ] Stream sensor data (Kafka/Pub-Sub)
- [ ] Live dashboards (WebSocket updates)
- [ ] Alerting system

### Phase 4: Add ML/Predictions (if business needs)
- [ ] Anomaly detection (Isolation Forest)
- [ ] Forecasting (Prophet, LSTM)
- [ ] Recommendation engine

### Phase 5: Scale to Multiple Buildings (if expanding)
- [ ] Multi-tenant support
- [ ] Federated learning (cross-building models)
- [ ] Distributed aggregation

---

## Conclusion

The SM2 Data Platform is a **three-layer ephemeral data stack**:

1. **Wide Data** (CSV) → **DuckDB** (transform) → Narrow Data
2. **Narrow Data** (CSV) → **InfluxDB** (aggregate) → Aggregated Data
3. **Aggregated Data** → **Parquet** (persist) → Public Dataset

**Designed for**:
- Cost efficiency (ephemeral = no persistent servers)
- Operational simplicity (files as single source of truth)
- Future extensibility (add Neo4j/Elasticsearch as needed)
- Multi-model processing (each tech does one thing well)

**Not designed for**:
- Real-time analytics (batch daily is sufficient)
- Petabyte-scale data (yet - scales horizontally if needed)
- Single unified query language (pay for specialization)

This is a **production-grade, cost-optimized, future-proof architecture** for sensor data processing.

---

**Document Status**: Architecture Definition ✅  
**Review Date**: Ready for team discussion  
**Next Phase**: Implementation roadmap (Phase 2-5 as business needs grow)
