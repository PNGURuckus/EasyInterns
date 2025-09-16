from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.models.application import ApplicationStatus, ApplicationStage, ApplicationSource
from app.schemas.common import Message
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationPublic, 
    ApplicationFilter, ApplicationActivityCreate, ApplicationStats
)

router = APIRouter()

@router.get("/", response_model=List[ApplicationPublic])
def read_applications(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
    status: Optional[List[ApplicationStatus]] = Query(None),
    stage: Optional[List[ApplicationStage]] = Query(None),
    source: Optional[List[ApplicationSource]] = Query(None),
    is_archived: Optional[bool] = None,
    search: Optional[str] = None,
    order_by: Optional[List[str]] = Query(None)
) -> Any:
    """
    Retrieve applications with filtering, searching, and pagination.
    """
    # Build filters
    filters = {}
    if status is not None:
        filters["status"] = status
    if stage is not None:
        filters["stage"] = stage
    if source is not None:
        filters["source"] = source
    if is_archived is not None:
        filters["is_archived"] = is_archived
    
    # Get applications
    applications, total = crud.application.get_multi_by_user(
        db, 
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        filters=filters,
        search=search,
        order_by=order_by or ["-applied_at", "-created_at"]
    )
    
    # Add X-Total-Count header for pagination
    response = JSONResponse(
        content=[app.dict() for app in applications]
    )
    response.headers["X-Total-Count"] = str(total)
    
    return response

@router.post("/", response_model=ApplicationPublic, status_code=status.HTTP_201_CREATED)
def create_application(
    *,
    db: Session = Depends(deps.get_db),
    application_in: ApplicationCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new application.
    """
    # Check if the internship exists
    internship = crud.internship.get(db, id=application_in.internship_id)
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The internship does not exist.",
        )
    
    # Check if the resume exists and belongs to the user
    if application_in.resume_id:
        resume = crud.resume.get(db, id=application_in.resume_id)
        if not resume or resume.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The resume does not exist or you don't have permission to use it.",
            )
    
    # Create the application
    application = crud.application.create_with_activity(
        db=db,
        obj_in=application_in,
        user_id=current_user.id
    )
    
    return application

@router.get("/{application_id}", response_model=ApplicationPublic)
def read_application(
    *,
    db: Session = Depends(deps.get_db),
    application_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get an application by ID.
    """
    application = crud.application.get_with_details(
        db, 
        id=application_id, 
        user_id=current_user.id
    )
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    
    return application

@router.put("/{application_id}", response_model=ApplicationPublic)
def update_application(
    *,
    db: Session = Depends(deps.get_db),
    application_id: UUID,
    application_in: ApplicationUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an application.
    """
    application = crud.application.get(db, id=application_id, user_id=current_user.id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    
    # Update the application
    application = crud.application.update(
        db, 
        db_obj=application, 
        obj_in=application_in
    )
    
    return application

@router.delete("/{application_id}", response_model=Message)
def delete_application(
    *,
    db: Session = Depends(deps.get_db),
    application_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an application.
    """
    application = crud.application.get(db, id=application_id, user_id=current_user.id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    
    crud.application.remove(db, id=application_id)
    
    return {"message": "Application deleted successfully"}

@router.post("/{application_id}/status", response_model=ApplicationPublic)
def update_application_status(
    *,
    db: Session = Depends(deps.get_db),
    application_id: UUID,
    status: ApplicationStatus = Body(..., embed=True),
    notes: Optional[str] = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an application's status.
    """
    application = crud.application.get(db, id=application_id, user_id=current_user.id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    
    # Update the status
    application = crud.application.update_status(
        db,
        db_obj=application,
        new_status=status,
        notes=notes,
        user_id=current_user.id
    )
    
    return application

@router.post("/{application_id}/activities", response_model=ApplicationPublic)
def add_application_activity(
    *,
    db: Session = Depends(deps.get_db),
    application_id: UUID,
    activity_in: ApplicationActivityCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Add an activity to an application.
    """
    application = crud.application.get(db, id=application_id, user_id=current_user.id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    
    # Add the activity
    application = crud.application.add_activity(
        db,
        db_obj=application,
        activity_type=activity_in.type,
        details=activity_in.details,
        user_id=current_user.id
    )
    
    return application

@router.get("/{application_id}/stats", response_model=ApplicationStats)
def get_application_stats(
    *,
    db: Session = Depends(deps.get_db),
    application_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get statistics for an application.
    """
    application = crud.application.get(db, id=application_id, user_id=current_user.id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    
    # In a real implementation, you might calculate stats specific to this application
    # For now, we'll return a simple response
    return {
        "total": 1,
        "by_status": {application.status: 1},
        "by_stage": {application.stage: 1},
        "by_source": {application.source: 1} if application.source else {},
        "by_month": {}
    }

@router.get("/stats/overview", response_model=ApplicationStats)
def get_applications_overview(
    *,
    db: Session = Depends(deps.get_db),
    time_period: str = "all",
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get an overview of application statistics.
    """
    return crud.application.get_stats(
        db,
        user_id=current_user.id,
        time_period=time_period
    )

@router.get("/upcoming/activities", response_model=List[dict])
def get_upcoming_activities(
    *,
    db: Session = Depends(deps.get_db),
    days_ahead: int = 7,
    limit: int = 10,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get upcoming activities related to applications.
    """
    return crud.application.get_upcoming_activities(
        db,
        user_id=current_user.id,
        days_ahead=days_ahead,
        limit=limit
    )
