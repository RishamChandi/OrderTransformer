"""
Database connection and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

try:
    from cloud_config import get_database_url
except ImportError:
    def get_database_url():
        return os.getenv('DATABASE_URL')

# Get database URL from environment or secrets
DATABASE_URL = get_database_url()

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

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