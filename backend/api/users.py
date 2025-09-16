"""
Users API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session
from backend.core.database import get_session
from backend.data.models import User, Bookmark
from backend.data.schemas import (
    UserResponse,
    UserProfileUpdate,
    BookmarkCreate,
    BookmarkResponse
)

router = APIRouter()


@router.get("/user", response_model=UserResponse)
async def get_current_user():
    """Get current authenticated user profile"""
    # TODO: Implement with Supabase auth
    mock_user = {
        "id": 1,
        "email": "john.doe@example.com",
        "name": "John Doe",
        "city": "Toronto",
        "region": "Ontario",
        "country": "Canada",
        "fields_of_interest": ["software_engineering", "data_science"],
        "skills": ["Python", "React", "JavaScript"],
        "created_at": "2024-01-15T10:00:00Z"
    }
    return UserResponse(**mock_user)


@router.put("/user", response_model=UserResponse)
async def update_user_profile(profile_data: UserProfileUpdate):
    """Update user profile"""
    # TODO: Implement with database
    mock_user = {
        "id": 1,
        "email": "john.doe@example.com",
        "name": profile_data.name or "John Doe",
        "city": profile_data.city or "Toronto",
        "region": profile_data.region or "Ontario",
        "country": profile_data.country or "Canada",
        "fields_of_interest": profile_data.fields_of_interest or ["software_engineering"],
        "skills": profile_data.skills or ["Python", "React"],
        "created_at": "2024-01-15T10:00:00Z"
    }
    return UserResponse(**mock_user)


@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def get_user_bookmarks():
    """Get user's bookmarked internships"""
    # TODO: Implement with database
    return []


@router.post("/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(bookmark_data: BookmarkCreate):
    """Bookmark an internship"""
    # TODO: Implement with database
    mock_bookmark = {
        "id": 1,
        "notes": bookmark_data.notes,
        "created_at": "2024-01-15T10:00:00Z",
        "internship": {
            "id": bookmark_data.internship_id,
            "title": "Software Engineering Intern",
            "description": "Build scalable solutions",
            "field_tag": "software_engineering",
            "city": "Toronto",
            "region": "Ontario",
            "country": "Canada",
            "modality": "hybrid",
            "salary_min": 25000,
            "salary_max": 30000,
            "salary_currency": "CAD",
            "duration_months": 4,
            "apply_url": "https://example.com/apply",
            "posted_at": "2024-01-15T10:00:00Z",
            "expires_at": "2024-02-15T23:59:59Z",
            "skills_required": ["React", "JavaScript"],
            "education_level": "bachelor",
            "experience_level": "entry",
            "government_program": False,
            "relevance_score": 0.95,
            "created_at": "2024-01-15T10:00:00Z",
            "company": {
                "id": 1,
                "name": "Tech Corp",
                "domain": "techcorp.com",
                "logo_url": "https://logo.clearbit.com/techcorp.com",
                "description": "Leading tech company",
                "headquarters_city": "Toronto",
                "headquarters_region": "Ontario",
                "headquarters_country": "Canada",
                "size_category": "large",
                "industry": "Technology"
            },
            "source": {
                "id": 1,
                "name": "job_bank_ca",
                "display_name": "Job Bank Canada",
                "source_type": "api"
            }
        }
    }
    return BookmarkResponse(**mock_bookmark)


@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: int):
    """Remove bookmark"""
    # TODO: Implement with database
    if bookmark_id != 1:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    return {"message": "Bookmark removed successfully"}
