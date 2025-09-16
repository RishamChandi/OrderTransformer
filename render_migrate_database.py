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
    Migrate ItemMapping table to support enhanced template structure.
    Adds new columns while maintaining backward compatibility.
    """
    
    engine = get_database_engine()
    
    try:
        with engine.connect() as conn:
            # Check if table exists
            inspector = inspect(engine)
            if 'item_mappings' not in inspector.get_table_names():
                logger.info("Creating item_mappings table...")
                # Create the table with all columns
                create_table_sql = """
                CREATE TABLE item_mappings (
                    id SERIAL PRIMARY KEY,
                    source VARCHAR(50) NOT NULL,
                    raw_item VARCHAR(100) NOT NULL,
                    mapped_item VARCHAR(100) NOT NULL,
                    key_type VARCHAR(50) NOT NULL DEFAULT 'vendor_item',
                    priority INTEGER DEFAULT 100,
                    active BOOLEAN DEFAULT TRUE,
                    vendor VARCHAR(100),
                    mapped_description TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                conn.execute(text(create_table_sql))
                conn.commit()
                logger.info("✅ Created item_mappings table")
                return True, "Created item_mappings table"
            
            # Check if new columns already exist
            columns = [col['name'] for col in inspector.get_columns('item_mappings')]
            
            new_columns = [
                ('key_type', "VARCHAR(50) NOT NULL DEFAULT 'vendor_item'"),
                ('priority', "INTEGER DEFAULT 100"),
                ('active', "BOOLEAN DEFAULT TRUE"),
                ('vendor', "VARCHAR(100)"),
                ('mapped_description', "TEXT"),
                ('notes', "TEXT")
            ]
            
            columns_added = []
            for col_name, col_definition in new_columns:
                if col_name not in columns:
                    try:
                        # Add column
                        alter_sql = f"ALTER TABLE item_mappings ADD COLUMN {col_name} {col_definition}"
                        conn.execute(text(alter_sql))
                        columns_added.append(col_name)
                        logger.info(f"✅ Added column: {col_name}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to add column {col_name}: {e}")
                        raise
            
            # Add indexes for better performance
            indexes_to_create = [
                ("idx_item_mappings_source", "CREATE INDEX IF NOT EXISTS idx_item_mappings_source ON item_mappings(source)"),
                ("idx_item_mappings_active", "CREATE INDEX IF NOT EXISTS idx_item_mappings_active ON item_mappings(active)"),
                ("idx_item_mappings_priority", "CREATE INDEX IF NOT EXISTS idx_item_mappings_priority ON item_mappings(priority)"),
                ("idx_item_mappings_key_type", "CREATE INDEX IF NOT EXISTS idx_item_mappings_key_type ON item_mappings(key_type)"),
                ("idx_item_mappings_lookup", "CREATE INDEX IF NOT EXISTS idx_item_mappings_lookup ON item_mappings(source, key_type, raw_item) WHERE active = TRUE")
            ]
            
            for idx_name, idx_sql in indexes_to_create:
                try:
                    conn.execute(text(idx_sql))
                    logger.info(f"✅ Created index: {idx_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Index creation warning for {idx_name}: {e}")
            
            # Commit the transaction
            conn.commit()
            
            if columns_added:
                logger.info(f"✅ Migration completed. Added columns: {', '.join(columns_added)}")
                return True, f"Migration completed. Added columns: {', '.join(columns_added)}"
            else:
                logger.info("✅ Migration skipped. All columns already exist.")
                return True, "Migration skipped. All columns already exist."
                
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False, f"Migration failed: {e}"

def migrate_csv_mappings_to_database():
    """
    Migrate CSV mapping files to the database
    """
    
    engine = get_database_engine()
    
    try:
        with engine.connect() as conn:
            # Check if we have any existing mappings
            result = conn.execute(text("SELECT COUNT(*) FROM item_mappings"))
            existing_count = result.scalar()
            
            if existing_count > 0:
                logger.info(f"✅ Database already has {existing_count} item mappings")
                return True, f"Database already has {existing_count} item mappings"
            
            # Import mappings from CSV files
            sources = ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx']
            total_imported = 0
            
            for source in sources:
                logger.info(f"📦 Importing mappings for {source}...")
                
                # Try different file locations
                csv_files = [
                    f"mappings/{source}/item_mapping.csv",
                    f"mappings/{source}/item_mapping.xlsx",
                    f"mappings/kehe_item_mapping.csv" if source == 'kehe' else None
                ]
                
                source_file = None
                for file_path in csv_files:
                    if file_path and os.path.exists(file_path):
                        source_file = file_path
                        break
                
                if not source_file:
                    logger.warning(f"⚠️ No item mapping file found for {source}")
                    continue
                
                try:
                    # Read the file
                    if source_file.endswith('.xlsx'):
                        df = pd.read_excel(source_file, dtype=str)
                    else:
                        df = pd.read_csv(source_file, dtype=str)
                    
                    if len(df) == 0:
                        logger.warning(f"⚠️ Empty mapping file for {source}")
                        continue
                    
                    # Handle different column structures
                    imported_count = 0
                    
                    if source == 'kehe':
                        # KEHE format: ['SPS Customer#', 'CompanyName', 'Vendor P.N', 'Xoro Item#', 'Xoro Description']
                        if len(df.columns) >= 4:
                            for _, row in df.iterrows():
                                if pd.notna(row.iloc[2]) and pd.notna(row.iloc[3]):  # Vendor P.N -> Xoro Item#
                                    raw_item = str(row.iloc[2]).strip()
                                    mapped_item = str(row.iloc[3]).strip()
                                    
                                    insert_sql = """
                                    INSERT INTO item_mappings (source, raw_item, mapped_item, key_type, priority, active)
                                    VALUES (:source, :raw_item, :mapped_item, :key_type, :priority, :active)
                                    ON CONFLICT (source, raw_item) DO NOTHING
                                    """
                                    
                                    conn.execute(text(insert_sql), {
                                        'source': source,
                                        'raw_item': raw_item,
                                        'mapped_item': mapped_item,
                                        'key_type': 'vendor_item',
                                        'priority': 100,
                                        'active': True
                                    })
                                    imported_count += 1
                    
                    elif source == 'unfi_east':
                        # UNFI East format: ['UPC', 'UNFI East ', 'Description', 'Xoro Item#', 'Xoro Description']
                        if len(df.columns) >= 4:
                            for _, row in df.iterrows():
                                if pd.notna(row.iloc[1]) and pd.notna(row.iloc[3]):  # UNFI East -> Xoro Item#
                                    raw_item = str(row.iloc[1]).strip()
                                    mapped_item = str(row.iloc[3]).strip()
                                    
                                    insert_sql = """
                                    INSERT INTO item_mappings (source, raw_item, mapped_item, key_type, priority, active)
                                    VALUES (:source, :raw_item, :mapped_item, :key_type, :priority, :active)
                                    ON CONFLICT (source, raw_item) DO NOTHING
                                    """
                                    
                                    conn.execute(text(insert_sql), {
                                        'source': source,
                                        'raw_item': raw_item,
                                        'mapped_item': mapped_item,
                                        'key_type': 'vendor_item',
                                        'priority': 100,
                                        'active': True
                                    })
                                    imported_count += 1
                    
                    else:
                        # Standard format: first two columns
                        if len(df.columns) >= 2:
                            for _, row in df.iterrows():
                                if pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                                    raw_item = str(row.iloc[0]).strip()
                                    mapped_item = str(row.iloc[1]).strip()
                                    
                                    insert_sql = """
                                    INSERT INTO item_mappings (source, raw_item, mapped_item, key_type, priority, active)
                                    VALUES (:source, :raw_item, :mapped_item, :key_type, :priority, :active)
                                    ON CONFLICT (source, raw_item) DO NOTHING
                                    """
                                    
                                    conn.execute(text(insert_sql), {
                                        'source': source,
                                        'raw_item': raw_item,
                                        'mapped_item': mapped_item,
                                        'key_type': 'vendor_item',
                                        'priority': 100,
                                        'active': True
                                    })
                                    imported_count += 1
                    
                    conn.commit()
                    total_imported += imported_count
                    logger.info(f"✅ Imported {imported_count} mappings for {source}")
                    
                except Exception as e:
                    logger.error(f"❌ Error importing mappings for {source}: {e}")
                    continue
            
            logger.info(f"✅ Total imported: {total_imported} item mappings")
            return True, f"Imported {total_imported} item mappings"
            
    except Exception as e:
        logger.error(f"❌ Failed to migrate CSV mappings: {e}")
        return False, f"Failed to migrate CSV mappings: {e}"

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
            
            # Create processed_orders table
            create_orders_sql = """
            CREATE TABLE IF NOT EXISTS processed_orders (
                id SERIAL PRIMARY KEY,
                order_number VARCHAR(100) NOT NULL,
                source VARCHAR(50) NOT NULL,
                customer_name VARCHAR(200),
                raw_customer_name VARCHAR(200),
                order_date TIMESTAMP,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_file VARCHAR(500)
            );
            """
            conn.execute(text(create_orders_sql))
            
            # Create order_line_items table
            create_line_items_sql = """
            CREATE TABLE IF NOT EXISTS order_line_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES processed_orders(id),
                item_number VARCHAR(200),
                raw_item_number VARCHAR(200),
                item_description TEXT,
                quantity INTEGER DEFAULT 1,
                unit_price DECIMAL(10,2) DEFAULT 0.0,
                total_price DECIMAL(10,2) DEFAULT 0.0
            );
            """
            conn.execute(text(create_line_items_sql))
            
            conn.commit()
            logger.info("✅ Created all required tables")
            return True, "Created all required tables"
            
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False, f"Failed to create tables: {e}"

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