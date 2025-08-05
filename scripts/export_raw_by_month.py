import subprocess
import pandas as pd
from datetime import datetime, timedelta
import io
import os

ORG = os.environ["INFLUX_ORG"]
TOKEN = os.environ["INFLUX_TOKEN"]
URL = os.environ["INFLUX_URL"]
BUCKET = "sensor_data"
MEASUREMENT = "nonadditive"

def run_flux_query(flux_query: str, debug_label: str):
    """Spustí Flux dotaz přes dočasný .flux soubor a vrátí surový výstup CLI."""
    filename = f"temp_query_{debug_label}.flux"
    with open(filename, "w") as f:
        f.write(flux_query)

    print(f"\n🔹 Spouštím Flux dotaz ({debug_label}):\n{flux_query}")

    result = subprocess.run([
        "influx", "query",
        "--org", ORG,
        "--token", TOKEN,
        "--host", URL,
        "--raw",
        "--file", filename
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Chyba při dotazu ({debug_label}):")
        print(result.stderr)
        return None

    output = result.stdout.strip()
    if not output:
        print(f"⚠️ Dotaz ({debug_label}) vrátil prázdný výstup.")
        return None

    print(f"\n🔹 Surový výstup CLI ({debug_label}) - prvních 10 řádků:")
    print("\n".join(output.splitlines()[:10]))
    return output

def parse_influx_csv(raw_output: str, label: str):
    """Odstraní 3 hlavičkové řádky a vrátí Pandas DataFrame."""
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

def get_time_query(extreme: str):
    """Vrátí min/max čas z bucketu."""
    desc = "desc: true" if extreme == "max" else "desc: false"
    flux_query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -100y)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
  |> group(columns: [])
  |> sort(columns: ["_time"], {desc})
  |> limit(n:1)
'''

    raw_output = run_flux_query(flux_query, f"{extreme}_time")
    if not raw_output:
        print(f"⚠️ Žádná data pro {extreme} čas. Pravděpodobně bucket prázdný.")
        return None

    df = parse_influx_csv(raw_output, f"{extreme}_time")
    if df is None or df.empty:
        print(f"⚠️ Nepodařilo se načíst DataFrame pro {extreme} čas.")
        return None

    return pd.to_datetime(df["_time"].iloc[0])

# --- Hlavní logika skriptu ---

start_ts = get_time_query("min")
end_ts = get_time_query("max")

if start_ts is None or end_ts is None:
    print("ℹ️ Raw bucket je prázdný, export se přeskočí.")
    exit(0)

print(f"\n✅ Detekován časový rozsah dat: {start_ts} → {end_ts}")

# Export po měsících
start = start_ts.replace(day=1)
end = end_ts.replace(day=1)

current = start
generated_files = []

while current <= end:
    next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_str = current.strftime("%Y-%m")
    output_file = f"gdrive/nonadditive_{month_str}.annotated.csv"

    flux_export = f'''
from(bucket: "{BUCKET}")
  |> range(start: {current.isoformat()}Z, stop: {next_month.isoformat()}Z)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
'''

    raw_output = run_flux_query(flux_export, f"export_{month_str}")
    if not raw_output:
        print(f"⚠️ Žádná data k exportu pro měsíc {month_str}, přeskočeno.")
        current = next_month
        continue

    # Uložíme čisté CSV bez hlaviček pro snadný reimport
    with open(output_file, "w", encoding="utf-8") as f:
        lines = raw_output.splitlines()
        # Ponecháme annotated CSV pro další import do Influxu
        f.write("\n".join(lines))

    print(f"\n📤 Soubor exportován: {output_file}")
    with open(output_file, encoding="utf-8") as f:
        print(f"📄 Náhled {output_file}:")
        for i in range(10):
            line = f.readline()
            if not line:
                break
            print(line.strip())

    generated_files.append(output_file)
    current = next_month

# Upload na Google Drive
print("\n☁️ Upload raw exportů na Google Drive")
subprocess.run([
    "rclone", "copy", "gdrive/", "sm2drive:Influx/", "--include", "nonadditive_*.annotated.csv"
], check=True)

print("\n✅ Export raw dat dokončen.")
print("📦 Exportované soubory:")
for file in generated_files:
    print("  ", file)
