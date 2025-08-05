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

if not all_data:
    raise ValueError("No data found.")

merged_df = pd.concat(all_data, ignore_index=True)
merged_df = merged_df.rename(columns={
    "time": "_time",
    "data_key": "quantity",
    "data_value": "_value"
})

# Přidej measurement
merged_df["_measurement"] = "nonadditive"

with open("nonadditive_combined.annotated.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        "#datatype", "string","long","dateTime:RFC3339","string","string","string","string","double"
    ])
    writer.writerow([
        "#group","false","false","false","true","true","true","true","false"
    ])
    writer.writerow([
        "#default","_result","","","","","","",""
    ])
    writer.writerow([
        "result","table","_time","_measurement","location","source","quantity","_field","_value"
    ])
    for i, row in merged_df.iterrows():
        writer.writerow([
            "_result",
            0,
            row["_time"],
            "nonadditive",
            row["location"],
            row["source"],
            row["quantity"],
            row["quantity"],  # _field = quantity
            row["_value"]
        ])
