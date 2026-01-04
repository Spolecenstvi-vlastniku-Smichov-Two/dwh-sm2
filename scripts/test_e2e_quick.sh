#!/bin/bash
# Rychlý E2E test bez InfluxDB a s syntetickými daty

set -e

echo "🚀 Rychlý E2E test SM2 Pipeline"
echo "================================"

# Kontrola závislostí
echo "🔍 Kontrola závislostí..."
for cmd in python3 dbt csvstack; do
    if ! command -v $cmd &> /dev/null; then
        echo "❌ Chybí: $cmd"
        exit 1
    fi
done
echo "✅ Všechny závislosti dostupné"

# Spuštění rychlého testu
python3 scripts/test_e2e_pipeline.py --skip-influx

echo "✅ Rychlý E2E test dokončen!"
