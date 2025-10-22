#!/usr/bin/env python3
"""
Simple KEHE CSV to Database Migration Script
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set database URL
os.environ['DATABASE_URL'] = 'sqlite:///orderparser_dev.db'

from database.service import DatabaseService

def main():
    print("KEHE CSV to Database Migration")
    print("=" * 50)
    
    # Use the fixed render mappings file
    csv_path = "mappings/kehe/render_item_mappings_fixed.csv"
    
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return False
    
    try:
        # Read the CSV
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} rows from {csv_path}")
        
        # Convert to database format
        mappings_data = []
        for _, row in df.iterrows():
            mapping_data = {
                'source': str(row['Source']).strip(),
                'raw_item': str(row['RawKeyValue']).strip(),
                'key_type': str(row['RawKeyType']).strip(),
                'mapped_item': str(row['MappedItemNumber']).strip(),
                'vendor': str(row['Vendor']).strip() if pd.notna(row['Vendor']) else None,
                'mapped_description': str(row['MappedDescription']).strip() if pd.notna(row['MappedDescription']) else None,
                'priority': int(row['Priority']),
                'active': str(row['Active']).upper() == 'TRUE',
                'notes': str(row['Notes']).strip() if pd.notna(row['Notes']) else None
            }
            mappings_data.append(mapping_data)
        
        print(f"Converted to {len(mappings_data)} database mappings")
        
        # Import to database
        db_service = DatabaseService()
        results = db_service.bulk_upsert_item_mappings(mappings_data)
        
        print("Migration Results:")
        print(f"  Added: {results['added']}")
        print(f"  Updated: {results['updated']}")
        print(f"  Errors: {results['errors']}")
        
        if results['errors'] > 0:
            print("Error Details:")
            for error in results['error_details'][:5]:
                print(f"  - {error}")
        
        # Verify import
        existing_mappings = db_service.get_item_mappings_advanced(source='kehe', active_only=True)
        print(f"Total Kehe mappings in database: {len(existing_mappings)}")
        
        return results['errors'] == 0
        
    except Exception as e:
        print(f"Migration error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
