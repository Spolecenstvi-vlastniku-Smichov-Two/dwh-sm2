# scripts/build_public_dataset.py
import glob
import json
import pandas as pd
from pathlib import Path
import subprocess
from datetime import datetime, timezone

# =======================
# Konfigurace & konstanty
# =======================
DATASET_NAME = "sm2_public_dataset"

LOCAL_AGG_DIR = Path("./gdrive")           # additive_YYYY-MM.hourly.csv / nonadditive_YYYY-MM.hourly.csv
OUT_DIR = Path("./public")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / f"{DATASET_NAME}.csv"
OUT_PARQUET = OUT_DIR / f"{DATASET_NAME}.parquet.gz"
OUT_README = OUT_DIR / "README.md"
OUT_SCHEMA = OUT_DIR / "schema.json"
OUT_LICENSE_PUBLIC = OUT_DIR / "LICENSE"   # kopie pro public/

LICENSE_REPO = Path("./LICENSE")           # hlavní LICENSE v kořeni repo

LOCATION_MAP_FILE = Path("./seeds/location_map.csv")
GDRIVE_TARGET_DIR = "sm2drive:Public"      # cílový adresář na Google Drive

# Veřejné schéma (pevně dané)
PUBLIC_COLS = ["time", "location", "source", "measurement", "data_key", "data_value"]

# Odkazy do README/schema
URL_BLOG = "https://horkovsm2.blogspot.com/"
URL_REPO = "https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2"
URL_WIKI = "https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2/wiki"

# Text krátké verze CC BY 4.0 (s odkazem na plné znění)
CC_BY_4_SHORT = """Creative Commons Attribution 4.0 International (CC BY 4.0)

You are free to:
  Share — copy and redistribute the material in any medium or format
  Adapt — remix, transform, and build upon the material for any purpose, even commercially.

Under the following terms:
  Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made.

Full legal code: https://creativecommons.org/licenses/by/4.0/legalcode
Human-readable summary: https://creativecommons.org/licenses/by/4.0/
"""

# ==============
# Pomocné funkce
# ==============
def find_monthly_files() -> list[str]:
    patterns = [
        "additive_????-??.hourly.csv",
        "nonadditive_????-??.hourly.csv",
    ]
    files = []
    for pat in patterns:
        files.extend((LOCAL_AGG_DIR / "").glob(pat))
    files = sorted(set(map(str, files)))
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
    """
    Vstup: měsíční agregát (additive/nonadditive).
    Cílové schéma: time,location,source,measurement,data_key,data_value
    Podporuje i legacy/canonical názvy a přemapuje je zpět.
    """
    df = pd.read_csv(path)

    # Legacy → canonical (přemapujeme rovnou na cílové názvy kde to dává smysl)
    legacy_map = {"_time": "time", "_value": "data_value", "_measurement": "measurement"}
    if any(c in df.columns for c in legacy_map):
        df = df.rename(columns=legacy_map)

    # Canonical → public (value→data_value, quantity→data_key)
    if "value" in df.columns and "data_value" not in df.columns:
        df = df.rename(columns={"value": "data_value"})
    if "quantity" in df.columns and "data_key" not in df.columns:
        df = df.rename(columns={"quantity": "data_key"})

    # Kontrola sloupců
    missing = [c for c in PUBLIC_COLS if c not in df.columns]
    if missing:
        print(f"⚠️ {path}: chybí sloupce {missing}")
        print("🔎 Sloupce v souboru:", list(df.columns))
        print("📄 Prvních 5 řádků:\n", df.head())
        raise ValueError(f"{path}: chybí sloupce {missing}")

    # Minimální typová normalizace
    df = df[PUBLIC_COLS].copy()
    df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    df["data_value"] = pd.to_numeric(df["data_value"], errors="coerce")
    return df

