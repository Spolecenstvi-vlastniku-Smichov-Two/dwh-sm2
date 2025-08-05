import os
import glob
import subprocess

raw_dir = "./gdrive/Influx/"
csv_files = glob.glob(os.path.join(raw_dir, "**/*.csv"), recursive=True)

if not csv_files:
    print("ℹ️ Žádné předchozí raw exporty ke kontrole/importu.")
    exit(0)

print("\n📂 Nalezené CSV soubory k importu:")
for csv_file in csv_files:
    print("  ", csv_file)

for csv_file in csv_files:
    if not os.path.exists(csv_file):
        print(f"⚠️ Soubor {csv_file} neexistuje, přeskočeno.")
        continue
    if os.path.getsize(csv_file) == 0:
        print(f"⚠️ Soubor {csv_file} je prázdný, přeskočeno.")
        continue

    print(f"📥 Importuji {csv_file} do InfluxDB...")
    result = subprocess.run([
        "influx", "write",
        "--bucket", "sensor_data",
        "--org", os.environ.get("INFLUX_ORG", "ci-org"),
        "--token", os.environ.get("INFLUX_TOKEN", ""),
        "--format", "csv",
        "--file", csv_file
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Chyba při importu {csv_file}:")
        print(result.stderr)
    else:
        print(f"✅ Soubor {csv_file} byl úspěšně importován.")
