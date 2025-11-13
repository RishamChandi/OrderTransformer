"""Script to delete KEHE customer mappings from StoreMapping table"""

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

def delete_kehe_legacy_mappings():
    """Delete KEHE customer mappings from StoreMapping table"""
    
    print("=" * 80)
    print("Deleting KEHE Legacy Customer Mappings from StoreMapping Table")
    print("=" * 80)
    
    try:
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            # Find all KEHE customer mappings in StoreMapping table
            kehe_mappings = session.query(StoreMapping).filter_by(
                source='kehe',
                store_type='customer'
            ).all()
            
            if not kehe_mappings:
                print("\n❌ No KEHE customer mappings found in StoreMapping table")
                return True
            
            print(f"\n✅ Found {len(kehe_mappings)} KEHE customer mapping(s) in StoreMapping table:")
            for i, mapping in enumerate(kehe_mappings, 1):
                print(f"  {i}. ID: {mapping.id}, Raw: '{mapping.raw_store_id}' → Mapped: '{mapping.mapped_store_name}'")
            
            # Confirm deletion (auto-confirm since user requested deletion)
            print(f"\n⚠️  WARNING: Deleting {len(kehe_mappings)} KEHE customer mapping(s) from StoreMapping table")
            print("Auto-confirming deletion as requested...")
            
            # Delete all KEHE customer mappings
            print("\n🗑️  Deleting KEHE customer mappings...")
            deleted_count = 0
            for mapping in kehe_mappings:
                session.delete(mapping)
                deleted_count += 1
                print(f"  ✅ Deleted ID {mapping.id}: {mapping.raw_store_id} → {mapping.mapped_store_name}")
            
            # Commit the deletions
            session.commit()
            print(f"\n✅ Successfully deleted {deleted_count} KEHE customer mapping(s)")
            
            # Verify deletion
            print("\n🔍 Verifying deletion...")
            remaining = session.query(StoreMapping).filter_by(
                source='kehe',
                store_type='customer'
            ).count()
            
            if remaining == 0:
                print("  ✅ All KEHE customer mappings have been deleted from StoreMapping table")
            else:
                print(f"  ⚠️  WARNING: {remaining} mapping(s) still remain")
                
    except Exception as e:
        print(f"\n❌ Error deleting KEHE customer mappings: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = delete_kehe_legacy_mappings()
    sys.exit(0 if success else 1)

