# scripts/export_raw_by_month.py
import subprocess
import pandas as pd
from datetime import timedelta
import io
import os
from pathlib import Path

ORG  = os.environ["INFLUX_ORG"]
TOKEN = os.environ["INFLUX_TOKEN"]
HOST  = os.environ["INFLUX_URL"]
BUCKET = "sensor_data"

EXPORT_DIR = Path("gdrive/Influx")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def run_flux_query(flux_query: str, debug_label: str):
    """Spustí Flux dotaz přes dočasný .flux soubor a vrátí surový výstup CLI (annotated CSV)."""
    filename = f"temp_query_{debug_label}.flux"
    Path(filename).write_text(flux_query, encoding="utf-8")

    print(f"\n🔹 Spouštím Flux dotaz ({debug_label}):\n{flux_query.strip()}\n")

    result = subprocess.run(
        [
            "influx", "query",
            "--org", ORG,
            "--token", TOKEN,
            "--host", HOST,
            "--raw",
            "--file", filename
        ],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"❌ Chyba při dotazu ({debug_label}):")
        print(result.stderr)
        return None

    output = result.stdout.strip()
    if not output:
        print(f"⚠️ Dotaz ({debug_label}) vrátil prázdný výstup.")
        return None

    print(f"🔹 Surový výstup CLI ({debug_label}) - prvních 10 řádků:")
    print("\n".join(output.splitlines()[:10]))
    return output

def parse_influx_csv(raw_output: str, label: str):
    """Odstraní 3 hlavičkové řádky a vrátí Pandas DataFrame pro rychlou kontrolu."""
    lines = raw_output.splitlines()
    if len(lines) <= 3:
        print(f"⚠️ Výstup pro {label} obsahuje méně než 4 řádky.")
        return None
    csv_clean = "\n".join(lines[3:])
    df = pd.read_csv(io.StringIO(csv_clean))
    print(f"\n🔹 Náhled DataFrame ({label}):")
    print(df.head())
    if "_time" not in df.columns:
        print(f"⚠️ Sloupec _time nebyl nalezen v datech {label}.")
        return None
    return df

def get_time_query(measurement: str, extreme: str):
    """Vrátí min/max čas z bucketu pro dané measurement (timestamp jako pandas.Timestamp)."""
    desc = "desc: true" if extreme == "max" else "desc: false"
    flux_query = f"""
from(bucket: "{BUCKET}")
  |> range(start: -100y)
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> group(columns: [])
  |> sort(columns: ["_time"], {desc})
  |> limit(n:1)
"""
    raw_output = run_flux_query(flux_query, f"{measurement}_{extreme}_time")
    if not raw_output:
        print(f"⚠️ Žádná data pro {measurement} / {extreme} čas.")
        return None

    df = parse_influx_csv(raw_output, f"{measurement}_{extreme}_time")
    if df is None or df.empty:
        print(f"⚠️ Nepodařilo se načíst DataFrame pro {measurement} / {extreme} čas.")
        return None

    return pd.to_datetime(df["_time"].iloc[0])

def export_measurement_monthly(measurement: str) -> list[str]:
    """Exportuje annotated CSV po měsících pro dané measurement. Vrací list vytvořených souborů."""
    print(f"\n📦 Export RAW (annotated) pro measurement: {measurement}")

    start_ts = get_time_query(measurement, "min")
    end_ts   = get_time_query(measurement, "max")

    if start_ts is None or end_ts is None:
        print(f"ℹ️ {measurement}: žádná data – export přeskočen.")
        return []

    print(f"✅ Detekován časový rozsah {measurement}: {start_ts} → {end_ts}")

    # Export po měsících (včetně okrajových měsíců)
    start = start_ts.replace(day=1)
    end   = end_ts.replace(day=1)

    current = start
    generated = []

    while current <= end:
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_str = current.strftime("%Y-%m")
        output_file = EXPORT_DIR / f"{measurement}_{month_str}.annotated.csv"

        start_str = current.strftime("%Y-%m-%dT%H:%M:%SZ")
        stop_str  = next_month.strftime("%Y-%m-%dT%H:%M:%SZ")

        flux_export = f"""
from(bucket: "{BUCKET}")
  |> range(start: {start_str}, stop: {stop_str})
  |> filter(fn: (r) => r._measurement == "{measurement}")
"""
        raw_output = run_flux_query(flux_export, f"{measurement}_export_{month_str}")
        if not raw_output:
            print(f"⚠️ Žádná data k exportu pro {measurement} {month_str}, přeskočeno.")
            current = next_month
            continue

        # Uložíme annotated CSV pro snadný reimport
        output_file.write_text(raw_output, encoding="utf-8")
        print(f"\n📤 Soubor exportován: {output_file}")
        with output_file.open(encoding="utf-8") as f:
            print(f"📄 Náhled {output_file.name}:")
            for i in range(10):
                line = f.readline()
                if not line:
                    break
                print(line.strip())

        generated.append(str(output_file))
        current = next_month

    return generated

def upload_generated(files: list[str]):
    if not files:
        print("\nℹ️ Nebyly vygenerovány žádné soubory – upload přeskočen.")
        return
    print("\n☁️ Upload raw exportů na Google Drive")
    # Bezpečně nahraj jen soubory, které skutečně existují:
    for f in files:
        rc = subprocess.run(
            ["rclone", "copyto", f, f"sm2drive:Influx/{Path(f).name}"],
            capture_output=True, text=True
        )
        if rc.returncode != 0:
            print(f"⚠️ Upload selhal pro {f}: {rc.stderr.strip()}")
        else:
            print(f"☁️ Upload hotov: sm2drive:Influx/{Path(f).name}")

# --- Hlavní běh ---
all_generated = []
# Export obou measurements
for m in ["nonadditive", "additive"]:
    all_generated += export_measurement_monthly(m)

print("\n✅ Export raw dat dokončen.")
print("📦 Exportované soubory:")
for file in all_generated:
    print("  ", file)

upload_generated(all_generated)
