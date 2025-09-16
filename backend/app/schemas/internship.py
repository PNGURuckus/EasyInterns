from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, validator
from app.models.base import JobType, WorkLocation, ExperienceLevel, SalaryFrequency

class InternshipBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str
    requirements: str
    responsibilities: str
    location: str
    location_type: WorkLocation
    employment_type: JobType
    experience_level: ExperienceLevel
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    is_active: bool = True
    application_deadline: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    benefits: Optional[List[str]] = None
    skills: List[str] = Field(default_factory=list)
    company_id: UUID
    posted_by: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None

class InternshipCreate(InternshipBase):
    pass

class InternshipUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    location: Optional[str] = None
    location_type: Optional[WorkLocation] = None
    employment_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    is_active: Optional[bool] = None
    application_deadline: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    benefits: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class InternshipInDBBase(InternshipBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    view_count: int = 0
    application_count: int = 0
    
    class Config:
        orm_mode = True

class Internship(InternshipInDBBase):
    pass

class InternshipInDB(InternshipInDBBase):
    pass

class InternshipSearchResults(BaseModel):
    results: List[Internship]
    total: int
    page: int
    limit: int
    total_pages: int

class InternshipStats(BaseModel):
    total_internships: int
    active_internships: int
    avg_salary: Optional[float]
    min_salary: Optional[float]
    max_salary: Optional[float]
    by_employment_type: Dict[str, int]
    by_experience_level: Dict[str, int]
    by_location: Dict[str, int]
    by_company: Dict[str, int]
