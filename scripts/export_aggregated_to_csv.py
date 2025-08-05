import subprocess
import pandas as pd
from datetime import datetime, timedelta
import io
import os
import glob

ORG = os.environ["INFLUX_ORG"]
TOKEN = os.environ["INFLUX_TOKEN"]
URL = os.environ["INFLUX_URL"]
BUCKET = "sensor_hourly"
MEASUREMENT = "nonadditive_hourly"

def get_time_query(extreme: str) -> pd.Timestamp:
    desc = "desc: true" if extreme == "max" else "desc: false"
    query = f'''
from(bucket: "{BUCKET}")
  |> range(start: 0)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"], {desc})
  |> limit(n:1)
'''
    result = subprocess.run([
        "influx", "query", "--org", ORG, "--token", TOKEN, "--url", URL, "--raw", "--execute", query
    ], capture_output=True, text=True, check=True)
    df = pd.read_csv(io.StringIO(result.stdout))
    return pd.to_datetime(df["_time"].iloc[0])

start = get_time_query("min").replace(day=1)
end = get_time_query("max").replace(day=1)

current = start
generated_files = []

while current <= end:
    next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_str = current.strftime("%Y-%m")
    output_file = f"gdrive/nonadditive_hourly_{month_str}.csv"
    flux = f'''
from(bucket: "{BUCKET}")
  |> range(start: {current.isoformat()}Z, stop: {next_month.isoformat()}Z)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
  |> filter(fn: (r) => r._field == "value")
  |> keep(columns: ["_time","_value","location","quantity","source"])
'''
    with open("temp_agg_export.flux", "w") as f:
        f.write(flux)

    print(f"📤 Exportuji agregovaná data {month_str} → {output_file}")
    with open(output_file, "w") as out:
        subprocess.run([
            "influx", "query",
            "--org", ORG,
            "--token", TOKEN,
            "--url", URL,
            "--file", "temp_agg_export.flux",
            "--raw"
        ], stdout=out, check=True)

    # Debug: ukázka souboru
    with open(output_file, encoding="utf-8") as f:
        print(f"\n📄 Náhled souboru {output_file}:")
        for i in range(10):
            line = f.readline()
            if not line:
                break
            print(line.strip())

    generated_files.append(output_file)
    current = next_month

# Upload na Google Drive
print("\n☁️ Upload aggregated CSV na Google Drive")
subprocess.run(["rclone", "copy", "gdrive/", "sm2drive:Influx/", "--include", "nonadditive_hourly_*.csv"], check=True)

print("\n✅ Export agregovaných dat dokončen.")
print("📦 Exportované soubory:")
for file in generated_files:
    print("  ", file)
