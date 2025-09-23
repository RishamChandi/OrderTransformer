#!/usr/bin/env python3
"""
Simple test for UNFI East migration
"""

import os
import sys
import pandas as pd

def simple_test():
    """Simple test function"""
    
    print("Starting simple migration test...")
    
    try:
        # Set database URL
        os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
        
        # Import database service
        from database.service import DatabaseService
        
        print("✓ Database service imported")
        
        # Initialize database service
        db_service = DatabaseService()
        print("✓ Database service initialized")
        
        # Test reading the CSV files
        csv_files = {
            'customer': 'mappings/unfi_east/customer_mapping.csv',
            'item': 'mappings/unfi_east/item_mapping.csv',
            'store': 'mappings/unfi_east/store_mapping.csv'
        }
        
        for mapping_type, file_path in csv_files.items():
            if os.path.exists(file_path):
                print(f"✓ Found {mapping_type} mapping file: {file_path}")
                df = pd.read_csv(file_path)
                print(f"  - {len(df)} rows found")
            else:
                print(f"❌ Missing {mapping_type} mapping file: {file_path}")
        
        # Test a simple customer mapping import
        print("\nTesting customer mapping import...")
        
        # Read customer mapping
        customer_df = pd.read_csv('mappings/unfi_east/customer_mapping.csv')
        
        # Convert to database format
        mappings_data = []
        for _, row in customer_df.iterrows():
            mapping_data = {
                'source': 'unfi_east',
                'raw_customer_id': str(row.get('StoreNumber', '')).strip(),
                'mapped_customer_name': str(row.get('CompanyName', '')).strip(),
                'customer_type': 'store',
                'priority': 100,
                'active': True,
                'notes': f'Account: {row.get("AccountNumber", "")}, ShipTo: {row.get("ShipToCompanyName", "")}'
            }
            mappings_data.append(mapping_data)
        
        print(f"Prepared {len(mappings_data)} customer mappings")
        
        # Import to database
        stats = db_service.bulk_upsert_customer_mappings(mappings_data)
        print(f"Import results: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = simple_test()
    if success:
        print("\n✅ Simple migration test passed!")
    else:
        print("\n❌ Simple migration test failed!")
    sys.exit(0 if success else 1)
