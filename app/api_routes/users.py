from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from ..repositories import get_repositories, get_session
from ..schemas import (
    UserProfile, UserProfileUpdate, BookmarkResponse, BookmarkCreate,
    SuccessResponse
)
from ..auth import get_current_user
from ..models import User

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get current user's profile"""
    import json
    
    # Parse JSON fields
    skills = json.loads(current_user.skills) if current_user.skills else []
    interests = json.loads(current_user.interests) if current_user.interests else []
    preferences = json.loads(current_user.preferences) if current_user.preferences else {}
    
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        location=current_user.location,
        education_level=current_user.education_level,
        visa_requirement=current_user.visa_requirement,
        remote_ok=current_user.remote_ok,
        skills=skills,
        interests=interests,
        preferences=preferences,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.put("/me", response_model=UserProfile)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update current user's profile"""
    import json
    
    repos = get_repositories(session)
    
    # Prepare update data
    update_data = {}
    for field, value in profile_update.dict(exclude_none=True).items():
        if field in ['skills', 'interests', 'preferences']:
            update_data[field] = json.dumps(value) if value is not None else None
        else:
            update_data[field] = value
    
    # Update user
    updated_user = repos['users'].update_user(current_user, **update_data)
    
    # Parse JSON fields for response
    skills = json.loads(updated_user.skills) if updated_user.skills else []
    interests = json.loads(updated_user.interests) if updated_user.interests else []
    preferences = json.loads(updated_user.preferences) if updated_user.preferences else {}
    
    return UserProfile(
        id=updated_user.id,
        email=updated_user.email,
        name=updated_user.name,
        location=updated_user.location,
        education_level=updated_user.education_level,
        visa_requirement=updated_user.visa_requirement,
        remote_ok=updated_user.remote_ok,
        skills=skills,
        interests=interests,
        preferences=preferences,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
    )

@router.get("/me/bookmarks", response_model=List[BookmarkResponse])
async def get_user_bookmarks(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get current user's bookmarked internships"""
    repos = get_repositories(session)
    bookmarks, total = repos['bookmarks'].get_user_bookmarks(
        user_id=current_user.id,
        page=page,
        limit=limit
    )
    
    return [BookmarkResponse.from_orm(bookmark) for bookmark in bookmarks]

@router.post("/me/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Bookmark an internship"""
    repos = get_repositories(session)
    
    # Check if internship exists
    internship = repos['internships'].get_internship_by_id(bookmark_data.internship_id)
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    try:
        bookmark = repos['bookmarks'].create_bookmark(
            user_id=current_user.id,
            internship_id=bookmark_data.internship_id,
            notes=bookmark_data.notes
        )
        
        # Log the bookmark action
        repos['click_logs'].log_action(
            user_id=current_user.id,
            internship_id=bookmark_data.internship_id,
            action="bookmark"
        )
        
        return BookmarkResponse.from_orm(bookmark)
        
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Internship already bookmarked")
        raise HTTPException(status_code=500, detail="Failed to create bookmark")

@router.delete("/me/bookmarks/{internship_id}", response_model=SuccessResponse)
async def delete_bookmark(
    internship_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Remove bookmark for an internship"""
    repos = get_repositories(session)
    
    success = repos['bookmarks'].delete_bookmark(
        user_id=current_user.id,
        internship_id=internship_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    return SuccessResponse(message="Bookmark removed successfully")

@router.get("/me/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get user activity statistics"""
    from sqlmodel import select, func
    from ..models import Bookmark, ClickLog
    
    # Count bookmarks
    bookmark_count = session.exec(
        select(func.count(Bookmark.id)).where(Bookmark.user_id == current_user.id)
    ).one()
    
    # Count applications (click logs with action='apply')
    application_count = session.exec(
        select(func.count(ClickLog.id)).where(
            ClickLog.user_id == current_user.id,
            ClickLog.action == "apply"
        )
    ).one()
    
    # Count views this month
    from datetime import datetime, timedelta
    month_ago = datetime.utcnow() - timedelta(days=30)
    
    views_this_month = session.exec(
        select(func.count(ClickLog.id)).where(
            ClickLog.user_id == current_user.id,
            ClickLog.action == "view",
            ClickLog.created_at >= month_ago
        )
    ).one()
    
    return {
        "bookmarks": bookmark_count,
        "applications": application_count,
        "views_this_month": views_this_month,
        "member_since": current_user.created_at.isoformat()
    }
