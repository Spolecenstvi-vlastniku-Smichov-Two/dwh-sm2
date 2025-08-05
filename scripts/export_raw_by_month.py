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

def get_time_query(extreme: str):
    desc = "desc: true" if extreme == "max" else "desc: false"
    query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -100y)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
  |> sort(columns: ["_time"], {desc})
  |> limit(n:1)
'''
    result = subprocess.run([
        "influx", "query",
        "--org", ORG,
        "--token", TOKEN,
        "--host", URL,
        "--raw",
        "--hide-headers",
        "--execute", query
    ], capture_output=True, text=True)

    if result.returncode != 0 or not result.stdout.strip():
        print(f"⚠️ Žádná data pro {extreme} čas. Pravděpodobně bucket prázdný.")
        return None

    # Debug: první řádky výstupu z CLI
    print(f"\n🔹 Debug {extreme} čas - první řádky CLI:")
    print("\n".join(result.stdout.splitlines()[:5]))

    df = pd.read_csv(io.StringIO(result.stdout))
    if "_time" not in df.columns or df.empty:
        print(f"⚠️ Žádná data pro {extreme} čas ani po načtení CSV.")
        return None

    return pd.to_datetime(df["_time"].iloc[0])

start_ts = get_time_query("min")
end_ts = get_time_query("max")

if start_ts is None or end_ts is None:
    print("ℹ️ Raw bucket je prázdný, export se přeskočí.")
    exit(0)

start = start_ts.replace(day=1)
end = end_ts.replace(day=1)

current = start
generated_files = []

while current <= end:
    next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_str = current.strftime("%Y-%m")
    output_file = f"gdrive/nonadditive_{month_str}.annotated.csv"
    flux = f'''
from(bucket: "{BUCKET}")
  |> range(start: {current.isoformat()}Z, stop: {next_month.isoformat()}Z)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
'''
    with open("temp_raw_export.flux", "w") as f:
        f.write(flux)

    print(f"📤 Exportuji RAW {month_str} → {output_file}")
    with open(output_file, "w") as out:
        subprocess.run([
            "influx", "query",
            "--org", ORG,
            "--token", TOKEN,
            "--host", URL,
            "--file", "temp_raw_export.flux",
            "--raw",
            "--hide-headers"
        ], stdout=out, check=True)

    # Debug: ukázka exportovaného souboru
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
print("\n☁️ Upload raw exportů na Google Drive")
subprocess.run([
    "rclone", "copy", "gdrive/", "sm2drive:Influx/", "--include", "nonadditive_*.annotated.csv"
], check=True)

print("\n✅ Export raw dat dokončen.")
print("📦 Exportované soubory:")
for file in generated_files:
    print("  ", file)