def write_readme_and_schema(df: pd.DataFrame):
    n_rows = len(df)
    time_min = df["time"].min() if n_rows else None
    time_max = df["time"].max() if n_rows else None
    meas_counts = df["measurement"].value_counts().to_dict() if n_rows else {}
    key_top = df["data_key"].value_counts().head(15).to_dict() if n_rows else {}

    created_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    citation = f"""If you use this dataset, please cite:
SM2 Public Dataset (Hourly Aggregates), {created_utc}, {URL_REPO}"""

    license_txt = """License: Creative Commons Attribution 4.0 International (CC BY 4.0)
You are free to share and adapt the data for any purpose, even commercially, provided you give appropriate credit."""

    readme = f"""# {DATASET_NAME}

**Created (UTC):** {created_utc}  
**Rows:** {n_rows}  
**Time range:** {time_min} → {time_max}

## Schema (CSV columns)

- `time` — ISO 8601 UTC, hourly timestamps  
- `location` — normalized building position (e.g., `1PP-S1`, `5NP-S9`)  
- `source` — original source of measurement (e.g., `Atrea`, `ThermoPro`)  
- `measurement` — one of `additive`, `nonadditive`  
- `data_key` — metric name (e.g., `temp_indoor`, `humidity_indoor`, …)  
- `data_value` — numeric; for `additive` it is hourly **sum()**; for `nonadditive` hourly **mean()**

## Counts

- Measurements: `{meas_counts}`
- Top data_keys: `{key_top}`

## Provenance

- Aggregated in InfluxDB with `aggregateWindow(every: 1h)`.
- Monthly exports (additive/nonadditive) merged into a single table.
- `location` normalized via `seeds/location_map.csv`.

## Links

- Blog: {URL_BLOG}
- Repository: {URL_REPO}
- Wiki: {URL_WIKI}

## Citation

{citation}

## License

{license_txt}
"""
    OUT_README.write_text(readme, encoding="utf-8")
    print(f"📘 README vygenerováno: {OUT_README}")

    schema = {
        "name": DATASET_NAME,
        "created_utc": created_utc,
        "format": "csv",
        "delimiter": ",",
        "encoding": "utf-8",
        "columns": [
            {"name": "time", "type": "datetime", "timezone": "UTC", "description": "ISO 8601 hourly timestamp"},
            {"name": "location", "type": "string", "description": "normalized building location (e.g., 1PP-S1, 5NP-S9)"},
            {"name": "source", "type": "string", "description": "measurement source (e.g., Atrea, ThermoPro)"},
            {"name": "measurement", "type": "string", "enum": ["additive", "nonadditive"]},
            {"name": "data_key", "type": "string", "description": "metric key (e.g., temp_indoor, humidity_indoor)"},
            {"name": "data_value", "type": "number", "description": "hourly aggregated value (sum for additive, mean for nonadditive)"}
        ],
        "primary_key": ["time","measurement","location","data_key","source"],
        "notes": {
            "aggregation": "Influx aggregateWindow(every: 1h)",
            "blog": URL_BLOG,
            "repo": URL_REPO,
            "wiki": URL_WIKI
        },
        "counts": {
            "rows": n_rows,
            "measurements": meas_counts,
            "top_data_keys": key_top
        },
        "license": "CC BY 4.0"
    }
    OUT_SCHEMA.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"🧾 schema.json vygenerováno: {OUT_SCHEMA}")

def write_license_files():
    """
    Zapíše LICENSE do kořene repo (./LICENSE) a kopii do ./public/LICENSE.
    Pokud už existuje, přepíše aktuálním obsahem (aby byl konzistentní).
    """
    LICENSE_REPO.write_text(CC_BY_4_SHORT, encoding="utf-8")
    print(f"📝 LICENSE zapsán do: {LICENSE_REPO}")

    OUT_LICENSE_PUBLIC.write_text(CC_BY_4_SHORT, encoding="utf-8")
    print(f"📝 LICENSE zapsán do: {OUT_LICENSE_PUBLIC}")

def upload_to_drive(path: Path):
    rc = subprocess.run(
        ["rclone", "copyto", str(path), f"{GDRIVE_TARGET_DIR}/{path.name}"],
        capture_output=True, text=True
    )
    if rc.returncode != 0:
        print(f"⚠️ Upload selhal: {path.name} -> {rc.stderr.strip()}")
    else:
        print(f"☁️ Upload hotov: {GDRIVE_TARGET_DIR}/{path.name}")

def validate(df: pd.DataFrame):
    print("\n🔎 Validace dat:")
    print("  • Počet řádků:", len(df))
    nulls = df[PUBLIC_COLS].isna().sum().to_dict()
    print("  • NaN podle sloupců:", nulls)
    if len(df):
        print("  • Časové okno:", df['time'].min(), "→", df['time'].max())
        print("  • Unikátní measurements:", sorted(df['measurement'].unique().tolist()))
        print("  • Příklad řádků:")
        print(df.head())

# =====
# Main
# =====
def main():
    files = find_monthly_files()
    if not files:
        print("ℹ️ Nenašel jsem žádné agregované měsíční CSV – konec.")
        # i když nejsou data, LICENSE vytvoříme/aktualizujeme
        write_license_files()
        upload_to_drive(OUT_LICENSE_PUBLIC)
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
    # Stabilní řazení (pro čitelnost)
    data = data.sort_values(["time","location","data_key","source"]).reset_index(drop=True)

    # Validace do logu
    validate(data)

    # Uložení CSV
    data.to_csv(OUT_CSV, index=False)
    print(f"\n💾 Uloženo CSV: {OUT_CSV} ({OUT_CSV.stat().st_size/1_048_576:.2f} MB)")

    # Uložení Parquet (rychlejší čtení)
    try:
        data.to_parquet(OUT_PARQUET, compression="gzip", index=False)
        print(f"💾 Uloženo Parquet: {OUT_PARQUET} ({OUT_PARQUET.stat().st_size/1_048_576:.2f} MB)")
    except Exception as e:
        print(f"⚠️ Parquet neuložen ({e}) – CSV stačí.")

    # README + schema + LICENSE
    write_readme_and_schema(data)
    write_license_files()

    # Uploady (přepíší „poslední verzi“)
    upload_to_drive(OUT_CSV)
    if OUT_PARQUET.exists():
        upload_to_drive(OUT_PARQUET)
    upload_to_drive(OUT_README)
    upload_to_drive(OUT_SCHEMA)
    upload_to_drive(OUT_LICENSE_PUBLIC)

if __name__ == "__main__":
    main()
