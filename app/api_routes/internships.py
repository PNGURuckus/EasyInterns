from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import Optional, List

from ..repositories import get_repositories, get_session
from ..schemas import (
    InternshipSearchParams, InternshipListResponse, InternshipDetailResponse,
    InternshipResponse, ContactEmailResponse
)
from ..models import Internship, ContactEmail
from ..auth import get_current_user_optional

router = APIRouter(prefix="/api/internships", tags=["internships"])

@router.get("", response_model=InternshipListResponse)
async def search_internships(
    q: Optional[str] = Query(None, description="Search query"),
    field_tags: Optional[List[str]] = Query(None, description="Field tags filter"),
    modality: Optional[List[str]] = Query(None, description="Modality filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    min_salary: Optional[float] = Query(None, description="Minimum salary"),
    max_salary: Optional[float] = Query(None, description="Maximum salary"),
    is_government: Optional[bool] = Query(None, description="Government positions only"),
    posted_after: Optional[str] = Query(None, description="Posted after date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("relevance", regex="^(relevance|posting_date|salary)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user_optional)
):
    """
    Search internships with filters and faceted search
    """
    try:
        # Parse posted_after if provided
        posted_after_dt = None
        if posted_after:
            from datetime import datetime
            posted_after_dt = datetime.fromisoformat(posted_after.replace('Z', '+00:00'))
        
        # Create search parameters
        search_params = InternshipSearchParams(
            q=q,
            field_tags=field_tags,
            modality=modality,
            location=location,
            min_salary=min_salary,
            max_salary=max_salary,
            is_government=is_government,
            posted_after=posted_after_dt,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        repos = get_repositories(session)
        result = repos['internships'].search_internships(
            search_params, 
            user_id=current_user.id if current_user else None
        )
        
        # Log search if user is authenticated
        if current_user and q:
            repos['click_logs'].log_action(
                user_id=current_user.id,
                internship_id=0,  # No specific internship
                action="search",
                metadata={"query": q, "filters": search_params.dict(exclude_none=True)}
            )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/{internship_id}", response_model=InternshipDetailResponse)
async def get_internship_detail(
    internship_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user_optional)
):
    """
    Get detailed internship information including contact emails and similar roles
    """
    repos = get_repositories(session)
    
    # Get the internship
    internship = repos['internships'].get_internship_by_id(internship_id)
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Get contact emails
    contact_emails_query = session.query(ContactEmail).filter(
        ContactEmail.internship_id == internship_id
    ).order_by(ContactEmail.confidence.desc()).all()
    
    contact_emails = [
        ContactEmailResponse(
            id=email.id,
            email=email.email,
            confidence=email.confidence,
            source_type=email.source_type,
            verified=email.verified
        )
        for email in contact_emails_query
    ]
    
    # Get similar internships
    similar_internships = repos['internships'].get_similar_internships(internship, limit=5)
    
    # Log view if user is authenticated
    if current_user:
        repos['click_logs'].log_action(
            user_id=current_user.id,
            internship_id=internship_id,
            action="view"
        )
    
    # Convert to response model
    internship_response = InternshipResponse.from_orm(internship)
    similar_responses = [InternshipResponse.from_orm(sim) for sim in similar_internships]
    
    return InternshipDetailResponse(
        **internship_response.dict(),
        contact_emails=contact_emails,
        similar_internships=similar_responses
    )

@router.post("/{internship_id}/view")
async def log_internship_view(
    internship_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user_optional)
):
    """
    Log that a user viewed an internship (for analytics)
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    repos = get_repositories(session)
    
    # Verify internship exists
    internship = repos['internships'].get_internship_by_id(internship_id)
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Log the view
    repos['click_logs'].log_action(
        user_id=current_user.id,
        internship_id=internship_id,
        action="view"
    )
    
    return {"success": True, "message": "View logged"}

@router.post("/{internship_id}/apply")
async def log_internship_apply(
    internship_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user_optional)
):
    """
    Log that a user applied to an internship (for analytics)
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    repos = get_repositories(session)
    
    # Verify internship exists
    internship = repos['internships'].get_internship_by_id(internship_id)
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Log the application
    repos['click_logs'].log_action(
        user_id=current_user.id,
        internship_id=internship_id,
        action="apply",
        metadata={"apply_url": internship.apply_url}
    )
    
    return {"success": True, "message": "Application logged"}

@router.post("/{internship_id}/email-copy")
async def log_email_copy(
    internship_id: int,
    email: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user_optional)
):
    """
    Log that a user copied a contact email (for analytics)
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    repos = get_repositories(session)
    
    # Verify internship exists
    internship = repos['internships'].get_internship_by_id(internship_id)
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Log the email copy
    repos['click_logs'].log_action(
        user_id=current_user.id,
        internship_id=internship_id,
        action="email_copy",
        metadata={"email": email}
    )
    
    return {"success": True, "message": "Email copy logged"}
