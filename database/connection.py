"""
Database connection and session management with environment switching
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from .env_config import get_database_url, get_environment, get_ssl_config

def create_database_engine():
    """Create database engine with environment-specific configuration"""
    database_url = get_database_url()
    env = get_environment()
    
    if not database_url:
        raise ValueError(f"DATABASE_URL not found for environment: {env}")
    
    # Configure engine based on environment
    engine_config = {
        'echo': False  # Set to True for SQL debugging
    }
    
    # Add SSL configuration for production
    if env == 'production':
        engine_config['connect_args'] = get_ssl_config()
    
    print(f"🔌 Connecting to {env} database...")
    
    try:
        engine = create_engine(database_url, **engine_config)
        # Test the connection
        connection = engine.connect()
        connection.close()
        print(f"✅ Connected to {env} database successfully")
        return engine
    except Exception as e:
        print(f"❌ Failed to connect to {env} database: {e}")
        
        # Enhanced fallback for development environments
        if env != 'production':
            print(f"🔄 Attempting fallback connection strategies...")
            
            # Strategy 1: Force disable SSL
            fallback_url = database_url.replace('?sslmode=require', '').replace('&sslmode=require', '')
            fallback_url = fallback_url.replace('?sslmode=prefer', '').replace('&sslmode=prefer', '')
            if 'sslmode=' not in fallback_url:
                fallback_url += '?sslmode=disable' if '?' not in fallback_url else '&sslmode=disable'
            
            try:
                print(f"📝 Trying with SSL disabled: {fallback_url[:50]}...")
                engine = create_engine(fallback_url, echo=False)
                connection = engine.connect()
                connection.close()
                print(f"✅ Connected to {env} database (SSL disabled)")
                return engine
            except Exception as e2:
                print(f"❌ SSL disabled connection failed: {e2}")
                
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