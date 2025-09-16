from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TSVECTOR
from pydantic import validator, HttpUrl, EmailStr, constr, conlist
from uuid import UUID, uuid4
from datetime import datetime, date
from enum import Enum

from .base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    ConfigMixin
)

if TYPE_CHECKING:
    from .user import User
    from .application import Application

class ResumeTemplate(str, Enum):
    """Available resume template designs"""
    ATS_CLEAN = "ats_clean"  # Optimized for ATS systems
    TWO_COLUMN = "two_column"  # Modern two-column layout
    CREATIVE_ACCENT = "creative_accent"  # For creative fields
    COMPACT_STUDENT = "compact_student"  # For students/entry-level
    EXECUTIVE = "executive"  # For experienced professionals
    MINIMALIST = "minimalist"  # Clean and simple design
    TIMELINE = "timeline"  # Chronological focus
    SKILLS_FIRST = "skills_first"  # Emphasizes skills section

class ContactMethod(str, Enum):
    """Preferred contact methods"""
    EMAIL = "email"
    PHONE = "phone"
    LINKEDIN = "linkedin"
    PORTFOLIO = "portfolio"

class ResumeStatus(str, Enum):
    """Status of the resume"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    TEMPLATE = "template"

class ExperienceLevel(str, Enum):
    """Professional experience level"""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"

class LanguageProficiency(str, Enum):
    """Language proficiency levels"""
    NATIVE = "native"
    FLUENT = "fluent"
    PROFICIENT = "proficient"
    INTERMEDIATE = "intermediate"
    BASIC = "basic"

class SkillLevel(str, Enum):
    """Skill proficiency levels"""
    NOVICE = "novice"
    BEGINNER = "beginner"
    COMPETENT = "competent"
    PROFICIENT = "proficient"
    EXPERT = "expert"

class EducationType(str, Enum):
    """Types of education"""
    DEGREE = "degree"
    DIPLOMA = "diploma"
    CERTIFICATE = "certificate"
    BOOTCAMP = "bootcamp"
    COURSE = "course"
    SELF_STUDY = "self_study"

class ResumeBase(SQLModel):
    """Base model for resume with all fields and validation"""
    # Core Metadata
    user_id: UUID = Field(
        ..., 
        foreign_key="users.id",
        description="ID of the user who owns this resume"
    )
    title: str = Field(
        ..., 
        max_length=100,
        description="Title/name of this resume version"
    )
    template: ResumeTemplate = Field(
        default=ResumeTemplate.ATS_CLEAN,
        description="Template design to use for this resume"
    )
    status: ResumeStatus = Field(
        default=ResumeStatus.DRAFT,
        description="Current status of the resume"
    )
    
    # Personal Information
    full_name: str = Field(
        ..., 
        max_length=100,
        description="Full legal name for the resume"
    )
    professional_title: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Professional title/headline"
    )
    email: EmailStr = Field(
        ...,
        description="Professional email address"
    )
    phone: Optional[constr(max_length=25)] = Field(
        default=None,
        description="Contact phone number with country code"
    )
    website: Optional[HttpUrl] = Field(
        default=None,
        description="Personal website or portfolio URL"
    )
    linkedin_url: Optional[HttpUrl] = Field(
        default=None,
        description="LinkedIn profile URL"
    )
    github_url: Optional[HttpUrl] = Field(
        default=None,
        description="GitHub profile URL"
    )
    location: Optional[str] = Field(
        default=None,
        max_length=100,
        description="City, Country format preferred"
    )
    preferred_contact: Optional[ContactMethod] = Field(
        default=ContactMethod.EMAIL,
        description="Preferred method of contact"
    )
    
    # Professional Summary
    summary: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Professional summary/objective statement"
    )
    
    # Experience
    experience: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="List of work experiences with details"
    )
    
    # Education
    education: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="List of education entries"
    )
    
    # Skills
    skills: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="List of skills with proficiency levels"
    )
    
    # Projects
    projects: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="List of relevant projects"
    )
    
    # Certifications
    certifications: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="List of professional certifications"
    )
    
    # Languages
    languages: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="List of languages with proficiency levels"
    )
    
    # Custom sections
    custom_sections: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="Custom sections that don't fit standard categories"
    )
    
    # Styling and Formatting
    styles: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="CSS styles and formatting options"
    )
    
    # Metadata
    is_public: bool = Field(
        default=False,
        description="Whether this resume is publicly accessible"
    )
    is_default: bool = Field(
        default=False,
        description="Whether this is the user's default resume"
    )
    experience_level: Optional[ExperienceLevel] = Field(
        default=None,
        description="Target experience level for this resume"
    )
    target_roles: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Target job roles/positions"
    )
    target_industries: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Target industries"
    )
    
    # SEO and Discoverability
    seo_keywords: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Keywords for search optimization"
    )
    
    # Validation
    @validator('experience')
    def validate_experience(cls, v):
        if not v:
            return v
        for exp in v:
            if not all(k in exp for k in ['title', 'company', 'start_date']):
                raise ValueError("Experience entries must include title, company, and start_date")
        return v
    
    @validator('education')
    def validate_education(cls, v):
        if not v:
            return v
        for edu in v:
            if not all(k in edu for k in ['institution', 'degree', 'field_of_study', 'start_date']):
                raise ValueError("Education entries must include institution, degree, field_of_study, and start_date")
        return v
    
    @validator('skills')
    def validate_skills(cls, v):
        if not v:
            return v
        for skill in v:
            if 'name' not in skill:
                raise ValueError("Skills must have a 'name' field")
        return v

class Resume(ResumeBase, BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin, table=True):
    __tablename__ = "resumes"
    
    # Database fields
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    
    # Additional DB-only fields
    version: int = Field(
        default=1,
        description="Version number of the resume"
    )
    slug: str = Field(
        default=None,
        index=True,
        nullable=False,
        description="URL-friendly version of the resume title"
    )
    
    # Full-text search
    search_vector: Optional[str] = Field(
        default=None,
        sa_type=TSVECTOR,
        description="Full-text search vector for searching resume content"
    )
    
    # Relationships
    user: "User" = Relationship(back_populates="resumes")
    applications: List["Application"] = Relationship(back_populates="resume")
    
    # Computed properties
    @property
    def last_updated(self) -> datetime:
        """Get the last updated timestamp"""
        return self.updated_at or self.created_at
    
    @property
    def is_ats_friendly(self) -> bool:
        """Check if the resume is ATS-friendly"""
        # Simple heuristic for ATS friendliness
        has_skills = len(self.skills) >= 5
        has_experience = len(self.experience) > 0
        has_education = len(self.education) > 0
        has_contact = bool(self.email and (self.phone or self.website))
        return all([has_skills, has_experience, has_education, has_contact])
    
    @property
    def word_count(self) -> int:
        """Approximate word count of the resume content"""
        content = f"{self.summary or ''} {' '.join(exp.get('description', '') for exp in self.experience)}"
        return len(content.split())
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
    
    # File storage
    pdf_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class ResumeCreate(ResumeBase):
    """Schema for creating a new resume"""
    user_id: UUID  # Required for creation
    title: str  # Required for creation
    full_name: str  # Required for creation
    email: EmailStr  # Required for creation
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Software Developer Resume",
                "full_name": "Alex Johnson",
                "email": "alex.johnson@example.com",
                "professional_title": "Senior Software Engineer",
                "phone": "+14165551234",
                "location": "Toronto, ON, Canada",
                "summary": "Experienced software engineer with 5+ years of full-stack development...",
                "status": "draft",
                "experience_level": "senior",
                "target_roles": ["Senior Software Engineer", "Tech Lead"],
                "target_industries": ["Technology", "SaaS", "Fintech"]
            }
        }

class ResumeUpdate(SQLModel):
    """Schema for updating an existing resume"""
    # Core Metadata
    title: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Title/name of this resume version"
    )
    template: Optional[ResumeTemplate] = Field(
        default=None,
        description="Template design to use for this resume"
    )
    status: Optional[ResumeStatus] = Field(
        default=None,
        description="Current status of the resume"
    )
    
    # Personal Information
    full_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Full legal name for the resume"
    )
    professional_title: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Professional title/headline"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Professional email address"
    )
    phone: Optional[constr(max_length=25)] = Field(
        default=None,
        description="Contact phone number with country code"
    )
    website: Optional[HttpUrl] = Field(
        default=None,
        description="Personal website or portfolio URL"
    )
    linkedin_url: Optional[HttpUrl] = Field(
        default=None,
        description="LinkedIn profile URL"
    )
    github_url: Optional[HttpUrl] = Field(
        default=None,
        description="GitHub profile URL"
    )
    location: Optional[str] = Field(
        default=None,
        max_length=100,
        description="City, Country format preferred"
    )
    preferred_contact: Optional[ContactMethod] = Field(
        default=None,
        description="Preferred method of contact"
    )
    
    # Content Sections
    summary: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Professional summary/objective statement"
    )
    experience: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of work experiences with details"
    )
    education: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of education entries"
    )
    skills: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of skills with proficiency levels"
    )
    projects: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of relevant projects"
    )
    certifications: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of professional certifications"
    )
    languages: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of languages with proficiency levels"
    )
    custom_sections: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Custom sections that don't fit standard categories"
    )
    
    # Styling and Formatting
    styles: Optional[Dict[str, Any]] = Field(
        default=None,
        description="CSS styles and formatting options"
    )
    
    # Metadata
    is_public: Optional[bool] = Field(
        default=None,
        description="Whether this resume is publicly accessible"
    )
    is_default: Optional[bool] = Field(
        default=None,
        description="Whether this is the user's default resume"
    )
    experience_level: Optional[ExperienceLevel] = Field(
        default=None,
        description="Target experience level for this resume"
    )
    target_roles: Optional[List[str]] = Field(
        default=None,
        description="Target job roles/positions"
    )
    target_industries: Optional[List[str]] = Field(
        default=None,
        description="Target industries"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Updated Software Developer Resume",
                "professional_title": "Senior Full-Stack Developer",
                "summary": "Updated summary with more experience...",
                "status": "published",
                "is_public": True,
                "is_default": True,
                "target_roles": ["Senior Software Engineer", "Tech Lead", "Engineering Manager"],
                "styles": {
                    "font_family": "Arial, sans-serif",
                    "primary_color": "#2563eb",
                    "secondary_color": "#1e40af"
                }
            }
        }

class ResumePublic(ResumeBase):
    """Schema for public resume data"""
    id: UUID
    slug: str
    version: int
    created_at: datetime
    updated_at: datetime
    is_ats_friendly: bool = False
    word_count: int = 0
    
    # URLs for generated assets
    pdf_url: Optional[HttpUrl] = None
    docx_url: Optional[HttpUrl] = None
    thumbnail_url: Optional[HttpUrl] = None
    share_url: Optional[HttpUrl] = None
    
    # View counts (for public resumes)
    view_count: int = 0
    last_viewed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
    
class ResumeExport(SQLModel):
    """Options for exporting a resume to different formats"""
    format: str = Field(
        default="pdf",
        regex="^(pdf|docx|txt|json|html|md)$",
        description="Export format"
    )
    include_contact: bool = Field(
        default=True,
        description="Include contact information"
    )
    include_photo: bool = Field(
        default=False,
        description="Include profile photo if available"
    )
    include_references: bool = Field(
        default=False,
        description="Include references section if available"
    )
    include_custom_sections: bool = Field(
        default=True,
        description="Include custom sections"
    )
    page_size: str = Field(
        default="letter",
        regex="^(letter|a4|a3|legal)$",
        description="Page size for PDF exports"
    )
    margin: str = Field(
        default="normal",
        regex="^(narrow|normal|moderate|wide)$",
        description="Page margins"
    )
    font_size: int = Field(
        default=11,
        ge=8,
        le=14,
        description="Base font size in points"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "format": "pdf",
                "include_contact": True,
                "include_photo": False,
                "page_size": "a4",
                "margin": "normal",
                "font_size": 11
            }
        }
    
class ResumeAIGenerate(SQLModel):
    """Options for AI-assisted resume generation"""
    job_description: str = Field(
        ...,
        min_length=50,
        max_length=5000,
        description="Job description to tailor the resume for"
    )
    tone: str = Field(
        default="professional",
        regex="^(professional|executive|technical|creative|academic)$",
        description="Writing style tone"
    )
    length: str = Field(
        default="standard",
        regex="^(brief|standard|detailed|comprehensive)$",
        description="Level of detail in the generated content"
    )
    include_metrics: bool = Field(
        default=True,
        description="Include quantifiable achievements and metrics"
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        max_items=5,
        description="Key areas to emphasize in the resume"
    )
    keywords: List[str] = Field(
        default_factory=list,
        max_items=20,
        description="Keywords to include for ATS optimization"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "job_description": "We are looking for a Senior Software Engineer with 5+ years of experience...",
                "tone": "technical",
                "length": "detailed",
                "include_metrics": True,
                "focus_areas": ["backend development", "system architecture", "team leadership"],
                "keywords": ["Python", "Django", "AWS", "Microservices", "Docker", "Kubernetes"]
            }
        }

class ResumeAIAnalyze(SQLModel):
    """Options for AI resume analysis"""
    job_description: Optional[str] = Field(
        default=None,
        min_length=50,
        max_length=5000,
        description="Job description to analyze against"
    )
    check_ats: bool = Field(
        default=True,
        description="Check ATS compatibility"
    )
    check_readability: bool = Field(
        default=True,
        description="Check readability and clarity"
    )
    check_impact: bool = Field(
        default=True,
        description="Check for impact and achievements"
    )
    check_skills: bool = Field(
        default=True,
        description="Check skills relevance and completeness"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "job_description": "Senior Developer position requiring...",
                "check_ats": True,
                "check_readability": True,
                "check_impact": True,
                "check_skills": True
            }
        }

class ResumeAIAnalysis(SQLModel):
    """Results of AI resume analysis"""
    overall_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall resume quality score (0-100)"
    )
    ats_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="ATS compatibility score if checked"
    )
    readability_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Readability score if checked"
    )
    impact_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Impact/achievements score if checked"
    )
    skills_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Skills relevance score if checked"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="List of resume strengths"
    )
    areas_for_improvement: List[str] = Field(
        default_factory=list,
        description="List of suggested improvements"
    )
    missing_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords from job description missing in resume"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "overall_score": 78,
                "ats_score": 82,
                "readability_score": 75,
                "impact_score": 70,
                "skills_score": 85,
                "strengths": [
                    "Strong technical skills section",
                    "Good use of action verbs",
                    "Clear work history"
                ],
                "areas_for_improvement": [
                    "Add more quantifiable achievements",
                    "Include more industry keywords",
                    "Expand on leadership experience"
                ],
                "missing_keywords": ["Docker", "AWS", "Agile"]
            }
        }
