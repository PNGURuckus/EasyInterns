from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from typing import Generator, AsyncGenerator

from app.core.config import settings

# Create SQLAlchemy engines
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=settings.SQL_ECHO,
)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for getting sync database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        yield session

def init_db() -> None:
    """Initialize database tables"""
    # Import all models here to ensure they are registered with the Base
    from app.models.user import User
    from app.models.company import Company
    from app.models.internship import Internship
    from app.models.resume import Resume
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
    
    # Create initial admin user if not exists
    from app.crud.user import user as crud_user
    from app.schemas.user import UserCreate
    
    db = SessionLocal()
    try:
        # Create admin user if not exists
        admin_email = "admin@example.com"
        admin_user = crud_user.get_by_email(db, email=admin_email)
        if not admin_user:
            user_in = UserCreate(
                email=admin_email,
                password="adminpassword",
                full_name="Admin User",
                is_superuser=True,
            )
            crud_user.create(db, obj_in=user_in)
            print("Created admin user")
    finally:
        db.close()

# For use in FastAPI lifespan event
def lifespan(app):
    # Initialize database
    init_db()
    yield
