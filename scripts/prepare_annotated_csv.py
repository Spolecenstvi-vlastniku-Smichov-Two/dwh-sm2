import pandas as pd
import csv
import os

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
