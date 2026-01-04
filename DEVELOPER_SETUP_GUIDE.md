# 🚀 Developer Environment Setup Guide

**Platform**: macOS (Intel/Apple Silicon)  
**IDE**: Visual Studio Code  
**Shell**: zsh  
**Target**: Full local development & testing of SM2 Data Pipeline  

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Prerequisites Check](#prerequisites-check)
3. [Installation (Step-by-Step)](#installation)
4. [VSCode Configuration](#vscode-configuration)
5. [Local Testing](#local-testing)
6. [Testing Procedures for Phase 1](#testing-procedures)
7. [Troubleshooting](#troubleshooting)
8. [Common Workflows](#common-workflows)

---

## Quick Start

Copy-paste these commands to get running in ~10 minutes:

```bash
# 1. Navigate to repo
cd /Users/lubomirkamensky/git/dwh-sm2

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install pandas pyarrow dbt-core dbt-duckdb

# 4. Install Rclone (macOS)
brew install rclone

# 5. Configure Rclone (interactive)
rclone config

# 6. Test Python scripts
python3 scripts/validate_schema.py
python3 scripts/quality_checks.py
python3 scripts/ingest_data.py

# Done! ✅
```

---

## Prerequisites Check

Before starting, verify you have:

```bash
# Check Xcode Command Line Tools (required for many tools)
xcode-select --version
# Expected: xcode-select version 2384

# If not installed:
xcode-select --install

# Check Homebrew (macOS package manager)
brew --version
# Expected: Homebrew 4.x.x

# If not installed:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Check Python (should be 3.9+)
python3 --version
# Expected: Python 3.9.6 or later

# Check zsh (default shell on modern macOS)
echo $SHELL
# Expected: /bin/zsh
```

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|------------|
| **macOS** | 11.0 | 13.0+ |
| **Python** | 3.9 | 3.10+ |
| **Disk Space** | 2 GB | 5 GB |
| **RAM** | 4 GB | 8 GB+ |
| **Git** | Latest | Latest |

---

## Installation

### Step 1: Clone Repository (if not already done)

```bash
# Create development directory
mkdir -p ~/git
cd ~/git

# Clone repository
git clone https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2.git
cd dwh-sm2

# Verify you're on main branch
git status
# Expected: On branch main
```

### Step 2: Python Virtual Environment

```bash
# Create virtual environment in project directory
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (prompt should show (venv))
echo $VIRTUAL_ENV
# Expected: /Users/lubomirkamensky/git/dwh-sm2/venv

# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel
```

**Note**: Always run `source venv/bin/activate` when opening new terminal window.

### Step 3: Python Dependencies

```bash
# Core data libraries
pip install pandas==1.5.3
pip install pyarrow==13.0.0

# dbt (for transformations)
pip install dbt-core==1.7.0
pip install dbt-duckdb==1.7.0

# Optional: SQL/formatting tools
pip install sqlfluff==2.3.0

# Optional: Development tools
pip install black pylint mypy pytest
```

**Save dependencies** (recommended):

```bash
# Generate requirements.txt
pip freeze > requirements.txt

# Later, restore with:
pip install -r requirements.txt
```

### Step 4: Install Rclone (Google Drive Integration)

Rclone is required to download files from Google Drive.

```bash
# Install Rclone via Homebrew
brew install rclone

# Verify installation
rclone --version
# Expected: rclone v1.66.0
```

**Configure Rclone for Google Drive**:

```bash
# Interactive configuration
rclone config

# Follow prompts:
# 1. Create new remote: name = "sm2drive"
# 2. Type: google cloud storage (option 15)
# 3. Follow Google OAuth flow to authorize
# 4. Verify: rclone lsd sm2drive:
```

**Test Rclone connection**:

```bash
# List root directory
rclone ls sm2drive:

# Test specific path
rclone ls sm2drive:Vzduchotechnika/Latest/

# If successful: shows files/folders from Google Drive
```

### Step 5: Install dbt

```bash
# dbt already installed via pip, but verify:
dbt --version
# Expected: dbt version 1.7.0

# Initialize dbt profile (if needed)
dbt debug --project-dir .

# Expected output:
# ✓ Installed dbt core version 1.7.0
# ✓ Local profiles.yml detected
# ✓ dbt_project.yml detected
```

### Step 6: Optional Tools (Recommended)

```bash
# Docker (for testing InfluxDB locally)
# Install from: https://docs.docker.com/desktop/install/mac-install/
# Verify:
docker --version

# Visual Studio Code extensions (see VSCode section)
# Git (should be pre-installed)
git --version
# Expected: git version 2.x.x
```

---

## VSCode Configuration

### Extension Installation

Install these extensions in VSCode for Python/dbt development:

**Essential Extensions**:
1. **Python** (Microsoft)
   - `ms-python.python`
   - Linting, debugging, IntelliSense
   
2. **Pylance** (Microsoft)
   - `ms-python.vscode-pylance`
   - Type checking, code completion
   
3. **Jupyter** (Microsoft)
   - `ms-toolsai.jupyter`
   - Interactive notebook support

4. **dbt Power User** (Fishtown Analytics)
   - `innoverio.vscode-dbt-power-user`
   - dbt model navigation, syntax highlighting

5. **SQLFluff** (SQL Formatter)
   - `dbt-labs.dbt-sql-parser`
   - SQL linting and formatting

**Recommended Extensions**:
6. **GitLens** (Eric Amodio)
   - Better Git integration
   
7. **Better Comments** (Aaron Bond)
   - Comment highlighting
   
8. **Error Lens** (Alexander
   - Inline error messages
   
9. **Markdown Preview Enhanced** (Yiyi Wang)
   - Better markdown viewing

### VSCode Settings

Create/update `.vscode/settings.json`:

```json
{
    "[python]": {
        "editor.defaultFormatter": "ms-python.python",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    },
    "[sql]": {
        "editor.defaultFormatter": "dbt-labs.dbt-sql-parser",
        "editor.formatOnSave": true
    },
    "[markdown]": {
        "editor.wordWrap": "on"
    },
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.pylintPath": "${workspaceFolder}/venv/bin/pylint",
    "python.formatting.provider": "black",
    "python.formatting.blackPath": "${workspaceFolder}/venv/bin/black",
    "editor.rulers": [88, 100],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/node_modules": true
    }
}
```

### VSCode Launch Configuration

Create `.vscode/launch.json` for debugging:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Python: validate_schema.py",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/scripts/validate_schema.py",
            "console": "integratedTerminal"
        },
        {
            "name": "Python: quality_checks.py",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/scripts/quality_checks.py",
            "console": "integratedTerminal"
        },
        {
            "name": "Python: ingest_data.py",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/scripts/ingest_data.py",
            "console": "integratedTerminal"
        }
    ]
}
```

### Terminal Integration in VSCode

Configure integrated terminal to use venv:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "terminal.integrated.defaultProfile.osx": "zsh",
    "terminal.integrated.profiles.osx": {
        "zsh": {
            "path": "/bin/zsh",
            "args": ["-l"]
        }
    }
}
```

---

## Local Testing

### Running Tests Locally

All scripts can run locally without external services (Google Drive, InfluxDB).

#### Test 1: Validate Schema Script

```bash
# Activate venv
source venv/bin/activate

# Run validation (will fail - no files, that's expected)
python3 scripts/validate_schema.py

# Expected output:
# SCHEMA VALIDATION
# ⚠️  SKIPPING: File not found: ./gdrive/fact.csv
# ⚠️  SKIPPING: File not found: ./gdrive/all_sensors_merged.csv
```

**Why it fails**: Files not present locally (that's OK - demonstrates error handling)

**To test with real files**:

```bash
# Download test data from Google Drive
rclone copy sm2drive:Vzduchotechnika/Latest/Upload ./test_data/ventilation --include "Graph*.csv"
rclone copy sm2drive:Indoor/Latest/Upload ./test_data/indoor --include "ThermoProSensor_export*.csv"

# Update script to use test data paths
# Edit scripts/validate_schema.py:
#   Line 135: csv_file: './test_data/ventilation/Graph*.csv'
#   Line 136: csv_file: './test_data/indoor/ThermoProSensor_export*.csv'

# Run again
python3 scripts/validate_schema.py
```

#### Test 2: Quality Checks Script

```bash
source venv/bin/activate
python3 scripts/quality_checks.py

# Expected output:
# DATA QUALITY CHECKS
# ⚠️  SKIPPING: File not found: ./gdrive/fact.csv
```

**To test with real data**:

```bash
# Download sample data
rclone copy sm2drive:Vzduchotechnika/Latest/Upload ./gdrive --include "Graph*.csv" --max-size 10M

# Run checks
python3 scripts/quality_checks.py

# Expected output (if data quality good):
# ✅ Null check: 0.05% (OK, threshold: 5.00%)
# ✅ Row count check: 365 rows (OK, min: 100)
# ✅ Date format check: All timestamps valid
# ALL QUALITY CHECKS PASSED
```

#### Test 3: Ingest Data Script

```bash
source venv/bin/activate
python3 scripts/ingest_data.py

# Expected output:
# DATA INGEST (DATA-DRIVEN)
# Loading datasources configuration...
# ✅ Loaded 2 datasources
# 
# Processing: ventilation (csv)
#   Downloading ventilation...
#   ✅ Downloaded 1 file(s)
# 
# Processing: indoor (csv)
#   Downloading indoor...
#   ✅ Downloaded 1 file(s)
# 
# INGEST SUMMARY
# Total files downloaded: 2
# ✅ All 2 datasource(s) downloaded successfully
```

### Testing dbt Models

```bash
# Parse project (checks syntax)
dbt parse

# Run dbt in debug mode
dbt debug

# Generate documentation (optional)
dbt docs generate

# Run specific model
dbt run --select ventilation

# Test data quality
dbt test
```

### Testing Workflows (GitHub Actions Simulation)

You can test GitHub Actions workflows locally using `act`:

```bash
# Install act
brew install act

# List available workflows
act -l

# Run specific workflow
act -j import-influx

# Run with secrets (if configured)
act --secret-file .env
```

---

## Testing Procedures for Phase 1

### Test Plan: Schema Validation + Data-Driven Ingest

This section describes how to test Phase 1 changes locally.

#### Prerequisites

```bash
source venv/bin/activate
mkdir -p ./test_data/{ventilation,indoor}
```

#### Test Case 1: Schema Validation - Normal Operation

**Objective**: Validate correct schema passes

**Setup**:
```bash
# Create test CSV with correct schema
cat > ./test_data/ventilation/test_fact.csv << 'EOF'
date,KOT1/Teplota venkovní,KOT1/Vlhkost venkovní
2024-01-01,10.5,65
2024-01-02,11.2,66
2024-01-03,9.8,64
EOF
```

**Execute**:
```bash
# Update scripts/validate_schema.py to test file path:
# csv_file: './test_data/ventilation/test_fact.csv'

python3 scripts/validate_schema.py
```

**Expected Result**:
```
✅ Schema validation passed: ventilation
   File: ./test_data/ventilation/test_fact.csv
   Rows: 3, Columns: 3

ALL VALIDATIONS PASSED
```

#### Test Case 2: Schema Validation - Format Changed

**Objective**: Detect when column names change

**Setup**:
```bash
# Create CSV with changed schema
cat > ./test_data/ventilation/test_fact_changed.csv << 'EOF'
timestamp,temperature,humidity
2024-01-01,10.5,65
2024-01-02,11.2,66
EOF
```

**Execute**:
```bash
# Update test path and run
python3 scripts/validate_schema.py
```

**Expected Result**:
```
❌ SCHEMA MISMATCH: ventilation
   Missing columns: {'date', 'KOT1/Teplota venkovní', 'KOT1/Vlhkost venkovní'}
   Actual columns: {'timestamp', 'temperature', 'humidity'}

ACTION: Check if ventilation data format changed!

VALIDATION FAILED
```

#### Test Case 3: Quality Checks - Normal Operation

**Objective**: Validate quality checks pass with good data

**Setup**:
```bash
# Create test CSV with good data
cat > ./test_data/ventilation/test_quality_good.csv << 'EOF'
date,KOT1/Teplota venkovní,KOT1/Vlhkost venkovní
2024-01-01,10.5,65.0
2024-01-02,11.2,66.0
2024-01-03,9.8,64.0
...
(100+ rows)
EOF
```

**Execute**:
```bash
python3 scripts/quality_checks.py
```

**Expected Result**:
```
✅ Null check: 0.00% (OK, threshold: 5.00%)
✅ Row count check: 365 rows (OK, min: 100)
✅ Date format check: All timestamps valid
✅ Future date check: No future dates

ALL QUALITY CHECKS PASSED: ventilation
```

#### Test Case 4: Quality Checks - High Null Percentage

**Objective**: Detect excessive nulls

**Setup**:
```bash
# Create CSV with many nulls (>5%)
cat > ./test_data/ventilation/test_quality_nulls.csv << 'EOF'
date,KOT1/Teplota venkovní,KOT1/Vlhkost venkovní
2024-01-01,10.5,
2024-01-02,,66.0
...
(more nulls)
EOF
```

**Execute**:
```bash
python3 scripts/quality_checks.py
```

**Expected Result**:
```
❌ High null percentage: 15.00% (threshold: 5.00%)

QUALITY CHECKS FAILED: ventilation
```

#### Test Case 5: Quality Checks - Invalid Timestamps

**Objective**: Detect unparseable or future dates

**Setup**:
```bash
# Create CSV with invalid dates
cat > ./test_data/ventilation/test_quality_dates.csv << 'EOF'
date,KOT1/Teplota venkovní,KOT1/Vlhkost venkovní
2025-12-31,10.5,65.0
invalid-date,11.2,66.0
2024-01-01,9.8,64.0
EOF
```

**Execute**:
```bash
python3 scripts/quality_checks.py
```

**Expected Result**:
```
⚠️  Future dates detected: 1 rows with timestamp > now
❌ Unparseable dates: 1 rows could not be parsed

QUALITY CHECKS FAILED: ventilation
```

#### Test Case 6: Data-Driven Ingest - Config Reading

**Objective**: Verify ingest script reads config correctly

**Execute**:
```bash
python3 scripts/ingest_data.py
```

**Verify**:
```bash
# Check that config is loaded
grep -c "name" seeds/datasources_config.csv
# Should show: 3 (1 header + 2 data rows)

# Check datasource names printed
# Should show: "ventilation", "indoor"
```

#### Test Case 7: Data-Driven Ingest - Skip Inactive

**Objective**: Verify inactive datasources are skipped

**Setup**:
```bash
# Add inactive datasource to config
echo "3,test_source,csv,sm2drive:Test,test*.csv,time;data,test,1,inactive,Test source" >> seeds/datasources_config.csv
```

**Execute**:
```bash
python3 scripts/ingest_data.py
```

**Expected Result**:
```
⏭️  SKIPPING: test_source (status: inactive)
```

### Test Execution Checklist

```bash
# 1. Schema Validation Tests
python3 scripts/validate_schema.py  # Normal
# ... with changed schema
# ... with missing files (OK)

# 2. Quality Checks Tests
python3 scripts/quality_checks.py  # Normal
# ... with high nulls
# ... with invalid dates
# ... with missing files (OK)

# 3. Data-Driven Ingest Tests
python3 scripts/ingest_data.py  # Config reading
# ... skip inactive
# ... error handling

# 4. End-to-End Test (if you have Rclone configured)
python3 scripts/ingest_data.py
python3 scripts/validate_schema.py
python3 scripts/quality_checks.py
```

### Automated Testing (pytest)

Create unit tests in `tests/test_phase1.py`:

```python
import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_schema_validation_valid_columns():
    """Test that valid schema passes."""
    from scripts.validate_schema import validate_datasource
    
    # Create test CSV
    test_df = pd.DataFrame({
        'date': ['2024-01-01'],
        'KOT1/Teplota venkovní': [10.5],
        'KOT1/Vlhkost venkovní': [65.0]
    })
    test_df.to_csv('./test_schema_valid.csv', index=False)
    
    # Should not raise
    assert validate_datasource('ventilation', './test_schema_valid.csv')


def test_schema_validation_missing_columns():
    """Test that missing columns fail."""
    from scripts.validate_schema import validate_datasource, SchemaValidationError
    
    # Create test CSV with missing column
    test_df = pd.DataFrame({
        'date': ['2024-01-01'],
        'KOT1/Teplota venkovní': [10.5]
        # Missing: KOT1/Vlhkost venkovní
    })
    test_df.to_csv('./test_schema_invalid.csv', index=False)
    
    # Should raise
    with pytest.raises(SchemaValidationError):
        validate_datasource('ventilation', './test_schema_invalid.csv')


def test_quality_checks_valid_data():
    """Test that good data passes quality checks."""
    from scripts.quality_checks import check_data_quality
    
    # Create test CSV with good data
    test_df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=200),
        'KOT1/Teplota venkovní': [10.5 + i*0.1 for i in range(200)],
        'KOT1/Vlhkost venkovní': [65.0 + i*0.1 for i in range(200)]
    })
    test_df.to_csv('./test_quality_valid.csv', index=False)
    
    # Should not raise
    assert check_data_quality('ventilation', './test_quality_valid.csv')


# Run with: pytest tests/test_phase1.py -v
```

### Integration Testing (Full Workflow)

```bash
#!/bin/bash
# tests/integration_test.sh

set -e

echo "🧪 Integration Test: Phase 1 Full Flow"

cd /Users/lubomirkamensky/git/dwh-sm2
source venv/bin/activate

echo "1️⃣  Testing Schema Validation..."
python3 scripts/validate_schema.py || true

echo "2️⃣  Testing Quality Checks..."
python3 scripts/quality_checks.py || true

echo "3️⃣  Testing Data-Driven Ingest..."
python3 scripts/ingest_data.py || true

echo "✅ Integration test complete"
```

Run with:
```bash
chmod +x tests/integration_test.sh
./tests/integration_test.sh
```

---

## Troubleshooting

### Python Issues

**Issue**: `ModuleNotFoundError: No module named 'pandas'`

```bash
# Solution: Install in venv
source venv/bin/activate
pip install pandas pyarrow
```

**Issue**: `python3: command not found`

```bash
# Solution: Use full path
/usr/bin/python3 --version

# Or add to PATH in ~/.zshrc
export PATH="/usr/local/bin:$PATH"
```

**Issue**: Wrong Python version

```bash
# Check which Python is active
which python3
which python

# Use python3 specifically (not python)
python3 scripts/validate_schema.py
```

### Rclone Issues

**Issue**: `rclone: command not found`

```bash
# Solution: Install
brew install rclone

# Verify
rclone --version
```

**Issue**: `Google Drive authentication fails`

```bash
# Solution: Reconfigure
rclone config

# Select: "Edit existing remote" → "sm2drive"
# Re-authorize via Google OAuth
```

**Issue**: `Failed to list remote path`

```bash
# Test connection
rclone ls sm2drive:

# If no response, check:
# 1. Internet connection
# 2. Google Drive access
# 3. Service account configuration

# Detailed troubleshoot
rclone -vv ls sm2drive:Vzduchotechnika/Latest/
```

### Git Issues

**Issue**: `fatal: not a git repository`

```bash
# Solution: Initialize or clone
git status

# Or from correct directory
cd /Users/lubomirkamensky/git/dwh-sm2
git status
```

**Issue**: `dirty working directory`

```bash
# Stash changes
git stash

# Or commit them
git add -A
git commit -m "your message"
```

### VSCode Issues

**Issue**: `Python interpreter not found`

```bash
# Solution: Select correct interpreter
Cmd + Shift + P → "Python: Select Interpreter"
→ Choose: ./venv/bin/python
```

**Issue**: Extensions not working

```bash
# Reload VSCode
Cmd + Shift + P → "Developer: Reload Window"
```

**Issue**: Terminal not using venv

```bash
# Close and reopen terminal (Ctrl + `)
# Or manually activate:
source venv/bin/activate
```

### dbt Issues

**Issue**: `Profile not found`

```bash
# Check profiles.yml location
cat profiles.yml

# Or use project dir flag
dbt debug --project-dir .
```

**Issue**: `Target database not found`

```bash
# For DuckDB (default), this is OK - file-based
# For InfluxDB, need running instance

# Check dbt_project.yml
cat dbt_project.yml
```

---

## Common Workflows

### Daily Development Workflow

```bash
# 1. Open terminal in VSCode (Ctrl + `)

# 2. Activate venv (or it auto-activates)
source venv/bin/activate

# 3. Check git status
git status

# 4. Create feature branch
git checkout -b feature/my-feature

# 5. Make changes in VSCode

# 6. Test locally
python3 scripts/validate_schema.py

# 7. Commit changes
git add scripts/my_script.py
git commit -m "feat: add new validation"

# 8. Push to GitHub
git push origin feature/my-feature

# 9. Create Pull Request on GitHub
```

### Testing Phase 1 Changes

```bash
# 1. Setup
cd /Users/lubomirkamensky/git/dwh-sm2
source venv/bin/activate

# 2. Test each component
echo "Testing schema validation..."
python3 scripts/validate_schema.py

echo "Testing quality checks..."
python3 scripts/quality_checks.py

echo "Testing data-driven ingest..."
python3 scripts/ingest_data.py

# 3. Test with real data (if Rclone configured)
rclone ls sm2drive:Vzduchotechnika/Latest/

# 4. Check results
echo "✅ All tests passed"
```

### Adding New Datasource (Post-Phase 1)

```bash
# 1. Update seeds/datasources_config.csv
echo "3,new_source,csv,sm2drive:NewData,new_*.csv,columns,types,1,planned,Description" >> seeds/datasources_config.csv

# 2. Change status to 'active' when ready
# ... edit CSV

# 3. Test ingest
python3 scripts/ingest_data.py

# 4. Validate schema
python3 scripts/validate_schema.py

# 5. Check quality
python3 scripts/quality_checks.py
```

### Running Full Pipeline Locally (Simulation)

```bash
#!/bin/bash
# scripts/local_test_full_pipeline.sh

source venv/bin/activate

echo "🚀 Local Pipeline Test"

# Step 1: Download data
echo "1️⃣  Ingest data..."
python3 scripts/ingest_data.py

# Step 2: Validate
echo "2️⃣  Validate schema..."
python3 scripts/validate_schema.py

# Step 3: Quality checks
echo "3️⃣  Quality checks..."
python3 scripts/quality_checks.py

# Step 4: Run dbt
echo "4️⃣  Running dbt models..."
dbt run

# Step 5: Test dbt
echo "5️⃣  Testing data quality..."
dbt test

# Step 6: Generate docs
echo "6️⃣  Generating documentation..."
dbt docs generate

echo "✅ Local pipeline test complete"
```

---

## Next Steps

1. **Run Quick Start** (5 min) - Get basic setup working
2. **Follow Installation** (10-15 min) - Complete full setup
3. **Configure VSCode** (5 min) - Extensions and settings
4. **Run Local Tests** (10 min) - Execute Phase 1 tests
5. **Review Testing Procedures** (20 min) - Understand test cases
6. **Add to PATH** (optional) - For quick access

---

## Additional Resources

### Documentation
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [Rclone Documentation](https://rclone.org/docs/)
- [dbt Documentation](https://docs.getdbt.com/)
- [VSCode Python Guide](https://code.visualstudio.com/docs/python/python-tutorial)

### Related Guides
- [PHASE_1_IMPLEMENTATION.md](PHASE_1_IMPLEMENTATION.md) - Phase 1 details
- [PHASE_1_DEPLOYMENT_CHECKLIST.md](PHASE_1_DEPLOYMENT_CHECKLIST.md) - Deployment
- [README.md](README.md) - Operational documentation
- [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md) - Long-term vision

### Commands Quick Reference

```bash
# Python/venv
python3 -m venv venv           # Create virtual environment
source venv/bin/activate       # Activate venv
pip install -r requirements.txt # Install dependencies
pip freeze > requirements.txt   # Save dependencies

# Rclone
rclone config                   # Configure remotes
rclone ls sm2drive:             # List files
rclone copy src dst             # Copy files
rclone -vv ls sm2drive:         # Verbose listing

# dbt
dbt parse                       # Parse project
dbt debug                       # Debug configuration
dbt run                         # Run models
dbt test                        # Test data
dbt docs generate               # Generate docs
dbt docs serve                  # View docs locally

# Git
git status                      # Check status
git add file                    # Stage changes
git commit -m "msg"             # Commit
git push origin branch          # Push to GitHub
git pull origin main            # Pull latest

# Testing
python3 scripts/validate_schema.py     # Test validation
python3 scripts/quality_checks.py      # Test quality
python3 scripts/ingest_data.py        # Test ingest
pytest tests/                          # Run unit tests
```

---

**Happy Developing! 🎉**

For questions or issues, check:
1. Troubleshooting section (this document)
2. PHASE_1_IMPLEMENTATION.md
3. GitHub Issues
4. Team Slack

