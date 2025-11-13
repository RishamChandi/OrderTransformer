"""Script to list all customer mappings in the database"""

import sys
import os
from collections import defaultdict

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from database.service import DatabaseService
from database.models import CustomerMapping
from database.connection import get_session

def list_all_customer_mappings():
    """List all customer mappings in the database"""
    
    print("=" * 80)
    print("Listing All Customer Mappings")
    print("=" * 80)
    
    try:
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            # Get all customer mappings
            all_mappings = session.query(CustomerMapping).all()
            
            if not all_mappings:
                print("\n❌ No customer mappings found in the database")
                return
            
            # Group by source
            mappings_by_source = defaultdict(list)
            for mapping in all_mappings:
                mappings_by_source[mapping.source].append(mapping)
            
            print(f"\n✅ Found {len(all_mappings)} total customer mapping(s) across {len(mappings_by_source)} source(s)\n")
            
            # List mappings by source
            for source, mappings in sorted(mappings_by_source.items()):
                print(f"Source: '{source}' ({len(mappings)} mapping(s))")
                print("-" * 80)
                
                # Show first 10 mappings
                for i, mapping in enumerate(mappings[:10]):
                    print(f"  {i+1}. ID: {mapping.id}, Raw: '{mapping.raw_customer_id}' → Mapped: '{mapping.mapped_customer_name}'")
                
                if len(mappings) > 10:
                    print(f"  ... and {len(mappings) - 10} more")
                print()
            
            # Check for KEHE-related sources
            print("\n" + "=" * 80)
            print("KEHE Source Analysis")
            print("=" * 80)
            
            kehe_sources = []
            for source in mappings_by_source.keys():
                if 'kehe' in source.lower():
                    kehe_sources.append(source)
            
            if kehe_sources:
                print(f"\n✅ Found {len(kehe_sources)} KEHE-related source(s):")
                for source in kehe_sources:
                    count = len(mappings_by_source[source])
                    print(f"  - '{source}': {count} mapping(s)")
            else:
                print("\n❌ No KEHE-related sources found")
                print("Available sources:")
                for source in sorted(mappings_by_source.keys()):
                    print(f"  - '{source}'")
                
    except Exception as e:
        print(f"\n❌ Error listing customer mappings: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = list_all_customer_mappings()
    sys.exit(0 if success else 1)

