"""
Database connection and session management with environment switching
"""

import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from .env_config import get_database_url, get_environment, get_ssl_config

def _mask_database_url(url: str) -> str:
    """Safely mask credentials in database URL for logging"""
    if not url:
        return 'EMPTY_URL'
    
    # Pattern to match postgresql://username:password@host:port/database
    pattern = r'(postgresql://)[^:]+:[^@]+@(.+)'
    match = re.match(pattern, url)
    
    if match:
        return f"{match.group(1)}***:***@{match.group(2)}"
    else:
        # Fallback: just show protocol and last part after @
        if '@' in url:
            parts = url.split('@')
            return f"{parts[0].split('://')[0]}://***:***@{parts[-1]}"
        else:
            return f"{url.split('://')[0]}://***" if '://' in url else "***"

def create_database_engine():
    """Create database engine with environment-specific configuration"""
    database_url = get_database_url()
    env = get_environment()
    
    if not database_url:
        raise ValueError(f"DATABASE_URL not found for environment: {env}")
    
    # Configure engine with connection pooling and stability settings
    engine_config = {
        'echo': False,  # Set to True for SQL debugging
        'pool_size': 5,  # Maintain 5 connections in pool
        'max_overflow': 10,  # Allow up to 10 overflow connections
        'pool_pre_ping': True,  # Validate connections before use
        'pool_recycle': 300,  # Recycle connections every 5 minutes
        'connect_args': {
            'connect_timeout': 30,  # 30 second connection timeout
            'application_name': 'order_transformer_dev'  # Identify our connections
        }
    }
    
    # Add SSL configuration for production and cloud databases
    if env == 'production':
        engine_config['connect_args'].update(get_ssl_config())
    elif 'neon' in database_url.lower() or 'aws' in database_url.lower():
        # For cloud databases like Neon, add stability settings
        engine_config['connect_args'].update({
            'keepalives_idle': 600,  # Start keepalives after 10 min
            'keepalives_interval': 30,  # Send keepalive every 30 sec
            'keepalives_count': 3   # Give up after 3 failed keepalives
        })
    
    print(f"🔌 Connecting to {env} database...")
    
    try:
        engine = create_engine(database_url, **engine_config)
        # Test the connection with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                connection = engine.connect()
                connection.close()
                print(f"✅ Connected to {env} database successfully (attempt {attempt + 1})")
                return engine
            except Exception as retry_error:
                if attempt < max_retries - 1:
                    print(f"⚠️ Connection attempt {attempt + 1} failed, retrying...")
                    import time
                    time.sleep(1)  # Wait 1 second before retry
                else:
                    raise retry_error
    except Exception as e:
        print(f"❌ Failed to connect to {env} database: {e}")
        
        # Enhanced fallback for development environments
        if env != 'production':
            print(f"🔄 Attempting fallback connection strategies...")
            
            # Strategy 1: Try with SSL allow (works with cloud databases like Neon)
            fallback_url = database_url.replace('?sslmode=require', '').replace('&sslmode=require', '')
            fallback_url = fallback_url.replace('?sslmode=prefer', '').replace('&sslmode=prefer', '')
            fallback_url = fallback_url.replace('?sslmode=disable', '').replace('&sslmode=disable', '')
            if 'sslmode=' not in fallback_url:
                fallback_url += '?sslmode=allow' if '?' not in fallback_url else '&sslmode=allow'
            
            try:
                print(f"📝 Trying with SSL allow: {_mask_database_url(fallback_url)}")
                engine = create_engine(fallback_url, echo=False)
                connection = engine.connect()
                connection.close()
                print(f"✅ Connected to {env} database (SSL allow)")
                return engine
            except Exception as e2:
                print(f"❌ SSL allow connection failed: {e2}")
                
                # Strategy 2: Try with SSL allow
                try:
                    allow_url = fallback_url.replace('sslmode=disable', 'sslmode=allow')
                    print(f"📝 Trying with SSL allow...")
                    engine = create_engine(allow_url, echo=False)
                    connection = engine.connect()
                    connection.close()
                    print(f"✅ Connected to {env} database (SSL allow)")
                    return engine
                except Exception as e3:
                    print(f"❌ All connection strategies failed. Last error: {e3}")
        
        # If all strategies fail, raise the original error
        raise Exception(f"Database connection failed after all retry attempts. Environment: {env}, Error: {e}")

# Create engine instance
engine = create_database_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database_engine():
    """Get the database engine"""
    return engine

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_session_direct() -> Session:
    """Get a database session directly (remember to close it)"""
    return SessionLocal()

def get_current_environment():
    """Get the current database environment"""
    return get_environment()