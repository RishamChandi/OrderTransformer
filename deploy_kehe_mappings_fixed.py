#!/usr/bin/env python3
"""
Deploy fixed Kehe mappings to Render server
This script creates the necessary files for deploying Kehe mappings without duplicates
"""

import os
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.service import DatabaseService
from database.connection import get_session

def deploy_kehe_mappings_fixed():
    print("Deploying Fixed Kehe Mappings to Render")
    print("=" * 50)
    
    try:
        # Set up database connection
        os.environ['DATABASE_URL'] = 'sqlite:///orderparser_dev.db'
        db_service = DatabaseService()
        
        # Export item mappings (using deduplicated data)
        print("Exporting item mappings...")
        item_mappings = db_service.get_item_mappings_advanced(source='kehe', active_only=True)
        
        if item_mappings:
            item_df = pd.DataFrame(item_mappings)
            item_df = item_df[['source', 'raw_item', 'key_type', 'mapped_item', 'vendor', 'mapped_description', 'priority', 'active', 'notes']]
            item_df.columns = ['Source', 'RawKeyValue', 'RawKeyType', 'MappedItemNumber', 'Vendor', 'MappedDescription', 'Priority', 'Active', 'Notes']
            
            # Save to render format
            render_item_path = "mappings/kehe/render_item_mappings_fixed.csv"
            item_df.to_csv(render_item_path, index=False)
            print(f"Exported {len(item_df)} item mappings to {render_item_path}")
        else:
            print("No item mappings found for Kehe")
        
        # Export customer mappings
        print("Exporting customer mappings...")
        customer_mappings = db_service.get_customer_mappings_advanced(source='kehe', active_only=True)
        
        if customer_mappings:
            customer_df = pd.DataFrame(customer_mappings)
            customer_df = customer_df[['source', 'raw_customer_id', 'mapped_customer_name', 'priority', 'active', 'notes']]
            customer_df.columns = ['Source', 'RawKeyValue', 'MappedCustomer', 'Priority', 'Active', 'Notes']
            
            # Save to render format
            render_customer_path = "mappings/kehe/render_customer_mappings_fixed.csv"
            customer_df.to_csv(render_customer_path, index=False)
            print(f"Exported {len(customer_df)} customer mappings to {render_customer_path}")
        else:
            print("No customer mappings found for Kehe")
        
        # Export store mappings
        print("Exporting store mappings...")
        store_mappings = db_service.get_store_mappings_advanced(source='kehe', active_only=True)
        
        if store_mappings:
            store_df = pd.DataFrame(store_mappings)
            store_df = store_df[['source', 'raw_store_id', 'mapped_store_name', 'priority', 'active', 'notes']]
            store_df.columns = ['Source', 'RawKeyValue', 'MappedStore', 'Priority', 'Active', 'Notes']
            
            # Save to render format
            render_store_path = "mappings/kehe/render_store_mappings_fixed.csv"
            store_df.to_csv(render_store_path, index=False)
            print(f"Exported {len(store_df)} store mappings to {render_store_path}")
        else:
            print("No store mappings found for Kehe")
        
        # Create the import script for Render
        import_script_content = '''#!/usr/bin/env python3
"""
Import Kehe mappings to Render database
"""

import os
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.service import DatabaseService

def import_kehe_mappings_fixed():
    print("Starting Kehe mapping import on Render server...")
    
    try:
        # Import item mappings
        item_csv_path = "mappings/kehe/render_item_mappings_fixed.csv"
        if os.path.exists(item_csv_path):
            print(f"[INFO] Importing item mappings from {item_csv_path}...")
            
            df = pd.read_csv(item_csv_path)
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
            
            db_service = DatabaseService()
            results = db_service.bulk_upsert_item_mappings(mappings_data)
            
            print(f"[SUCCESS] Item mappings: {results['added']} added, {results['updated']} updated, {results['errors']} errors")
            
            if results['errors'] > 0:
                print(f"[WARNING] {results['errors']} errors occurred during item mapping import")
                for error in results['error_details'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
        else:
            print(f"[WARNING] Item mappings file not found: {item_csv_path}")
        
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
    success = import_kehe_mappings_fixed()
    sys.exit(0 if success else 1)
'''
        
        # Save the import script
        import_script_path = "render_import_kehe_mappings_fixed.py"
        with open(import_script_path, 'w', encoding='utf-8') as f:
            f.write(import_script_content)
        
        print(f"Created import script: {import_script_path}")
        
        print("\nDeployment files created:")
        print(f"  - {render_item_path}")
        print(f"  - {render_customer_path}")
        print(f"  - {render_store_path}")
        print(f"  - {import_script_path}")
        
        print("\nTo deploy to Render:")
        print("1. Upload the CSV files to the mappings/kehe/ directory on Render")
        print("2. Upload the import script to the root directory on Render")
        print("3. Run: python render_import_kehe_mappings_fixed.py")
        
        return True
        
    except Exception as e:
        print(f"Deployment preparation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = deploy_kehe_mappings_fixed()
    sys.exit(0 if success else 1)
