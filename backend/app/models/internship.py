from datetime import datetime
from typing import Optional, List, TYPE_CHECKING, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from uuid import UUID, uuid4

from .base import (
    BaseModel, 
    InternshipStatus, 
    ApplicationStatus,
    ContactMethod, 
    JobType, 
    WorkLocation, 
    ExperienceLevel,
    EducationLevel,
    SalaryFrequency,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin
)

if TYPE_CHECKING:
    from .user import User, Bookmark, Application
    from .company import Company

class InternshipBase(SQLModel):
    # Basic Information
    title: str = Field(..., max_length=255, description="Title of the internship position")
    description: str = Field(..., max_length=10000, description="Detailed description of the internship")
    
    # Requirements and Responsibilities
    requirements: List[str] = Field(
        default_factory=list, 
        sa_column=Column(JSONB),
        description="List of requirements for the internship"
    )
    responsibilities: List[str] = Field(
        default_factory=list, 
        sa_column=Column(JSONB),
        description="List of responsibilities for the intern"
    )
    benefits: List[str] = Field(
        default_factory=list, 
        sa_column=Column(JSONB),
        description="List of benefits offered"
    )
    skills: List[str] = Field(
        default_factory=list, 
        sa_column=Column(JSONB),
        description="List of required skills"
    )
    
    # Location Information
    location: str = Field(..., max_length=255, description="Physical location of the internship")
    work_location: WorkLocation = Field(
        default=WorkLocation.ONSITE,
        description="Type of work location (onsite, remote, hybrid)"
    )
    
    # Job Details
    job_type: JobType = Field(
        default=JobType.INTERNSHIP,
        description="Type of employment (full-time, part-time, etc.)"
    )
    experience_level: ExperienceLevel = Field(
        default=ExperienceLevel.ENTRY_LEVEL,
        description="Required experience level"
    )
    education_required: EducationLevel = Field(
        default=EducationLevel.BACHELORS,
        description="Minimum education level required"
    )
    
    # Dates
    posted_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the internship was posted"
    )
    application_deadline: Optional[datetime] = Field(
        default=None,
        description="Deadline for applications (if any)"
    )
    start_date: Optional[datetime] = Field(
        default=None,
        description="Expected start date of the internship"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Expected end date of the internship"
    )
    
    # Compensation
    salary_min: Optional[float] = Field(
        default=None,
        description="Minimum salary/compensation offered"
    )
    salary_max: Optional[float] = Field(
        default=None,
        description="Maximum salary/compensation offered"
    )
    salary_currency: str = Field(
        default="CAD",
        max_length=3,
        description="Currency of the salary (ISO 4217 code)"
    )
    salary_frequency: SalaryFrequency = Field(
        default=SalaryFrequency.YEARLY,
        description="Frequency of the salary payment"
    )
    
    # Status
    status: InternshipStatus = Field(
        default=InternshipStatus.DRAFT,
        description="Current status of the internship listing"
    )
    is_featured: bool = Field(
        default=False,
        description="Whether this internship is featured/promoted"
    )
    
    # Metadata
    source: str = Field(
        default="manual",
        description="Source of the internship listing (manual, indeed, etc.)"
    )
    source_id: Optional[str] = Field(
        default=None,
        index=True,
        description="ID from the source system"
    )
    source_url: Optional[str] = Field(
        default=None,
        description="URL to the original listing"
    )
    
    # Relationships
    company_id: UUID = Field(
        foreign_key="companies.id",
        description="Company offering the internship"
    )
    
class Internship(InternshipBase, BaseModel, table=True):
    __tablename__ = "internships"
    
    # Explicit primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    
    # Relationships
    company: "Company" = Relationship(back_populates="internships")
    posted_by_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    posted_by: Optional["User"] = Relationship(back_populates="internships")
    bookmarks: List["Bookmark"] = Relationship(back_populates="internship")
    applications: List["Application"] = Relationship(back_populates="internship")
    
    # Add indexes for common queries
    __table_args__ = {'extend_existing': True}  
    
    def __repr__(self) -> str:
        return f"<Internship {self.title} at {self.company.name if self.company else 'Unknown Company'}>"
    
    @property
    def is_active(self) -> bool:
        """Check if the internship is currently active"""
        now = datetime.utcnow()
        if self.status != InternshipStatus.PUBLISHED:
            return False
        if self.application_deadline and self.application_deadline < now:
            return False
        return True
    
    @property
    def application_count(self) -> int:
        """Get the number of applications for this internship"""
        return len(self.applications) if hasattr(self, 'applications') else 0
    
    # Search vector for full-text search
    search_vector: Optional[str] = Field(default=None, sa_type="tsvector")
    
    class Config:
        from_attributes = True

class InternshipCreate(InternshipBase):
    """Schema for creating a new internship"""
    company_id: UUID
    posted_by_id: Optional[UUID] = None
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Software Engineering Intern",
                "description": "Join our team as a software engineering intern...",
                "location": "Toronto, ON",
                "work_location": "hybrid",
                "job_type": "internship",
                "requirements": ["Python", "JavaScript", "Problem-solving skills"],
                "responsibilities": ["Develop features", "Write tests", "Code reviews"],
                "skills": ["Python", "Django", "React"],
                "company_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }

