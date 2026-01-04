#!/bin/bash
# Kompletní E2E test s reálnými daty a InfluxDB

set -e

echo "🚀 Kompletní E2E test SM2 Pipeline"
echo "==================================="

# Kontrola závislostí
echo "🔍 Kontrola závislostí..."
for cmd in python3 dbt csvstack docker curl rclone; do
    if ! command -v $cmd &> /dev/null; then
        echo "❌ Chybí: $cmd"
        exit 1
    fi
done

# Kontrola Docker daemon
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon není spuštěn"
    exit 1
fi

# Kontrola rclone konfigurace
if ! rclone lsd sm2drive: &> /dev/null; then
    echo "❌ Rclone není nakonfigurován pro sm2drive"
    echo "Spusťte: rclone config"
    exit 1
fi

echo "✅ Všechny závislosti dostupné"

# Spuštění kompletního testu
python3 scripts/test_e2e_pipeline.py --with-real-data

echo "✅ Kompletní E2E test dokončen!"
