from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union
from sqlmodel import SQLModel, Field, Relationship, Column, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TSVECTOR
from pydantic import validator, HttpUrl, EmailStr, constr, conlist, BaseModel
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from enum import Enum, auto

from .base import (
    BaseModel as BaseDBModel,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    ConfigMixin
)

if TYPE_CHECKING:
    from .user import User
    from .internship import Internship
    from .resume import Resume

class ApplicationStatus(str, Enum):
    """Status of a job application"""
    DRAFT = "draft"  # Application is being worked on
    APPLIED = "applied"  # Application submitted
    UNDER_REVIEW = "under_review"  # Application is being reviewed
    SCREENING = "screening"  # Initial screening (resume/phone)
    INTERVIEWING = "interviewing"  # In interview process
    ASSESSMENT = "assessment"  # Technical/coding assessment
    REFERENCE_CHECK = "reference_check"  # Checking references
    OFFER_PENDING = "offer_pending"  # Offer is being prepared
    OFFER_EXTENDED = "offer_extended"  # Offer made to candidate
    OFFER_ACCEPTED = "offer_accepted"  # Offer accepted
    OFFER_DECLINED = "offer_declined"  # Offer declined
    HIRED = "hired"  # Candidate hired
    REJECTED = "rejected"  # Application rejected
    WITHDRAWN = "withdrawn"  # Candidate withdrew
    CLOSED = "closed"  # Position filled by someone else
    
    @classmethod
    def get_ordered_statuses(cls) -> List[str]:
        """Get statuses in their natural progression order"""
        return [
            cls.DRAFT,
            cls.APPLIED,
            cls.UNDER_REVIEW,
            cls.SCREENING,
            cls.INTERVIEWING,
            cls.ASSESSMENT,
            cls.REFERENCE_CHECK,
            cls.OFFER_PENDING,
            cls.OFFER_EXTENDED,
            cls.OFFER_ACCEPTED,
            cls.HIRED,
            cls.OFFER_DECLINED,
            cls.REJECTED,
            cls.WITHDRAWN,
            cls.CLOSED
        ]

class ApplicationSource(str, Enum):
    """Where the application originated from"""
    COMPANY_WEBSITE = "company_website"
    JOB_BOARD = "job_board"
    REFERRAL = "referral"
    RECRUITER = "recruiter"
    CAREER_FAIR = "career_fair"
    NETWORKING = "networking"
    COLD_APPLICATION = "cold_application"
    INTERNAL_REFERRAL = "internal_referral"
    CAMPUS_RECRUITING = "campus_recruiting"
    OTHER = "other"

class ApplicationStage(str, Enum):
    """Current stage in the application process"""
    APPLICATION = "application"
    SCREENING = "screening"
    ASSESSMENT = "assessment"
    INTERVIEW = "interview"
    FINAL_INTERVIEW = "final_interview"
    REFERENCE_CHECK = "reference_check"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"

class Application(BaseDBModel, TimestampMixin, SoftDeleteMixin, AuditMixin, table=True):
    """Model representing a job application"""
    __tablename__ = "applications"
    __table_args__ = {'extend_existing': True}
    
    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    
    # Foreign keys
    user_id: UUID = Field(
        ...,
        foreign_key="users.id",
        index=True,
        description="ID of the user who submitted the application"
    )
    internship_id: UUID = Field(
        ...,
        foreign_key="internships.id",
        index=True,
        description="ID of the internship being applied for"
    )
    resume_id: UUID = Field(
        ...,
        foreign_key="resumes.id",
        description="ID of the resume used for this application"
    )
    
    # Core fields
    status: ApplicationStatus = Field(
        default=ApplicationStatus.DRAFT,
        index=True,
        description="Current status of the application"
    )
    stage: ApplicationStage = Field(
        default=ApplicationStage.APPLICATION,
        index=True,
        description="Current stage in the application process"
    )
    source: ApplicationSource = Field(
        default=ApplicationSource.COMPANY_WEBSITE,
        description="How the applicant found this position"
    )
    
    # Application details
    cover_letter: Optional[str] = Field(
        default=None,
        description="Cover letter content"
    )
    answers: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Responses to application questions"
    )
    
    # Tracking
    applied_at: Optional[datetime] = Field(
        default=None,
        index=True,
        description="When the application was submitted"
    )
    last_status_change: Optional[datetime] = Field(
        default=None,
        description="When the status was last changed"
    )
    
    # Relationships
    user: "User" = Relationship(back_populates="applications")
    internship: "Internship" = Relationship(back_populates="applications")
    resume: "Resume" = Relationship(back_populates="applications")
    
    # Activity tracking
    activity_log: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="Log of all activities related to this application"
    )
    
    # Metadata
    is_archived: bool = Field(
        default=False,
        index=True,
        description="Whether this application is archived"
    )
    is_referral: bool = Field(
        default=False,
        description="Whether this application came through a referral"
    )
    referral_details: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Details about the referral, if applicable"
    )
    
    # Computed properties
    @property
    def days_since_applied(self) -> Optional[int]:
        """Number of days since the application was submitted"""
        if not self.applied_at:
            return None
        return (datetime.utcnow() - self.applied_at).days
    
    @property
    def is_active(self) -> bool:
        """Whether this application is still active"""
        return self.status not in [
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.CLOSED,
            ApplicationStatus.OFFER_DECLINED
        ]
    
    @property
    def needs_follow_up(self) -> bool:
        """Whether this application needs follow-up"""
        if not self.last_status_change:
            return False
            
        # If it's been more than 7 days since last update and still in early stages
        days_since_update = (datetime.utcnow() - self.last_status_change).days
        return (
            days_since_update > 7 and 
            self.status in [
                ApplicationStatus.APPLIED,
                ApplicationStatus.UNDER_REVIEW,
                ApplicationStatus.SCREENING
            ]
        )
    
    # Methods
    def add_activity(self, activity_type: str, details: Dict[str, Any], user_id: Optional[UUID] = None) -> None:
        """Add an activity to the log"""
        activity = {
            "id": str(uuid4()),
            "type": activity_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "user_id": str(user_id) if user_id else None
        }
        self.activity_log = self.activity_log or []
        self.activity_log.append(activity)
    
    def update_status(self, new_status: ApplicationStatus, notes: Optional[str] = None, user_id: Optional[UUID] = None) -> None:
        """Update the application status and log the change"""
        old_status = self.status
        self.status = new_status
        self.last_status_change = datetime.utcnow()
        
        if new_status == ApplicationStatus.APPLIED and not self.applied_at:
            self.applied_at = datetime.utcnow()
        
        # Log the status change
        self.add_activity(
            activity_type="status_change",
            details={
                "old_status": old_status,
                "new_status": new_status,
                "notes": notes
            },
            user_id=user_id
        )
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }

