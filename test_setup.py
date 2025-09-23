#!/usr/bin/env python3
import os
import sys

# Set environment
os.environ['ENVIRONMENT'] = 'local'
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'

print("Environment variables set:")
print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

try:
    print("Testing imports...")
    from database.models import Base
    print("✓ Models imported")
    
    from database.connection import get_database_engine
    print("✓ Connection imported")
    
    print("Creating database engine...")
    engine = get_database_engine()
    print("✓ Database engine created")
    
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")
    
    print("Testing database service...")
    from database.service import DatabaseService
    db_service = DatabaseService()
    print("✓ Database service created")
    
    print("All tests passed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
