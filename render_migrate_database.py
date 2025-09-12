#!/usr/bin/env python3
"""
Render Database Migration Script
Complete migration script for deploying to Render PostgreSQL hosting
"""

import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_environment():
    """Check if running in proper environment with required variables"""
    print("🔍 Checking environment...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
        
    environment = os.getenv('ENVIRONMENT', 'development')
    print(f"   Environment: {environment}")
    print(f"   Database URL: {database_url[:50]}...")
    
    return True

def initialize_database():
    """Initialize database schema"""
    print("\n🏗️ Initializing database schema...")
    
    try:
        from database.models import Base
        from database.connection import get_engine
        
        # Create all tables
        engine = get_engine()
        Base.metadata.create_all(engine)
        
        print("✅ Database schema initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def migrate_kehe_mappings():
    """Migrate KEHE item mappings from CSV"""
    print("\n📦 Migrating KEHE mappings...")
    
    try:
        from database.service import DatabaseService
        
        csv_path = project_root / "mappings" / "kehe_item_mapping.csv"
        if not csv_path.exists():
            print(f"⚠️ KEHE CSV not found: {csv_path}")
            return True  # Not critical
            
        # Load and process CSV
        df = pd.read_csv(csv_path, dtype=str)
        df = df.drop_duplicates(subset=['KeHE Number'], keep='first')
        
        db_service = DatabaseService()
        
        # Convert to database format
        mappings = []
        for _, row in df.iterrows():
            # Vendor item mapping
            mappings.append({
                'source': 'kehe',
                'raw_item': str(row['KeHE Number']).strip(),
                'mapped_item': str(row['ItemNumber']).strip(),
                'key_type': 'vendor_item',
                'priority': 100,
                'active': True,
                'vendor': 'KEHE',
                'mapped_description': str(row['Description']).strip() if pd.notna(row['Description']) else None,
                'notes': 'Render migration - KEHE vendor mapping'
            })
            
            # UPC mapping if available
            if pd.notna(row['UPC']) and str(row['UPC']).strip():
                mappings.append({
                    'source': 'kehe',
                    'raw_item': str(row['UPC']).strip(),
                    'mapped_item': str(row['ItemNumber']).strip(),
                    'key_type': 'upc',
                    'priority': 90,
                    'active': True,
                    'vendor': 'KEHE',
                    'mapped_description': str(row['Description']).strip() if pd.notna(row['Description']) else None,
                    'notes': 'Render migration - KEHE UPC mapping'
                })
        
        # Bulk insert
        result = db_service.bulk_upsert_item_mappings(mappings)
        print(f"✅ KEHE migration: {result['added']} added, {result['updated']} updated, {result['errors']} errors")
        
        return True
        
    except Exception as e:
        print(f"❌ KEHE migration failed: {e}")
        return False

def migrate_store_mappings():
    """Migrate store and customer mappings"""
    print("\n🏪 Migrating store mappings...")
    
    try:
        from database.service import DatabaseService
        
        db_service = DatabaseService()
        
        # KEHE customer mappings
        kehe_customer_path = project_root / "mappings" / "kehe_customer_mapping.csv"
        if kehe_customer_path.exists():
            df = pd.read_csv(kehe_customer_path, dtype=str)
            
            for _, row in df.iterrows():
                db_service.upsert_store_mapping(
                    source='kehe',
                    raw_store_id=str(row['Ship To Location']).strip(),
                    mapped_company_name=str(row['Company Name']).strip(),
                    notes='Render migration - KEHE customer'
                )
            
            print(f"✅ Migrated {len(df)} KEHE customer mappings")
        
        # Add other store mappings as needed
        print("✅ Store mappings migration completed")
        return True
        
    except Exception as e:
        print(f"❌ Store migration failed: {e}")
        return False

def validate_migration():
    """Validate the migration results"""
    print("\n🧪 Validating migration...")
    
    try:
        from database.service import DatabaseService
        from utils.mapping_utils import MappingUtils
        
        db_service = DatabaseService()
        mapping_utils = MappingUtils()
        
        # Check KEHE mappings count
        kehe_mappings = db_service.get_item_mappings_advanced(source='kehe')
        print(f"   📊 KEHE mappings in database: {len(kehe_mappings)}")
        
        # Test sample resolution
        test_cases = [
            {'vendor_item': '00110368'},
            {'vendor_item': '02313478'},
            {'vendor_item': '00308376'}
        ]
        
        resolved_count = 0
        for test_case in test_cases:
            resolved = mapping_utils.resolve_item_number(
                item_attributes=test_case,
                source='kehe'
            )
            if resolved:
                resolved_count += 1
                vendor_item = test_case['vendor_item']
                print(f"   ✅ {vendor_item} → {resolved}")
        
        print(f"   📈 Resolution success: {resolved_count}/{len(test_cases)} items")
        
        if resolved_count >= 2:  # At least 2/3 should resolve
            print("✅ Migration validation passed")
            return True
        else:
            print("⚠️ Migration validation concerns - low resolution rate")
            return False
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def main():
    """Main migration process"""
    print("🚀 Render Database Migration")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        return False
    
    # Initialize schema
    if not initialize_database():
        print("❌ Database initialization failed")
        return False
    
    # Migrate data
    success = True
    success &= migrate_kehe_mappings()
    success &= migrate_store_mappings()
    
    if success:
        success &= validate_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("📋 Next steps:")
        print("   1. Test health endpoint: /?health=check")
        print("   2. Upload sample KEHE order file")
        print("   3. Verify item resolution works")
    else:
        print("\n❌ Migration completed with errors")
        print("   Review logs and retry failed components")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)