#!/usr/bin/env python3
"""
Render deployment fix for StoreMapping table schema
This script removes the old raw_name and mapped_name columns
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fix_store_mapping_schema():
    """Fix StoreMapping table schema for Render deployment"""
    
    try:
        # Import after path setup
        from database.connection import get_database_engine
        
        engine = get_database_engine()
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                print("Checking store_mappings table structure...")
                
                # Check if raw_name column exists
                result = conn.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'store_mappings' 
                    AND column_name = 'raw_name'
                """)
                
                raw_name_exists = result.fetchone() is not None
                
                if raw_name_exists:
                    print("Found raw_name column, removing it...")
                    conn.execute("ALTER TABLE store_mappings DROP COLUMN raw_name")
                    print("✅ Dropped raw_name column")
                else:
                    print("✅ raw_name column already removed")
                
                # Check if mapped_name column exists
                result = conn.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'store_mappings' 
                    AND column_name = 'mapped_name'
                """)
                
                mapped_name_exists = result.fetchone() is not None
                
                if mapped_name_exists:
                    print("Found mapped_name column, removing it...")
                    conn.execute("ALTER TABLE store_mappings DROP COLUMN mapped_name")
                    print("✅ Dropped mapped_name column")
                else:
                    print("✅ mapped_name column already removed")
                
                # Commit transaction
                trans.commit()
                print("✅ Schema fix completed successfully!")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during schema fix: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    print("Fixing StoreMapping table schema for Render deployment...")
    success = fix_store_mapping_schema()
    if success:
        print("✅ Schema fix completed!")
    else:
        print("❌ Schema fix failed!")
        sys.exit(1)
