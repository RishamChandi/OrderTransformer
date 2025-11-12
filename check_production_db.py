"""
Diagnostic script to check production database structure and data
for customer mappings to identify why delete doesn't work
"""
import os
import sys

# Set environment to production to connect to production DB
os.environ['ENVIRONMENT'] = 'production'

from database.service import DatabaseService
from database.models import CustomerMapping, StoreMapping
from sqlalchemy import inspect

def check_database_structure(db_service):
    """Check if customer_mappings table exists and has correct structure"""
    print("=" * 80)
    print("DATABASE STRUCTURE CHECK")
    print("=" * 80)
    
    with db_service.get_session() as session:
        inspector = inspect(session.bind)
        
        # Check if customer_mappings table exists
        tables = inspector.get_table_names()
        print(f"\n📊 Available tables: {', '.join(tables)}")
        
        if 'customer_mappings' in tables:
            print("✅ customer_mappings table EXISTS")
            
            # Get column info
            columns = inspector.get_columns('customer_mappings')
            print(f"\n📋 customer_mappings columns:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']} (nullable={col['nullable']})")
        else:
            print("❌ customer_mappings table DOES NOT EXIST")
        
        if 'store_mappings' in tables:
            print("\n✅ store_mappings table EXISTS")
            
            # Check for customer type in store_mappings
            columns = inspector.get_columns('store_mappings')
            print(f"\n📋 store_mappings columns:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']} (nullable={col['nullable']})")

def check_kehe_customer_mappings(db_service):
    """Check KEHE customer mappings in both tables"""
    print("\n" + "=" * 80)
    print("KEHE CUSTOMER MAPPINGS DATA CHECK")
    print("=" * 80)
    
    with db_service.get_session() as session:
        # Check CustomerMapping table
        print("\n1️⃣ Checking CustomerMapping table:")
        customer_mappings = session.query(CustomerMapping).filter(
            CustomerMapping.source.in_(['kehe', 'kehe_sps', 'kehe___sps', 'KEHE - SPS'])
        ).all()
        
        print(f"   Found {len(customer_mappings)} customer mappings in CustomerMapping table")
        if customer_mappings:
            print("   Sample records:")
            for i, cm in enumerate(customer_mappings[:5]):
                print(f"     {i+1}. ID={cm.id}, source='{cm.source}', raw='{cm.raw_customer_id}', mapped='{cm.mapped_customer_name}'")
        
        # Check StoreMapping table for customer type
        print("\n2️⃣ Checking StoreMapping table (store_type='customer'):")
        store_customer_mappings = session.query(StoreMapping).filter(
            StoreMapping.source.in_(['kehe', 'kehe_sps', 'kehe___sps', 'KEHE - SPS']),
            StoreMapping.store_type == 'customer'
        ).all()
        
        print(f"   Found {len(store_customer_mappings)} customer mappings in StoreMapping table")
        if store_customer_mappings:
            print("   Sample records:")
            for i, sm in enumerate(store_customer_mappings[:5]):
                print(f"     {i+1}. ID={sm.id}, source='{sm.source}', raw='{sm.raw_store_id}', mapped='{sm.mapped_store_name}'")
        
        # Check all KEHE sources
        print("\n3️⃣ All KEHE source variations found:")
        all_kehe_sources_customer = session.query(CustomerMapping.source).filter(
            CustomerMapping.source.like('%kehe%')
        ).distinct().all()
        print(f"   In CustomerMapping: {[s[0] for s in all_kehe_sources_customer]}")
        
        all_kehe_sources_store = session.query(StoreMapping.source).filter(
            StoreMapping.source.like('%kehe%'),
            StoreMapping.store_type == 'customer'
        ).distinct().all()
        print(f"   In StoreMapping (customer type): {[s[0] for s in all_kehe_sources_store]}")

def test_migration(db_service):
    """Test if migration would work"""
    print("\n" + "=" * 80)
    print("MIGRATION TEST")
    print("=" * 80)
    
    stats = db_service.migrate_legacy_customer_mappings('kehe')
    print(f"\n📊 Migration results: {stats}")
    
    if stats['migrated'] > 0 or stats['updated'] > 0:
        print("✅ Migration found and moved legacy mappings")
    else:
        print("ℹ️ No legacy mappings found to migrate")

def main():
    print("🔍 PRODUCTION DATABASE DIAGNOSTIC")
    print("=" * 80)
    
    try:
        db_service = DatabaseService()
        
        # Check structure
        check_database_structure(db_service)
        
        # Check data
        check_kehe_customer_mappings(db_service)
        
        # Test migration
        test_migration(db_service)
        
        print("\n" + "=" * 80)
        print("✅ DIAGNOSTIC COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

