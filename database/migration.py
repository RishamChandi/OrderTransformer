"""
Database migration utilities for item mapping template enhancement
"""

from sqlalchemy import text, inspect
from .connection import get_database_engine
import logging

logger = logging.getLogger(__name__)

def migrate_item_mapping_table():
    """
    Migrate ItemMapping table to support enhanced template structure.
    Adds new columns while maintaining backward compatibility.
    """
    
    engine = get_database_engine()
    
    try:
        with engine.connect() as conn:
            # Check if new columns already exist
            inspector = inspect(engine)
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
                        logger.info(f"Added column: {col_name}")
                        
                    except Exception as e:
                        logger.error(f"Failed to add column {col_name}: {e}")
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
                    logger.info(f"Created index: {idx_name}")
                except Exception as e:
                    logger.warning(f"Index creation warning for {idx_name}: {e}")
            
            # Commit the transaction
            conn.commit()
            
            if columns_added:
                logger.info(f"Migration completed. Added columns: {', '.join(columns_added)}")
                return True, f"Migration completed. Added columns: {', '.join(columns_added)}"
            else:
                logger.info("Migration skipped. All columns already exist.")
                return True, "Migration skipped. All columns already exist."
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False, f"Migration failed: {e}"

def migrate_existing_mappings():
    """
    Migrate existing CSV-based mappings to the new database structure.
    Sets appropriate defaults for existing records.
    """
    
    engine = get_database_engine()
    
    try:
        with engine.connect() as conn:
            # Update existing records to have default values for new columns
            update_sql = """
            UPDATE item_mappings 
            SET 
                key_type = COALESCE(key_type, 'vendor_item'),
                priority = COALESCE(priority, 100),
                active = COALESCE(active, TRUE)
            WHERE key_type IS NULL OR priority IS NULL OR active IS NULL
            """
            
            result = conn.execute(text(update_sql))
            conn.commit()
            
            rows_updated = result.rowcount
            logger.info(f"Updated {rows_updated} existing mapping records with default values")
            
            return True, f"Updated {rows_updated} existing mapping records"
            
    except Exception as e:
        logger.error(f"Failed to migrate existing mappings: {e}")
        return False, f"Failed to migrate existing mappings: {e}"

def run_full_migration():
    """
    Run complete migration process for item mapping enhancement
    """
    
    logger.info("Starting item mapping table migration...")
    
    # Step 1: Update table structure
    success, message = migrate_item_mapping_table()
    if not success:
        return False, message
        
    # Step 2: Migrate existing data
    success, migrate_message = migrate_existing_mappings()
    if not success:
        return False, migrate_message
        
    full_message = f"{message}. {migrate_message}"
    logger.info(f"Full migration completed: {full_message}")
    
    return True, full_message