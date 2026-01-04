#!/usr/bin/env python3
"""
Schema validation script for SM2 data pipeline.
Validates that CSV files match expected schema before processing.
"""

import pandas as pd
import sys
from pathlib import Path

# Expected schemas for each datasource
EXPECTED_SCHEMAS = {
    'ventilation': {
        'required_columns': {'date', 'KOT1/Teplota venkovní', 'KOT1/Vlhkost venkovní'},
        'csv_file': './gdrive/merged.csv'  # Raw wide format
    },
    'indoor': {
        'required_columns': {'Datetime', 'Temperature_Celsius', 'Relative_Humidity(%)', 'Location'},
        'csv_file': './gdrive/all_sensors_merged.csv'  # Raw merged format
    }
}

class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass

def validate_datasource(datasource_name: str, csv_file: str) -> bool:
    """
    Validate schema for a specific datasource.
    
    Args:
        datasource_name: Name of the datasource
        csv_file: Path to CSV file to validate
        
    Returns:
        True if validation passes
        
    Raises:
        SchemaValidationError: If validation fails
    """
    if not Path(csv_file).exists():
        print(f"⚠️  SKIPPING: File not found: {csv_file}")
        return True
    
    try:
        df = pd.read_csv(csv_file)
        actual_columns = set(df.columns)
        expected_columns = EXPECTED_SCHEMAS[datasource_name]['required_columns']
        
        missing_columns = expected_columns - actual_columns
        
        if missing_columns:
            print(f"❌ SCHEMA MISMATCH: {datasource_name}")
            print(f"   File: {csv_file}")
            print(f"   Missing columns: {missing_columns}")
            print(f"   Expected columns: {expected_columns}")
            print(f"   Actual columns: {actual_columns}")
            print(f"")
            print(f"   ACTION: Check if {datasource_name} data format changed!")
            raise SchemaValidationError(f"Missing columns in {datasource_name}: {missing_columns}")
        
        print(f"✅ Schema validation passed: {datasource_name}")
        print(f"   File: {csv_file}")
        print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
        
        return True
        
    except Exception as e:
        if isinstance(e, SchemaValidationError):
            raise
        print(f"❌ Error validating {datasource_name}: {e}")
        raise SchemaValidationError(f"Validation error for {datasource_name}: {e}")

def main():
    """Main validation function."""
    print("SCHEMA VALIDATION")
    print()
    
    validation_failed = False
    
    for datasource_name, config in EXPECTED_SCHEMAS.items():
        try:
            validate_datasource(datasource_name, config['csv_file'])
        except SchemaValidationError:
            validation_failed = True
        print()
    
    if validation_failed:
        print("VALIDATION FAILED")
        sys.exit(1)
    else:
        print("ALL VALIDATIONS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