class ApplicationCreate(SQLModel):
    """Schema for creating a new application"""
    internship_id: UUID = Field(..., description="ID of the internship to apply for")
    resume_id: UUID = Field(..., description="ID of the resume to use for this application")
    cover_letter: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Cover letter content"
    )
    answers: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Responses to application questions"
    )
    source: ApplicationSource = Field(
        default=ApplicationSource.COMPANY_WEBSITE,
        description="How you found this position"
    )
    is_referral: bool = Field(
        default=False,
        description="Whether this is a referral application"
    )
    referral_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Referral details if this is a referral"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "internship_id": "123e4567-e89b-12d3-a456-426614174000",
                "resume_id": "223e4567-e89b-12d3-a456-426614174001",
                "cover_letter": "Dear Hiring Manager...",
                "source": "company_website",
                "is_referral": True,
                "referral_details": {
                    "referrer_name": "Jane Smith",
                    "referrer_email": "jane.smith@example.com",
                    "relationship": "Former Colleague"
                },
                "answers": {
                    "eligibility": "Yes, I am authorized to work in Canada",
                    "availability": "Available to start in 2 weeks",
                    "salary_expectations": "Negotiable based on the total compensation package"
                }
            }
        }

class ApplicationUpdate(SQLModel):
    """Schema for updating an existing application"""
    status: Optional[ApplicationStatus] = Field(
        default=None,
        description="New status for the application"
    )
    stage: Optional[ApplicationStage] = Field(
        default=None,
        description="Current stage in the application process"
    )
    cover_letter: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Updated cover letter content"
    )
    answers: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated responses to application questions"
    )
    is_archived: Optional[bool] = Field(
        default=None,
        description="Whether to archive this application"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Private notes about this application"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "status": "interviewing",
                "stage": "interview",
                "is_archived": False,
                "notes": "Phone interview scheduled for next Tuesday at 2pm"
            }
        }

class ApplicationPublic(SQLModel):
    """Schema for public application data"""
    id: UUID
    status: ApplicationStatus
    stage: ApplicationStage
    source: ApplicationSource
    applied_at: Optional[datetime] = None
    last_status_change: Optional[datetime] = None
    is_archived: bool = False
    is_referral: bool = False
    
    # Related data
    internship: Dict[str, Any]
    resume: Dict[str, Any]
    
    # Computed fields
    days_since_applied: Optional[int] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }

class ApplicationFilter(SQLModel):
    """Filter options for querying applications"""
    status: Optional[List[ApplicationStatus]] = Field(
        default=None,
        description="Filter by application status"
    )
    stage: Optional[List[ApplicationStage]] = Field(
        default=None,
        description="Filter by application stage"
    )
    source: Optional[List[ApplicationSource]] = Field(
        default=None,
        description="Filter by application source"
    )
    is_archived: Optional[bool] = Field(
        default=None,
        description="Filter by archived status"
    )
    is_referral: Optional[bool] = Field(
        default=None,
        description="Filter by referral status"
    )
    applied_after: Optional[date] = Field(
        default=None,
        description="Filter by applications submitted after this date"
    )
    applied_before: Optional[date] = Field(
        default=None,
        description="Filter by applications submitted before this date"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search term to filter applications by company name, position, or notes"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "status": ["applied", "under_review", "interviewing"],
                "is_archived": False,
                "applied_after": "2023-01-01",
                "search": "software engineer"
            }
        }

class ApplicationActivityCreate(SQLModel):
    """Schema for adding an activity to an application"""
    type: str = Field(..., description="Type of activity")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Details about the activity"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="When the activity occurred (defaults to now)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "type": "interview_scheduled",
                "details": {
                    "interview_type": "technical",
                    "scheduled_time": "2023-06-15T14:30:00Z",
                    "interviewers": ["John Doe", "Jane Smith"],
                    "location": "Zoom Meeting",
                    "notes": "Focus on algorithms and system design"
                }
            }
        }

class ApplicationStats(SQLModel):
    """Statistics about applications"""
    total: int = 0
    by_status: Dict[ApplicationStatus, int] = {}
    by_stage: Dict[ApplicationStage, int] = {}
    by_source: Dict[ApplicationSource, int] = {}
    by_month: Dict[str, int] = {}
    
    class Config:
        from_attributes = True
        json_encoders = {
            ApplicationStatus: lambda x: x.value,
            ApplicationStage: lambda x: x.value,
            ApplicationSource: lambda x: x.value
        }
