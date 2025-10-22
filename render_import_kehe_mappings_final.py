#!/usr/bin/env python3
"""
Import Kehe mappings to Render database - Final Version
This script imports the clean, deduplicated Kehe mappings
"""

import os
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.service import DatabaseService

def import_kehe_mappings_final():
    print("Starting Kehe mapping import on Render server (Final Version)...")
    print("=" * 60)
    
    try:
        # Import item mappings
        item_csv_path = "mappings/kehe/render_item_mappings_final.csv"
        if os.path.exists(item_csv_path):
            print(f"[INFO] Importing item mappings from {item_csv_path}...")
            
            df = pd.read_csv(item_csv_path)
            print(f"[INFO] Loaded {len(df)} rows from CSV")
            
            # Check for duplicates in CSV
            duplicates = df['RawKeyValue'].duplicated().sum()
            if duplicates > 0:
                print(f"[WARNING] CSV contains {duplicates} duplicate entries!")
                return False
            
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
            
            print(f"[INFO] Converted to {len(mappings_data)} database mappings")
            
            db_service = DatabaseService()
            results = db_service.bulk_upsert_item_mappings(mappings_data)
            
            print(f"[SUCCESS] Item mappings: {results['added']} added, {results['updated']} updated, {results['errors']} errors")
            
            if results['errors'] > 0:
                print(f"[ERROR] {results['errors']} errors occurred during item mapping import")
                for error in results['error_details'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
                return False
        else:
            print(f"[ERROR] Item mappings file not found: {item_csv_path}")
            return False
        
        # Import customer mappings
        customer_csv_path = "mappings/kehe/render_customer_mappings_fixed.csv"
        if os.path.exists(customer_csv_path):
            print(f"[INFO] Importing customer mappings from {customer_csv_path}...")
            
            df = pd.read_csv(customer_csv_path)
            mappings_data = []
            
            for _, row in df.iterrows():
                mapping_data = {
                    'source': str(row['Source']).strip(),
                    'raw_customer_id': str(row['RawKeyValue']).strip(),
                    'mapped_customer_name': str(row['MappedCustomer']).strip(),
                    'priority': int(row['Priority']),
                    'active': str(row['Active']).upper() == 'TRUE',
                    'notes': str(row['Notes']).strip() if pd.notna(row['Notes']) else None
                }
                mappings_data.append(mapping_data)
            
            db_service = DatabaseService()
            results = db_service.bulk_upsert_customer_mappings(mappings_data)
            
            print(f"[SUCCESS] Customer mappings: {results['added']} added, {results['updated']} updated, {results['errors']} errors")
            
            if results['errors'] > 0:
                print(f"[WARNING] {results['errors']} errors occurred during customer mapping import")
                for error in results['error_details'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
        else:
            print(f"[WARNING] Customer mappings file not found: {customer_csv_path}")
        
        # Import store mappings
        store_csv_path = "mappings/kehe/render_store_mappings_fixed.csv"
        if os.path.exists(store_csv_path):
            print(f"[INFO] Importing store mappings from {store_csv_path}...")
            
            df = pd.read_csv(store_csv_path)
            mappings_data = []
            
            for _, row in df.iterrows():
                mapping_data = {
                    'source': str(row['Source']).strip(),
                    'raw_store_id': str(row['RawKeyValue']).strip(),
                    'mapped_store_name': str(row['MappedStore']).strip(),
                    'priority': int(row['Priority']),
                    'active': str(row['Active']).upper() == 'TRUE',
                    'notes': str(row['Notes']).strip() if pd.notna(row['Notes']) else None
                }
                mappings_data.append(mapping_data)
            
            db_service = DatabaseService()
            results = db_service.bulk_upsert_store_mappings(mappings_data)
            
            print(f"[SUCCESS] Store mappings: {results['added']} added, {results['updated']} updated, {results['errors']} errors")
            
            if results['errors'] > 0:
                print(f"[WARNING] {results['errors']} errors occurred during store mapping import")
                for error in results['error_details'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
        else:
            print(f"[WARNING] Store mappings file not found: {store_csv_path}")
        
        print("[SUCCESS] All Kehe mappings imported successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_kehe_mappings_final()
    sys.exit(0 if success else 1)
