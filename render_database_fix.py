#!/usr/bin/env python3
"""
Render database fix - remove old columns from store_mappings table
Run this on Render to fix the schema issue
"""

import os
import sys
from sqlalchemy import text

def fix_database_schema():
    """Fix the database schema by removing old columns"""
    
    try:
        # Import database modules
        from database.connection import get_database_engine
        
        engine = get_database_engine()
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                print("🔍 Checking store_mappings table structure...")
                
                # Check current columns
                result = conn.execute(text("""
                    SELECT column_name, is_nullable, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'store_mappings' 
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                print("Current columns:")
                for col in columns:
                    print(f"  - {col[0]} ({col[1]}, {col[2]})")
                
                # Check if raw_name exists
                raw_name_exists = any(col[0] == 'raw_name' for col in columns)
                mapped_name_exists = any(col[0] == 'mapped_name' for col in columns)
                
                if raw_name_exists:
                    print("\n🗑️ Removing raw_name column...")
                    conn.execute(text("ALTER TABLE store_mappings DROP COLUMN raw_name"))
                    print("✅ Dropped raw_name column")
                else:
                    print("✅ raw_name column already removed")
                
                if mapped_name_exists:
                    print("🗑️ Removing mapped_name column...")
                    conn.execute(text("ALTER TABLE store_mappings DROP COLUMN mapped_name"))
                    print("✅ Dropped mapped_name column")
                else:
                    print("✅ mapped_name column already removed")
                
                # Commit transaction
                trans.commit()
                print("\n✅ Database schema fixed successfully!")
                
                # Verify final structure
                result = conn.execute(text("""
                    SELECT column_name, is_nullable, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'store_mappings' 
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                print("\nFinal columns:")
                for col in columns:
                    print(f"  - {col[0]} ({col[1]}, {col[2]})")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during schema fix: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing Render database schema...")
    success = fix_database_schema()
    if success:
        print("✅ Schema fix completed!")
    else:
        print("❌ Schema fix failed!")
        sys.exit(1)
