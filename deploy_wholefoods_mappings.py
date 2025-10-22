#!/usr/bin/env python3
"""
Deployment script for Whole Foods mappings on Render
This script is designed to be run during Render deployment
"""

import os
import sys
import pandas as pd
from pathlib import Path

def deploy_wholefoods_mappings():
    """Deploy Whole Foods mappings to production database"""
    
    print("🚀 Starting Whole Foods mappings deployment...")
    
    # Set production environment
    os.environ['ENVIRONMENT'] = 'production'
    
    try:
        # Import database modules
        from database.models import Base
        from database.connection import get_database_engine
        from database.service import DatabaseService
        from database.migration import run_full_migration
        
        print("✓ Database modules imported")
        
        # Initialize database
        engine = get_database_engine()
        print("✓ Database engine created")
        
        # Run migration for enhanced item mapping structure
        print("🔄 Running database migration...")
        success, message = run_full_migration()
        if success:
            print(f"✅ Migration completed: {message}")
        else:
            print(f"❌ Migration failed: {message}")
            return False
        
        # Initialize database service
        db_service = DatabaseService()
        print("✓ Database service initialized")
        
        # Define mapping files
        mapping_files = {
            'customer': 'mappings/wholefoods/Xoro Whole Foods Customer Mapping 9-17-25.csv',
            'item': 'mappings/wholefoods/Xoro Whole Foods Item Mapping 9-17-25.csv',
            'store': 'mappings/wholefoods/Xoro Whole Foods Store Mapping 9-17-25.csv'
        }
        
        total_imported = 0
        
        for mapping_type, file_path in mapping_files.items():
            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {file_path}")
                continue
                
            try:
                print(f"📄 Processing {mapping_type} mappings...")
                
                # Read CSV file
                df = pd.read_csv(file_path)
                print(f"   Found {len(df)} rows")
                
                # Convert to list of dictionaries for bulk import
                mappings_data = []
                for _, row in df.iterrows():
                    mapping_data = {}
                    
                    if mapping_type == 'customer':
                        mapping_data = {
                            'source': str(row.get('Source', 'wholefoods')).strip(),
                            'raw_customer_id': str(row.get('RawCustomerID', '')).strip(),
                            'mapped_customer_name': str(row.get('MappedCustomerName', '')).strip(),
                            'customer_type': str(row.get('CustomerType', 'store')).strip(),
                            'priority': int(row.get('Priority', 100)),
                            'active': str(row.get('Active', 'TRUE')).upper() == 'TRUE',
                            'notes': str(row.get('Notes', '')).strip() if pd.notna(row.get('Notes')) else None
                        }
                    elif mapping_type == 'item':
                        mapping_data = {
                            'source': str(row.get('Source', 'wholefoods')).strip(),
                            'raw_item': str(row.get('RawKeyValue', '')).strip(),
                            'key_type': str(row.get('RawKeyType', 'vendor_item')).strip(),
                            'mapped_item': str(row.get('MappedItemNumber', '')).strip(),
                            'vendor': str(row.get('Vendor', '')).strip() if pd.notna(row.get('Vendor')) else None,
                            'mapped_description': str(row.get('MappedDescription', '')).strip() if pd.notna(row.get('MappedDescription')) else None,
                            'priority': int(row.get('Priority', 100)),
                            'active': str(row.get('Active', 'TRUE')).upper() == 'TRUE',
                            'notes': str(row.get('Notes', '')).strip() if pd.notna(row.get('Notes')) else None
                        }
                    elif mapping_type == 'store':
                        mapping_data = {
                            'source': str(row.get('Source', 'wholefoods')).strip(),
                            'raw_store_id': str(row.get('RawStoreID', '')).strip(),
                            'mapped_store_name': str(row.get('MappedStoreName', '')).strip(),
                            'store_type': str(row.get('StoreType', 'retail')).strip(),
                            'priority': int(row.get('Priority', 100)),
                            'active': str(row.get('Active', 'TRUE')).upper() == 'TRUE',
                            'notes': str(row.get('Notes', '')).strip() if pd.notna(row.get('Notes')) else None
                        }
                    
                    # Skip empty rows
                    if mapping_data.get('raw_customer_id') or mapping_data.get('raw_item') or mapping_data.get('raw_store_id'):
                        mappings_data.append(mapping_data)
                
                # Bulk import mappings
                if mapping_type == 'customer':
                    stats = db_service.bulk_upsert_customer_mappings(mappings_data)
                elif mapping_type == 'item':
                    stats = db_service.bulk_upsert_item_mappings(mappings_data)
                elif mapping_type == 'store':
                    stats = db_service.bulk_upsert_store_mappings(mappings_data)
                
                print(f"   ✅ Imported: {stats.get('added', 0)} new, {stats.get('updated', 0)} updated")
                if stats.get('errors', 0) > 0:
                    print(f"   ⚠️  Errors: {stats.get('errors', 0)}")
                
                total_imported += stats.get('added', 0) + stats.get('updated', 0)
                
            except Exception as e:
                print(f"❌ Error importing {mapping_type} mappings: {e}")
                return False
        
        # Verify deployment
        print(f"\n🔍 Verifying deployment...")
        
        customer_mappings = db_service.get_customer_mappings_advanced(source='wholefoods', active_only=True)
        item_mappings = db_service.get_item_mappings_advanced(source='wholefoods', active_only=True)
        store_mappings = db_service.get_store_mappings_advanced(source='wholefoods', active_only=True)
        
        print(f"   Customer mappings: {len(customer_mappings)} active")
        print(f"   Item mappings: {len(item_mappings)} active")
        print(f"   Store mappings: {len(store_mappings)} active")
        
        print(f"\n✅ Deployment completed successfully!")
        print(f"   Total mappings processed: {total_imported}")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = deploy_wholefoods_mappings()
    sys.exit(0 if success else 1)
