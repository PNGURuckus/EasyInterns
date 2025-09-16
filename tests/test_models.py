import pytest
from datetime import datetime, date
from sqlmodel import Session, create_engine
from sqlalchemy.pool import StaticPool

from app.models import (
    User, Company, Internship, ContactEmail, Resume, 
    Bookmark, ClickLog, Source, SQLModel
)

@pytest.fixture
def engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture
def session(engine):
    """Create test database session."""
    with Session(engine) as session:
        yield session

class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, session: Session):
        """Test creating a user."""
        user = User(
            id="test-user-id",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            school="University of Toronto",
            degree="Computer Science",
            graduation_year=2025,
            gpa=3.8,
            skills=["Python", "JavaScript"],
            interests=["Software Engineering"]
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.id == "test-user-id"
        assert user.email == "test@example.com"
        assert user.full_name == "John Doe"
        assert user.skills == ["Python", "JavaScript"]
    
    def test_user_full_name_property(self):
        """Test user full name property."""
        user = User(
            id="test-id",
            email="test@example.com",
            first_name="John",
            last_name="Doe"
        )
        assert user.full_name == "John Doe"
        
        user.last_name = None
        assert user.full_name == "John"
        
        user.first_name = None
        user.last_name = "Doe"
        assert user.full_name == "Doe"

class TestCompanyModel:
    """Test Company model functionality."""
    
    def test_company_creation(self, session: Session):
        """Test creating a company."""
        company = Company(
            name="Tech Corp",
            domain="techcorp.com",
            description="Leading technology company",
            industry="Technology",
            size="1000-5000",
            headquarters="Toronto, ON"
        )
        
        session.add(company)
        session.commit()
        session.refresh(company)
        
        assert company.name == "Tech Corp"
        assert company.domain == "techcorp.com"
        assert company.id is not None

class TestInternshipModel:
    """Test Internship model functionality."""
    
    def test_internship_creation(self, session: Session):
        """Test creating an internship."""
        # Create company first
        company = Company(name="Tech Corp", domain="techcorp.com")
        session.add(company)
        session.commit()
        
        internship = Internship(
            title="Software Engineering Intern",
            company_id=company.id,
            location="Toronto, ON",
            description="Join our development team...",
            requirements="Computer Science student",
            salary_min=50000,
            salary_max=60000,
            modality="hybrid",
            field_tag="software_engineering",
            apply_url="https://example.com/apply",
            source="indeed",
            external_id="test-123",
            posting_date=date.today(),
            is_government=False
        )
        
        session.add(internship)
        session.commit()
        session.refresh(internship)
        
        assert internship.title == "Software Engineering Intern"
        assert internship.company_id == company.id
        assert internship.salary_range == "$50,000 - $60,000"
        assert internship.id is not None
    
    def test_internship_salary_range_property(self):
        """Test salary range property."""
        internship = Internship(
            title="Test Intern",
            company_id="test-company",
            apply_url="https://example.com",
            source="test",
            external_id="test-123"
        )
        
        # Both min and max
        internship.salary_min = 50000
        internship.salary_max = 60000
        assert internship.salary_range == "$50,000 - $60,000"
        
        # Only min
        internship.salary_max = None
        assert internship.salary_range == "$50,000+"
        
        # Only max
        internship.salary_min = None
        internship.salary_max = 60000
        assert internship.salary_range == "Up to $60,000"
        
        # Neither
        internship.salary_max = None
        assert internship.salary_range == "Not specified"

class TestContactEmailModel:
    """Test ContactEmail model functionality."""
    
    def test_contact_email_creation(self, session: Session):
        """Test creating a contact email."""
        # Create internship first
        company = Company(name="Tech Corp")
        session.add(company)
        session.commit()
        
        internship = Internship(
            title="Test Intern",
            company_id=company.id,
            apply_url="https://example.com",
            source="test",
            external_id="test-123"
        )
        session.add(internship)
        session.commit()
        
        contact_email = ContactEmail(
            internship_id=internship.id,
            email="hiring@techcorp.com",
            confidence_score=0.85,
            extraction_method="domain_pattern",
            name="HR Team"
        )
        
        session.add(contact_email)
        session.commit()
        session.refresh(contact_email)
        
        assert contact_email.email == "hiring@techcorp.com"
        assert contact_email.confidence_score == 0.85
        assert contact_email.internship_id == internship.id

class TestResumeModel:
    """Test Resume model functionality."""
    
    def test_resume_creation(self, session: Session):
        """Test creating a resume."""
        resume = Resume(
            user_id="test-user-id",
            title="Software Engineering Resume",
            template="ats_clean",
            content={
                "summary": "Passionate computer science student...",
                "education": [{"school": "University of Toronto"}],
                "experience": [],
                "skills": ["Python", "JavaScript"]
            },
            is_ai_enhanced=True
        )
        
        session.add(resume)
        session.commit()
        session.refresh(resume)
        
        assert resume.title == "Software Engineering Resume"
        assert resume.template == "ats_clean"
        assert resume.is_ai_enhanced is True
        assert "summary" in resume.content

class TestBookmarkModel:
    """Test Bookmark model functionality."""
    
    def test_bookmark_creation(self, session: Session):
        """Test creating a bookmark."""
        # Create dependencies
        company = Company(name="Tech Corp")
        session.add(company)
        session.commit()
        
        internship = Internship(
            title="Test Intern",
            company_id=company.id,
            apply_url="https://example.com",
            source="test",
            external_id="test-123"
        )
        session.add(internship)
        session.commit()
        
        bookmark = Bookmark(
            user_id="test-user-id",
            internship_id=internship.id
        )
        
        session.add(bookmark)
        session.commit()
        session.refresh(bookmark)
        
        assert bookmark.user_id == "test-user-id"
        assert bookmark.internship_id == internship.id
        assert bookmark.created_at is not None

class TestClickLogModel:
    """Test ClickLog model functionality."""
    
    def test_click_log_creation(self, session: Session):
        """Test creating a click log."""
        # Create dependencies
        company = Company(name="Tech Corp")
        session.add(company)
        session.commit()
        
        internship = Internship(
            title="Test Intern",
            company_id=company.id,
            apply_url="https://example.com",
            source="test",
            external_id="test-123"
        )
        session.add(internship)
        session.commit()
        
        click_log = ClickLog(
            user_id="test-user-id",
            internship_id=internship.id,
            action="apply",
            metadata={"source": "browse_page"}
        )
        
        session.add(click_log)
        session.commit()
        session.refresh(click_log)
        
        assert click_log.user_id == "test-user-id"
        assert click_log.action == "apply"
        assert click_log.metadata["source"] == "browse_page"

class TestSourceModel:
    """Test Source model functionality."""
    
    def test_source_creation(self, session: Session):
        """Test creating a source."""
        source = Source(
            name="indeed",
            display_name="Indeed",
            base_url="https://indeed.com",
            is_active=True,
            rate_limit=100,
            last_scraped=datetime.now()
        )
        
        session.add(source)
        session.commit()
        session.refresh(source)
        
        assert source.name == "indeed"
        assert source.display_name == "Indeed"
        assert source.is_active is True
        assert source.rate_limit == 100

class TestModelRelationships:
    """Test model relationships."""
    
    def test_company_internships_relationship(self, session: Session):
        """Test company to internships relationship."""
        company = Company(name="Tech Corp")
        session.add(company)
        session.commit()
        
        internship1 = Internship(
            title="Intern 1",
            company_id=company.id,
            apply_url="https://example.com/1",
            source="test",
            external_id="test-1"
        )
        internship2 = Internship(
            title="Intern 2",
            company_id=company.id,
            apply_url="https://example.com/2",
            source="test",
            external_id="test-2"
        )
        
        session.add_all([internship1, internship2])
        session.commit()
        
        # Refresh to load relationships
        session.refresh(company)
        
        assert len(company.internships) == 2
        assert internship1 in company.internships
        assert internship2 in company.internships
    
    def test_internship_contact_emails_relationship(self, session: Session):
        """Test internship to contact emails relationship."""
        company = Company(name="Tech Corp")
        session.add(company)
        session.commit()
        
        internship = Internship(
            title="Test Intern",
            company_id=company.id,
            apply_url="https://example.com",
            source="test",
            external_id="test-123"
        )
        session.add(internship)
        session.commit()
        
        email1 = ContactEmail(
            internship_id=internship.id,
            email="hr@techcorp.com",
            confidence_score=0.9
        )
        email2 = ContactEmail(
            internship_id=internship.id,
            email="hiring@techcorp.com",
            confidence_score=0.8
        )
        
        session.add_all([email1, email2])
        session.commit()
        
        session.refresh(internship)
        
        assert len(internship.contact_emails) == 2
        assert email1 in internship.contact_emails
        assert email2 in internship.contact_emails
