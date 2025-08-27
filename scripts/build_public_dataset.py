# scripts/build_public_dataset.py
import os
import glob
import json
import pandas as pd
from pathlib import Path
import subprocess
from datetime import datetime, timezone

# === Konfigurace ===
AGG_SOURCE_REMOTE = "sm2drive:Normalized"  # odkud případně číst agregované měsíční CSV (workflow je stáhne do ./gdrive)
LOCAL_AGG_DIR = Path("./gdrive")           # kde budou additive_YYYY-MM.hourly.csv / nonadditive_YYYY-MM.hourly.csv
OUT_DIR = Path("./public")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "public_dataset.csv"
OUT_PARQUET = OUT_DIR / "public_dataset.parquet.gz"
OUT_README = OUT_DIR / "README.md"
OUT_SCHEMA = OUT_DIR / "schema.json"

LOCATION_MAP_FILE = Path("./seeds/location_map.csv")
GDRIVE_TARGET_DIR = "sm2drive:Public"   # cílový adresář na Google Drive

REQUIRED_COLS = ["time", "value", "measurement", "location", "quantity", "source"]

def find_monthly_files() -> list[str]:
    patterns = [
        "additive_????-??.hourly.csv",
        "nonadditive_????-??.hourly.csv",
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(str(LOCAL_AGG_DIR / pat)))
    files = sorted(set(files))
    print("📄 Nalezené agregované soubory:", len(files))
    for f in files[:10]:
        print("  •", f)
    if len(files) > 10:
        print(f"  … a dalších {len(files)-10} souborů")
    return files

def load_location_map() -> dict:
    if not LOCATION_MAP_FILE.exists():
        print(f"⚠️ Mapping soubor {LOCATION_MAP_FILE} neexistuje – přemapování location se přeskočí.")
        return {}
    df = pd.read_csv(LOCATION_MAP_FILE, dtype=str)
    if not {"from","to"}.issubset(df.columns):
        print("⚠️ Mapping soubor neobsahuje sloupce 'from,to' – přemapování se přeskočí.")
        return {}
    mapping = dict(zip(df["from"], df["to"]))
    print(f"🔁 Načten mapping location: {len(mapping)} položek")
    return mapping

def load_and_align(path: str) -> pd.DataFrame:
    # Očekáváme čistý formát z export_aggregated_to_csv.py: time,value,measurement,location,quantity,source
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        # fallback, kdyby někdo pustil starší export
        rename = {"_time":"time","_value":"value","_measurement":"measurement"}
        df = df.rename(columns=rename)
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: chybí sloupce {missing}")

    df = df[REQUIRED_COLS].copy()
    df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df

def write_readme_and_schema(df: pd.DataFrame):
    # --- README.md ---
    n_rows = len(df)
    time_min = df["time"].min() if n_rows else None
    time_max = df["time"].max() if n_rows else None
    meas_counts = df["measurement"].value_counts().to_dict() if n_rows else {}
    qty_top = df["quantity"].value_counts().head(15).to_dict() if n_rows else {}

    created_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    readme = f"""# SM2 Public Hourly Dataset

**Created (UTC):** {created_utc}  
**Rows:** {n_rows}  
**Time range:** {time_min} → {time_max}

## Schema

Columns (CSV):

- `time` — ISO 8601 UTC, hourly timestamps  
- `value` — numeric; for `additive` it is hourly **sum()**; for `nonadditive` hourly **mean()**  
- `measurement` — one of `additive`, `nonadditive`  
- `location` — normalized building position (e.g., `1PP-S1`, `5NP-S9`)  
- `quantity` — metric name (e.g., `temp_indoor`, `humidity_indoor`, …)  
- `source` — original source of measurement (e.g., `Atrea`, `ThermoPro`)

Units and semantics depend on `quantity` (documented separately if needed).

## Counts

- Measurements: `{meas_counts}`
- Top quantities: `{qty_top}`

## Provenance

Data aggregated in InfluxDB (1h window).  
Exported monthly → merged here.  
`location` mapped using `seeds/location_map.csv`.  

## License

Specify your preferred license here (e.g., CC BY 4.0).
"""
    OUT_README.write_text(readme, encoding="utf-8")
    print(f"📘 README vygenerováno: {OUT_README}")

    # --- schema.json ---
    schema = {
        "name": "sm2_public_hourly",
        "created_utc": created_utc,
        "format": "csv",
        "delimiter": ",",
        "encoding": "utf-8",
        "columns": [
            {"name": "time", "type": "datetime", "timezone": "UTC", "description": "ISO 8601 hourly timestamp"},
            {"name": "value", "type": "number", "description": "hourly aggregated value (sum for additive, mean for nonadditive)"},
            {"name": "measurement", "type": "string", "enum": ["additive","nonadditive"]},
            {"name": "location", "type": "string", "description": "normalized building location (e.g., 1PP-S1, 5NP-S9)"},
            {"name": "quantity", "type": "string", "description": "metric key (e.g., temp_indoor, humidity_indoor)"},
            {"name": "source", "type": "string", "description": "measurement source (e.g., Atrea, ThermoPro)"}
        ],
        "primary_key": ["time","measurement","location","quantity","source"],
        "notes": "Influx aggregateWindow(every: 1h). Values are deterministic per key.",
        "counts": {
            "rows": n_rows,
            "measurements": meas_counts,
            "top_quantities": qty_top
        }
    }
    OUT_SCHEMA.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"🧾 schema.json vygenerováno: {OUT_SCHEMA}")

def upload_to_drive(path: Path):
    rc = subprocess.run(
        ["rclone", "copyto", str(path), f"{GDRIVE_TARGET_DIR}/{path.name}"],
        capture_output=True, text=True
    )
    if rc.returncode != 0:
        print(f"⚠️ Upload selhal: {path.name} -> {rc.stderr.strip()}")
    else:
        print(f"☁️ Upload hotov: {GDRIVE_TARGET_DIR}/{path.name}")

def main():
    files = find_monthly_files()
    if not files:
        print("ℹ️ Nenašel jsem žádné agregované měsíční CSV – konec.")
        return

    location_map = load_location_map()

    parts = []
    for p in files:
        df = load_and_align(p)
        if location_map:
            df["location"] = df["location"].replace(location_map)
        parts.append(df)
        print(f"✅ {Path(p).name}: {len(df)} řádků")

    data = pd.concat(parts, ignore_index=True)
    # stabilní řazení pro čitelný CSV
    data = data.sort_values(["time","location","quantity","source"]).reset_index(drop=True)

    # Uložení CSV
    data.to_csv(OUT_CSV, index=False)
    print(f"\n💾 Uloženo CSV: {OUT_CSV} ({OUT_CSV.stat().st_size/1_048_576:.2f} MB)")

    # Uložení Parquet (rychlejší čtení, komprimované)
    try:
        data.to_parquet(OUT_PARQUET, compression="gzip", index=False)
        print(f"💾 Uloženo Parquet: {OUT_PARQUET} ({OUT_PARQUET.stat().st_size/1_048_576:.2f} MB)")
    except Exception as e:
        print(f"⚠️ Parquet neuložen ({e}) – CSV stačí.")

    # README + schema
    write_readme_and_schema(data)

    # Uploady
    upload_to_drive(OUT_CSV)
    if OUT_PARQUET.exists():
        upload_to_drive(OUT_PARQUET)
    upload_to_drive(OUT_README)
    upload_to_drive(OUT_SCHEMA)

if __name__ == "__main__":
    main()
