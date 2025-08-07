
import os
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime
from io import StringIO

# Konfigurace
ORG = os.getenv("INFLUX_ORG")
TOKEN = os.getenv("INFLUX_TOKEN")
URL = os.getenv("INFLUX_URL", "http://localhost:8086")
EXPORT_DIR = "./exports/hourly"
BUCKET = "sm2"
GDRIVE_REMOTE = "sm2drive:Influx"

# Spuštění Flux dotazu a získání CSV výstupu
def run_query(flux_query):
    result = subprocess.run(
        [
            "influx", "query",
            f"--org={ORG}",
            f"--token={TOKEN}",
            "--raw", "--output", "csv",
            f"--query={flux_query}"
        ],
        capture_output=True, text=True
    )

    print("🔍 STATUS CODE:", result.returncode)
    if result.stderr:
        print("⚠️ STDERR:", result.stderr.strip())
    print("📄 STDOUT (náhled):", result.stdout[:500])
    return result.stdout

# Parsování CSV výstupu InfluxDB
def parse_csv_to_df(csv_output):
    try:
        df = pd.read_csv(StringIO(csv_output), comment="#")
        if "_time" not in df.columns:
            print("⚠️ Sloupec _time nenalezen.")
            return None
        return df
    except Exception as e:
        print("❌ Chyba při čtení CSV:", str(e))
        return None

# Získání časového rozsahu dat
def get_min_max_time():
    print("🔹 Zjišťuji rozsah časů...")

    query_min = f'''
    from(bucket: "{BUCKET}")
      |> range(start: 0)
      |> keep(columns: ["_time"])
      |> sort(columns: ["_time"], desc: false)
      |> limit(n:1)
    '''
    query_max = f'''
    from(bucket: "{BUCKET}")
      |> range(start: 0)
      |> keep(columns: ["_time"])
      |> sort(columns: ["_time"], desc: true)
      |> limit(n:1)
    '''

    min_output = run_query(query_min)
    max_output = run_query(query_max)

    if not min_output.strip() or not max_output.strip():
        print("⚠️ Prázdný výstup dotazu pro min/max čas.")
        return None, None

    df_min = parse_csv_to_df(min_output)
    df_max = parse_csv_to_df(max_output)

    if df_min is None or df_max is None or df_min.empty or df_max.empty:
        print("⚠️ Žádná data pro min/max čas. Pravděpodobně bucket prázdný.")
        return None, None

    return df_min["_time"].iloc[0], df_max["_time"].iloc[0]

# Export dotazu do souborů
def export_measurement(measurement_filter, aggregate_fn):
    print(f"📤 Spouštím dotaz pro {measurement_filter} (fn: {aggregate_fn})...")

    min_time, max_time = get_min_max_time()
    if not min_time or not max_time:
        return []

    query = f'''
    from(bucket: "{BUCKET}")
      |> range(start: time(v: "{min_time}"), stop: time(v: "{max_time}"))
      |> filter(fn: (r) => r["_measurement"] == "{measurement_filter}")
      |> aggregateWindow(every: 1h, fn: {aggregate_fn}, createEmpty: false)
      |> yield(name: "hourly")
    '''

    csv_output = run_query(query)
    df = parse_csv_to_df(csv_output)
    if df is None or df.empty:
        print(f"⚠️ Žádná data pro {measurement_filter}.")
        return []

    df["_time"] = pd.to_datetime(df["_time"])
    df["year_month"] = df["_time"].dt.to_period("M").astype(str)

    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    files = []

    for ym, group in df.groupby("year_month"):
        filename = f"{measurement_filter}_{ym}.hourly.csv"
        filepath = os.path.join(EXPORT_DIR, filename)
        group.drop(columns=["year_month"], inplace=True)
        group.to_csv(filepath, index=False)
        print(f"✅ Uloženo: {filename}")
        files.append(filepath)

        # Upload na GDrive
        rclone_cmd = ["rclone", "copyto", filepath, f"{GDRIVE_REMOTE}/{filename}"]
        subprocess.run(rclone_cmd)

    return files

def main():
    exported_files = []
    exported_files += export_measurement("additive", "sum")
    exported_files += export_measurement("nonadditive", "mean")

    if not exported_files:
        print("ℹ️ Nebyly vytvořeny žádné soubory k uploadu.")
    else:
        print(f"✅ Celkem exportováno a nahráno: {len(exported_files)} souborů.")

if __name__ == "__main__":
    main()
