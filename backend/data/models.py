"""
SQLModel data models for EasyInterns v2
Production-grade with proper indices and relationships
"""
from sqlmodel import SQLModel, Field, Relationship, Index, Column, String, Text
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid


class FieldTag(str, Enum):
    """Internship field categories"""
    SOFTWARE_ENGINEERING = "software_engineering"
    DATA_SCIENCE = "data_science"
    PRODUCT_MANAGEMENT = "product_management"
    DESIGN_UX_UI = "design_ux_ui"
    MARKETING = "marketing"
    FINANCE = "finance"
    CONSULTING = "consulting"
    SALES = "sales"
    OPERATIONS = "operations"
    RESEARCH = "research"
    CYBERSECURITY = "cybersecurity"
    DEVOPS = "devops"
    BUSINESS_ANALYST = "business_analyst"
    PROJECT_MANAGEMENT = "project_management"
    HEALTHCARE = "healthcare"
    OTHER = "other"


class Modality(str, Enum):
    """Work modality options"""
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"


class ConfidenceLevel(str, Enum):
    """Email confidence levels"""
    HIGH = "high"      # >= 0.8
    MEDIUM = "medium"  # >= 0.5
    LOW = "low"        # < 0.5


# Base Models
class TimestampMixin(SQLModel):
    """Mixin for created_at and updated_at timestamps"""
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(TimestampMixin, table=True):
    """User model with Supabase integration"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    supabase_id: str = Field(unique=True, index=True)  # Supabase Auth UUID
    email: str = Field(unique=True, index=True)
    name: Optional[str] = None
    
    # Profile fields
    city: Optional[str] = Field(default=None, index=True)
    region: Optional[str] = Field(default=None, index=True)  # Province/State
    country: str = Field(default="Canada", index=True)
    fields_of_interest: List[FieldTag] = Field(default=[], sa_column=Column("fields_of_interest", String))
    skills: List[str] = Field(default=[], sa_column=Column("skills", String))
    
    # Relationships
    resumes: List["Resume"] = Relationship(back_populates="user")
    bookmarks: List["Bookmark"] = Relationship(back_populates="user")
    click_logs: List["ClickLog"] = Relationship(back_populates="user")


class Company(TimestampMixin, table=True):
    """Company model with logo and contact info"""
    __tablename__ = "companies"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    domain: Optional[str] = Field(default=None, unique=True, index=True)
    logo_url: Optional[str] = None
    description: Optional[str] = Field(default=None, sa_column=Column("description", Text))
    
    # Location
    headquarters_city: Optional[str] = Field(default=None, index=True)
    headquarters_region: Optional[str] = Field(default=None, index=True)
    headquarters_country: Optional[str] = Field(default="Canada", index=True)
    
    # Company size and type
    size_category: Optional[str] = None  # startup, small, medium, large, enterprise
    industry: Optional[str] = Field(default=None, index=True)
    
    # Relationships
    internships: List["Internship"] = Relationship(back_populates="company")
    contact_emails: List["ContactEmail"] = Relationship(back_populates="company")


class Source(TimestampMixin, table=True):
    """Scraping source registry"""
    __tablename__ = "sources"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # "job_bank_ca", "indeed_ca", etc.
    display_name: str  # "Job Bank Canada", "Indeed Canada"
    source_type: str = Field(index=True)  # "api", "html", "rss"
    base_url: str
    enabled: bool = Field(default=True, index=True)
    cooldown_seconds: int = Field(default=300)
    last_scraped_at: Optional[datetime] = Field(default=None, index=True)
    
    # Relationships
    internships: List["Internship"] = Relationship(back_populates="source")


class Internship(TimestampMixin, table=True):
    """Core internship model with full-text search"""
    __tablename__ = "internships"
    __table_args__ = (
        Index("idx_internship_search", "title", "description", postgresql_using="gin"),
        Index("idx_internship_field_date", "field_tag", "posted_at"),
        Index("idx_internship_location", "city", "region", "country"),
        Index("idx_internship_modality", "modality"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Core fields
    title: str = Field(index=True)
    description: str = Field(sa_column=Column("description", Text))
    field_tag: FieldTag = Field(index=True)
    
    # Location
    city: Optional[str] = Field(default=None, index=True)
    region: Optional[str] = Field(default=None, index=True)  # Province/State
    country: str = Field(default="Canada", index=True)
    modality: Modality = Field(index=True)
    
    # Job details
    salary_min: Optional[int] = Field(default=None, index=True)
    salary_max: Optional[int] = Field(default=None, index=True)
    salary_currency: str = Field(default="CAD")
    duration_months: Optional[int] = None
    
    # Application
    apply_url: str
    external_id: Optional[str] = Field(default=None, index=True)  # Source's job ID
    posted_at: Optional[datetime] = Field(default=None, index=True)
    expires_at: Optional[datetime] = Field(default=None, index=True)
    
    # Metadata
    skills_required: List[str] = Field(default=[], sa_column=Column("skills_required", String))
    education_level: Optional[str] = None  # "bachelor", "master", "phd", "diploma"
    experience_level: Optional[str] = None  # "entry", "junior", "mid", "senior"
    government_program: bool = Field(default=False, index=True)
    
    # Scoring
    relevance_score: Optional[float] = Field(default=None, index=True)
    
    # Foreign Keys
    company_id: int = Field(foreign_key="companies.id", index=True)
    source_id: int = Field(foreign_key="sources.id", index=True)
    
    # Relationships
    company: Company = Relationship(back_populates="internships")
    source: Source = Relationship(back_populates="internships")
    bookmarks: List["Bookmark"] = Relationship(back_populates="internship")
    click_logs: List["ClickLog"] = Relationship(back_populates="internship")
    contact_emails: List["ContactEmail"] = Relationship(back_populates="internship")


class ContactEmail(TimestampMixin, table=True):
    """Extracted contact emails with confidence scoring"""
    __tablename__ = "contact_emails"
    __table_args__ = (
        Index("idx_contact_email_confidence", "confidence_score"),
        Index("idx_contact_email_unique", "email", "company_id", unique=True),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    confidence_score: float = Field(index=True)  # 0.0 to 1.0
    confidence_level: ConfidenceLevel = Field(index=True)
    
    # Email metadata
    email_type: str = Field(index=True)  # "careers", "hr", "recruiting", "contact"
    name: Optional[str] = None  # Contact person name if found
    title: Optional[str] = None  # Job title if found
    
    # Validation
    mx_verified: bool = Field(default=False)
    last_verified_at: Optional[datetime] = None
    
    # Foreign Keys
    company_id: int = Field(foreign_key="companies.id", index=True)
    internship_id: Optional[int] = Field(foreign_key="internships.id", index=True)
    
    # Relationships
    company: Company = Relationship(back_populates="contact_emails")
    internship: Optional[Internship] = Relationship(back_populates="contact_emails")


class Resume(TimestampMixin, table=True):
    """Resume builder with templates and AI enhancement"""
    __tablename__ = "resumes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # User-given name
    template_key: str = Field(index=True)  # "ats_clean", "modern_two_col", etc.
    
    # Resume data (JSON)
    json_data: dict = Field(default={}, sa_column=Column("json_data", String))
    
    # Generated files
    pdf_url: Optional[str] = None  # Supabase Storage URL
    pdf_generated_at: Optional[datetime] = None
    
    # AI enhancement
    ai_enhanced: bool = Field(default=False)
    ai_enhanced_at: Optional[datetime] = None
    
    # Foreign Keys
    user_id: int = Field(foreign_key="users.id", index=True)
    
    # Relationships
    user: User = Relationship(back_populates="resumes")


class Bookmark(TimestampMixin, table=True):
    """User bookmarks for internships"""
    __tablename__ = "bookmarks"
    __table_args__ = (
        Index("idx_bookmark_unique", "user_id", "internship_id", unique=True),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    notes: Optional[str] = Field(default=None, sa_column=Column("notes", Text))
    
    # Foreign Keys
    user_id: int = Field(foreign_key="users.id", index=True)
    internship_id: int = Field(foreign_key="internships.id", index=True)
    
    # Relationships
    user: User = Relationship(back_populates="bookmarks")
    internship: Internship = Relationship(back_populates="bookmarks")


class ClickLog(TimestampMixin, table=True):
    """User interaction tracking"""
    __tablename__ = "click_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    action: str = Field(index=True)  # "view", "apply", "bookmark", "email_copy"
    click_metadata: Optional[str] = None  # JSON string for additional data
    
    # Foreign Keys
    user_id: int = Field(foreign_key="users.id", index=True)
    internship_id: int = Field(foreign_key="internships.id", index=True)
    
    # Relationships
    user: User = Relationship(back_populates="click_logs")
    internship: Internship = Relationship(back_populates="click_logs")
