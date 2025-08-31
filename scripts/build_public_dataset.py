import os
import glob
import json
import pandas as pd
from pathlib import Path
import subprocess
from datetime import datetime, timezone

# === Konfigurace ===
AGG_SOURCE_REMOTE = "sm2drive:Normalized"  # odkud případně číst agregované měsíční CSV
LOCAL_AGG_DIR = Path("./gdrive")           # kde budou additive_YYYY-MM.hourly.csv / nonadditive_YYYY-MM.hourly.csv
OUT_DIR = Path("./public")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "sm2_public_dataset.csv.gz"
OUT_PARQUET = OUT_DIR / "sm2_public_dataset.parquet"
OUT_README = OUT_DIR / "README.md"
OUT_SCHEMA = OUT_DIR / "schema.json"
OUT_LICENSE = OUT_DIR / "LICENSE"

LOCATION_MAP_FILE = Path("./seeds/location_map.csv")
GDRIVE_TARGET_DIR = "sm2drive:Public"   # cílový adresář na Google Drive

REQUIRED_COLS = ["time", "location", "source", "measurement", "data_key", "data_value"]

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
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: chybí sloupce {missing}")
    df = df[REQUIRED_COLS].copy()
    df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    df["data_value"] = pd.to_numeric(df["data_value"], errors="coerce")
    return df

def write_readme_and_schema(df: pd.DataFrame):
    n_rows = len(df)
    time_min = df["time"].min() if n_rows else None
    time_max = df["time"].max() if n_rows else None
    meas_counts = df["measurement"].value_counts().to_dict() if n_rows else {}
    qty_top = df["data_key"].value_counts().head(15).to_dict() if n_rows else {}
    created_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    readme = f"""# SM2 Public Hourly Dataset

**Created (UTC):** {created_utc}  
**Rows:** {n_rows}  
**Time range:** {time_min} → {time_max}

## Schema

Columns (CSV):

- `time` — ISO 8601 UTC, hourly timestamps  
- `data_value` — numeric; for `additive` it is hourly **sum()**; for `nonadditive` hourly **mean()**  
- `measurement` — one of `additive`, `nonadditive`  
- `location` — normalized building position (e.g., `1PP-S1`, `5NP-S9`)  
- `data_key` — metric name (e.g., `temp_indoor`, `humidity_indoor`, …)  
- `source` — original source of measurement (e.g., `Atrea`, `ThermoPro`)

## Counts

- Measurements: `{meas_counts}`
- Top data_keys: `{qty_top}`

## Provenance

Data aggregated in InfluxDB (1h window).  
Exported monthly → merged here.  
`location` mapped using `seeds/location_map.csv`.  

## License

This dataset is licensed under **CC BY 4.0**.  
Please cite: [horkovsm2.blogspot.com](https://horkovsm2.blogspot.com/) and  
[github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2](https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2)
"""
    OUT_README.write_text(readme, encoding="utf-8")
    print(f"📘 README vygenerováno: {OUT_README}")

    schema = {
        "name": "sm2_public_dataset",
        "created_utc": created_utc,
        "format": "csv.gz",
        "encoding": "utf-8",
        "columns": [
            {"name": "time", "type": "datetime", "timezone": "UTC"},
            {"name": "data_value", "type": "number"},
            {"name": "measurement", "type": "string", "enum": ["additive","nonadditive"]},
            {"name": "location", "type": "string"},
            {"name": "data_key", "type": "string"},
            {"name": "source", "type": "string"}
        ],
        "primary_key": ["time","measurement","location","data_key","source"],
        "counts": {
            "rows": n_rows,
            "measurements": meas_counts,
            "top_data_keys": qty_top
        }
    }
    OUT_SCHEMA.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"🧾 schema.json vygenerováno: {OUT_SCHEMA}")

    license_text = """Creative Commons Attribution 4.0 International (CC BY 4.0)

You are free to:

- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material for any purpose, even commercially.

Under the following terms:

- Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made.

License text: https://creativecommons.org/licenses/by/4.0/
"""
    OUT_LICENSE.write_text(license_text, encoding="utf-8")
    print(f"📜 LICENSE vygenerováno: {OUT_LICENSE}")

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
    data = data.sort_values(["time","location","data_key","source"]).reset_index(drop=True)

    data.to_csv(OUT_CSV, index=False, compression="gzip")
    print(f"💾 Uloženo CSV: {OUT_CSV} ({OUT_CSV.stat().st_size/1_048_576:.2f} MB)")

    try:
        data.to_parquet(OUT_PARQUET, index=False)
        print(f"💾 Uloženo Parquet: {OUT_PARQUET} ({OUT_PARQUET.stat().st_size/1_048_576:.2f} MB)")
    except Exception as e:
        print(f"⚠️ Parquet neuložen ({e}) – CSV stačí.")

    write_readme_and_schema(data)
    upload_to_drive(OUT_CSV)
    if OUT_PARQUET.exists():
        upload_to_drive(OUT_PARQUET)
    upload_to_drive(OUT_README)
    upload_to_drive(OUT_SCHEMA)
    upload_to_drive(OUT_LICENSE)

if __name__ == "__main__":
    main()
