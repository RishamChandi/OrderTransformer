"""
Diagnostic script to check production database structure and data
for customer mappings to identify issues with KEHE and UNFI East
"""
import os
import sys

# Set environment to production to connect to production DB
# This will use DATABASE_URL from environment variables
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

def check_customer_mappings_for_source(db_service, source_name, source_variations):
    """Check customer mappings for a specific source"""
    print("\n" + "=" * 80)
    print(f"{source_name.upper()} CUSTOMER MAPPINGS DATA CHECK")
    print("=" * 80)
    
    with db_service.get_session() as session:
        # Check CustomerMapping table
        print(f"\n1️⃣ Checking CustomerMapping table for {source_name}:")
        customer_mappings = session.query(CustomerMapping).filter(
            CustomerMapping.source.in_(source_variations)
        ).all()
        
        print(f"   Found {len(customer_mappings)} customer mappings in CustomerMapping table")
        if customer_mappings:
            print("   Sample records:")
            for i, cm in enumerate(customer_mappings[:10]):
                print(f"     {i+1}. ID={cm.id}, source='{cm.source}', raw='{cm.raw_customer_id}', mapped='{cm.mapped_customer_name}', type='{cm.customer_type}', active={cm.active}")
        else:
            print("   ⚠️ NO CUSTOMER MAPPINGS FOUND in CustomerMapping table!")
        
        # Check StoreMapping table for customer type (legacy data)
        print(f"\n2️⃣ Checking StoreMapping table (store_type='customer') for {source_name}:")
        store_customer_mappings = session.query(StoreMapping).filter(
            StoreMapping.source.in_(source_variations),
            StoreMapping.store_type == 'customer'
        ).all()
        
        print(f"   Found {len(store_customer_mappings)} customer mappings in StoreMapping table (LEGACY)")
        if store_customer_mappings:
            print("   Sample records:")
            for i, sm in enumerate(store_customer_mappings[:10]):
                print(f"     {i+1}. ID={sm.id}, source='{sm.source}', raw='{sm.raw_store_id}', mapped='{sm.mapped_store_name}', type='{sm.store_type}', active={sm.active}")
        
        # Check all source variations found
        print(f"\n3️⃣ All {source_name} source variations found:")
        all_sources_customer = session.query(CustomerMapping.source).filter(
            CustomerMapping.source.in_(source_variations)
        ).distinct().all()
        print(f"   In CustomerMapping: {[s[0] for s in all_sources_customer]}")
        
        all_sources_store = session.query(StoreMapping.source).filter(
            StoreMapping.source.in_(source_variations),
            StoreMapping.store_type == 'customer'
        ).distinct().all()
        print(f"   In StoreMapping (customer type): {[s[0] for s in all_sources_store]}")
    
    # Test the mapping lookup function (outside session)
    print(f"\n4️⃣ Testing mapping lookup function:")
    from utils.mapping_utils import MappingUtils
    mapping_utils = MappingUtils(use_database=True)
    
    # Test with common lookup values
    if source_name.lower() == 'kehe':
        test_values = ['569813430012', '569813430041', '0569813430012']
    elif source_name.lower() == 'unfi east':
        test_values = ['RCH', 'HOW', 'CHE', '128 RCH', '129 HOW']
    else:
        test_values = ['TEST1', 'TEST2']
    
    for test_val in test_values:
        result = mapping_utils.get_customer_mapping(test_val, source_name.lower().replace(' ', '_'))
        print(f"   Lookup '{test_val}' -> '{result}'")

def test_migration(db_service, source_name):
    """Test if migration would work"""
    print("\n" + "=" * 80)
    print(f"MIGRATION TEST for {source_name.upper()}")
    print("=" * 80)
    
    stats = db_service.migrate_legacy_customer_mappings(source_name.lower().replace(' ', '_'))
    print(f"\n📊 Migration results: {stats}")
    
    if stats['migrated'] > 0 or stats['updated'] > 0:
        print("✅ Migration found and moved legacy mappings")
    else:
        print("ℹ️ No legacy mappings found to migrate")

def main():
    print("🔍 PRODUCTION DATABASE DIAGNOSTIC")
    print("=" * 80)
    print(f"Environment: {os.getenv('ENVIRONMENT', 'NOT SET')}")
    print(f"DATABASE_URL set: {'YES' if os.getenv('DATABASE_URL') else 'NO'}")
    if os.getenv('DATABASE_URL'):
        # Mask the URL for security
        db_url = os.getenv('DATABASE_URL')
        if '@' in db_url:
            masked = db_url.split('@')[0].split('://')[0] + '://***:***@' + db_url.split('@')[1]
            print(f"DATABASE_URL: {masked}")
    
    try:
        db_service = DatabaseService()
        
        # Check structure
        check_database_structure(db_service)
        
        # Check KEHE data
        check_customer_mappings_for_source(
            db_service, 
            'KEHE', 
            ['kehe', 'kehe_sps', 'kehe___sps', 'KEHE - SPS', 'KEHE_SPS', 'KEHE___SPS']
        )
        
        # Check UNFI East data
        check_customer_mappings_for_source(
            db_service,
            'UNFI East',
            ['unfi_east', 'unfi east', 'UNFI East', 'UNFI_EAST', 'Unfi East']
        )
        
        # Test migrations
        test_migration(db_service, 'kehe')
        test_migration(db_service, 'unfi_east')
        
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

