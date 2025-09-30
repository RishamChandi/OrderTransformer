#!/usr/bin/env python3
"""
Script to deploy Kehe mappings to Render server
This script will export the local database mappings and prepare them for deployment
"""

import pandas as pd
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.service import DatabaseService

def export_kehe_mappings_for_render():
    """Export all Kehe mappings to CSV files for Render deployment"""
    
    print("Starting Kehe mapping export for Render deployment...")
    
    # Set environment for local database
    os.environ['ENVIRONMENT'] = 'local'
    os.environ['DATABASE_URL'] = 'sqlite:///orderparser_dev.db'
    
    # Initialize database service
    db_service = DatabaseService()
    
    try:
        # Export item mappings
        print("[INFO] Exporting Kehe item mappings...")
        item_df = db_service.export_item_mappings_to_dataframe(source='kehe')
        
        # Save to CSV for Render deployment
        item_export_file = 'mappings/kehe/render_item_mappings.csv'
        item_df.to_csv(item_export_file, index=False)
        print(f"[SUCCESS] Exported {len(item_df)} item mappings to {item_export_file}")
        
        # Export customer mappings
        print("[INFO] Exporting Kehe customer mappings...")
        customer_df = db_service.export_customer_mappings_to_dataframe(source='kehe')
        
        # Save to CSV for Render deployment
        customer_export_file = 'mappings/kehe/render_customer_mappings.csv'
        customer_df.to_csv(customer_export_file, index=False)
        print(f"[SUCCESS] Exported {len(customer_df)} customer mappings to {customer_export_file}")
        
        # Export store mappings
        print("[INFO] Exporting Kehe store mappings...")
        store_df = db_service.export_store_mappings_to_dataframe(source='kehe')
        
        # Save to CSV for Render deployment
        store_export_file = 'mappings/kehe/render_store_mappings.csv'
        store_df.to_csv(store_export_file, index=False)
        print(f"[SUCCESS] Exported {len(store_df)} store mappings to {store_export_file}")
        
        # Create a summary report
        print("\n" + "="*60)
        print("RENDER DEPLOYMENT SUMMARY")
        print("="*60)
        print(f"Item Mappings: {len(item_df)}")
        print(f"Customer Mappings: {len(customer_df)}")
        print(f"Store Mappings: {len(store_df)}")
        print(f"Total Mappings: {len(item_df) + len(customer_df) + len(store_df)}")
        
        # Verify the critical items are included
        critical_items = ['00387166', '00110380']
        print("\nCritical Item Verification:")
        for item in critical_items:
            if item in item_df['RawKeyValue'].values:
                mapped = item_df[item_df['RawKeyValue'] == item]['MappedItemNumber'].iloc[0]
                print(f"[SUCCESS] {item} -> {mapped}")
            else:
                print(f"[ERROR] {item} NOT FOUND in export!")
        
        print("\nFiles ready for Render deployment:")
        print(f"- {item_export_file}")
        print(f"- {customer_export_file}")
        print(f"- {store_export_file}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Export failed: {str(e)}")
        return False

def create_render_migration_script():
    """Create a script to import Kehe mappings on Render server"""
    
    script_content = '''#!/usr/bin/env python3
"""
Render server script to import Kehe mappings from CSV files
Run this script on the Render server to populate the database with mappings
"""

import pandas as pd
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.service import DatabaseService

def import_kehe_mappings():
    """Import Kehe mappings from CSV files to database"""
    
    print("Starting Kehe mapping import on Render server...")
    
    # Initialize database service (uses Render environment automatically)
    db_service = DatabaseService()
    
    try:
        # Import item mappings
        item_file = 'mappings/kehe/render_item_mappings.csv'
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
        customer_file = 'mappings/kehe/render_customer_mappings.csv'
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
        store_file = 'mappings/kehe/render_store_mappings.csv'
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
        
        print("\\n[SUCCESS] All Kehe mappings imported successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Import failed: {str(e)}")
        return False

if __name__ == '__main__':
    import_kehe_mappings()
'''
    
    script_file = 'render_import_kehe_mappings.py'
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    print(f"[SUCCESS] Created Render import script: {script_file}")
    return script_file

def main():
    """Main function"""
    
    print("Starting Kehe mapping deployment preparation...")
    print("="*60)
    
    # Export mappings for Render
    if export_kehe_mappings_for_render():
        print("\n[SUCCESS] Export completed successfully!")
        
        # Create Render import script
        script_file = create_render_migration_script()
        
        print("\n" + "="*60)
        print("DEPLOYMENT INSTRUCTIONS")
        print("="*60)
        print("1. Commit the exported CSV files to your repository")
        print("2. Deploy to Render server")
        print(f"3. Run the import script on Render: python {script_file}")
        print("4. Verify mappings are working in the web interface")
        
    else:
        print("\n[ERROR] Export failed!")

if __name__ == '__main__':
    main()
