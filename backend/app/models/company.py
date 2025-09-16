from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from pydantic import validator, EmailStr, HttpUrl, field_validator
from uuid import UUID, uuid4

from .base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    ConfigMixin
)

if TYPE_CHECKING:
    from .internship import Internship
    from .user import User

class CompanySize(str, Enum):
    MICRO = "1-10"
    SMALL = "11-50"
    SMALL_MEDIUM = "51-200"
    MEDIUM = "201-500"
    LARGE_MEDIUM = "501-1000"
    LARGE = "1001-5000"
    ENTERPRISE = "5001+"

class CompanyBase(SQLModel):
    # Basic Information
    name: str = Field(
        ..., 
        max_length=255, 
        index=True,
        description="Official company name"
    )
    legal_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Legal/registered company name if different from display name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Detailed company description"
    )
    short_description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Brief company tagline or summary"
    )
    
    # Company Details
    website: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Company website URL"
    )
    logo_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="URL to company logo image"
    )
    cover_image_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="URL to company cover/banner image"
    )
    
    # Industry & Classification
    industry: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Primary industry sector"
    )
    industries: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="List of all relevant industries/sectors"
    )
    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Tags for categorization and search"
    )
    
    # Size and Structure
    size: Optional[CompanySize] = Field(
        default=None,
        description="Approximate number of employees"
    )
    founded_year: Optional[int] = Field(
        default=None,
        ge=1800,
        le=datetime.now().year,
        description="Year the company was founded"
    )
    company_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Type of company (Public, Private, Non-profit, etc.)"
    )
    
    # Location
    hq_location: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Headquarters location (City, Country)"
    )
    locations: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="List of office locations with details"
    )
    
    # Social Media
    linkedin_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="LinkedIn company page URL"
    )
    twitter_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Twitter profile URL"
    )
    github_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="GitHub organization URL"
    )
    facebook_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Facebook page URL"
    )
    instagram_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Instagram profile URL"
    )
    
    # Contact Information
    contact_email: Optional[EmailStr] = Field(
        default=None,
        description="General contact email"
    )
    contact_phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Primary contact phone number"
    )
    
    # Additional Metadata
    tech_stack: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Technologies used by the company"
    )
    benefits: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Employee benefits offered"
    )
    
    # Company Culture
    mission: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Company mission statement"
    )
    values: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Company core values"
    )
    
    # Validation
    @validator('founded_year')
    def validate_founded_year(cls, v):
        if v is not None and (v < 1800 or v > datetime.now().year):
            raise ValueError("Invalid founding year")
        return v
    
class Company(CompanyBase, BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin, table=True):
    __tablename__ = "companies"
    
    # Database fields
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    
    # Additional DB-only fields
    slug: str = Field(
        default=None,
        index=True,
        nullable=False,
        description="URL-friendly version of the company name"
    )
    
    # Relationships
    internships: List["Internship"] = Relationship(back_populates="company")
    users: List["User"] = Relationship(back_populates="company")
    
    # Search vector for full-text search
    search_vector: Optional[str] = Field(default=None, sa_type="tsvector")
    
    # Table configuration
    __table_args__ = {'extend_existing': True}
    
    def __repr__(self) -> str:
        return f"<Company {self.name} ({self.id})>"
    
    @property
    def active_internships_count(self) -> int:
        """Get count of active internships"""
        if not hasattr(self, 'internships'):
            return 0
        now = datetime.utcnow()
        return sum(1 for i in self.internships if i.is_active)
    
    @property
    def social_links(self) -> Dict[str, str]:
        """Get dictionary of social media links"""
        return {
            'website': str(self.website) if self.website else None,
            'linkedin': str(self.linkedin_url) if self.linkedin_url else None,
            'twitter': str(self.twitter_url) if self.twitter_url else None,
            'github': str(self.github_url) if self.github_url else None,
            'facebook': str(self.facebook_url) if self.facebook_url else None,
            'instagram': str(self.instagram_url) if self.instagram_url else None,
        }
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

class CompanyCreate(CompanyBase):
    """Schema for creating a new company"""
    name: str  # Required field from base
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Acme Corp",
                "legal_name": "Acme Corporation Inc.",
                "website": "https://acme.example.com",
                "description": "A leading provider of innovative solutions...",
                "industry": "Technology",
                "industries": ["Technology", "SaaS", "Artificial Intelligence"],
                "size": "201-500",
                "founded_year": 2010,
                "hq_location": "Toronto, ON, Canada",
                "contact_email": "info@acme.example.com",
                "linkedin_url": "https://linkedin.com/company/acme-corp"
            }
        }

