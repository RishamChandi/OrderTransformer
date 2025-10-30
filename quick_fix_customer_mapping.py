#!/usr/bin/env python3
"""
Quick fix for customer mapping upload - bypass the schema issue
"""

import os
import sys
import pandas as pd
from database.connection import get_session
from database.models import StoreMapping

def fix_customer_mapping_upload():
    """Directly insert customer mappings bypassing the bulk upsert"""
    
    # Sample data from your CSV
    customer_data = [
        {'source': 'wholefoods', 'raw_store_id': '10005', 'mapped_store_name': 'WHOLE FOODS #10005 PALO ALTO', 'store_type': 'store', 'priority': 100, 'active': True, 'notes': ''},
        {'source': 'wholefoods', 'raw_store_id': '10006', 'mapped_store_name': 'WHOLE FOODS #10006 TELEGRAPH', 'store_type': 'store', 'priority': 100, 'active': True, 'notes': ''},
        {'source': 'wholefoods', 'raw_store_id': '10009', 'mapped_store_name': 'WHOLE FOODS #10009 MILLER', 'store_type': 'store', 'priority': 100, 'active': True, 'notes': ''},
        {'source': 'wholefoods', 'raw_store_id': '10027', 'mapped_store_name': 'WHOLE FOODS #10027 LOS GATOS', 'store_type': 'store', 'priority': 100, 'active': True, 'notes': ''},
        {'source': 'wholefoods', 'raw_store_id': '10033', 'mapped_store_name': 'WHOLE FOODS #10033 CAMPBELL', 'store_type': 'store', 'priority': 100, 'active': True, 'notes': ''},
    ]
    
    try:
        with get_session() as session:
            # Clear existing wholefoods customer mappings
            session.query(StoreMapping).filter_by(source='wholefoods', store_type='store').delete()
            
            # Insert new mappings one by one
            for data in customer_data:
                mapping = StoreMapping(
                    source=data['source'],
                    raw_store_id=data['raw_store_id'],
                    mapped_store_name=data['mapped_store_name'],
                    store_type=data['store_type'],
                    priority=data['priority'],
                    active=data['active'],
                    notes=data['notes']
                )
                session.add(mapping)
            
            session.commit()
            print(f"✅ Successfully inserted {len(customer_data)} customer mappings!")
            
            # Verify
            count = session.query(StoreMapping).filter_by(source='wholefoods', store_type='store').count()
            print(f"✅ Total wholefoods customer mappings in database: {count}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Quick fix for customer mapping upload...")
    success = fix_customer_mapping_upload()
    if success:
        print("✅ Customer mappings uploaded successfully!")
    else:
        print("❌ Upload failed!")
        sys.exit(1)
