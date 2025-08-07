import os
import subprocess
import pandas as pd
from io import StringIO
from datetime import datetime
from dateutil import tz

# Parametry prostředí
bucket = "sensor_data"
org = os.environ.get("INFLUX_ORG", "ci-org")
token = os.environ.get("INFLUX_TOKEN", "")
url = os.environ.get("INFLUX_URL", "http://localhost:8086")

# Výstupní složka
output_dir = "./gdrive"
os.makedirs(output_dir, exist_ok=True)

# Definice měření a jejich agregací
measurement_configs = {
    "additive": "sum",
    "nonadditive": "mean"
}

def process_measurement(measurement, aggregation):
    print(f"\n📤 Spouštím dotaz pro {measurement} (fn: {aggregation})...")

    query = f'''
from(bucket: "{bucket}")
  |> range(start: 0)
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> aggregateWindow(every: 1h, fn: {aggregation}, createEmpty: false)
  |> yield(name: "{aggregation}")
'''

    result = subprocess.run([
        "influx", "query",
        "--org", org,
        "--token", token,
        "--url", url,
        "--raw",
        "--format", "csv",
        "--query", query
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Dotaz pro {measurement} selhal:")
        print(result.stderr)
        return []

    print(f"✅ Výsledky {measurement} načteny, zpracovávám...")

    df = pd.read_csv(StringIO(result.stdout), comment='#')
    if df.empty:
        print(f"⚠️ Žádná data pro {measurement}.")
        return []

    # Čas do lokalního pásma
    df['_time'] = pd.to_datetime(df['_time']).dt.tz_localize('UTC').dt.tz_convert('Europe/Prague')
    df['month'] = df['_time'].dt.strftime('%Y-%m')

    exported_files = []

    for month, group in df.groupby('month'):
        filename = f"{measurement}_hourly_{month}.csv"
        output_path = os.path.join(output_dir, filename)
        group.drop(columns=['month'], inplace=True)
        group.to_csv(output_path, index=False)
        exported_files.append(filename)
        print(f"💾 Uložen: {output_path}")

    return exported_files

# Zpracování všech měření
all_exported_files = []

for measurement, agg_func in measurement_configs.items():
    exported = process_measurement(measurement, agg_func)
    all_exported_files.extend(exported)

# Upload všech souborů na Google Drive
if all_exported_files:
    print("\n🚀 Uploaduji na Google Drive (sm2drive:Normalized/)...")
    upload = subprocess.run([
        "rclone", "copy",
        output_dir,
        "sm2drive:Normalized/",
        "--include", "*_hourly_*.csv"
    ], capture_output=True, text=True)

    if upload.returncode != 0:
        print("❌ Upload selhal:")
        print(upload.stderr)
    else:
        print("✅ Upload na Google Drive byl úspěšný.")
else:
    print("ℹ️ Nebyly vytvořeny žádné soubory k uploadu.")
