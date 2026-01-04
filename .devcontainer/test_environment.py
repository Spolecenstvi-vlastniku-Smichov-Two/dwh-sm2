#!/usr/bin/env python3
"""
Test prostředí pro devcontainer.
Kontroluje dostupnost všech potřebných nástrojů a služeb.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_command(cmd, version_flag='--version'):
    """Kontrola dostupnosti příkazu"""
    try:
        result = subprocess.run([cmd, version_flag], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def check_service(url, timeout=5):
    """Kontrola dostupnosti HTTP služby"""
    try:
        import urllib.request
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except:
        return False

def check_file_exists(path):
    """Kontrola existence souboru"""
    return Path(path).exists()

def main():
    """Hlavní funkce pro kontrolu prostředí"""
    print("🔍 Kontrola devcontainer prostředí...")
    print("=" * 50)
    
    checks = [
        # Python a základní nástroje
        ("Python 3", lambda: check_command("python3")),
        ("pip", lambda: check_command("pip")),
        ("dbt", lambda: check_command("dbt")),
        ("rclone", lambda: check_command("rclone")),
        ("csvkit", lambda: check_command("csvstack")),
        ("curl", lambda: check_command("curl")),
        ("git", lambda: check_command("git")),
        
        # Docker a databáze
        ("Docker", lambda: check_command("docker")),
        ("DuckDB CLI", lambda: check_command("duckdb", "-version")),
        ("InfluxDB CLI", lambda: check_command("influx", "version")),
        
        # Služby
        ("InfluxDB service", lambda: check_service("http://localhost:8086/health")),
        ("DuckDB HTTP", lambda: check_service("http://localhost:9000")),
        
        # Soubory a adresáře
        ("Workspace", lambda: check_file_exists("/workspace")),
        ("Database dir", lambda: check_file_exists("/workspace/db")),
        ("dbt project", lambda: check_file_exists("/workspace/dbt_project.yml")),
        ("profiles.yml", lambda: check_file_exists("/workspace/profiles.yml")),
        
        # Python balíčky
        ("pandas", lambda: __import__("pandas") is not None),
        ("pyarrow", lambda: __import__("pyarrow") is not None),
    ]
    
    failed_checks = []
    
    for name, check_func in checks:
        try:
            if check_func():
                print(f"✅ {name}")
            else:
                print(f"❌ {name}")
                failed_checks.append(name)
        except Exception as e:
            print(f"⚠️  {name} - {e}")
            failed_checks.append(name)
    
    print("=" * 50)
    
    if failed_checks:
        print(f"❌ Selhalo {len(failed_checks)} kontrol:")
        for check in failed_checks:
            print(f"  - {check}")
        print("\n💡 Tipy pro řešení:")
        print("  - Restartujte devcontainer")
        print("  - Zkontrolujte Docker resources")
        print("  - Spusťte: docker-compose up -d")
        sys.exit(1)
    else:
        print("✅ Všechny kontroly prošly úspěšně!")
        print("🚀 Prostředí je připraveno pro vývoj")
        sys.exit(0)

if __name__ == "__main__":
    main()
