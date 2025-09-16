import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.db.base_class import Base
from app.db.session import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.internship import Internship
from app.models.company import Company
from app.models.resume import Resume
from app.models.application import Application
from app.models.bookmark import Bookmark, BookmarkFolder

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the test database and tables
Base.metadata.create_all(bind=engine)

# Override the get_db dependency to use our test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Apply the override
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

# Fixtures
@pytest.fixture(scope="session")
def db():
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Create the tables
    Base.metadata.create_all(bind=connection)

    yield session

    # Clean up
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def normal_user_token_headers(test_user):
    """Get a token for the test user."""
    from app.core.security import create_access_token
    access_token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def test_company(db):
    """Create a test company."""
    company = Company(
        name="Test Company",
        description="A test company",
        website="https://testcompany.com",
        logo_url="https://testcompany.com/logo.png",
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@pytest.fixture
def test_internship(db, test_company):
    """Create a test internship."""
    internship = Internship(
        title="Test Internship",
        description="A test internship",
        company_id=test_company.id,
        location="Remote",
        employment_type="FULL_TIME",
        is_active=True,
    )
    db.add(internship)
    db.commit()
    db.refresh(internship)
    return internship

@pytest.fixture
def test_resume(db, test_user):
    """Create a test resume."""
    resume = Resume(
        user_id=test_user.id,
        title="Test Resume",
        file_path="/resumes/test_resume.pdf",
        is_public=False,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume

# Add more fixtures as needed for other models

# Clean up after tests
def pytest_sessionfinish(session, exitstatus):
    """Clean up the test database after all tests have run."""
    Base.metadata.drop_all(bind=engine)
