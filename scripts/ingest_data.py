#!/usr/bin/env python3
"""
Data-driven ingest script for SM2 data pipeline.
Reads datasource configuration from seeds/datasources_config.csv
and downloads data accordingly.
"""

import pandas as pd
import subprocess
import sys
from pathlib import Path

def load_datasources_config() -> pd.DataFrame:
    """Load datasources configuration from CSV."""
    config_file = Path("seeds/datasources_config.csv")
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    df = pd.read_csv(config_file)
    return df

def download_csv_source(datasource: dict) -> bool:
    """
    Download CSV files from Google Drive using rclone.
    
    Args:
        datasource: Dictionary with datasource configuration
        
    Returns:
        True if download successful
    """
    name = datasource['name']
    location = datasource['location']
    file_pattern = datasource['file_pattern']
    
    # Create local directory
    local_dir = Path(f"./raw/{name}")
    local_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"  Downloading {name}...")
    print(f"  From: {location}")
    print(f"  Pattern: {file_pattern}")
    print(f"  To: {local_dir}")
    
    try:
        # Use rclone to download files
        cmd = [
            "rclone", "copy",
            location,
            str(local_dir),
            "--include", file_pattern
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  ❌ Download failed: {result.stderr}")
            return False
        
        # Count downloaded files
        downloaded_files = list(local_dir.glob(file_pattern.replace('*', '*')))
        print(f"  ✅ Downloaded {len(downloaded_files)} file(s)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Download error: {e}")
        return False

def process_datasource(datasource: dict) -> bool:
    """
    Process a single datasource based on its type.
    
    Args:
        datasource: Dictionary with datasource configuration
        
    Returns:
        True if processing successful
    """
    source_type = datasource['source_type']
    status = datasource['status']
    
    if status != 'active':
        print(f"⏭️  SKIPPING: {datasource['name']} (status: {status})")
        return True
    
    print(f"Processing: {datasource['name']} ({source_type})")
    
    if source_type == 'csv':
        return download_csv_source(datasource)
    elif source_type == 'api':
        print(f"  ⚠️  API sources not yet implemented")
        return True
    else:
        print(f"  ❌ Unknown source type: {source_type}")
        return False

def main():
    """Main ingest function."""
    print("DATA INGEST (DATA-DRIVEN)")
    print()
    
    try:
        # Load configuration
        print("Loading datasources configuration...")
        config_df = load_datasources_config()
        print(f"✅ Loaded {len(config_df)} datasources")
        print()
        
        # Process each datasource
        total_files = 0
        failed_datasources = []
        
        for _, row in config_df.iterrows():
            datasource = row.to_dict()
            
            success = process_datasource(datasource)
            
            if not success:
                failed_datasources.append(datasource['name'])
            
            print()
        
        # Summary
        print("INGEST SUMMARY")
        print(f"Total files downloaded: {total_files}")
        
        if failed_datasources:
            print(f"❌ Failed datasources: {', '.join(failed_datasources)}")
            sys.exit(1)
        else:
            print(f"✅ All {len(config_df)} datasource(s) downloaded successfully")
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Ingest failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
