#!/usr/bin/env python3
"""
Render server script to import Whole Foods mappings from CSV files
Run this script on the Render server to populate the database with mappings
"""

import pandas as pd
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.service import DatabaseService

def import_wholefoods_mappings():
    """Import Whole Foods mappings from CSV files to database"""
    
    print("Starting Whole Foods mapping import on Render server...")
    
    # Initialize database service (uses Render environment automatically)
    db_service = DatabaseService()
    
    try:
        # Import item mappings
        item_file = 'mappings/wholefoods/render_item_mappings.csv'
        if os.path.exists(item_file):
            print(f"[INFO] Importing item mappings from {item_file}...")
            item_df = pd.read_csv(item_file)
            
            # Convert to database format
            mappings_data = []
            for _, row in item_df.iterrows():
                mappings_data.append({
                    'source': str(row['Source']),
                    'raw_item': str(row['RawKeyValue']),
                    'mapped_item': str(row['MappedItemNumber']),
                    'key_type': str(row['RawKeyType']),
                    'priority': int(row['Priority']),
                    'active': bool(row['Active']),
                    'vendor': str(row['Vendor']) if pd.notna(row['Vendor']) else None,
                    'mapped_description': str(row['MappedDescription']) if pd.notna(row['MappedDescription']) else None,
                    'notes': str(row['Notes']) if pd.notna(row['Notes']) else None
                })
            
            result = db_service.bulk_upsert_item_mappings(mappings_data)
            print(f"[SUCCESS] Item mappings: {result['added']} added, {result['updated']} updated, {result['errors']} errors")
        else:
            print(f"[WARNING] Item mapping file not found: {item_file}")
        
        # Import customer mappings
        customer_file = 'mappings/wholefoods/render_customer_mappings.csv'
        if os.path.exists(customer_file):
            print(f"[INFO] Importing customer mappings from {customer_file}...")
            customer_df = pd.read_csv(customer_file)
            
            # Convert to database format
            mappings_data = []
            for _, row in customer_df.iterrows():
                mappings_data.append({
                    'source': str(row['Source']),
                    'raw_customer_id': str(row['RawCustomerID']),
                    'mapped_customer_name': str(row['MappedCustomerName']),
                    'customer_type': str(row['CustomerType']),
                    'priority': int(row['Priority']),
                    'active': bool(row['Active']),
                    'notes': str(row['Notes']) if pd.notna(row['Notes']) else None
                })
            
            result = db_service.bulk_upsert_customer_mappings(mappings_data)
            print(f"[SUCCESS] Customer mappings: {result['added']} added, {result['updated']} updated, {result['errors']} errors")
        else:
            print(f"[WARNING] Customer mapping file not found: {customer_file}")
        
        # Import store mappings
        store_file = 'mappings/wholefoods/render_store_mappings.csv'
        if os.path.exists(store_file):
            print(f"[INFO] Importing store mappings from {store_file}...")
            store_df = pd.read_csv(store_file)
            
            # Convert to database format
            mappings_data = []
            for _, row in store_df.iterrows():
                mappings_data.append({
                    'source': str(row['Source']),
                    'raw_store_id': str(row['RawStoreID']),
                    'mapped_store_name': str(row['MappedStoreName']),
                    'store_type': str(row['StoreType']),
                    'priority': int(row['Priority']),
                    'active': bool(row['Active']),
                    'notes': str(row['Notes']) if pd.notna(row['Notes']) else None
                })
            
            result = db_service.bulk_upsert_store_mappings(mappings_data)
            print(f"[SUCCESS] Store mappings: {result['added']} added, {result['updated']} updated, {result['errors']} errors")
        else:
            print(f"[WARNING] Store mapping file not found: {store_file}")
        
        print("\n[SUCCESS] All mappings imported successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Import failed: {str(e)}")
        return False

if __name__ == '__main__':
    import_wholefoods_mappings()
