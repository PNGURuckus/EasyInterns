from .user import UserBase, UserCreate, UserInDB, UserUpdate, UserPublic, UserRole
from .token import Token, TokenPayload
from .internship import (
    Internship,
    InternshipCreate,
    InternshipUpdate,
    InternshipInDBBase as InternshipInDB,
    InternshipSearchResults,
    InternshipStats,
)
from app.models.base import JobType, WorkLocation, ExperienceLevel, SalaryFrequency

# Re-export the UserBase as User for backward compatibility
User = UserBase

__all__ = [
    "User",
    "UserBase",
    "UserCreate",
    "UserInDB",
    "UserUpdate",
    "UserPublic",
    "UserRole",
    "Token",
    "TokenPayload",
    "Internship",
    "InternshipCreate",
    "InternshipUpdate",
    "InternshipInDB",
    "InternshipSearchResults",
    "InternshipStats",
    "JobType",
    "WorkLocation",
    "ExperienceLevel",
    "SalaryFrequency",
]
