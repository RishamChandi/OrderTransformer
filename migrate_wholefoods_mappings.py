#!/usr/bin/env python3
"""
Migration script for Whole Foods mappings
Imports new Whole Foods mappings to production database
"""

import os
import sys
import pandas as pd
from pathlib import Path
from database.models import Base
from database.connection import get_database_engine, get_session
from database.service import DatabaseService
from database.migration import run_full_migration

def migrate_wholefoods_mappings():
    """Migrate Whole Foods mappings to production database"""
    
    print("=" * 60)
    print("Whole Foods Mappings Migration Script")
    print("=" * 60)
    
    # Check environment
    env = os.getenv('ENVIRONMENT', 'local')
    print(f"Current environment: {env}")
    
    if env == 'local':
        print("⚠️  Running in local environment. Set ENVIRONMENT=production for production migration.")
        response = input("Continue with local migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return False
    
    try:
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
        migration_summary = {}
        
        for mapping_type, file_path in mapping_files.items():
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue
                
            try:
                print(f"\n📄 Processing {mapping_type} mappings from {file_path}")
                
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
                    for error in stats.get('error_details', [])[:5]:  # Show first 5 errors
                        print(f"      - {error}")
                
                migration_summary[mapping_type] = {
                    'added': stats.get('added', 0),
                    'updated': stats.get('updated', 0),
                    'errors': stats.get('errors', 0)
                }
                
                total_imported += stats.get('added', 0) + stats.get('updated', 0)
                
            except Exception as e:
                print(f"❌ Error importing {mapping_type} mappings: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Verify migration
        print(f"\n🔍 Verifying migration...")
        
        # Check customer mappings
        customer_mappings = db_service.get_customer_mappings_advanced(source='wholefoods', active_only=True)
        print(f"   Customer mappings: {len(customer_mappings)} active")
        
        # Check item mappings
        item_mappings = db_service.get_item_mappings_advanced(source='wholefoods', active_only=True)
        print(f"   Item mappings: {len(item_mappings)} active")
        
        # Check store mappings
        store_mappings = db_service.get_store_mappings_advanced(source='wholefoods', active_only=True)
        print(f"   Store mappings: {len(store_mappings)} active")
        
        # Migration summary
        print(f"\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Total mappings processed: {total_imported}")
        print(f"Environment: {env}")
        print(f"Timestamp: {pd.Timestamp.now()}")
        
        for mapping_type, stats in migration_summary.items():
            print(f"\n{mapping_type.upper()} MAPPINGS:")
            print(f"  Added: {stats['added']}")
            print(f"  Updated: {stats['updated']}")
            print(f"  Errors: {stats['errors']}")
        
        print(f"\n✅ Migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_migration_backup():
    """Create a backup of current mappings before migration"""
    
    print("Creating migration backup...")
    
    try:
        from datetime import datetime
        import json
        
        db_service = DatabaseService()
        
        # Export current mappings
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'environment': os.getenv('ENVIRONMENT', 'local'),
            'mappings': {}
        }
        
        # Export customer mappings
        customer_mappings = db_service.get_customer_mappings_advanced(source='wholefoods', active_only=False)
        backup_data['mappings']['customer'] = len(customer_mappings)
        
        # Export item mappings
        item_mappings = db_service.get_item_mappings_advanced(source='wholefoods', active_only=False)
        backup_data['mappings']['item'] = len(item_mappings)
        
        # Export store mappings
        store_mappings = db_service.get_store_mappings_advanced(source='wholefoods', active_only=False)
        backup_data['mappings']['store'] = len(store_mappings)
        
        # Save backup info
        backup_file = f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"✓ Backup created: {backup_file}")
        print(f"  Customer mappings: {backup_data['mappings']['customer']}")
        print(f"  Item mappings: {backup_data['mappings']['item']}")
        print(f"  Store mappings: {backup_data['mappings']['store']}")
        
        return backup_file
        
    except Exception as e:
        print(f"❌ Backup creation failed: {e}")
        return None

def main():
    """Main migration function"""
    
    # Check if we should create a backup
    if os.getenv('ENVIRONMENT', 'local') == 'production':
        backup_file = create_migration_backup()
        if not backup_file:
            print("❌ Cannot proceed without backup. Exiting.")
            return False
    
    # Run migration
    success = migrate_wholefoods_mappings()
    
    if success:
        print(f"\n🎉 Migration completed successfully!")
        print(f"\nNext steps:")
        print(f"1. Test the order processor with sample files")
        print(f"2. Monitor the application for any issues")
        print(f"3. Update documentation if needed")
    else:
        print(f"\n❌ Migration failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
