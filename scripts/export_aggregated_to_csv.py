# scripts/export_aggregated_to_csv.py
import os
import subprocess
import pandas as pd
from pathlib import Path
from io import StringIO

# --- Konfigurace ---
ORG   = os.getenv("INFLUX_ORG", "ci-org")
TOKEN = os.getenv("INFLUX_TOKEN", "ci-secret-token")
HOST  = os.getenv("INFLUX_URL", "http://influxdb:8086")  # použijeme --host
BUCKET = "sensor_data"
EXPORT_DIR = "./gdrive"
GDRIVE_REMOTE = "sm2drive:Normalized"  # kam pushnout agregované CSV

# SAFE MODE - ochrana proti přepsání produkčních dat
SAFE_MODE = os.getenv("SAFE_MODE", "1")  # Default: bezpečný režim
TEST_MODE = os.getenv("TEST_MODE", "0")  # Explicitní test režim

Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)

def run_query_file(flux_query: str, label: str) -> str | None:
    """Zapíše flux do temp souboru a spustí 'influx query --file'. Vrací stdout (CSV) nebo None."""
    tmp_path = Path(f"tmp_{label}.flux")
    tmp_path.write_text(flux_query, encoding="utf-8")

    print(f"\n🔹 Spouštím Flux ({label}) přes --file: {tmp_path}")
    print(flux_query.strip(), "\n")

    res = subprocess.run(
        [
            "influx", "query",
            "--org", ORG,
            "--token", TOKEN,
            "--host", HOST,
            "--raw",
            "--file", str(tmp_path),
        ],
        capture_output=True, text=True
    )

    print("🔍 STATUS CODE:", res.returncode)
    if res.stderr.strip():
        print("⚠️ STDERR:", res.stderr.strip())
    head = "\n".join(res.stdout.splitlines()[:10])
    print("📄 STDOUT (prvních 10 řádků):\n" + head)

    if res.returncode != 0 or not res.stdout.strip():
        return None
    return res.stdout

def parse_influx_csv(csv_text: str) -> pd.DataFrame:
    """Načte CSV z Influx CLI; komentáře (#group/#datatype/#default) ignoruje."""
    try:
        df = pd.read_csv(StringIO(csv_text), comment="#")
        return df
    except Exception as e:
        print("❌ Chyba při čtení CSV:", e)
        return pd.DataFrame()

def get_min_max_time(measurement: str) -> tuple[str | None, str | None]:
    """Zjistí minimální a maximální _time v bucketu pro dané measurement. Vrací ISO stringy."""
    print("🔹 Zjišťuji rozsah časů...")

    q_min = f"""
from(bucket: "{BUCKET}")
  |> range(start: -100y)
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: 1)
"""
    q_max = f"""
from(bucket: "{BUCKET}")
  |> range(start: -100y)
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 1)
"""

    out_min = run_query_file(q_min, f"{measurement}_min_time")
    out_max = run_query_file(q_max, f"{measurement}_max_time")
    if not out_min or not out_max:
        print("⚠️ Prázdný výstup dotazu pro min/max čas.")
        return None, None

    df_min = parse_influx_csv(out_min)
    df_max = parse_influx_csv(out_max)

    if df_min.empty or df_max.empty or "_time" not in df_min.columns or "_time" not in df_max.columns:
        print("⚠️ Žádná data pro min/max čas.")
        return None, None

    min_time = str(df_min["_time"].iloc[0])
    max_time = str(df_max["_time"].iloc[0])
    print(f"✅ Rozsah {measurement}: {min_time} → {max_time}")
    return min_time, max_time

def clean_and_write_monthly(df: pd.DataFrame, measurement: str) -> list[str]:
    """Přejmenuje sloupce, vybere požadované a uloží po měsících."""
    if df.empty:
        return []

    # Přejmenování a výběr sloupců
    rename_map = {"_time": "time", "_value": "data_value", "_measurement": "measurement", "quantity": "data_key"}
    df = df.rename(columns=rename_map)
    needed = ["time", "location", "source", "measurement", "data_key", "data_value"]
    # některé zdroje nemusí mít všechny tagy – ošetřit chybějící:
    for col in needed:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[needed].copy()

    # Rozdělení po měsících
    df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    df = df.dropna(subset=["time"])
    if df.empty:
        return []

    df["year_month"] = df["time"].dt.strftime("%Y-%m")
    out_files: list[str] = []

    for ym, g in df.groupby("year_month"):
        g2 = g.drop(columns=["year_month"]).copy()
        fname = f"{measurement}_{ym}.hourly.csv"
        fpath = str(Path(EXPORT_DIR) / fname)
        g2.to_csv(fpath, index=False)
        print(f"✅ Uloženo: {fpath}")

        # Upload na GDrive (pouze pokud není SAFE_MODE)
        if SAFE_MODE == "1" and TEST_MODE != "1":
            print(f"🛡️  SAFE MODE: Upload přeskočen pro {fname}")
        else:
            rc = subprocess.run(["rclone", "copyto", fpath, f"{GDRIVE_REMOTE}/{fname}"],
                                capture_output=True, text=True)
            if rc.returncode != 0:
                print(f"⚠️ Upload selhal pro {fname}: {rc.stderr.strip()}")
            else:
                print(f"☁️ Upload hotov: {GDRIVE_REMOTE}/{fname}")

        out_files.append(fpath)

    return out_files

def export_measurement_hourly(measurement: str, fn: str) -> list[str]:
    """Agregace 1h pro dané measurement a uložení do měsíčních CSV (čisté CSV)."""
    print(f"\n📤 Agreguji '{measurement}' (fn: {fn}) ...")
    t_min, t_max = get_min_max_time(measurement)
    if not t_min or not t_max:
        print(f"ℹ️ Measurement '{measurement}' nemá data – přeskočeno.")
        return []

    q = f"""
from(bucket: "{BUCKET}")
  |> range(start: time(v: "{t_min}"), stop: time(v: "{t_max}"))
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> aggregateWindow(every: 1h, fn: {fn}, createEmpty: false)
  |> keep(columns: ["_time","_value","_measurement","location","quantity","source"])
  |> yield(name: "hourly")
"""
    out = run_query_file(q, f"{measurement}_hourly")
    if not out:
        print(f"⚠️ Žádný výstup pro '{measurement}'.")
        return []

    df = parse_influx_csv(out)
    if df.empty or "_time" not in df.columns:
        print(f"⚠️ Výsledný DataFrame pro '{measurement}' je prázdný.")
        return []

    return clean_and_write_monthly(df, measurement)

def main():
    created: list[str] = []
    # additive -> sum, nonadditive -> mean
    created += export_measurement_hourly("additive", "sum")
    created += export_measurement_hourly("nonadditive", "mean")

    if not created:
        print("\nℹ️ Nebyly vytvořeny žádné soubory k uploadu.")
    else:
        print(f"\n✅ Hotovo. Vzniklo {len(created)} souborů.")
        for p in created:
            print("  -", p)

if __name__ == "__main__":
    main()

