# SM2 Data Pipeline - Makefile pro lokální testování

.PHONY: help test-quick test-full test-phase1 test-dbt test-influx setup clean

help:
	@echo "SM2 Data Pipeline - Lokální testování"
	@echo "====================================="
	@echo ""
	@echo "Dostupné příkazy:"
	@echo "  setup        - Nastavení lokálního prostředí"
	@echo "  test-quick   - Rychlý E2E test (bez InfluxDB, syntetická data)"
	@echo "  test-full    - Kompletní E2E test (s InfluxDB, reálná data)"
	@echo "  test-phase1  - Test pouze Phase 1 (validation + ingest)"
	@echo "  test-dbt     - Test pouze dbt transformací"
	@echo "  test-influx  - Test pouze InfluxDB pipeline"
	@echo "  clean        - Úklid testovacích souborů"
	@echo ""

setup:
	@echo "🔧 Nastavení lokálního prostředí..."
	pip install -r requirements.txt
	mkdir -p gdrive public test_e2e
	chmod +x scripts/test_e2e_*.sh
	chmod +x scripts/validate_schema.py
	chmod +x scripts/quality_checks.py
	chmod +x scripts/ingest_data.py
	@echo "✅ Prostředí nastaveno"

test-quick:
	@echo "🚀 Spouštím rychlý E2E test..."
	bash scripts/test_e2e_quick.sh

test-full:
	@echo "🚀 Spouštím kompletní E2E test..."
	bash scripts/test_e2e_full.sh

test-phase1:
	@echo "🔍 Test Phase 1: Schema validation + Data-driven ingest"
	python3 scripts/validate_schema.py || true
	python3 scripts/quality_checks.py || true
	python3 scripts/ingest_data.py || true

test-dbt:
	@echo "🏗️ Test dbt transformací"
	dbt parse --project-dir .
	dbt seed --project-dir .
	dbt run --project-dir .
	dbt test --project-dir .

test-influx:
	@echo "📊 Test InfluxDB pipeline"
	@echo "Spouštím InfluxDB Docker..."
	docker run -d --name influxdb-test \
		-p 8086:8086 \
		-e DOCKER_INFLUXDB_INIT_MODE=setup \
		-e DOCKER_INFLUXDB_INIT_USERNAME=dev \
		-e DOCKER_INFLUXDB_INIT_PASSWORD=devpassword \
		-e DOCKER_INFLUXDB_INIT_ORG=dev \
		-e DOCKER_INFLUXDB_INIT_BUCKET=sensor_data \
		-e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=devtoken \
		influxdb:2.7 || true
	@echo "Čekám na spuštění InfluxDB..."
	sleep 10
	curl -f http://localhost:8086/health
	python3 scripts/prepare_annotated_csv.py || true
	python3 scripts/export_aggregated_to_csv.py || true
	@echo "Zastavuji test InfluxDB..."
	docker stop influxdb-test || true
	docker rm influxdb-test || true

clean:
	@echo "🧹 Úklid testovacích souborů..."
	rm -rf test_e2e/
	rm -f gdrive/merged.csv
	rm -f gdrive/all_sensors_merged.csv
	rm -f gdrive/*hourly.csv
	rm -f public/sm2_public_dataset.*
	docker stop influxdb-test 2>/dev/null || true
	docker rm influxdb-test 2>/dev/null || true
	@echo "✅ Úklid dokončen"

# Aliasy pro pohodlí
quick: test-quick
full: test-full
phase1: test-phase1
dbt: test-dbt
influx: test-influx
