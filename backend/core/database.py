"""
Database connection and session management
"""
from sqlmodel import SQLModel, create_engine, Session
from .config import settings
# Models will be imported by the modules that need them
import logging

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True
)

def create_db_and_tables():
    """Create database tables"""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session
