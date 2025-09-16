from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import random

from sqlalchemy.orm import Session

from app import models, schemas
from app.models.application import ApplicationStatus, ApplicationStage, ApplicationSource
from app.crud import application as crud_application


def create_random_application(
    db: Session,
    user_id: int,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    source: Optional[str] = None,
    **kwargs
) -> models.Application:
    """Create a random application for testing"""
    if status is None:
        status = random.choice(list(ApplicationStatus)).value
    if stage is None:
        stage = random.choice(list(ApplicationStage)).value
    if source is None:
        source = random.choice(list(ApplicationSource)).value
    
    # Create a random company and internship if not provided
    if "internship_id" not in kwargs:
        from .internship import create_random_internship
        internship = create_random_internship(db)
        kwargs["internship_id"] = internship.id
    
    # Create a random resume if not provided
    if "resume_id" not in kwargs:
        from .resume import create_random_resume
        resume = create_random_resume(db, user_id=user_id)
        kwargs["resume_id"] = resume.id
    
    application_in = schemas.ApplicationCreate(
        status=status,
        stage=stage,
        source=source,
        notes=f"Test application notes {uuid4()}",
        **kwargs
    )
    
    return crud_application.application.create_with_activity(
        db=db,
        obj_in=application_in,
        user_id=user_id
    )


def create_application_activity(
    db: Session,
    application_id: UUID,
    user_id: int,
    activity_type: str,
    details: Dict[str, Any]
) -> models.Application:
    """Add an activity to an application"""
    return crud_application.application.add_activity(
        db=db,
        db_obj=crud_application.application.get(db, id=application_id, user_id=user_id),
        activity_type=activity_type,
        details=details,
        user_id=user_id
    )
