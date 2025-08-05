import subprocess
import pandas as pd
import io
import os

ORG = os.environ["INFLUX_ORG"]
TOKEN = os.environ["INFLUX_TOKEN"]
URL = os.environ["INFLUX_URL"]
BUCKET = "sensor_data"

query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -100y)
  |> limit(n:10)
'''

print("🔹 Spouštím jednoduchý dotaz pro prvních 10 řádků:\n", query)

result = subprocess.run([
    "influx", "query",
    "--org", ORG,
    "--token", TOKEN,
    "--host", URL,
    "--raw",
    "--execute", query
], capture_output=True, text=True)

if result.returncode != 0:
    print("❌ Chyba při dotazu na InfluxDB:")
    print(result.stderr)
    exit(1)

raw_output = result.stdout.strip()
if not raw_output:
    print("⚠️ Žádná data z bucketu, výstup prázdný.")
    exit(0)

print("\n🔹 Surový výstup CLI (prvních 20 řádků):")
print("\n".join(raw_output.splitlines()[:20]))

# Pokus o načtení Pandasem
try:
    df = pd.read_csv(io.StringIO(raw_output))
    print("\n🔹 Náhled Pandas DataFrame:")
    print(df.head(10))
    print("\n🔹 Sloupce v DataFrame:")
    print(df.columns.tolist())
except Exception as e:
    print("❌ Chyba při načítání CSV Pandasem:", e)
