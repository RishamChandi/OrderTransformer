"""Script to delete all KEHE customer mappings from the database"""

import sys
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from database.service import DatabaseService
from database.models import CustomerMapping
from database.connection import get_session

def delete_kehe_customer_mappings():
    """Delete all KEHE customer mappings from the database"""
    
    print("=" * 80)
    print("Deleting KEHE Customer Mappings")
    print("=" * 80)
    
    try:
        db_service = DatabaseService()
        
        # KEHE source name variants
        kehe_sources = [
            'kehe',
            'kehe_sps',
            'kehe___sps',
            'kehe - sps',
            'KEHE - SPS',
            'KEHE',
            'KEHE_SPS'
        ]
        
        deleted_count = 0
        total_mappings = 0
        
        with db_service.get_session() as session:
            # First, count all KEHE customer mappings
            for source in kehe_sources:
                mappings = session.query(CustomerMapping).filter_by(source=source).all()
                count = len(mappings)
                if count > 0:
                    print(f"\nFound {count} customer mappings with source='{source}'")
                    total_mappings += count
                    
                    # Show sample mappings
                    for i, mapping in enumerate(mappings[:5]):  # Show first 5
                        print(f"  {i+1}. {mapping.raw_customer_id} → {mapping.mapped_customer_name}")
                    if count > 5:
                        print(f"  ... and {count - 5} more")
            
            if total_mappings == 0:
                print("\n❌ No KEHE customer mappings found in the database")
                return
            
            # Ask for confirmation
            print(f"\n⚠️  WARNING: This will delete {total_mappings} KEHE customer mapping(s)")
            print("Press Enter to continue or Ctrl+C to cancel...")
            try:
                input()
            except KeyboardInterrupt:
                print("\n❌ Deletion cancelled by user")
                return
            
            # Delete all KEHE customer mappings
            print("\n🗑️  Deleting KEHE customer mappings...")
            for source in kehe_sources:
                mappings = session.query(CustomerMapping).filter_by(source=source).all()
                if mappings:
                    for mapping in mappings:
                        session.delete(mapping)
                        deleted_count += 1
                    print(f"  ✅ Deleted {len(mappings)} mapping(s) with source='{source}'")
            
            # Commit the deletions
            session.commit()
            print(f"\n✅ Successfully deleted {deleted_count} KEHE customer mapping(s)")
            
            # Verify deletion
            print("\n🔍 Verifying deletion...")
            remaining_count = 0
            for source in kehe_sources:
                remaining = session.query(CustomerMapping).filter_by(source=source).count()
                if remaining > 0:
                    print(f"  ⚠️  WARNING: {remaining} mapping(s) still exist with source='{source}'")
                    remaining_count += remaining
            
            if remaining_count == 0:
                print("  ✅ All KEHE customer mappings have been deleted")
            else:
                print(f"  ⚠️  {remaining_count} mapping(s) still remain (may be case-sensitive)")
                
    except Exception as e:
        print(f"\n❌ Error deleting KEHE customer mappings: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = delete_kehe_customer_mappings()
    sys.exit(0 if success else 1)

