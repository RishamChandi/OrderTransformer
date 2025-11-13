"""Script to check KEHE mappings in StoreMapping table"""

import sys
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from database.service import DatabaseService
from database.models import StoreMapping
from database.connection import get_session

def check_kehe_store_mappings():
    """Check for KEHE mappings in StoreMapping table"""
    
    print("=" * 80)
    print("Checking KEHE Store Mappings")
    print("=" * 80)
    
    try:
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            # Check all store mappings
            all_store_mappings = session.query(StoreMapping).all()
            
            if not all_store_mappings:
                print("\n❌ No store mappings found in the database")
                return
            
            # Group by source
            from collections import defaultdict
            mappings_by_source = defaultdict(list)
            for mapping in all_store_mappings:
                mappings_by_source[mapping.source].append(mapping)
            
            print(f"\n✅ Found {len(all_store_mappings)} total store mapping(s) across {len(mappings_by_source)} source(s)\n")
            
            # Check for KEHE-related sources
            kehe_sources = []
            kehe_customer_mappings = []
            
            for source, mappings in mappings_by_source.items():
                if 'kehe' in source.lower():
                    kehe_sources.append(source)
                    # Check for customer type mappings
                    for mapping in mappings:
                        if mapping.store_type == 'customer':
                            kehe_customer_mappings.append(mapping)
            
            if kehe_sources:
                print(f"✅ Found {len(kehe_sources)} KEHE-related source(s):")
                for source in kehe_sources:
                    count = len(mappings_by_source[source])
                    customer_count = len([m for m in mappings_by_source[source] if m.store_type == 'customer'])
                    print(f"  - '{source}': {count} mapping(s) ({customer_count} customer type)")
                    
                    # Show customer mappings
                    if customer_count > 0:
                        print(f"\n    Customer Mappings for '{source}':")
                        for mapping in mappings_by_source[source]:
                            if mapping.store_type == 'customer':
                                print(f"      ID: {mapping.id}, Raw: '{mapping.raw_store_id}' → Mapped: '{mapping.mapped_store_name}'")
            else:
                print("\n❌ No KEHE-related sources found in StoreMapping table")
                print("\nAvailable sources:")
                for source in sorted(mappings_by_source.keys()):
                    count = len(mappings_by_source[source])
                    customer_count = len([m for m in mappings_by_source[source] if m.store_type == 'customer'])
                    print(f"  - '{source}': {count} mapping(s) ({customer_count} customer type)")
            
            # Show all KEHE customer mappings if found
            if kehe_customer_mappings:
                print(f"\n" + "=" * 80)
                print(f"Found {len(kehe_customer_mappings)} KEHE customer mappings in StoreMapping table")
                print("=" * 80)
                for mapping in kehe_customer_mappings:
                    print(f"  ID: {mapping.id}, Source: '{mapping.source}', Raw: '{mapping.raw_store_id}' → Mapped: '{mapping.mapped_store_name}'")
                
    except Exception as e:
        print(f"\n❌ Error checking store mappings: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = check_kehe_store_mappings()
    sys.exit(0 if success else 1)

