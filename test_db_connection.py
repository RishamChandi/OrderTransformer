"""
Quick script to test database connection and show which database is being used
"""
import os
import sys

# Load .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("ℹ️ python-dotenv not installed, skipping .env file")
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}")

print("\n" + "="*60)
print("DATABASE CONNECTION TEST")
print("="*60)

# Check environment variables
print("\n📋 Environment Variables:")
env = os.getenv('ENVIRONMENT', 'NOT SET')
db_url = os.getenv('DATABASE_URL', 'NOT SET')

print(f"  ENVIRONMENT: {env}")
if db_url != 'NOT SET':
    # Mask the password in the URL
    if '@' in db_url:
        parts = db_url.split('@')
        masked = parts[0].split('://')[0] + '://***:***@' + parts[1]
        print(f"  DATABASE_URL: {masked}")
    else:
        print(f"  DATABASE_URL: {db_url}")
else:
    print(f"  DATABASE_URL: NOT SET")

# Try to connect
print("\n🔌 Testing Connection...")
try:
    from database.env_config import get_environment, get_database_url
    from database.connection import get_database_engine
    
    env = get_environment()
    db_url = get_database_url()
    
    print(f"\n✅ Environment detected: {env}")
    
    # Mask the URL
    if '@' in db_url:
        masked_url = db_url.split('@')[0].split('://')[0] + '://***:***@' + db_url.split('@')[1].split('/')[0] + '/...'
    else:
        masked_url = db_url[:80] + '...' if len(db_url) > 80 else db_url
    
    print(f"✅ Database URL: {masked_url}")
    
    # Check if it's production database
    if 'render.com' in db_url.lower():
        print("✅ Detected: Production Database (Render)")
    elif 'sqlite' in db_url.lower():
        print("✅ Detected: Local SQLite Database")
    elif 'amazonaws.com' in db_url.lower():
        print("✅ Detected: AWS RDS Database")
    else:
        print("⚠️ Unknown database type")
    
    # Try to connect
    engine = get_database_engine()
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("\n✅ Connection successful!")
        
        # Try to query customer mappings to verify it's the right database
        try:
            from sqlalchemy import text
            result = conn.execute(text("SELECT COUNT(*) FROM customer_mappings WHERE source = 'unfi_east'"))
            count = result.scalar()
            print(f"✅ Found {count} UNFI East customer mappings in database")
            
            if count > 0:
                print("✅ This appears to be the PRODUCTION database!")
            else:
                print("⚠️ No UNFI East mappings found - might be a different database")
        except Exception as query_e:
            print(f"⚠️ Could not query mappings: {query_e}")
            print("   (This is okay if tables don't exist yet)")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ Test Complete!")
print("="*60)
