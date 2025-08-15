"""
Environment-based database configuration
Automatically switches between development and production databases
"""
import os
from typing import Optional

def get_environment() -> str:
    """
    Determine the current environment based on various indicators
    Returns: 'production', 'development', or 'local'
    """
    # Check for explicit environment override
    explicit_env = os.getenv('ENVIRONMENT', '').lower()
    if explicit_env in ['production', 'development', 'local']:
        return explicit_env
    
    # Check for Replit deployment (default to development for Replit)
    if (os.getenv('REPL_ID') or 
        os.getenv('REPLIT_DB_URL') or 
        os.getenv('REPL_SLUG') or
        os.getenv('REPL_OWNER') or
        '/home/runner' in os.getcwd()):
        # For Replit deployments, treat as production unless explicitly set to development
        return 'production' if os.getenv('REPLIT_DEPLOYMENT') else 'development'
    
    # Check for Streamlit Cloud environment
    if os.getenv('STREAMLIT_SHARING') or os.getenv('STREAMLIT_CLOUD'):
        return 'production'
    
    # Default to local development
    return 'local'

def get_database_url() -> str:
    """
    Get the appropriate database URL based on environment
    """
    env = get_environment()
    db_url = os.getenv('DATABASE_URL', '')
    
    if not db_url:
        raise ValueError(f"DATABASE_URL environment variable not found for {env} environment")
    
    if env == 'production':
        # For production (including Replit deployments), use SSL based on the URL
        if 'sslmode=' not in db_url:
            # For Replit deployments, use allow instead of require for better compatibility
            if os.getenv('REPL_ID'):
                db_url += '?sslmode=allow' if '?' not in db_url else '&sslmode=allow'
            else:
                # For other production environments, require SSL
                db_url += '?sslmode=require' if '?' not in db_url else '&sslmode=require'
        return db_url
    
    elif env == 'development':
        # Force disable SSL for development environment
        if db_url:
            # Remove any SSL requirements and add disable SSL
            db_url = db_url.replace('?sslmode=require', '').replace('&sslmode=require', '')
            db_url = db_url.replace('?sslmode=prefer', '').replace('&sslmode=prefer', '')
            db_url = db_url.replace('?sslmode=allow', '').replace('&sslmode=allow', '')
            # Explicitly disable SSL for development
            db_url += '?sslmode=disable' if '?' not in db_url else '&sslmode=disable'
        return db_url
    
    else:  # local
        # Use local database with SSL disabled
        if db_url:
            # Disable SSL for local development
            if 'sslmode=' not in db_url:
                db_url += '?sslmode=disable' if '?' not in db_url else '&sslmode=disable'
        else:
            db_url = 'postgresql://localhost/orderparser_dev?sslmode=disable'
        return db_url

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