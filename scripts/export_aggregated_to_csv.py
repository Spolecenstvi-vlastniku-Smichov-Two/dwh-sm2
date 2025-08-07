import os
import subprocess
import csv
from io import StringIO
from pathlib import Path
from datetime import datetime
import json

# Nastavení prostředí
ORG = os.environ.get("INFLUX_ORG", "ci-org")
TOKEN = os.environ.get("INFLUX_TOKEN", "")
EXPORT_DIR = "./exports_hourly"
REMOTE_DIR = "sm2drive:Influx"

# Zajistí, že adresář existuje
Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)

def run_query(flux_query):
    return subprocess.run(
        [
            "influx", "query",
            "--org", ORG,
            "--token", TOKEN,
            "--raw", "--output", "csv",
            "--execute", flux_query
        ],
        capture_output=True, text=True
    )

def parse_first_time_from_query(result):
    if result.returncode != 0 or not result.stdout.strip():
        return None

    f = StringIO(result.stdout)
    reader = csv.DictReader(f)
    for row in reader:
        return row.get("_time")
    return None

def get_min_max_time():
    print("🔹 Zjišťuji rozsah časů...")

    min_result = run_query(
        'from(bucket: "sensor_data") |> range(start: 0) |> keep(columns: ["_time"]) |> sort(columns: ["_time"], desc: false) |> limit(n:1)'
    )
    max_result = run_query(
        'from(bucket: "sensor_data") |> range(start: 0) |> keep(columns: ["_time"]) |> sort(columns: ["_time"], desc: true) |> limit(n:1)'
    )

    min_time = parse_first_time_from_query(min_result)
    max_time = parse_first_time_from_query(max_result)

    if not min_time or not max_time:
        print("⚠️ Žádná data pro min/max čas. Pravděpodobně bucket prázdný.")
        return None, None

    print(f"🕓 Časový rozsah: {min_time} – {max_time}")
    return min_time, max_time

def split_csv_by_month(csv_text, measurement_type):
    rows_by_month = {}
    f = StringIO(csv_text)
    reader = csv.DictReader(f)
    for row in reader:
        timestamp = row["_time"]
        month = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m")
        rows_by_month.setdefault(month, []).append(row)

    written_files = []
    for month, rows in rows_by_month.items():
        output_file = os.path.join(EXPORT_DIR, f"{measurement_type}_{month}.hourly.csv")
        with open(output_file, "w", newline="") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ Exportováno: {output_file}")
        written_files.append(output_file)

    return written_files

def export_measurement(measurement_type, agg_func):
    print(f"\n📤 Spouštím dotaz pro {measurement_type} (fn: {agg_func})...")

    min_time, max_time = get_min_max_time()
    if not min_time or not max_time:
        return []

    flux_query = f'''
    from(bucket: "sensor_data")
        |> range(start: time(v: "{min_time}"), stop: time(v: "{max_time}"))
        |> filter(fn: (r) => r._measurement == "{measurement_type}")
        |> aggregateWindow(every: 1h, fn: {agg_func}, createEmpty: false)
        |> yield()
    '''.strip()

    result = run_query(flux_query)
    if result.returncode != 0:
        print(f"❌ Dotaz selhal:\n{result.stderr}")
        return []

    if not result.stdout.strip():
        print("⚠️ Výsledek je prázdný.")
        return []

    return split_csv_by_month(result.stdout, measurement_type)

def upload_to_drive(files):
    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"☁️ Upload na Google Drive: {filename}")
        subprocess.run(["rclone", "copy", file_path, REMOTE_DIR])

def main():
    exported_files = []
    exported_files += export_measurement("additive", "sum")
    exported_files += export_measurement("nonadditive", "mean")

    if exported_files:
        upload_to_drive(exported_files)
    else:
        print("ℹ️ Nebyly vytvořeny žádné soubory k uploadu.")

if __name__ == "__main__":
    main()
