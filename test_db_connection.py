#!/usr/bin/env python3
"""
Test database connection for UNFI East migration
"""

import os
import sys

def test_database_connection():
    """Test database connection"""
    
    print("Testing database connection...")
    
    try:
        # Set database URL
        os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
        
        # Import database service
        from database.service import DatabaseService
        
        print("✓ Database service imported successfully")
        
        # Initialize database service
        db_service = DatabaseService()
        print("✓ Database service initialized")
        
        # Test a simple query
        with db_service.get_session() as session:
            print("✓ Database session created")
            
            # Test query
            from database.models import CustomerMapping
            count = session.query(CustomerMapping).count()
            print(f"✓ Database query successful - {count} customer mappings found")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_connection()
    if success:
        print("\n✅ Database connection test passed!")
    else:
        print("\n❌ Database connection test failed!")
    sys.exit(0 if success else 1)
