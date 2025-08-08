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
    # Check for Streamlit Cloud environment
    if os.getenv('STREAMLIT_SHARING') or os.getenv('STREAMLIT_CLOUD'):
        return 'production'
    
    # Check for production indicators
    if os.getenv('ENVIRONMENT') == 'production':
        return 'production'
    
    # Check if we're in Replit (development) - more reliable detection
    if (os.getenv('REPL_ID') or 
        os.getenv('REPLIT_DB_URL') or 
        os.getenv('REPL_SLUG') or
        '/home/runner' in os.getcwd()):
        return 'development'
    
    # Default to local development
    return 'local'

def get_database_url() -> str:
    """
    Get the appropriate database URL based on environment
    """
    env = get_environment()
    db_url = os.getenv('DATABASE_URL', '')
    
    if env == 'production':
        # Use production database URL with SSL
        if db_url and 'sslmode=' not in db_url:
            # Ensure SSL is enabled for production
            db_url += '?sslmode=require' if '?' not in db_url else '&sslmode=require'
        return db_url
    
    elif env == 'development':
        # Force disable SSL for Replit development environment
        if db_url:
            # Remove any SSL requirements and add disable SSL
            db_url = db_url.replace('?sslmode=require', '').replace('&sslmode=require', '')
            db_url = db_url.replace('?sslmode=prefer', '').replace('&sslmode=prefer', '')
            # Explicitly disable SSL for development
            db_url += '?sslmode=disable' if '?' not in db_url else '&sslmode=disable'
        return db_url or 'postgresql://localhost/orderparser_dev?sslmode=disable'
    
    else:  # local
        # Use local database or fallback
        return db_url or 'postgresql://localhost/orderparser_dev?sslmode=disable'

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