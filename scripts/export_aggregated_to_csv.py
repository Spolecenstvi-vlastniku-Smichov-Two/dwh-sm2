
import os
import subprocess
import pandas as pd
from datetime import datetime
from pathlib import Path

# Konfigurace
ORG = os.getenv("INFLUX_ORG", "ci-org")
TOKEN = os.getenv("INFLUX_TOKEN", "ci-secret-token")
BUCKET = "sensor_data"
EXPORT_DIR = "./gdrive"

def run_query(flux_query):
    result = subprocess.run(
        [
            "influx", "query",
            f"--org={ORG}",
            f"--token={TOKEN}",
            "--raw", "--output", "csv",
            f"--query={flux_query}"  # << OPRAVA ZDE
        ],
        capture_output=True, text=True
    )
    return result


def parse_csv_to_df(csv_output):
    try:
        from io import StringIO
        df = pd.read_csv(StringIO(csv_output), comment="#")
        return df
    except Exception as e:
        print(f"❌ Chyba při čtení CSV: {e}")
        return pd.DataFrame()

def get_min_max_time():
    print("🔹 Zjišťuji rozsah časů...")

    min_query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -100y)
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"])
  |> limit(n:1)
'''
    max_query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -100y)
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n:1)
'''

    min_output = run_query(min_query)
    max_output = run_query(max_query)

    if not min_output or not max_output:
        print("⚠️ Žádná data pro min/max čas. Pravděpodobně bucket prázdný.")
        return None, None

    min_df = parse_csv_to_df(min_output)
    max_df = parse_csv_to_df(max_output)

    if "_time" not in min_df.columns or "_time" not in max_df.columns:
        print("⚠️ Žádná data pro min/max čas. Pravděpodobně bucket prázdný.")
        return None, None

    return min_df["_time"].iloc[0], max_df["_time"].iloc[0]

def export_measurement(measurement_type, aggregation_fn):
    print(f"📤 Spouštím dotaz pro {measurement_type} (fn: {aggregation_fn})...")
    min_time, max_time = get_min_max_time()
    if not min_time or not max_time:
        return []

    query = f'''
from(bucket: "{BUCKET}")
  |> range(start: time(v: "{min_time}"), stop: time(v: "{max_time}"))
  |> filter(fn: (r) => r._measurement == "{measurement_type}")
  |> aggregateWindow(every: 1h, fn: {aggregation_fn}, createEmpty: false)
  |> yield(name: "hourly")
'''

    output = run_query(query)
    if not output:
        return []

    df = parse_csv_to_df(output)
    if df.empty or "_time" not in df.columns:
        print(f"⚠️ Výsledek pro {measurement_type} je prázdný nebo neobsahuje sloupec _time.")
        return []

    df["_time"] = pd.to_datetime(df["_time"])
    df["month"] = df["_time"].dt.strftime("%Y-%m")
    files = []

    for month, group in df.groupby("month"):
        filename = f"{measurement_type}_{month}.hourly.csv"
        filepath = os.path.join(EXPORT_DIR, filename)
        group.drop(columns=["month"], inplace=True)
        group.to_csv(filepath, index=False)
        print(f"✅ Uložen soubor: {filename}")
        files.append(filepath)

    return files

def upload_to_drive(filepath):
    filename = os.path.basename(filepath)
    remote_path = f"sm2drive:Influx/{filename}"
    print(f"☁️ Upload na Google Drive: {filename}")
    subprocess.run(["rclone", "copy", filepath, remote_path])

def main():
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)

    exported_files = []
    exported_files += export_measurement("additive", "sum")
    exported_files += export_measurement("nonadditive", "mean")

    if not exported_files:
        print("ℹ️ Nebyly vytvořeny žádné soubory k uploadu.")
        return

    for f in exported_files:
        upload_to_drive(f)

if __name__ == "__main__":
    main()
