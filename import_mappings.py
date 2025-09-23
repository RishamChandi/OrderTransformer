#!/usr/bin/env python3
import os
import sys
import pandas as pd

# Set environment
os.environ['ENVIRONMENT'] = 'local'
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'

print("Importing Whole Foods mappings...")

try:
    from database.service import DatabaseService
    db_service = DatabaseService()
    print("✓ Database service created")
    
    # Define mapping files
    mapping_files = {
        'customer': 'mappings/wholefoods/Xoro Whole Foods Customer Mapping 9-17-25.csv',
        'item': 'mappings/wholefoods/Xoro Whole Foods Item Mapping 9-17-25.csv',
        'store': 'mappings/wholefoods/Xoro Whole Foods Store Mapping 9-17-25.csv'
    }
    
    total_imported = 0
    
    for mapping_type, file_path in mapping_files.items():
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
            
        try:
            print(f"\nProcessing {mapping_type} mappings from {file_path}")
            
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
            
            print(f"   Imported: {stats.get('added', 0)} new, {stats.get('updated', 0)} updated")
            if stats.get('errors', 0) > 0:
                print(f"   Errors: {stats.get('errors', 0)}")
                for error in stats.get('error_details', [])[:5]:  # Show first 5 errors
                    print(f"      - {error}")
            
            total_imported += stats.get('added', 0) + stats.get('updated', 0)
            
        except Exception as e:
            print(f"Error importing {mapping_type} mappings: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nTotal mappings imported: {total_imported}")
    
    # Verify mappings
    print("\nVerifying imported mappings...")
    
    # Check customer mappings
    customer_mappings = db_service.get_customer_mappings_advanced(source='wholefoods', active_only=True)
    print(f"   Customer mappings: {len(customer_mappings)} active")
    
    # Check item mappings
    item_mappings = db_service.get_item_mappings_advanced(source='wholefoods', active_only=True)
    print(f"   Item mappings: {len(item_mappings)} active")
    
    # Check store mappings
    store_mappings = db_service.get_store_mappings_advanced(source='wholefoods', active_only=True)
    print(f"   Store mappings: {len(store_mappings)} active")
    
    # Show sample mappings
    if customer_mappings:
        print(f"\n   Sample customer mapping: {customer_mappings[0]['raw_customer_id']} -> {customer_mappings[0]['mapped_customer_name']}")
    
    if item_mappings:
        print(f"   Sample item mapping: {item_mappings[0]['raw_item']} -> {item_mappings[0]['mapped_item']}")
    
    if store_mappings:
        print(f"   Sample store mapping: {store_mappings[0]['raw_store_id']} -> {store_mappings[0]['mapped_store_name']}")
    
    print("\n✓ Mapping import completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
