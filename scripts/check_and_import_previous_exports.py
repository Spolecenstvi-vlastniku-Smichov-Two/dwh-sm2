
import pandas as pd
import subprocess
import os

ANNOTATED_FILE = "nonadditive_combined.annotated.csv"
ORG = os.environ["INFLUX_ORG"]
TOKEN = os.environ["INFLUX_TOKEN"]
URL = os.environ["INFLUX_URL"]
BUCKET = "sensor_data"

print(f"\n🔍 Načítám: {ANNOTATED_FILE}")
df = pd.read_csv(ANNOTATED_FILE, comment='#')
df["_time"] = pd.to_datetime(df["_time"])
min_month = df["_time"].min().to_period("M").strftime("%Y-%m")
max_month = df["_time"].max().to_period("M").strftime("%Y-%m")
months = pd.period_range(start=min_month, end=max_month, freq="M").strftime("%Y-%m").tolist()

imported = False
for month in months:
    fname = os.path.join("gdrive", f"nonadditive_{month}.annotated.csv")
    if os.path.exists(fname):
        print(f"⬅️ Importuji starý export: {fname}")
        subprocess.run([
            "influx", "write",
            "--bucket", BUCKET,
            "--org", ORG,
            "--token", TOKEN,
            "--url", URL,
            "--format", "csv",
            "--file", fname
        ], check=True)
        imported = True

if not imported:
    print("ℹ️ Žádné historické raw exporty nenalezeny. Pokračuji pouze s novým souborem.")

print(f"⬅️ Importuji nový soubor: {ANNOTATED_FILE}")
subprocess.run([
    "influx", "write",
    "--bucket", BUCKET,
    "--org", ORG,
    "--token", TOKEN,
    "--url", URL,
    "--format", "csv",
    "--file", ANNOTATED_FILE
], check=True)
