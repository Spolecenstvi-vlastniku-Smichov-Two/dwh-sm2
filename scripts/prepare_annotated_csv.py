import pandas as pd
import csv
import os
import json
import subprocess

mapping_df = pd.read_csv("./seeds/mapping_sources.csv", encoding="utf-8-sig")
all_data = []

for _, row in mapping_df.iterrows():
    file_name = os.path.join("gdrive", row["file_nm"])
    source_name = row["source_nm"]
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, encoding="utf-8-sig")
        df["source"] = source_name
        all_data.append(df)
        print(f"📥 Načten soubor {file_name} s {len(df)} řádky")

if not all_data:
    raise ValueError("No data found.")

merged_df = pd.concat(all_data, ignore_index=True)
merged_df = merged_df.rename(columns={
    "time": "_time",
    "data_key": "quantity",
    "data_value": "_value"
})

# Oprava času do RFC3339
merged_df["_time"] = pd.to_datetime(merged_df["_time"], errors="coerce")
merged_df = merged_df.dropna(subset=["_time"])
merged_df["_time"] = merged_df["_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

# Přidej measurement a field
merged_df["_measurement"] = "nonadditive"

# Debug: náhled spojených dat
print("\n📊 Náhled spojených dat:")
print(merged_df.head())

output_file = "nonadditive_combined.annotated.csv"
with open(output_file, "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        "#datatype","dateTime:RFC3339","string","string","string","string","double"
    ])
    writer.writerow([
        "#group","false","true","true","true","true","false"
    ])
    writer.writerow([
        "#default","","","","","",""
    ])
    writer.writerow([
        "_time","_measurement","location","source","quantity","_field","_value"
    ])
    for _, row in merged_df.iterrows():
        writer.writerow([
            row["_time"],
            "nonadditive",
            row["location"],
            row["source"],
            row["quantity"],
            row["quantity"],  # _field = quantity
            row["_value"]
        ])

# Debug: ukázka souboru
print("\n📄 Ukázka vygenerovaného CSV:")
with open(output_file, encoding="utf-8") as f:
    for i in range(10):
        line = f.readline()
        if not line:
            break
        print(line.strip())

# --- Import dat do InfluxDB ---
print("\n📥 Importuji data do InfluxDB...")
try:
    import_result = subprocess.run([
        "influx", "write",
        "--org", os.getenv("INFLUX_ORG", "dev"),
        "--token", os.getenv("INFLUX_TOKEN", "devtoken"),
        "--host", os.getenv("INFLUX_URL", "http://influxdb:8086"),
        "--bucket", "sensor_data",
        "--file", output_file
    ], capture_output=True, text=True, timeout=60)
    
    if import_result.returncode == 0:
        print(f"✅ Data úspěšně importována do InfluxDB")
        print(f"   Řádků: {len(merged_df)}")
    else:
        print(f"❌ Import do InfluxDB selhal: {import_result.stderr}")
        
except Exception as e:
    print(f"❌ Chyba při importu do InfluxDB: {e}")

# --- Nově přidáno: zjištění unikátních měsíců ve vstupních datech ---
merged_df["_time_dt"] = pd.to_datetime(merged_df["_time"])
merged_df["year_month"] = merged_df["_time_dt"].dt.to_period("M").astype(str)

unique_months = sorted(merged_df["year_month"].unique())
print("\n📅 Detekované měsíce v datech:")
for month in unique_months:
    print(f" - {month}")

# 💾 Uložení seznamu měsíců do JSON
with open("months_to_process.json", "w") as f:
    json.dump(unique_months, f, indent=2)
