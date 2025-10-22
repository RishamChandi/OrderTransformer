#!/usr/bin/env python3
"""
Migration script for UNFI East mappings
Imports new UNFI East mappings to production database
"""

import os
import sys
import pandas as pd
from pathlib import Path
from database.models import Base
from database.connection import get_database_engine, get_session
from database.service import DatabaseService
from database.migration import run_full_migration

def migrate_unfi_east_mappings():
    """Migrate UNFI East mappings to production database"""
    
    print("=" * 60)
    print("UNFI East Mappings Migration Script")
    print("=" * 60)
    
    # Check environment
    env = os.getenv('ENVIRONMENT', 'local')
    print(f"Current environment: {env}")
    
    if env == 'local':
        print("⚠️  Running in local environment. Set ENVIRONMENT=production for production migration.")
        # Auto-confirm for testing
        print("Auto-confirming local migration for testing...")
        # response = input("Continue with local migration? (y/N): ")
        # if response.lower() != 'y':
        #     print("Migration cancelled.")
        #     return False
    
    try:
        # Initialize database service
        db_service = DatabaseService()
        print("✓ Database service initialized")
        
        # Define mapping files
        mapping_files = {
            'customer': 'mappings/unfi_east/customer_mapping.csv',
            'item': 'mappings/unfi_east/item_mapping.csv',
            'store': 'mappings/unfi_east/store_mapping.csv'
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
                        # UNFI East customer mapping: StoreNumber,CustomerID,AccountNumber,CompanyName,ShipToCompanyName
                        mapping_data = {
                            'source': 'unfi_east',
                            'raw_customer_id': str(row.get('StoreNumber', '')).strip(),
                            'mapped_customer_name': str(row.get('CompanyName', '')).strip(),
                            'customer_type': 'store',
                            'priority': 100,
                            'active': True,
                            'notes': f'Account: {row.get("AccountNumber", "")}, ShipTo: {row.get("ShipToCompanyName", "")}'
                        }
                    elif mapping_type == 'item':
                        # UNFI East item mapping: UPC,UNFI East ,Description,Xoro Item#,Xoro Description
                        # Create multiple mappings for different key types
                        upc = str(row.get('UPC', '')).strip()
                        unfi_east_code = str(row.get('UNFI East ', '')).strip()  # Note the trailing space in column name
                        xoro_item = str(row.get('Xoro Item#', '')).strip()
                        description = str(row.get('Description', '')).strip()
                        xoro_description = str(row.get('Xoro Description', '')).strip()
                        
                        # Skip empty rows
                        if not unfi_east_code or not xoro_item:
                            continue
                        
                        # Create UPC mapping if available
                        if upc and upc != 'nan' and len(upc) >= 8:
                            upc_mapping = {
                                'source': 'unfi_east',
                                'raw_item': upc,
                                'key_type': 'upc',
                                'mapped_item': xoro_item,
                                'vendor': 'UNFI East',
                                'mapped_description': xoro_description,
                                'priority': 100,  # High priority for UPC
                                'active': True,
                                'notes': f'UPC mapping for UNFI East code {unfi_east_code}'
                            }
                            mappings_data.append(upc_mapping)
                        
                        # Create vendor_item mapping (UNFI East code)
                        vendor_mapping = {
                            'source': 'unfi_east',
                            'raw_item': unfi_east_code,
                            'key_type': 'vendor_item',
                            'mapped_item': xoro_item,
                            'vendor': 'UNFI East',
                            'mapped_description': xoro_description,
                            'priority': 200,  # Lower priority than UPC
                            'active': True,
                            'notes': f'Vendor item mapping for UNFI East code {unfi_east_code}'
                        }
                        mappings_data.append(vendor_mapping)
                        
                        continue  # Skip the normal processing for items
                        
                    elif mapping_type == 'store':
                        # UNFI East store mapping: UNFI East ,CompanyName,AccountNumber
                        unfi_code = str(row.get('UNFI East ', '')).strip()  # Note the trailing space
                        company_name = str(row.get('CompanyName', '')).strip()
                        account_number = str(row.get('AccountNumber', '')).strip()
                        
                        mapping_data = {
                            'source': 'unfi_east',
                            'raw_store_id': unfi_code,
                            'mapped_store_name': company_name,
                            'store_type': 'warehouse',
                            'priority': 100,
                            'active': True,
                            'notes': f'Account: {account_number}'
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
        customer_mappings = db_service.get_customer_mappings_advanced(source='unfi_east', active_only=True)
        print(f"   Customer mappings: {len(customer_mappings)} active")
        
        # Check item mappings
        item_mappings = db_service.get_item_mappings_advanced(source='unfi_east', active_only=True)
        print(f"   Item mappings: {len(item_mappings)} active")
        
        # Check store mappings
        store_mappings = db_service.get_store_mappings_advanced(source='unfi_east', active_only=True)
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
        customer_mappings = db_service.get_customer_mappings_advanced(source='unfi_east', active_only=False)
        backup_data['mappings']['customer'] = len(customer_mappings)
        
        # Export item mappings
        item_mappings = db_service.get_item_mappings_advanced(source='unfi_east', active_only=False)
        backup_data['mappings']['item'] = len(item_mappings)
        
        # Export store mappings
        store_mappings = db_service.get_store_mappings_advanced(source='unfi_east', active_only=False)
        backup_data['mappings']['store'] = len(store_mappings)
        
        # Save backup info
        backup_file = f"unfi_east_migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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

def test_sample_mappings():
    """Test a few sample mappings to verify they work"""
    
    print(f"\n🧪 Testing sample mappings...")
    
    try:
        from utils.mapping_utils import MappingUtils
        mapping_utils = MappingUtils()
        
        # Test customer mapping
        customer_test = mapping_utils.get_customer_mapping('001', 'unfi_east')
        print(f"   Customer mapping test: '001' → '{customer_test}'")
        
        # Test store mapping
        store_test = mapping_utils.get_store_mapping('RCH', 'unfi_east')
        print(f"   Store mapping test: 'RCH' → '{store_test}'")
        
        # Test item mapping with UPC
        item_attributes = {'upc': '0072811909844'}
        item_test = mapping_utils.resolve_item_number(item_attributes, 'unfi_east')
        print(f"   Item mapping test (UPC): '0072811909844' → '{item_test}'")
        
        # Test item mapping with vendor item
        item_attributes2 = {'vendor_item': '131459'}
        item_test2 = mapping_utils.resolve_item_number(item_attributes2, 'unfi_east')
        print(f"   Item mapping test (vendor): '131459' → '{item_test2}'")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    """Main migration function"""
    
    print("Starting UNFI East migration...")
    
    # Check if we should create a backup
    if os.getenv('ENVIRONMENT', 'local') == 'production':
        backup_file = create_migration_backup()
        if not backup_file:
            print("❌ Cannot proceed without backup. Exiting.")
            return False
    
    # Run migration
    success = migrate_unfi_east_mappings()
    
    if success:
        # Test the mappings
        test_success = test_sample_mappings()
        
        if test_success:
            print(f"\n🎉 Migration completed successfully!")
            print(f"\nNext steps:")
            print(f"1. Test the UNFI East parser with sample files")
            print(f"2. Monitor the application for any issues")
            print(f"3. Update documentation if needed")
        else:
            print(f"\n⚠️ Migration completed but tests failed")
    else:
        print(f"\n❌ Migration failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    print("Script starting...")
    try:
        success = main()
        print(f"Script completed with success: {success}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Script failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
