
import os
import subprocess
import csv
from datetime import datetime
from collections import defaultdict
from pathlib import Path

ORG = os.environ.get("INFLUX_ORG", "ci-org")
TOKEN = os.environ.get("INFLUX_TOKEN", "")
URL = os.environ.get("INFLUX_URL", "http://localhost:8086")

EXPORT_DIR = "./exports"
Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)

def get_min_max_time():
    base_query = '''
from(bucket: "sensor_data")
  |> range(start: -100y)
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> group(columns: [])
  |> sort(columns: ["_time"], desc: {desc})
  |> limit(n:1)
'''

    min_query = base_query.format(measurement="nonadditive", desc="false")
    max_query = base_query.format(measurement="nonadditive", desc="true")

    min_time = run_query(min_query)
    max_time = run_query(max_query)

    if not min_time or not max_time:
        print("⚠️ Žádná data pro min/max čas. Pravděpodobně bucket prázdný.")
        return None, None

    return min_time[0]["_time"], max_time[0]["_time"]

def run_query(flux_query):
    result = subprocess.run(
        [
            "influx", "query",
            "--org", ORG,
            "--token", TOKEN,
            "--raw", "--output", "csv",
            "--query", flux_query
        ],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print("❌ Dotaz selhal:")
        print(result.stderr)
        return []

    lines = result.stdout.strip().split("\n")
    reader = csv.DictReader(lines)
    return list(reader)

def export_measurement(measurement, agg_fn):
    print(f"📤 Spouštím dotaz pro {measurement} (fn: {agg_fn})...")

    min_time, max_time = get_min_max_time()
    if not min_time or not max_time:
        return []

    flux_query = f'''
from(bucket: "sensor_data")
  |> range(start: time(v: "{min_time}"), stop: time(v: "{max_time}"))
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> aggregateWindow(every: 1h, fn: {agg_fn}, createEmpty: false)
  |> yield(name: "hourly")
'''

    rows = run_query(flux_query)
    if not rows:
        print(f"⚠️ Žádná data pro {measurement}")
        return []

    output_by_month = defaultdict(list)
    for row in rows:
        try:
            timestamp = datetime.fromisoformat(row["_time"].replace("Z", "+00:00"))
            month = timestamp.strftime("%Y-%m")
            output_by_month[month].append(row)
        except Exception as e:
            print(f"⚠️ Chyba při zpracování řádku: {e}")

    uploaded_files = []
    for month, records in output_by_month.items():
        filename = f"{measurement}_{month}.hourly.csv"
        filepath = os.path.join(EXPORT_DIR, filename)

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)

        print(f"✅ Exportováno {len(records)} řádků do {filepath}")

        # Upload to Google Drive
        gdrive_path = f"sm2drive:Influx/{filename}"
        upload_result = subprocess.run(["rclone", "copy", filepath, gdrive_path])
        if upload_result.returncode == 0:
            print(f"☁️  Nahráno na {gdrive_path}")
            uploaded_files.append(filepath)
        else:
            print(f"⚠️  Upload na {gdrive_path} selhal.")

    return uploaded_files

def main():
    exported_files = []
    exported_files += export_measurement("additive", "sum")
    exported_files += export_measurement("nonadditive", "mean")

    if not exported_files:
        print("ℹ️ Nebyly vytvořeny žádné soubory k uploadu.")

if __name__ == "__main__":
    main()
