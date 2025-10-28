#!/usr/bin/env python3
"""
KEHE CSV to Database Migration Script
Migrates existing KEHE item mappings from CSV format to new database template system
"""

import pandas as pd
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path dynamically
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.service import DatabaseService
from database.connection import get_session

def load_existing_kehe_mappings(csv_path: str) -> pd.DataFrame:
    """Load existing KEHE CSV mappings"""
    
    try:
        print(f"📂 Loading KEHE mappings from: {csv_path}")
        
        # Read CSV with proper data types
        df = pd.read_csv(csv_path, dtype=str)
        
        print(f"✅ Loaded {len(df)} rows")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Show sample data
        print("\n📝 Sample mappings:")
        for i, row in df.head(3).iterrows():
            print(f"  {row['KeHE Number']} → {row['ItemNumber']} ({row['Description'][:50]}...)")
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        raise

def convert_to_database_format(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert CSV data to new database template format"""
    
    mappings_data = []
    seen_combinations = set()  # Track unique (key_type, raw_item) combinations
    
    print(f"\n🔄 Converting {len(df)} CSV rows to database format...")
    
    # Remove duplicates based on KeHE Number, keeping first occurrence
    df_deduped = df.drop_duplicates(subset=['KeHE Number'], keep='first')
    print(f"📋 Removed {len(df) - len(df_deduped)} duplicate KeHE Numbers")
    
    for index, row in df_deduped.iterrows():
        kehe_number = str(row['KeHE Number']).strip()
        item_number = str(row['ItemNumber']).strip()
        description = str(row['Description']).strip() if pd.notna(row['Description']) else None
        upc = str(row['UPC']).strip() if pd.notna(row['UPC']) and str(row['UPC']).strip() != 'nan' else None
        
        # Skip empty rows
        if not kehe_number or not item_number:
            print(f"⚠️ Skipping empty row {index + 1}")
            continue
        
        # Create vendor_item mapping (primary)
        vendor_key = ('vendor_item', kehe_number)
        if vendor_key not in seen_combinations:
            vendor_mapping = {
                'source': 'kehe',
                'raw_item': kehe_number,
                'mapped_item': item_number,
                'key_type': 'vendor_item',
                'priority': 100,  # High priority for vendor_item
                'active': True,
                'vendor': 'KEHE',
                'mapped_description': description,
                'notes': f'Migrated from CSV - Primary vendor mapping'
            }
            mappings_data.append(vendor_mapping)
            seen_combinations.add(vendor_key)
        
        # Create UPC mapping if available (backup)
        if upc and len(upc) >= 8:  # Valid UPC should be at least 8 digits
            upc_key = ('upc', upc)
            if upc_key not in seen_combinations:
                upc_mapping = {
                    'source': 'kehe',
                    'raw_item': upc,
                    'mapped_item': item_number,
                    'key_type': 'upc',
                    'priority': 200,  # Lower priority for UPC backup
                    'active': True,
                    'vendor': 'KEHE',
                    'mapped_description': description,
                    'notes': f'Migrated from CSV - UPC backup for {kehe_number}'
                }
                mappings_data.append(upc_mapping)
                seen_combinations.add(upc_key)
    
    print(f"✅ Converted to {len(mappings_data)} database mappings")
    print(f"   📦 Vendor mappings: {len([m for m in mappings_data if m['key_type'] == 'vendor_item'])}")
    print(f"   🏷️ UPC mappings: {len([m for m in mappings_data if m['key_type'] == 'upc'])}")
    
    return mappings_data

def migrate_to_database(mappings_data: List[Dict[str, Any]]) -> bool:
    """Migrate mappings to database using DatabaseService"""
    
    try:
        print(f"\n💾 Migrating {len(mappings_data)} mappings to database...")
        
        db_service = DatabaseService()
        
        # Use bulk upsert to handle duplicates gracefully
        results = db_service.bulk_upsert_item_mappings(mappings_data)
        
        # Report results
        print(f"\n📊 Migration Results:")
        print(f"   ➕ Added: {results['added']}")
        print(f"   🔄 Updated: {results['updated']}")  
        print(f"   ❌ Errors: {results['errors']}")
        
        if results['errors'] > 0:
            print(f"\n⚠️ Error Details:")
            for error in results['error_details'][:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(results['error_details']) > 5:
                print(f"   ... and {len(results['error_details']) - 5} more errors")
        
        # Verify migration
        with get_session() as session:
            kehe_count = session.query(db_service.ItemMapping).filter_by(source='kehe').count()
            print(f"\n✅ Verification: {kehe_count} KEHE mappings now in database")
        
        # Consider migration successful if most mappings were processed
        success_rate = (results['added'] + results['updated']) / len(mappings_data) if mappings_data else 0
        return success_rate >= 0.9  # 90% success rate
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def test_sample_mappings(db_service: DatabaseService) -> bool:
    """Test a few sample mappings to verify they work"""
    
    print(f"\n🧪 Testing sample mappings...")
    
    # Test cases from the CSV
    test_cases = [
        ("00110368", "vendor_item", "17-041-1"),  # First row
        ("728119098687", "upc", "17-041-1"),     # UPC from first row
        ("02313478", "vendor_item", "12-006-2"),  # Second row
        ("00308376", "vendor_item", "8-400-1"),   # Third row
    ]
    
    all_passed = True
    
    for raw_value, key_type, expected_mapped in test_cases:
        try:
            # Test using the resolve_item_number method
            from utils.mapping_utils import MappingUtils
            mapping_utils = MappingUtils()
            
            # Use correct method signature: item_attributes dict
            item_attributes = {key_type: raw_value}
            resolved = mapping_utils.resolve_item_number(
                item_attributes=item_attributes,
                source='kehe'
            )
            
            if resolved == expected_mapped:
                print(f"   ✅ {key_type} {raw_value} → {resolved}")
            else:
                print(f"   ❌ {key_type} {raw_value} → {resolved} (expected {expected_mapped})")
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ {key_type} {raw_value} → ERROR: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Main migration function"""
    
    print("🚀 KEHE CSV to Database Migration")
    print("=" * 50)
    
    # Path to existing CSV file (relative to project root)
    csv_path = project_root / "mappings" / "kehe_item_mapping.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return False
    
    try:
        # Step 1: Load existing CSV
        df = load_existing_kehe_mappings(csv_path)
        
        # Step 2: Convert to database format
        mappings_data = convert_to_database_format(df)
        
        # Step 3: Migrate to database
        success = migrate_to_database(mappings_data)
        
        if success:
            # Step 4: Test sample mappings
            db_service = DatabaseService()
            test_success = test_sample_mappings(db_service)
            
            if test_success:
                print(f"\n🎉 Migration completed successfully!")
                print(f"   📦 {len(mappings_data)} mappings migrated")
                print(f"   ✅ All tests passed")
                return True
            else:
                print(f"\n⚠️ Migration completed but some tests failed")
                return False
        else:
            print(f"\n❌ Migration failed")
            return False
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)