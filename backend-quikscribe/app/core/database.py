"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine with production-ready settings
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=getattr(settings, 'db_pool_size', 20),
    max_overflow=getattr(settings, 'db_max_overflow', 30),
    pool_timeout=getattr(settings, 'db_pool_timeout', 30),
    echo=settings.debug,  # Log SQL queries in debug mode
    future=True  # Use SQLAlchemy 2.0 style
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Dependency injection for database sessions
def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI routes.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!") 