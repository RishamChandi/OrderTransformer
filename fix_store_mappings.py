#!/usr/bin/env python3
"""
Fix Store Mappings Table Structure
Specifically addresses the raw_store_id column issue
"""

import os
import sys
import pandas as pd
from sqlalchemy import text, inspect, create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_engine():
    """Get database engine from environment"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Ensure proper PostgreSQL URL format
    if not database_url.startswith('postgresql://'):
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return create_engine(database_url, echo=False)

def fix_store_mappings_table():
    """
    Fix the store_mappings table structure
    """
    
    engine = get_database_engine()
    
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # Check if store_mappings table exists
            if 'store_mappings' not in inspector.get_table_names():
                logger.info("Creating store_mappings table from scratch...")
                create_sql = """
                CREATE TABLE store_mappings (
                    id SERIAL PRIMARY KEY,
                    source VARCHAR(50) NOT NULL,
                    raw_store_id VARCHAR(100) NOT NULL,
                    mapped_store_name VARCHAR(200) NOT NULL,
                    store_type VARCHAR(50) DEFAULT 'retail',
                    active BOOLEAN DEFAULT TRUE,
                    priority INTEGER DEFAULT 100,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, raw_store_id)
                );
                """
                conn.execute(text(create_sql))
                conn.commit()
                logger.info("✅ Created store_mappings table with new structure")
                return True, "Table created successfully"
            
            # Table exists, check its structure
            existing_columns = [col['name'] for col in inspector.get_columns('store_mappings')]
            logger.info(f"Existing columns: {existing_columns}")
            
            # Check if we need to migrate from old structure
            if 'raw_name' in existing_columns and 'raw_store_id' not in existing_columns:
                logger.info("Migrating from old table structure...")
                
                # Step 1: Add new columns
                logger.info("Adding new columns...")
                new_columns_sql = [
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS raw_store_id VARCHAR(100)",
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS mapped_store_name VARCHAR(200)",
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS store_type VARCHAR(50) DEFAULT 'retail'",
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE",
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 100",
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS notes TEXT"
                ]
                
                for sql in new_columns_sql:
                    logger.info(f"Executing: {sql}")
                    conn.execute(text(sql))
                    conn.commit()
                
                # Step 2: Migrate data from old columns to new columns
                logger.info("Migrating data from old columns...")
                migrate_data_sql = """
                UPDATE store_mappings 
                SET raw_store_id = COALESCE(raw_name, ''),
                    mapped_store_name = COALESCE(mapped_name, '')
                WHERE raw_store_id IS NULL OR mapped_store_id IS NULL;
                """
                conn.execute(text(migrate_data_sql))
                conn.commit()
                
                # Step 3: Drop old columns (optional - we'll keep them for safety)
                logger.info("✅ Migration completed - keeping old columns for safety")
                
            elif 'raw_store_id' not in existing_columns:
                logger.info("Adding missing raw_store_id column...")
                add_columns_sql = [
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS raw_store_id VARCHAR(100)",
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS mapped_store_name VARCHAR(200)",
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS store_type VARCHAR(50) DEFAULT 'retail'",
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE",
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 100",
                    "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS notes TEXT"
                ]
                
                for sql in add_columns_sql:
                    logger.info(f"Executing: {sql}")
                    conn.execute(text(sql))
                    conn.commit()
                
                logger.info("✅ Added missing columns")
            else:
                logger.info("✅ Table structure is already correct")
            
            # Verify the final structure
            final_columns = [col['name'] for col in inspector.get_columns('store_mappings')]
            logger.info(f"Final columns: {final_columns}")
            
            # Check if raw_store_id exists
            if 'raw_store_id' in final_columns:
                logger.info("✅ raw_store_id column exists - table structure is correct")
                return True, "Table structure fixed successfully"
            else:
                logger.error("❌ raw_store_id column still missing after migration")
                return False, "Migration failed - raw_store_id column missing"
        
    except Exception as e:
        logger.error(f"❌ Failed to fix store_mappings table: {e}")
        return False, f"Failed to fix store_mappings table: {e}"

def create_customer_mappings_table():
    """
    Ensure customer_mappings table exists
    """
    
    engine = get_database_engine()
    
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            if 'customer_mappings' not in inspector.get_table_names():
                logger.info("Creating customer_mappings table...")
                create_sql = """
                CREATE TABLE customer_mappings (
                    id SERIAL PRIMARY KEY,
                    source VARCHAR(50) NOT NULL,
                    raw_customer_id VARCHAR(100) NOT NULL,
                    mapped_customer_name VARCHAR(200) NOT NULL,
                    customer_type VARCHAR(50) DEFAULT 'store',
                    active BOOLEAN DEFAULT TRUE,
                    priority INTEGER DEFAULT 100,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, raw_customer_id)
                );
                """
                conn.execute(text(create_sql))
                conn.commit()
                logger.info("✅ Created customer_mappings table")
            else:
                logger.info("✅ customer_mappings table already exists")
        
        return True, "Customer mappings table ready"
        
    except Exception as e:
        logger.error(f"❌ Failed to create customer_mappings table: {e}")
        return False, f"Failed to create customer_mappings table: {e}"

def main():
    """Main fix function"""
    
    logger.info("🔧 Starting store mappings table fix...")
    
    try:
        # Step 1: Fix store_mappings table
        success, message = fix_store_mappings_table()
        if not success:
            logger.error(f"❌ Store mappings fix failed: {message}")
            return False
        
        # Step 2: Ensure customer_mappings table exists
        success, message = create_customer_mappings_table()
        if not success:
            logger.error(f"❌ Customer mappings creation failed: {message}")
            return False
        
        logger.info("🎉 Store mappings table fix completed successfully!")
        logger.info("✅ The 'raw_store_id' column should now exist")
        logger.info("✅ You can now refresh your app and test store mappings")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fix failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
