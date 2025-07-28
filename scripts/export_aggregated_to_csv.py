
import subprocess
import pandas as pd
from datetime import datetime, timedelta
import io
import os

ORG = os.environ["INFLUX_ORG"]
TOKEN = os.environ["INFLUX_TOKEN"]
URL = os.environ["INFLUX_URL"]
BUCKET = "sensor_hourly"
MEASUREMENT = "nonadditive_hourly"

query = f'''
from(bucket: "{BUCKET}")
  |> range(start: 0)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"])
  |> limit(n:1)
'''
result = subprocess.run([
    "influx", "query", "--org", ORG, "--token", TOKEN, "--url", URL, "--raw", "--execute", query
], capture_output=True, text=True, check=True)
first_time = pd.to_datetime(pd.read_csv(io.StringIO(result.stdout))["_time"].iloc[0])

query = f'''
from(bucket: "{BUCKET}")
  |> range(start: 0)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n:1)
'''
result = subprocess.run([
    "influx", "query", "--org", ORG, "--token", TOKEN, "--url", URL, "--raw", "--execute", query
], capture_output=True, text=True, check=True)
last_time = pd.to_datetime(pd.read_csv(io.StringIO(result.stdout))["_time"].iloc[0])

start = datetime(first_time.year, first_time.month, 1)
end = datetime(last_time.year, last_time.month, 1)

current = start
while current <= end:
    next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_str = current.strftime("%Y-%m")
    output_file = f"gdrive/nonadditive_hourly_{month_str}.csv"
    flux = f'''
from(bucket: "{BUCKET}")
  |> range(start: {current.isoformat()}Z, stop: {next_month.isoformat()}Z)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
  |> filter(fn: (r) => r._field == "value")
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "value", "location", "quantity", "source"])
'''
    with open("temp_export.flux", "w") as f:
        f.write(flux)
    print(f"📤 Exportuji agregovaná data do: {output_file}")
    with open(output_file, "w") as out:
        subprocess.run([
            "influx", "query",
            "--org", ORG,
            "--token", TOKEN,
            "--url", URL,
            "--file", "temp_export.flux"
        ], stdout=out, check=True)
    current = next_month

print("☁️ Upload na Google Drive")
subprocess.run(["rclone", "copy", "gdrive/", "sm2drive:Influx/", "--include", "nonadditive_hourly_*.csv"], check=True)
