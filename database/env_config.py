"""
Environment-based database configuration
Automatically switches between development and production databases
"""
import os
from typing import Optional

# Load .env file early to ensure DATABASE_URL is available
# CRITICAL: Use override=True to ensure .env file values override any existing environment variables
# This prevents PowerShell environment variables from overriding .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Load .env file and OVERRIDE any existing environment variables
except ImportError:
    pass  # python-dotenv not installed, that's okay

def get_environment() -> str:
    """
    Determine the current environment based on various indicators
    Returns: 'production', 'development', or 'local'
    
    Priority:
    1. Explicit ENVIRONMENT variable
    2. Render.com database URL -> production
    3. Other cloud deployment indicators -> production
    4. Default to local
    """
    # Check for explicit environment override (highest priority)
    explicit_env = os.getenv('ENVIRONMENT', '').lower()
    if explicit_env in ['production', 'development', 'local']:
        return explicit_env
    
    # Check if DATABASE_URL contains render.com -> default to production
    db_url = os.getenv('DATABASE_URL', '').lower()
    if 'render.com' in db_url:
        return 'production'
    
    # Check for Render deployment environment
    if os.getenv('RENDER') or os.getenv('RENDER_SERVICE_NAME'):
        return 'production'
    
    # Check for Streamlit Cloud environment
    if os.getenv('STREAMLIT_SHARING') or os.getenv('STREAMLIT_CLOUD'):
        return 'production'
    
    # Check for other cloud database URLs -> production
    if db_url:
        cloud_indicators = [
            'amazonaws.com', 'rds.amazonaws.com',
            'neon.tech', 'supabase.co', 'heroku.com',
            'azure.com', 'gcp.sql', 'cloudsql'
        ]
        if any(indicator in db_url for indicator in cloud_indicators):
            return 'production'
    
    # Check for Replit deployment (legacy support)
    if (os.getenv('REPL_ID') or 
        os.getenv('REPLIT_DB_URL') or 
        os.getenv('REPL_SLUG') or
        os.getenv('REPL_OWNER') or
        '/home/runner' in os.getcwd()):
        return 'production' if os.getenv('REPLIT_DEPLOYMENT') else 'development'
    
    # Default to local development
    return 'local'

def get_database_url() -> str:
    """
    Get the appropriate database URL based on environment
    ONLY supports Render PostgreSQL database - SQLite is NOT supported
    
    CRITICAL: This application ONLY uses Render PostgreSQL database.
    SQLite is completely disabled to ensure data consistency.
    """
    env = get_environment()
    db_url = os.getenv('DATABASE_URL', '')
    
    # CRITICAL: REJECT SQLite completely - application only uses Render database
    if 'sqlite' in db_url.lower():
        raise ValueError(
            "❌ SQLite database is NOT supported in this application.\n"
            "This application ONLY uses the Render PostgreSQL database.\n"
            "Please set DATABASE_URL to your Render database URL.\n"
            "Example: DATABASE_URL=postgresql://user:pass@host.render.com/dbname\n"
            "Get your Render database URL from: https://dashboard.render.com"
        )
    
    if not db_url:
        raise ValueError(
            f"❌ DATABASE_URL environment variable not found for {env} environment.\n"
            f"This application REQUIRES a Render PostgreSQL database.\n"
            f"Please set DATABASE_URL to your Render database URL.\n"
            f"Get your Render database URL from: https://dashboard.render.com"
        )
    
    # CRITICAL: If DATABASE_URL contains render.com, always use it (even in local environment)
    # This ensures the local app uses the same database as production
    if 'render.com' in db_url.lower():
        print(f"✅ Detected Render database URL - will use production database")
        print(f"⚠️ NOTE: Local app will connect to Render production database")
        print(f"⚠️ All data changes will affect production database")
        
        # Remove any existing sslmode parameters to avoid conflicts
        if '?' in db_url:
            base_url, params_str = db_url.split('?', 1)
            param_parts = [p for p in params_str.split('&') if not p.startswith('sslmode=')]
            db_url = base_url + ('?' + '&'.join(param_parts) if param_parts else '')
        
        # Render PostgreSQL requires SSL
        separator = '&' if '?' in db_url else '?'
        db_url = f"{db_url}{separator}sslmode=require"
        return db_url
    
    # If not Render database, check if it's another PostgreSQL database
    if 'postgresql://' in db_url.lower() or 'postgres://' in db_url.lower():
        print(f"⚠️ WARNING: Using non-Render PostgreSQL database")
        print(f"⚠️ This application is designed for Render database")
        print(f"⚠️ For production use, use Render database: https://dashboard.render.com")
        
        # Remove any existing sslmode parameters to avoid conflicts
        if '?' in db_url:
            base_url, params_str = db_url.split('?', 1)
            param_parts = [p for p in params_str.split('&') if not p.startswith('sslmode=')]
            db_url = base_url + ('?' + '&'.join(param_parts) if param_parts else '')
        
        # Add SSL mode based on environment
        separator = '&' if '?' in db_url else '?'
        if env == 'production':
            db_url = f"{db_url}{separator}sslmode=require"
        else:
            db_url = f"{db_url}{separator}sslmode=allow"
        return db_url
    
    # Reject any other database types (this should never be reached if code is correct)
    raise ValueError(
        f"❌ Unsupported database URL: {db_url[:50]}...\n"
        f"This application ONLY supports Render PostgreSQL database.\n"
        f"Please set DATABASE_URL to your Render database URL.\n"
        f"Get your Render database URL from: https://dashboard.render.com"
    )

def should_initialize_database() -> bool:
    """
    Determine if we should auto-initialize the database
    """
    env = get_environment()
    
    # Only auto-initialize in development/local environments
    return env in ['development', 'local']

def get_ssl_config() -> dict:
    """
    Get SSL configuration based on environment
    """
    env = get_environment()
    
    if env == 'production':
        return {'sslmode': 'require'}
    else:
        return {'sslmode': 'prefer'}  # Allow both SSL and non-SSL for development