#!/usr/bin/env python3
"""
Initialize the database schema only - no automatic mapping loading
All mappings should be managed through the UI
"""

from database.models import Base
from database.connection import get_database_engine
from database.service import DatabaseService
from database.migration import run_full_migration

def init_database():
    """Initialize database tables only - no mapping data loading"""
    
    engine = get_database_engine()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    
    # Run item mapping template migration
    success, message = run_full_migration()
    if success:
        print(f"✅ Migration completed: {message}")
    else:
        print(f"❌ Migration failed: {message}")
        return False
    
    print("Database initialization complete!")
    print("ℹ️  All mappings should be managed through the UI - no automatic loading")

if __name__ == "__main__":
    init_database()