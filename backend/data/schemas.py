"""
Pydantic v2 schemas for API requests/responses
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.data.models import FieldTag, Modality, ConfidenceLevel


# Request Schemas
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    fields_of_interest: Optional[List[FieldTag]] = None
    skills: Optional[List[str]] = None


class InternshipSearchParams(BaseModel):
    q: Optional[str] = None  # Search query
    field: Optional[List[FieldTag]] = None
    skills: Optional[List[str]] = None
    country: Optional[str] = "Canada"
    region: Optional[str] = None  # Province/State
    city: Optional[str] = None
    modality: Optional[List[Modality]] = None
    salary_min: Optional[int] = None
    posted_within_days: Optional[int] = None
    source: Optional[List[str]] = None
    sort: str = Field(default="relevance")  # relevance, date, salary
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    include_low_confidence: bool = Field(default=False)


class ResumeCreate(BaseModel):
    name: str
    template_key: str
    json_data: Dict[str, Any]


class ResumeUpdate(BaseModel):
    name: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None


class BookmarkCreate(BaseModel):
    internship_id: int
    notes: Optional[str] = None


# Response Schemas
class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    domain: Optional[str]
    logo_url: Optional[str]
    description: Optional[str]
    headquarters_city: Optional[str]
    headquarters_region: Optional[str]
    headquarters_country: Optional[str]
    size_category: Optional[str]
    industry: Optional[str]


class ContactEmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    confidence_score: float
    confidence_level: ConfidenceLevel
    email_type: str
    name: Optional[str]
    title: Optional[str]
    mx_verified: bool


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    display_name: str
    source_type: str


class InternshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: str
    field_tag: FieldTag
    city: Optional[str]
    region: Optional[str]
    country: str
    modality: Modality
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: str
    duration_months: Optional[int]
    apply_url: str
    posted_at: Optional[datetime]
    expires_at: Optional[datetime]
    skills_required: List[str]
    education_level: Optional[str]
    experience_level: Optional[str]
    government_program: bool
    relevance_score: Optional[float]
    created_at: datetime
    
    # Related objects
    company: CompanyResponse
    source: SourceResponse


class InternshipDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    internship: InternshipResponse
    contact_emails: List[ContactEmailResponse]
    is_bookmarked: bool = False


class SearchFacet(BaseModel):
    key: str
    count: int


class SearchFacets(BaseModel):
    fields: List[SearchFacet]
    regions: List[SearchFacet]
    cities: List[SearchFacet]
    modalities: List[SearchFacet]
    sources: List[SearchFacet]
    government_programs: int


class InternshipListResponse(BaseModel):
    items: List[InternshipResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    facets: SearchFacets


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    name: Optional[str]
    city: Optional[str]
    region: Optional[str]
    country: str
    fields_of_interest: List[FieldTag]
    skills: List[str]
    created_at: datetime


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    template_key: str
    json_data: Dict[str, Any]
    pdf_url: Optional[str]
    pdf_generated_at: Optional[datetime]
    ai_enhanced: bool
    ai_enhanced_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    notes: Optional[str]
    created_at: datetime
    internship: InternshipResponse


class ScrapeJobResponse(BaseModel):
    job_id: str
    status: str  # "queued", "running", "completed", "failed"
    source: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    items_scraped: Optional[int]
    error_message: Optional[str]


# AI Enhancement Schemas
class AIEnhanceRequest(BaseModel):
    resume_id: int
    target_field: Optional[FieldTag] = None
    target_internship_id: Optional[int] = None


class AIEnhanceResponse(BaseModel):
    enhanced_summary: Optional[str]
    enhanced_bullets: List[str]
    tailored_keywords: List[str]
