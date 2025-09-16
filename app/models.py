from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, JSON, Text
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import relationship


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True)
    email: str = Field(index=True)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    school: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    skills: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    interests: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # No relationships required for tests

    @property
    def full_name(self) -> str:
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts)


class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    domain: Optional[str] = Field(default=None, index=True)
    description: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    headquarters: Optional[str] = None

    # Relationships defined after class declarations


class Source(SQLModel, table=True):
    __tablename__ = "sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    display_name: str
    base_url: Optional[str] = None
    is_active: bool = Field(default=True)
    rate_limit: Optional[int] = None
    last_scraped: Optional[datetime] = None


class Internship(SQLModel, table=True):
    __tablename__ = "internships"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    company_id: int = Field(foreign_key="companies.id", index=True)
    location: Optional[str] = Field(default=None, index=True)
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_min: Optional[float] = Field(default=None, index=True)
    salary_max: Optional[float] = Field(default=None, index=True)
    modality: Optional[str] = Field(default=None, index=True)
    field_tag: Optional[str] = Field(default=None, index=True)
    apply_url: str
    source: Optional[str] = Field(default=None, index=True)
    external_id: Optional[str] = Field(default=None, index=True)
    posting_date: Optional[date] = Field(default=None, index=True)
    application_deadline: Optional[date] = Field(default=None, index=True)
    is_government: bool = Field(default=False, index=True)
    is_active: bool = Field(default=True, index=True)
    relevance_score: Optional[float] = Field(default=None, index=True)
    source_id: Optional[int] = Field(default=None, foreign_key="sources.id")
    # Freshness tracking
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    last_checked_at: Optional[datetime] = Field(default=None, index=True)

    # Relationships defined after class declarations

    @property
    def salary_range(self) -> str:
        if self.salary_min and self.salary_max:
            return f"${int(self.salary_min):,} - ${int(self.salary_max):,}"
        if self.salary_min and not self.salary_max:
            return f"${int(self.salary_min):,}+"
        if self.salary_max and not self.salary_min:
            return f"Up to ${int(self.salary_max):,}"
        return "Not specified"


class ContactEmail(SQLModel, table=True):
    __tablename__ = "contact_emails"

    id: Optional[int] = Field(default=None, primary_key=True)
    internship_id: int = Field(foreign_key="internships.id", index=True)
    email: str = Field(index=True)
    confidence_score: float = Field(index=True)
    extraction_method: Optional[str] = None
    name: Optional[str] = None

    # Relationship defined after class declarations


class Resume(SQLModel, table=True):
    __tablename__ = "resumes"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    title: str
    template: str
    content: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    is_ai_enhanced: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Bookmark(SQLModel, table=True):
    __tablename__ = "bookmarks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    internship_id: int = Field(foreign_key="internships.id", index=True)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # No relationship properties required for current tests


from pydantic import ConfigDict


class ClickLog(SQLModel, table=True):
    __tablename__ = "click_logs"
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    internship_id: int = Field(foreign_key="internships.id", index=True)
    action: str = Field(index=True)
    model_metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata", sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Provide convenient attribute access under reserved name on instances
    def __getattribute__(self, name: str):
        if name == "metadata":
            return object.__getattribute__(self, "model_metadata")
        return super().__getattribute__(name)

# Define SQLAlchemy relationships after all classes are declared to avoid
# SQLModel field/type inspection conflicts.
Company.internships = relationship("Internship", back_populates="company")
Internship.company = relationship("Company", back_populates="internships")
Internship.contact_emails = relationship("ContactEmail", back_populates="internship")
ContactEmail.internship = relationship("Internship", back_populates="contact_emails")