class CompanyUpdate(SQLModel):
    """Schema for updating company information"""
    name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Company name"
    )
    legal_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Legal/registered company name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Detailed company description"
    )
    short_description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Brief company tagline or summary"
    )
    website: Optional[HttpUrl] = Field(
        default=None,
        description="Company website URL"
    )
    logo_url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to company logo image"
    )
    cover_image_url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to company cover/banner image"
    )
    industry: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Primary industry sector"
    )
    industries: Optional[List[str]] = Field(
        default=None,
        description="List of all relevant industries/sectors"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags for categorization and search"
    )
    size: Optional[CompanySize] = Field(
        default=None,
        description="Approximate number of employees"
    )
    founded_year: Optional[int] = Field(
        default=None,
        ge=1800,
        le=datetime.now().year,
        description="Year the company was founded"
    )
    company_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Type of company (Public, Private, Non-profit, etc.)"
    )
    hq_location: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Headquarters location (City, Country)"
    )
    locations: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of office locations with details"
    )
    linkedin_url: Optional[HttpUrl] = Field(
        default=None,
        description="LinkedIn company page URL"
    )
    twitter_url: Optional[HttpUrl] = Field(
        default=None,
        description="Twitter profile URL"
    )
    github_url: Optional[HttpUrl] = Field(
        default=None,
        description="GitHub organization URL"
    )
    facebook_url: Optional[HttpUrl] = Field(
        default=None,
        description="Facebook page URL"
    )
    instagram_url: Optional[HttpUrl] = Field(
        default=None,
        description="Instagram profile URL"
    )
    contact_email: Optional[EmailStr] = Field(
        default=None,
        description="General contact email"
    )
    contact_phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Primary contact phone number"
    )
    tech_stack: Optional[List[str]] = Field(
        default=None,
        description="Technologies used by the company"
    )
    benefits: Optional[List[str]] = Field(
        default=None,
        description="Employee benefits offered"
    )
    mission: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Company mission statement"
    )
    values: Optional[List[str]] = Field(
        default=None,
        description="Company core values"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "description": "Updated company description...",
                "website": "https://new-website.example.com",
                "size": "501-1000",
                "tags": ["AI", "Machine Learning", "Cloud Computing"],
                "tech_stack": ["Python", "React", "AWS", "Kubernetes"],
                "benefits": ["Health Insurance", "Remote Work", "Stock Options"]
            }
        }

class CompanyPublic(CompanyBase):
    """Schema for public company data"""
    id: UUID
    slug: str
    created_at: datetime
    updated_at: datetime
    active_internships_count: int = 0
    social_links: Dict[str, Optional[str]]
    
    class Config:
        from_attributes = True
    
class CompanyFilter(SQLModel):
    """Filter options for querying companies"""
    search: Optional[str] = Field(
        default=None,
        description="Search term to filter by company name, description, or industry"
    )
    industry: Optional[List[str]] = Field(
        default=None,
        description="Filter by industry (exact match)"
    )
    industries: Optional[List[str]] = Field(
        default=None,
        description="Filter by multiple industries (OR match)"
    )
    size: Optional[List[CompanySize]] = Field(
        default=None,
        description="Filter by company size"
    )
    location: Optional[str] = Field(
        default=None,
        description="Filter by headquarters location (partial match)"
    )
    has_internships: Optional[bool] = Field(
        default=None,
        description="Filter companies that have active internships"
    )
    tech_stack: Optional[List[str]] = Field(
        default=None,
        description="Filter by technologies used by the company (AND match)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by company tags (AND match)"
    )
    min_employee_count: Optional[int] = Field(
        default=None,
        ge=1,
        description="Minimum number of employees"
    )
    max_employee_count: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of employees"
    )
    founded_after: Optional[int] = Field(
        default=None,
        ge=1800,
        le=datetime.now().year,
        description="Filter companies founded after this year"
    )
    founded_before: Optional[int] = Field(
        default=None,
        ge=1800,
        le=datetime.now().year,
        description="Filter companies founded before this year"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "search": "tech startup",
                "industries": ["Technology", "SaaS"],
                "size": ["1-10", "11-50"],
                "tech_stack": ["Python", "React"],
                "founded_after": 2010,
                "has_internships": True
            }
        }
