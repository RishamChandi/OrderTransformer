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
    if os.getenv('STREAMLIT_SHARING'):
        return 'production'
    
    # Check for production indicators
    if os.getenv('ENVIRONMENT') == 'production':
        return 'production'
    
    # Check if we're in Replit (development)
    if os.getenv('REPL_ID') or os.getenv('REPLIT_DB_URL'):
        return 'development'
    
    # Default to local development
    return 'local'

def get_database_url() -> str:
    """
    Get the appropriate database URL based on environment
    """
    env = get_environment()
    
    if env == 'production':
        # Use production database URL with SSL
        db_url = os.getenv('DATABASE_URL')
        if db_url and not db_url.endswith('?sslmode=require'):
            # Ensure SSL is enabled for production
            db_url += '?sslmode=require' if '?' not in db_url else '&sslmode=require'
        return db_url
    
    elif env == 'development':
        # Use Replit's local PostgreSQL without SSL requirements
        return os.getenv('DATABASE_URL', '').replace('?sslmode=require', '').replace('&sslmode=require', '')
    
    else:  # local
        # Use local database or fallback
        return os.getenv('DATABASE_URL', 'postgresql://localhost/orderparser_dev')

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