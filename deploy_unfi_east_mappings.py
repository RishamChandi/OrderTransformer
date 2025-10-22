#!/usr/bin/env python3
"""
Deploy UNFI East mappings to Render production environment
This script is designed to be run on Render after deployment
"""

import os
import sys
import pandas as pd
from pathlib import Path
from database.service import DatabaseService

def deploy_unfi_east_mappings():
    """Deploy UNFI East mappings to Render production database"""
    
    print("=" * 60)
    print("UNFI East Mappings Deployment to Render")
    print("=" * 60)
    
    # Check if we're in production environment
    env = os.getenv('ENVIRONMENT', 'local')
    if env != 'production':
        print(f"⚠️  Current environment: {env}")
        print("This script is designed for production deployment on Render")
        return False
    
    try:
        # Initialize database service
        db_service = DatabaseService()
        print("✓ Database service initialized")
        
        # Define mapping data (embedded in script for Render deployment)
        mapping_data = {
            'customer': [
                {'StoreNumber': '001', 'CustomerID': 'UE001', 'AccountNumber': 'ACC001', 'CompanyName': 'UNFI EAST CUSTOMER 1', 'ShipToCompanyName': 'UNFI EAST STORE 1'},
                {'StoreNumber': '002', 'CustomerID': 'UE002', 'AccountNumber': 'ACC002', 'CompanyName': 'UNFI EAST CUSTOMER 2', 'ShipToCompanyName': 'UNFI EAST STORE 2'},
                {'StoreNumber': '003', 'CustomerID': 'UE003', 'AccountNumber': 'ACC003', 'CompanyName': 'UNFI EAST CUSTOMER 3', 'ShipToCompanyName': 'UNFI EAST STORE 3'},
            ],
            'store': [
                {'UNFI East ': 'RCH', 'CompanyName': 'UNFI EAST - RICHBURG', 'AccountNumber': '4609'},
                {'UNFI East ': 'HOW', 'CompanyName': 'UNFI EAST - HOWELL', 'AccountNumber': '4610'},
                {'UNFI East ': 'CHE', 'CompanyName': 'UNFI EAST CHESTERFIELD', 'AccountNumber': '5099'},
                {'UNFI East ': 'YOR', 'CompanyName': 'UNFI EAST YORK PA', 'AccountNumber': '5102'},
                {'UNFI East ': 'IOW', 'CompanyName': 'UNFI EAST IOWA CITY', 'AccountNumber': '5150'},
                {'UNFI East ': 'DAY', 'CompanyName': 'UNFI EAST DAYVILLE CT', 'AccountNumber': '5155'},
                {'UNFI East ': 'GRW', 'CompanyName': 'UNFI EAST GREENWOOD IN', 'AccountNumber': '5156'},
                {'UNFI East ': 'ATL', 'CompanyName': 'UNFI EAST ATLANTA GA', 'AccountNumber': '5168'},
                {'UNFI East ': 'SAR', 'CompanyName': 'UNFI EAST SARASOTA FL', 'AccountNumber': '5175'},
                {'UNFI East ': 'HVA', 'CompanyName': 'UNFI EAST - HUDSON VALLEY WSHE', 'AccountNumber': '5178'},
                {'UNFI East ': 'RAC', 'CompanyName': 'UNFI EAST - RACINE WAREHOUSE', 'AccountNumber': '5200'},
                {'UNFI East ': 'TWC', 'CompanyName': 'UNFI EAST PRESCOTT WI', 'AccountNumber': '5235'},
                {'UNFI East ': 'MAN', 'CompanyName': 'UNFI EAST MANCHESTER', 'AccountNumber': '5760'},
                {'UNFI East ': 'SRQ', 'CompanyName': 'UNFI EAST SARASOTA FL', 'AccountNumber': '5780'},
            ],
            'item': [
                # Sample item mappings - in production, this would be loaded from a file or database
                {'UPC': '0072811909844', 'UNFI East ': '131459', 'Description': 'PESTO,GENOVESE', 'Xoro Item#': '17-001-1', 'Xoro Description': 'C&A Basil Genovese Pesto Sauce 6/7.9oz'},
                {'UPC': '0072811909846', 'UNFI East ': '131460', 'Description': 'PESTO,ARTICHOKE', 'Xoro Item#': '17-001-2', 'Xoro Description': 'C&A Artichoke Lemon Pesto Sauce 6/7.9oz'},
                {'UPC': '0072811909849', 'UNFI East ': '131461', 'Description': 'PESTO,SUNDRIED TOMATO', 'Xoro Item#': '17-001-4', 'Xoro Description': 'C&A Sun-Dried Tomato Pesto 6/7.9oz'},
                # Add more items as needed
            ]
        }
        
        total_imported = 0
        deployment_summary = {}
        
        for mapping_type, data in mapping_data.items():
            try:
                print(f"\n📄 Processing {mapping_type} mappings...")
                
                # Convert to list of dictionaries for bulk import
                mappings_data = []
                for row in data:
                    mapping_data = {}
                    
                    if mapping_type == 'customer':
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
                        upc = str(row.get('UPC', '')).strip()
                        unfi_east_code = str(row.get('UNFI East ', '')).strip()
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
                                'priority': 100,
                                'active': True,
                                'notes': f'UPC mapping for UNFI East code {unfi_east_code}'
                            }
                            mappings_data.append(upc_mapping)
                        
                        # Create vendor_item mapping
                        vendor_mapping = {
                            'source': 'unfi_east',
                            'raw_item': unfi_east_code,
                            'key_type': 'vendor_item',
                            'mapped_item': xoro_item,
                            'vendor': 'UNFI East',
                            'mapped_description': xoro_description,
                            'priority': 200,
                            'active': True,
                            'notes': f'Vendor item mapping for UNFI East code {unfi_east_code}'
                        }
                        mappings_data.append(vendor_mapping)
                        
                        continue  # Skip the normal processing for items
                        
                    elif mapping_type == 'store':
                        unfi_code = str(row.get('UNFI East ', '')).strip()
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
                    for error in stats.get('error_details', [])[:3]:  # Show first 3 errors
                        print(f"      - {error}")
                
                deployment_summary[mapping_type] = {
                    'added': stats.get('added', 0),
                    'updated': stats.get('updated', 0),
                    'errors': stats.get('errors', 0)
                }
                
                total_imported += stats.get('added', 0) + stats.get('updated', 0)
                
            except Exception as e:
                print(f"❌ Error importing {mapping_type} mappings: {e}")
                return False
        
        # Verify deployment
        print(f"\n🔍 Verifying deployment...")
        
        # Check customer mappings
        customer_mappings = db_service.get_customer_mappings_advanced(source='unfi_east', active_only=True)
        print(f"   Customer mappings: {len(customer_mappings)} active")
        
        # Check item mappings
        item_mappings = db_service.get_item_mappings_advanced(source='unfi_east', active_only=True)
        print(f"   Item mappings: {len(item_mappings)} active")
        
        # Check store mappings
        store_mappings = db_service.get_store_mappings_advanced(source='unfi_east', active_only=True)
        print(f"   Store mappings: {len(store_mappings)} active")
        
        # Deployment summary
        print(f"\n" + "=" * 60)
        print("DEPLOYMENT SUMMARY")
        print("=" * 60)
        print(f"Total mappings processed: {total_imported}")
        print(f"Environment: {env}")
        print(f"Timestamp: {pd.Timestamp.now()}")
        
        for mapping_type, stats in deployment_summary.items():
            print(f"\n{mapping_type.upper()} MAPPINGS:")
            print(f"  Added: {stats['added']}")
            print(f"  Updated: {stats['updated']}")
            print(f"  Errors: {stats['errors']}")
        
        print(f"\n✅ UNFI East mappings deployed successfully to Render!")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main deployment function"""
    
    print("🚀 Deploying UNFI East mappings to Render production...")
    
    success = deploy_unfi_east_mappings()
    
    if success:
        print(f"\n🎉 Deployment completed successfully!")
        print(f"\nUNFI East mappings are now available in production.")
    else:
        print(f"\n❌ Deployment failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
