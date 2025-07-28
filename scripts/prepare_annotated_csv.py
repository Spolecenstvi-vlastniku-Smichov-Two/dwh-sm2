
import pandas as pd
import csv
import os

mapping_df = pd.read_csv("mapping_sources.csv", encoding="utf-8-sig")
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
    "data_value": "value"
})

with open("nonadditive_combined.annotated.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["#datatype", "string", "dateTime:RFC3339", "string", "string", "string", "double"])
    writer.writerow(["#group", "false", "false", "true", "true", "true", "false"])
    writer.writerow(["#default", "_result", "", "", "", "", ""])
    writer.writerow(["_result", "_time", "quantity", "location", "source", "value"])
    for _, row in merged_df.iterrows():
        writer.writerow(["_result", row["_time"], row["quantity"], row["location"], row["source"], row["value"]])
