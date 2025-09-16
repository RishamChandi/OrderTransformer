#!/usr/bin/env python3
"""
Render Database Migration Script
Fixes the item_mappings table schema and migrates CSV data to database
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

def migrate_item_mapping_table():
    """
    Migrate item_mappings table to include new columns
    """
    
    engine = get_database_engine()
    
    try:
        with engine.connect() as conn:
            # Check if table exists
            inspector = inspect(engine)
            if 'item_mappings' not in inspector.get_table_names():
                logger.info("Creating item_mappings table...")
                create_item_mappings_sql = """
                CREATE TABLE item_mappings (
                    id SERIAL PRIMARY KEY,
                    source VARCHAR(50) NOT NULL,
                    raw_item VARCHAR(100) NOT NULL,
                    mapped_item VARCHAR(100) NOT NULL,
                    key_type VARCHAR(50) DEFAULT 'vendor_item',
                    priority INTEGER DEFAULT 100,
                    active BOOLEAN DEFAULT TRUE,
                    vendor VARCHAR(100),
                    mapped_description TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, raw_item, key_type)
                );
                """
                conn.execute(text(create_item_mappings_sql))
                conn.commit()
                logger.info("✅ Created item_mappings table")
            else:
                # Table exists, check and add missing columns
                logger.info("Checking item_mappings table structure...")
                
                # Get existing columns
                existing_columns = [col['name'] for col in inspector.get_columns('item_mappings')]
                
                # Add missing columns
                new_columns = {
                    'key_type': "ALTER TABLE item_mappings ADD COLUMN IF NOT EXISTS key_type VARCHAR(50) DEFAULT 'vendor_item'",
                    'priority': "ALTER TABLE item_mappings ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 100",
                    'active': "ALTER TABLE item_mappings ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE",
                    'vendor': "ALTER TABLE item_mappings ADD COLUMN IF NOT EXISTS vendor VARCHAR(100)",
                    'mapped_description': "ALTER TABLE item_mappings ADD COLUMN IF NOT EXISTS mapped_description TEXT",
                    'notes': "ALTER TABLE item_mappings ADD COLUMN IF NOT EXISTS notes TEXT"
                }
                
                for col_name, sql in new_columns.items():
                    if col_name not in existing_columns:
                        logger.info(f"Adding column: {col_name}")
                        conn.execute(text(sql))
                        conn.commit()
                        logger.info(f"✅ Added column: {col_name}")
                    else:
                        logger.info(f"Column {col_name} already exists")
        
        return True, "Item mappings table migration completed"
        
    except Exception as e:
        logger.error(f"❌ Failed to migrate item_mappings table: {e}")
        return False, f"Failed to migrate item_mappings table: {e}"

def create_other_tables():
    """
    Create other required tables if they don't exist
    """
    
    engine = get_database_engine()
    
    try:
        with engine.connect() as conn:
            # Create customer_mappings table
            create_customer_mappings_sql = """
            CREATE TABLE IF NOT EXISTS customer_mappings (
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
            conn.execute(text(create_customer_mappings_sql))
            logger.info("✅ Created customer_mappings table")
            
            # Create store_mappings table (enhanced)
            create_store_mappings_sql = """
            CREATE TABLE IF NOT EXISTS store_mappings (
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
            conn.execute(text(create_store_mappings_sql))
            logger.info("✅ Created store_mappings table")
            
            # Check if old store_mappings table exists and migrate it
            inspector = inspect(engine)
            if 'store_mappings' in inspector.get_table_names():
                existing_columns = [col['name'] for col in inspector.get_columns('store_mappings')]
                
                # If old structure exists, migrate it
                if 'raw_name' in existing_columns and 'raw_store_id' not in existing_columns:
                    logger.info("Migrating old store_mappings table structure...")
                    
                    # Add new columns
                    migration_sql = [
                        "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS raw_store_id VARCHAR(100)",
                        "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS mapped_store_name VARCHAR(200)",
                        "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS store_type VARCHAR(50) DEFAULT 'retail'",
                        "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE",
                        "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 100",
                        "ALTER TABLE store_mappings ADD COLUMN IF NOT EXISTS notes TEXT"
                    ]
                    
                    for sql in migration_sql:
                        conn.execute(text(sql))
                        conn.commit()
                    
                    # Migrate data from old columns to new columns
                    migrate_data_sql = """
                    UPDATE store_mappings 
                    SET raw_store_id = raw_name,
                        mapped_store_name = mapped_name
                    WHERE raw_store_id IS NULL OR mapped_store_name IS NULL;
                    """
                    conn.execute(text(migrate_data_sql))
                    conn.commit()
                    
                    logger.info("✅ Migrated store_mappings table structure")
            
            # Create processed_orders table
            create_orders_sql = """
            CREATE TABLE IF NOT EXISTS processed_orders (
                id SERIAL PRIMARY KEY,
                order_number VARCHAR(100) NOT NULL,
                source VARCHAR(50) NOT NULL,
                customer_name VARCHAR(200),
                store_name VARCHAR(200),
                order_date DATE,
                total_amount DECIMAL(10,2),
                status VARCHAR(50) DEFAULT 'processed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            conn.execute(text(create_orders_sql))
            logger.info("✅ Created processed_orders table")
            
            # Create order_line_items table
            create_line_items_sql = """
            CREATE TABLE IF NOT EXISTS order_line_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES processed_orders(id),
                item_number VARCHAR(100),
                description TEXT,
                quantity INTEGER,
                unit_price DECIMAL(10,2),
                total_price DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            conn.execute(text(create_line_items_sql))
            logger.info("✅ Created order_line_items table")
            
            # Create conversion_history table
            create_history_sql = """
            CREATE TABLE IF NOT EXISTS conversion_history (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(200) NOT NULL,
                source VARCHAR(50) NOT NULL,
                orders_count INTEGER DEFAULT 0,
                line_items_count INTEGER DEFAULT 0,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            conn.execute(text(create_history_sql))
            logger.info("✅ Created conversion_history table")
        
        return True, "All tables created successfully"
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False, f"Failed to create tables: {e}"

def migrate_csv_mappings_to_database():
    """
    Migrate CSV mapping files to database
    """
    
    engine = get_database_engine()
    
    try:
        # Define mapping file paths
        mapping_files = {
            'kehe': {
                'item': 'mappings/kehe_item_mapping.csv',
                'customer': 'mappings/kehe/customer_mapping.csv',
                'store': 'mappings/kehe/xoro_store_mapping.csv'
            },
            'wholefoods': {
                'item': 'mappings/wholefoods/item_mapping.csv',
                'customer': 'mappings/wholefoods/customer_mapping.csv',
                'store': 'mappings/wholefoods/xoro_store_mapping.csv'
            },
            'unfi_east': {
                'item': 'mappings/unfi_east/item_mapping.csv',
                'customer': 'mappings/unfi_east/customer_mapping.csv',
                'store': 'mappings/unfi_east/xoro_store_mapping.csv'
            },
            'unfi_west': {
                'item': 'mappings/unfi_west/item_mapping.csv',
                'customer': 'mappings/unfi_west/customer_mapping.csv',
                'store': 'mappings/unfi_west/xoro_store_mapping.csv'
            },
            'tkmaxx': {
                'item': 'mappings/tkmaxx/item_mapping.csv',
                'customer': 'mappings/tkmaxx/customer_mapping.csv',
                'store': 'mappings/tkmaxx/xoro_store_mapping.csv'
            }
        }
        
        total_migrated = 0
        
        for source, files in mapping_files.items():
            logger.info(f"Processing {source} mappings...")
            
            # Process item mappings
            if os.path.exists(files['item']):
                try:
                    df = pd.read_csv(files['item'])
                    logger.info(f"Found {len(df)} item mappings for {source}")
                    
                    # Migrate to database
                    for _, row in df.iterrows():
                        # Handle different CSV formats
                        if 'KeHE Number' in df.columns:
                            # KEHE format
                            raw_item = str(row.get('KeHE Number', ''))
                            mapped_item = str(row.get('ItemNumber', ''))
                            key_type = 'vendor_item'
                        elif 'RawKeyValue' in df.columns:
                            # Standard format
                            raw_item = str(row.get('RawKeyValue', ''))
                            mapped_item = str(row.get('MappedItemNumber', ''))
                            key_type = str(row.get('RawKeyType', 'vendor_item'))
                        else:
                            # Fallback
                            raw_item = str(row.get('raw_item', ''))
                            mapped_item = str(row.get('mapped_item', ''))
                            key_type = 'vendor_item'
                        
                        if raw_item and mapped_item:
                            insert_sql = """
                            INSERT INTO item_mappings (source, raw_item, mapped_item, key_type, priority, active, vendor, mapped_description, notes)
                            VALUES (%(source)s, %(raw_item)s, %(mapped_item)s, %(key_type)s, %(priority)s, %(active)s, %(vendor)s, %(mapped_description)s, %(notes)s)
                            ON CONFLICT (source, raw_item, key_type) DO UPDATE SET
                                mapped_item = EXCLUDED.mapped_item,
                                priority = EXCLUDED.priority,
                                active = EXCLUDED.active,
                                vendor = EXCLUDED.vendor,
                                mapped_description = EXCLUDED.mapped_description,
                                notes = EXCLUDED.notes,
                                updated_at = CURRENT_TIMESTAMP
                            """
                            
                            with engine.connect() as conn:
                                conn.execute(text(insert_sql), {
                                    'source': source,
                                    'raw_item': raw_item,
                                    'mapped_item': mapped_item,
                                    'key_type': key_type,
                                    'priority': 100,
                                    'active': True,
                                    'vendor': source.upper(),
                                    'mapped_description': str(row.get('Description', '')),
                                    'notes': f'Migrated from CSV - {source}'
                                })
                                conn.commit()
                    
                    total_migrated += len(df)
                    logger.info(f"✅ Migrated {len(df)} item mappings for {source}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not migrate item mappings for {source}: {e}")
            
            # Process customer mappings
            if os.path.exists(files['customer']):
                try:
                    df = pd.read_csv(files['customer'])
                    logger.info(f"Found {len(df)} customer mappings for {source}")
                    
                    for _, row in df.iterrows():
                        raw_customer_id = str(row.get('Raw Customer ID', row.get('raw_customer_id', '')))
                        mapped_customer_name = str(row.get('Mapped Customer Name', row.get('mapped_customer_name', '')))
                        
                        if raw_customer_id and mapped_customer_name:
                            insert_sql = """
                            INSERT INTO customer_mappings (source, raw_customer_id, mapped_customer_name, customer_type, priority, active, notes)
                            VALUES (%(source)s, %(raw_customer_id)s, %(mapped_customer_name)s, %(customer_type)s, %(priority)s, %(active)s, %(notes)s)
                            ON CONFLICT (source, raw_customer_id) DO UPDATE SET
                                mapped_customer_name = EXCLUDED.mapped_customer_name,
                                customer_type = EXCLUDED.customer_type,
                                priority = EXCLUDED.priority,
                                active = EXCLUDED.active,
                                notes = EXCLUDED.notes,
                                updated_at = CURRENT_TIMESTAMP
                            """
                            
                            with engine.connect() as conn:
                                conn.execute(text(insert_sql), {
                                    'source': source,
                                    'raw_customer_id': raw_customer_id,
                                    'mapped_customer_name': mapped_customer_name,
                                    'customer_type': 'store',
                                    'priority': 100,
                                    'active': True,
                                    'notes': f'Migrated from CSV - {source}'
                                })
                                conn.commit()
                    
                    total_migrated += len(df)
                    logger.info(f"✅ Migrated {len(df)} customer mappings for {source}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not migrate customer mappings for {source}: {e}")
            
            # Process store mappings
            if os.path.exists(files['store']):
                try:
                    df = pd.read_csv(files['store'])
                    logger.info(f"Found {len(df)} store mappings for {source}")
                    
                    for _, row in df.iterrows():
                        raw_store_id = str(row.get('Raw Store ID', row.get('raw_store_id', row.get('raw_name', ''))))
                        mapped_store_name = str(row.get('Mapped Store Name', row.get('mapped_store_name', row.get('mapped_name', ''))))
                        
                        if raw_store_id and mapped_store_name:
                            insert_sql = """
                            INSERT INTO store_mappings (source, raw_store_id, mapped_store_name, store_type, priority, active, notes)
                            VALUES (%(source)s, %(raw_store_id)s, %(mapped_store_name)s, %(store_type)s, %(priority)s, %(active)s, %(notes)s)
                            ON CONFLICT (source, raw_store_id) DO UPDATE SET
                                mapped_store_name = EXCLUDED.mapped_store_name,
                                store_type = EXCLUDED.store_type,
                                priority = EXCLUDED.priority,
                                active = EXCLUDED.active,
                                notes = EXCLUDED.notes,
                                updated_at = CURRENT_TIMESTAMP
                            """
                            
                            with engine.connect() as conn:
                                conn.execute(text(insert_sql), {
                                    'source': source,
                                    'raw_store_id': raw_store_id,
                                    'mapped_store_name': mapped_store_name,
                                    'store_type': 'retail',
                                    'priority': 100,
                                    'active': True,
                                    'notes': f'Migrated from CSV - {source}'
                                })
                                conn.commit()
                    
                    total_migrated += len(df)
                    logger.info(f"✅ Migrated {len(df)} store mappings for {source}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not migrate store mappings for {source}: {e}")
        
        return True, f"Successfully migrated {total_migrated} mappings from CSV files"
        
    except Exception as e:
        logger.error(f"❌ Failed to migrate CSV mappings: {e}")
        return False, f"Failed to migrate CSV mappings: {e}"

def main():
    """Main migration function"""
    
    logger.info("🚀 Starting Render database migration...")
    
    try:
        # Step 1: Create all required tables
        success, message = create_other_tables()
        if not success:
            logger.error(f"❌ Table creation failed: {message}")
            return False
        
        # Step 2: Migrate item_mappings table structure
        success, message = migrate_item_mapping_table()
        if not success:
            logger.error(f"❌ Table migration failed: {message}")
            return False
        
        # Step 3: Import CSV mappings to database
        success, message = migrate_csv_mappings_to_database()
        if not success:
            logger.error(f"❌ CSV migration failed: {message}")
            return False
        
        logger.info("🎉 Database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)