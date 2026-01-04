#!/usr/bin/env python3
"""
Data quality checks for SM2 data pipeline.
Validates data quality before InfluxDB import.
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Quality thresholds for each datasource
QUALITY_THRESHOLDS = {
    'ventilation': {
        'null_pct_max': 0.05,  # 5% max nulls
        'row_count_min': 100,
        'row_count_max': 100000,
        'csv_file': './gdrive/fact.csv',
        'timestamp_column': 'date'
    },
    'indoor': {
        'null_pct_max': 0.05,  # 5% max nulls
        'row_count_min': 100,
        'row_count_max': 100000,
        'csv_file': './gdrive/all_sensors_merged.csv',
        'timestamp_column': 'time'
    }
}

class QualityCheckError(Exception):
    """Raised when quality check fails."""
    pass

def check_data_quality(datasource_name: str, csv_file: str) -> bool:
    """
    Check data quality for a specific datasource.
    
    Args:
        datasource_name: Name of the datasource
        csv_file: Path to CSV file to check
        
    Returns:
        True if all checks pass
        
    Raises:
        QualityCheckError: If any check fails
    """
    if not Path(csv_file).exists():
        print(f"⚠️  SKIPPING: File not found: {csv_file}")
        return True
    
    try:
        df = pd.read_csv(csv_file)
        config = QUALITY_THRESHOLDS[datasource_name]
        
        print(f"Checking: {datasource_name}")
        print(f"File: {csv_file}")
        print("------")
        
        # Check null percentage
        null_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
        threshold = config['null_pct_max']
        
        if null_pct > threshold:
            print(f"❌ High null percentage: {null_pct:.2%} (threshold: {threshold:.2%})")
            raise QualityCheckError(f"High null percentage in {datasource_name}: {null_pct:.2%}")
        else:
            print(f"✅ Null check: {null_pct:.2%} (OK, threshold: {threshold:.2%})")
        
        # Check row count
        row_count = len(df)
        if row_count < config['row_count_min']:
            print(f"❌ Too few rows: {row_count} (min: {config['row_count_min']})")
            raise QualityCheckError(f"Too few rows in {datasource_name}: {row_count}")
        else:
            print(f"✅ Row count check: {row_count} rows (OK, min: {config['row_count_min']})")
        
        if row_count > config['row_count_max']:
            print(f"❌ Too many rows: {row_count} (max: {config['row_count_max']})")
            raise QualityCheckError(f"Too many rows in {datasource_name}: {row_count}")
        else:
            print(f"✅ Row count check: {row_count} rows (OK, max: {config['row_count_max']})")
        
        # Check timestamp format
        timestamp_col = config['timestamp_column']
        if timestamp_col in df.columns:
            try:
                timestamps = pd.to_datetime(df[timestamp_col])
                print(f"✅ Date format check: All timestamps valid")
                
                # Check for future dates
                now = datetime.now()
                future_dates = timestamps > now
                if future_dates.any():
                    future_count = future_dates.sum()
                    print(f"⚠️  Future dates detected: {future_count} rows with timestamp > now")
                else:
                    print(f"✅ Future date check: No future dates")
                
                # Show date range
                min_date = timestamps.min()
                max_date = timestamps.max()
                date_range = (max_date - min_date).days
                print(f"✅ Date range: {min_date.date()} to {max_date.date()} ({date_range} days)")
                
            except Exception as e:
                print(f"❌ Date format check failed: {e}")
                raise QualityCheckError(f"Invalid timestamps in {datasource_name}: {e}")
        
        print(f"")
        print(f"ALL QUALITY CHECKS PASSED: {datasource_name}")
        return True
        
    except Exception as e:
        if isinstance(e, QualityCheckError):
            raise
        print(f"❌ Error checking {datasource_name}: {e}")
        raise QualityCheckError(f"Quality check error for {datasource_name}: {e}")

def main():
    """Main quality check function."""
    print("DATA QUALITY CHECKS")
    print()
    
    checks_failed = False
    
    for datasource_name, config in QUALITY_THRESHOLDS.items():
        try:
            check_data_quality(datasource_name, config['csv_file'])
        except QualityCheckError:
            checks_failed = True
        print()
    
    if checks_failed:
        print("QUALITY CHECKS FAILED")
        sys.exit(1)
    else:
        print("ALL QUALITY CHECKS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