class InternshipUpdate(SQLModel):
    """Schema for updating an existing internship"""
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    work_location: Optional[WorkLocation] = None
    job_type: Optional[JobType] = None
    status: Optional[InternshipStatus] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_frequency: Optional[SalaryFrequency] = None
    application_deadline: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_featured: Optional[bool] = None
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Updated Software Engineering Intern",
                "location": "Vancouver, BC",
                "work_location": "remote",
                "salary_min": 50000,
                "salary_currency": "CAD",
                "salary_frequency": "yearly"
            }
        }
    
class InternshipPublic(InternshipBase):
    """Schema for public internship data"""
    id: UUID
    company: "CompanyPublic"
    posted_by: Optional["UserPublic"] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    application_count: int
    
    class Config:
        from_attributes = True
    
class InternshipFilter(SQLModel):
    """Filter options for querying internships"""
    search: Optional[str] = Field(
        default=None, 
        description="Search term to filter by title, description, or company name"
    )
    company_id: Optional[UUID] = Field(
        default=None,
        description="Filter by company ID"
    )
    location: Optional[str] = Field(
        default=None,
        description="Filter by location (partial match)"
    )
    work_location: Optional[List[WorkLocation]] = Field(
        default=None,
        description="Filter by work location type (onsite, remote, hybrid)"
    )
    job_type: Optional[List[JobType]] = Field(
        default=None,
        description="Filter by job type (full-time, part-time, etc.)"
    )
    experience_level: Optional[List[ExperienceLevel]] = Field(
        default=None,
        description="Filter by required experience level"
    )
    min_salary: Optional[float] = Field(
        default=None,
        ge=0,
        description="Filter by minimum salary (in specified currency)"
    )
    max_salary: Optional[float] = Field(
        default=None,
        ge=0,
        description="Filter by maximum salary (in specified currency)"
    )
    salary_currency: Optional[str] = Field(
        default="CAD",
        max_length=3,
        description="Currency for salary filters (ISO 4217 code)"
    )
    status: Optional[InternshipStatus] = Field(
        default=InternshipStatus.PUBLISHED,
        description="Filter by internship status"
    )
    posted_within_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Filter by number of days since posting"
    )
    skills: Optional[List[str]] = Field(
        default=None,
        description="Filter by required skills (AND match)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "search": "software engineer",
                "location": "Toronto",
                "work_location": ["remote", "hybrid"],
                "min_salary": 40000,
                "salary_currency": "CAD",
                "skills": ["Python", "Django"]
            }
        }
    
class BookmarkBase(SQLModel):
    """Base schema for internship bookmarks"""
    user_id: UUID = Field(foreign_key="users.id", description="ID of the user who bookmarked")
    internship_id: UUID = Field(foreign_key="internships.id", description="ID of the bookmarked internship")
    notes: Optional[str] = Field(
        default=None, 
        max_length=500, 
        description="Optional notes about the bookmark"
    )
    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="Tags for organizing bookmarks"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "internship_id": "223e4567-e89b-12d3-a456-426614174000",
                "notes": "Great opportunity with interesting tech stack",
                "tags": ["python", "remote"]
            }
        }
    
class Bookmark(BookmarkBase, BaseModel, table=True):
    __tablename__ = "bookmarks"
    
    # Explicit primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    
    # Relationships
    user: "User" = Relationship(back_populates="bookmarks")
    internship: "Internship" = Relationship(back_populates="bookmarks")
    
    # Table configuration
    __table_args__ = {'extend_existing': True}
    
    def __repr__(self) -> str:
        return f"<Bookmark user_id={self.user_id} internship_id={self.internship_id}>"
    
    class Config:
        from_attributes = True

class ApplicationBase(SQLModel):
    """Base schema for internship applications"""
    user_id: UUID = Field(foreign_key="users.id", description="ID of the applicant")
    internship_id: UUID = Field(foreign_key="internships.id", description="ID of the internship being applied to")
    status: ApplicationStatus = Field(
        default=ApplicationStatus.APPLIED,
        description="Current status of the application"
    )
    resume_id: Optional[UUID] = Field(
        default=None, 
        foreign_key="resumes.id",
        description="ID of the resume used for this application"
    )
    cover_letter: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Cover letter content (if required)"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Additional notes or comments about the application"
    )
    metadata_: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSONB),
        alias="metadata",
        description="Additional metadata about the application"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "internship_id": "223e4567-e89b-12d3-a456-426614174000",
                "status": "applied",
                "cover_letter": "I am excited to apply for this position...",
                "metadata": {
                    "application_source": "company_website",
                    "referred_by": "John Doe"
                }
            }
        }
    
class Application(ApplicationBase, BaseModel, table=True):
    __tablename__ = "applications"
    
    # Explicit primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    
    # Relationships
    user: "User" = Relationship(back_populates="applications")
    internship: "Internship" = Relationship(back_populates="applications")
    resume: Optional["Resume"] = Relationship(back_populates="applications")
    
    # Track application events
    submitted_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="When the application was submitted"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="When the application was last updated"
    )
    
    # Status tracking
    status_changed_at: Optional[datetime] = Field(
        default=None,
        description="When the status was last changed"
    )
    
    def __repr__(self) -> str:
        return f"<Application user_id={self.user_id} internship_id={self.internship_id} status={self.status}>"
    
    def update_status(self, new_status: ApplicationStatus) -> None:
        """Update the application status and track the change"""
        if new_status != self.status:
            self.status = new_status
            self.status_changed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    class Config:
        from_attributes = True
