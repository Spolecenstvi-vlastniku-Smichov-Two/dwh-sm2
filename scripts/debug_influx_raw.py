import subprocess
import pandas as pd
import io
import os

ORG = os.environ["INFLUX_ORG"]
TOKEN = os.environ["INFLUX_TOKEN"]
URL = os.environ["INFLUX_URL"]
BUCKET = "sensor_data"

flux_query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -100y)
  |> limit(n:10)
'''

# uložíme query do dočasného souboru
with open("temp_debug_query.flux", "w") as f:
    f.write(flux_query)

print("🔹 Spouštím jednoduchý dotaz pro prvních 10 řádků...")

result = subprocess.run([
    "influx", "query",
    "--org", ORG,
    "--token", TOKEN,
    "--host", URL,
    "--raw",
    "--file", "temp_debug_query.flux"
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

# Odstraníme první 3 řádky (#group, #datatype, #default)
lines = raw_output.splitlines()
if len(lines) <= 3:
    print("⚠️ Výstup obsahuje méně než 4 řádky, nemohu načíst data.")
    exit(0)

clean_csv = "\n".join(lines[3:])

# Pokus o načtení Pandasem
try:
    df = pd.read_csv(io.StringIO(clean_csv))
    print("\n🔹 Náhled Pandas DataFrame (po odstranění hlavičkových řádků):")
    print(df.head(10))
    print("\n🔹 Sloupce v DataFrame:")
    print(df.columns.tolist())

    if "_time" in df.columns:
        print("\n✅ Sloupec _time nalezen, teorie potvrzena.")
    else:
        print("\n⚠️ Sloupec _time nebyl nalezen, stále problém s hlavičkou.")
except Exception as e:
    print("❌ Chyba při načítání CSV Pandasem:", e)
