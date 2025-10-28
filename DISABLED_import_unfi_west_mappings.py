#!/usr/bin/env python3
"""
Import UNFI West mappings from CSV to database
"""

import os
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set database URL
os.environ['DATABASE_URL'] = 'sqlite:///orderparser_dev.db'

from database.service import DatabaseService

def import_unfi_west_mappings():
    print("Importing UNFI West mappings from CSV to database")
    print("=" * 50)
    
    try:
        # Read the UNFI West mapping CSV
        csv_path = "mappings/unfi_west/item_mapping.csv"
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return False
        
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} rows from UNFI West mapping CSV")
        
        # Convert to database format
        mappings_data = []
        for _, row in df.iterrows():
            # Use the 'UNFI West' column as raw_item and 'Xoro ItemNumber' as mapped_item
            raw_item = str(row['UNFI West']).strip()
            mapped_item = str(row['Xoro ItemNumber']).strip()
            mapped_description = str(row['Xoro Description']).strip() if pd.notna(row['Xoro Description']) else None
            
            if raw_item and mapped_item:
                mapping_data = {
                    'source': 'unfi_west',
                    'raw_item': raw_item,
                    'key_type': 'vendor_item',
                    'mapped_item': mapped_item,
                    'vendor': 'UNFI West',
                    'mapped_description': mapped_description,
                    'priority': 100,
                    'active': True,
                    'notes': 'Imported from CSV'
                }
                mappings_data.append(mapping_data)
        
        print(f"Converted to {len(mappings_data)} database mappings")
        
        # Import to database
        db_service = DatabaseService()
        results = db_service.bulk_upsert_item_mappings(mappings_data)
        
        print("Import results:")
        print(f"  Added: {results['added']}")
        print(f"  Updated: {results['updated']}")
        print(f"  Errors: {results['errors']}")
        
        if results['errors'] > 0:
            print("Error details:")
            for error in results['error_details'][:5]:
                print(f"  - {error}")
        
        # Verify import
        existing_mappings = db_service.get_item_mappings_advanced(source='unfi_west', active_only=True)
        print(f"Total UNFI West mappings in database: {len(existing_mappings)}")
        
        # Show sample mappings
        if existing_mappings:
            print("\nSample mappings:")
            for i, mapping in enumerate(existing_mappings[:5]):
                raw_item = mapping['raw_item']
                mapped_item = mapping['mapped_item']
                desc = mapping['mapped_description']
                print(f"  {raw_item} -> {mapped_item} ({desc})")
        
        return results['errors'] == 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_unfi_west_mappings()
    sys.exit(0 if success else 1)
