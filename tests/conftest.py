import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

from app.database import get_session
from app.config import get_settings
from main import app

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def session(engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    with Session(engine) as session:
        yield session

@pytest.fixture(scope="function")
def override_get_session(session: Session):
    """Override the get_session dependency."""
    def _override_get_session():
        return session
    return _override_get_session

@pytest.fixture(scope="function")
async def client(override_get_session) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_settings():
    """Mock application settings for testing."""
    settings = get_settings()
    settings.database_url = TEST_DATABASE_URL
    settings.environment = "testing"
    settings.debug = True
    return settings

@pytest.fixture
def sample_internship_data():
    """Sample internship data for testing."""
    return {
        "title": "Software Engineering Intern",
        "company_name": "Tech Corp",
        "location": "Toronto, ON",
        "description": "Join our team as a software engineering intern...",
        "requirements": "Computer Science student, Python experience",
        "salary_min": 50000,
        "salary_max": 60000,
        "modality": "hybrid",
        "field_tag": "software_engineering",
        "apply_url": "https://example.com/apply",
        "source": "indeed",
        "external_id": "test-123"
    }

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "school": "University of Toronto",
        "degree": "Computer Science",
        "graduation_year": 2025,
        "skills": ["Python", "JavaScript", "React"],
        "interests": ["Software Engineering", "Data Science"]
    }

@pytest.fixture
def sample_resume_data():
    """Sample resume data for testing."""
    return {
        "title": "Software Engineering Resume",
        "template": "ats_clean",
        "content": {
            "summary": "Passionate computer science student...",
            "education": [{
                "school": "University of Toronto",
                "degree": "Bachelor of Computer Science",
                "graduation_year": 2025,
                "gpa": 3.8
            }],
            "experience": [{
                "title": "Software Development Intern",
                "company": "Previous Corp",
                "start_date": "2023-05-01",
                "end_date": "2023-08-31",
                "description": "Developed web applications..."
            }],
            "skills": ["Python", "JavaScript", "React", "SQL"],
            "projects": [{
                "name": "Personal Portfolio",
                "description": "Built a responsive portfolio website...",
                "technologies": ["React", "Node.js", "MongoDB"]
            }]
        }
    }
