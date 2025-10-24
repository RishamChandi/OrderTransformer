#!/usr/bin/env python3
"""
Migration script to load UNFI East customer mappings from Excel file into database
"""

import pandas as pd
import os
from database.service import DatabaseService

def migrate_unfi_east_customer_mappings():
    """Migrate UNFI East customer mappings from Excel to database"""
    
    # Initialize database service
    db_service = DatabaseService()
    
    # Path to the Excel file
    excel_file = 'attached_assets/UNFI EAST STORE TO CUSTOMER MAPPING_1753461773530.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return False
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_file)
        print(f"✅ Loaded Excel file with {len(df)} rows")
        
        # Prepare mappings data for database
        mappings_data = []
        
        for _, row in df.iterrows():
            unfi_code = str(row['UNFI East ']).strip().upper()
            company_name = str(row['CompanyName']).strip()
            
            if unfi_code and company_name and unfi_code != 'nan' and company_name != 'nan':
                mappings_data.append({
                    'source': 'unfi_east',
                    'raw_name': unfi_code,
                    'mapped_name': company_name,
                    'store_type': 'distributor',
                    'priority': 100,
                    'active': True,
                    'notes': f'Migrated from Excel file - UNFI East code {unfi_code}'
                })
        
        # Add any missing mappings that we've discovered from PDFs
        additional_mappings = [
            {'unfi_code': 'SS', 'company_name': 'UNFI EAST SARASOTA FL'},
            {'unfi_code': 'HH', 'company_name': 'UNFI EAST HOWELL NJ'},
            {'unfi_code': 'GG', 'company_name': 'UNFI EAST GREENWOOD IN'},
            {'unfi_code': 'JJ', 'company_name': 'UNFI EAST HOWELL NJ'},
            {'unfi_code': 'MM', 'company_name': 'UNFI EAST YORK PA'},
        ]
        
        for mapping in additional_mappings:
            # Check if mapping already exists
            exists = any(m['raw_name'] == mapping['unfi_code'] for m in mappings_data)
            if not exists:
                mappings_data.append({
                    'source': 'unfi_east',
                    'raw_name': mapping['unfi_code'],
                    'mapped_name': mapping['company_name'],
                    'store_type': 'distributor',
                    'priority': 100,
                    'active': True,
                    'notes': f'Added missing mapping - UNFI East code {mapping["unfi_code"]}'
                })
        
        print(f"✅ Prepared {len(mappings_data)} mappings for database")
        
        # Bulk insert into database
        result = db_service.bulk_upsert_store_mappings(mappings_data)
        
        if result['success']:
            print(f"✅ Successfully migrated {result['inserted']} new mappings")
            print(f"✅ Updated {result['updated']} existing mappings")
            return True
        else:
            print(f"❌ Migration failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting UNFI East customer mapping migration...")
    success = migrate_unfi_east_customer_mappings()
    
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
