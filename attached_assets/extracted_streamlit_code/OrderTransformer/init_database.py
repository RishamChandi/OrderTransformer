#!/usr/bin/env python3
"""
Initialize the database schema
"""

from database.models import Base
from database.connection import get_database_engine
from database.service import DatabaseService

def init_database():
    """Initialize database tables"""
    
    engine = get_database_engine()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    
    # Load existing Excel mappings into database
    db_service = DatabaseService()
    
    # Import store mappings from Excel files
    import pandas as pd
    import os
    
    sources = ['wholefoods', 'unfi_west', 'unfi', 'tkmaxx']
    
    for source in sources:
        store_mapping_file = f'mappings/{source}/store_mapping.xlsx'
        if os.path.exists(store_mapping_file):
            try:
                df = pd.read_excel(store_mapping_file)
                if len(df.columns) >= 2:
                    for _, row in df.iterrows():
                        if pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                            db_service.save_store_mapping(
                                source=source,
                                raw_name=str(row.iloc[0]).strip(),
                                mapped_name=str(row.iloc[1]).strip()
                            )
                    print(f"Imported store mappings for {source}")
            except Exception as e:
                print(f"Error importing store mappings for {source}: {e}")
        
        # Import item mappings
        item_mapping_file = f'mappings/{source}/item_mapping.xlsx'
        if os.path.exists(item_mapping_file):
            try:
                df = pd.read_excel(item_mapping_file)
                if len(df.columns) >= 2:
                    for _, row in df.iterrows():
                        if pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                            db_service.save_item_mapping(
                                source=source,
                                raw_item=str(row.iloc[0]).strip(),
                                mapped_item=str(row.iloc[1]).strip()
                            )
                    print(f"Imported item mappings for {source}")
            except Exception as e:
                print(f"Error importing item mappings for {source}: {e}")
    
    print("Database initialization complete!")

if __name__ == "__main__":
    init_database()