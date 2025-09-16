"""
Application-related schemas
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field, validator
from uuid import UUID

from .common import Status, TimestampMixin, SoftDeleteMixin, ResponseModel, PaginatedResponse

class ApplicationStatus(str, Enum):
    """Status of a job application"""
    DRAFT = "draft"
    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    ASSESSMENT = "assessment"
    REFERENCE_CHECK = "reference_check"
    OFFER_PENDING = "offer_pending"
    OFFER_EXTENDED = "offer_extended"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    CLOSED = "closed"

    @classmethod
    def get_ordered_statuses(cls):
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
            cls.OFFER_DECLINED,
            cls.HIRED,
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

class ApplicationBase(BaseModel):
    """Base schema for Application"""
    status: ApplicationStatus = Field(
        default=ApplicationStatus.DRAFT,
        description="Current status of the application"
    )
    stage: ApplicationStage = Field(
        default=ApplicationStage.APPLICATION,
        description="Current stage in the application process"
    )
    source: ApplicationSource = Field(
        default=ApplicationSource.COMPANY_WEBSITE,
        description="How the application was submitted"
    )
    is_archived: bool = Field(
        default=False,
        description="Whether the application is archived"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Private notes about the application"
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional custom fields for the application"
    )

class ApplicationCreate(ApplicationBase):
    """Schema for creating a new application"""
    internship_id: UUID = Field(..., description="ID of the internship being applied to")
    resume_id: UUID = Field(..., description="ID of the resume being used")
    cover_letter_id: Optional[UUID] = Field(
        None,
        description="ID of the cover letter (if any)"
    )

class ApplicationUpdate(ApplicationBase):
    """Schema for updating an existing application"""
    status: Optional[ApplicationStatus] = None
    stage: Optional[ApplicationStage] = None
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class ApplicationInDBBase(ApplicationBase, TimestampMixin, SoftDeleteMixin):
    """Base database model for Application"""
    id: UUID
    user_id: UUID
    internship_id: UUID
    resume_id: UUID
    cover_letter_id: Optional[UUID] = None
    applied_at: Optional[datetime] = None
    last_status_change: Optional[datetime] = None

    class Config:
        orm_mode = True

class Application(ApplicationInDBBase):
    """Full Application model with relationships"""
    pass

class ApplicationPublic(BaseModel):
    """Public view of an application (safe to expose)"""
    id: UUID
    status: ApplicationStatus
    stage: ApplicationStage
    source: ApplicationSource
    applied_at: Optional[datetime] = None
    last_status_change: Optional[datetime] = None
    is_archived: bool = False
    is_referral: bool = False
    internship: Dict[str, Any] = Field(
        default_factory=dict,
        description="Basic internship details"
    )
    resume: Dict[str, Any] = Field(
        default_factory=dict,
        description="Basic resume details"
    )
    days_since_applied: Optional[int] = Field(
        None,
        description="Number of days since application was submitted"
    )
    is_active: bool = Field(
        True,
        description="Whether the application is currently active"
    )

    class Config:
        orm_mode = True

class ApplicationInDB(ApplicationInDBBase):
    """Application model for database operations"""
    pass

# Response models
class ApplicationResponse(ResponseModel[Application]):
    """Response model for a single application"""
    pass

class ApplicationListResponse(PaginatedResponse[Application]):
    """Response model for paginated list of applications"""
    pass
