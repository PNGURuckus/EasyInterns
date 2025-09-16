from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.models.application import (
    Application, ApplicationCreate, ApplicationUpdate, 
    ApplicationPublic, ApplicationStatus, ApplicationStage, ApplicationSource,
    ApplicationFilter, ApplicationActivityCreate, ApplicationStats
)
from app.models.user import User
from app.models.internship import Internship
from app.crud.base import CRUDBase

class CRUDApplication(CRUDBase[Application, ApplicationCreate, ApplicationUpdate]):
    """CRUD operations for Application model"""
    
    def get_multi_by_user(
        self, 
        db: Session, 
        *, 
        user_id: UUID,
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
        order_by: Optional[List[str]] = None
    ) -> tuple[list[Application], int]:
        """
        Get applications for a specific user with filtering, searching and pagination.
        
        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of filters to apply
            search: Search term to filter results
            order_by: List of fields to order by (prefix with '-' for descending)
            
        Returns:
            Tuple of (applications, total_count)
        """
        query = self._base_query.where(Application.user_id == user_id)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(Application, field):
                    if isinstance(value, list):
                        query = query.where(getattr(Application, field).in_(value))
                    else:
                        query = query.where(getattr(Application, field) == value)
        
        # Apply search
        if search:
            search_conditions = []
            search_fields = [
                'cover_letter', 'notes',
                'internship.title', 'internship.company.name',
                'internship.description'
            ]
            
            for field in search_fields:
                if '.' in field:
                    # Handle related fields (e.g., internship.title)
                    rel_model, rel_field = field.split('.')
                    if hasattr(Application, rel_model):
                        search_conditions.append(
                            getattr(getattr(Application, rel_model).property.entity.class_, rel_field)
                            .ilike(f'%{search}%')
                        )
                elif hasattr(Application, field):
                    search_conditions.append(
                        getattr(Application, field).ilike(f'%{search}%')
                    )
            
            if search_conditions:
                query = query.where(or_(*search_conditions))
        
        # Get total count before pagination
        total = db.scalar(
            select([func.count()])
            .select_from(query.subquery())
        ) or 0
        
        # Apply ordering
        if order_by:
            order_clauses = []
            for field in order_by:
                if field.startswith('-'):
                    order_field = field[1:]
                    if hasattr(Application, order_field):
                        order_clauses.append(desc(getattr(Application, order_field)))
                else:
                    if hasattr(Application, field):
                        order_clauses.append(asc(getattr(Application, field)))
            
            if order_clauses:
                query = query.order_by(*order_clauses)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Eager load relationships
        query = query.options(
            joinedload(Application.internship).joinedload(Internship.company),
            joinedload(Application.resume)
        )
        
        results = db.execute(query).unique().scalars().all()
        return results, total
    
    def get_with_details(self, db: Session, id: UUID, user_id: Optional[UUID] = None) -> Optional[Application]:
        """
        Get an application with all its details.
        
        Args:
            db: Database session
            id: Application ID
            user_id: Optional user ID to ensure ownership
            
        Returns:
            Application with relationships loaded
        """
        query = self._base_query.where(Application.id == id)
        
        if user_id:
            query = query.where(Application.user_id == user_id)
        
        query = query.options(
            joinedload(Application.user),
            joinedload(Application.internship).joinedload(Internship.company),
            joinedload(Application.resume)
        )
        
        return db.execute(query).unique().scalar_one_or_none()
    
    def create_with_activity(
        self, 
        db: Session, 
        *, 
        obj_in: ApplicationCreate, 
        user_id: UUID,
        **kwargs
    ) -> Application:
        """
        Create a new application and log the initial activity.
        
        Args:
            db: Database session
            obj_in: Application data
            user_id: ID of the user creating the application
            **kwargs: Additional fields to set on the application
            
        Returns:
            The created application
        """
        try:
            # Create the application
            db_obj = Application(
                **obj_in.dict(exclude_unset=True),
                user_id=user_id,
                **kwargs
            )
            
            # Set initial status and timestamps
            db_obj.status = ApplicationStatus.DRAFT
            db_obj.stage = ApplicationStage.APPLICATION
            db_obj.applied_at = None
            db_obj.last_status_change = datetime.utcnow()
            
            # Add initial activity
            db_obj.activity_log = [{
                'id': str(UUID()),
                'type': 'status_change',
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': str(user_id),
                'details': {
                    'old_status': None,
                    'new_status': ApplicationStatus.DRAFT,
                    'notes': 'Application created'
                }
            }]
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise
    
    def update_status(
        self, 
        db: Session, 
        *, 
        db_obj: Application, 
        new_status: ApplicationStatus,
        notes: Optional[str] = None,
        user_id: Optional[UUID] = None,
        **kwargs
    ) -> Application:
        """
        Update the status of an application and log the change.
        
        Args:
            db: Database session
            db_obj: The application to update
            new_status: New status to set
            notes: Optional notes about the status change
            user_id: ID of the user making the change
            **kwargs: Additional fields to update
            
        Returns:
            The updated application
        """
        old_status = db_obj.status
        
        # Update the status and timestamps
        db_obj.status = new_status
        db_obj.last_status_change = datetime.utcnow()
        
        # Set applied_at timestamp if this is the first time the application is submitted
        if new_status == ApplicationStatus.APPLIED and not db_obj.applied_at:
            db_obj.applied_at = datetime.utcnow()
        
        # Update any additional fields
        for field, value in kwargs.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)
        
        # Log the status change
        activity = {
            'id': str(UUID()),
            'type': 'status_change',
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': str(user_id) if user_id else None,
            'details': {
                'old_status': old_status,
                'new_status': new_status,
                'notes': notes or f'Status changed from {old_status} to {new_status}'
            }
        }
        
        if db_obj.activity_log is None:
            db_obj.activity_log = [activity]
        else:
            db_obj.activity_log.append(activity)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def add_activity(
        self, 
        db: Session, 
        *, 
        db_obj: Application, 
        activity_type: str,
        details: Dict[str, Any],
        user_id: Optional[UUID] = None
    ) -> Application:
        """
        Add an activity to an application's activity log.
        
        Args:
            db: Database session
            db_obj: The application to update
            activity_type: Type of activity (e.g., 'note', 'interview', 'email')
            details: Details about the activity
            user_id: ID of the user who performed the activity
            
        Returns:
            The updated application
        """
        activity = {
            'id': str(UUID()),
            'type': activity_type,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': str(user_id) if user_id else None,
            'details': details
        }
        
        if db_obj.activity_log is None:
            db_obj.activity_log = [activity]
        else:
            db_obj.activity_log.append(activity)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_stats(
        self, 
        db: Session, 
        user_id: UUID,
        time_period: str = 'all',
        **filters
    ) -> ApplicationStats:
        """
        Get statistics about a user's applications.
        
        Args:
            db: Database session
            user_id: ID of the user
            time_period: Time period to filter by ('7d', '30d', '90d', 'year', 'all')
            **filters: Additional filters to apply
            
        Returns:
            ApplicationStats object with statistics
        """
        # Calculate date range based on time_period
        now = datetime.utcnow()
        date_filters = {}
        
        if time_period == '7d':
            date_filters['applied_at'] = (now - timedelta(days=7), now)
        elif time_period == '30d':
            date_filters['applied_at'] = (now - timedelta(days=30), now)
        elif time_period == '90d':
            date_filters['applied_at'] = (now - timedelta(days=90), now)
        elif time_period == 'year':
            date_filters['applied_at'] = (now - timedelta(days=365), now)
        
        # Base query
        query = self._base_query.where(Application.user_id == user_id)
        
        # Apply date filters
        if 'applied_at' in date_filters:
            start_date, end_date = date_filters['applied_at']
            query = query.where(
                and_(
                    Application.applied_at >= start_date,
                    Application.applied_at <= end_date
                )
            )
        
        # Apply additional filters
        for field, value in filters.items():
            if hasattr(Application, field) and value is not None:
                if isinstance(value, (list, tuple, set)):
                    query = query.where(getattr(Application, field).in_(value))
                else:
                    query = query.where(getattr(Application, field) == value)
        
        # Get all matching applications
        applications = db.execute(query).scalars().all()
        
        # Calculate statistics
        stats = ApplicationStats(
            total=len(applications),
            by_status={},
            by_stage={},
            by_source={},
            by_month={}
        )
        
        # Group by status, stage, and source
        for app in applications:
            # Count by status
            status = app.status.value if app.status else 'unknown'
            stats.by_status[status] = stats.by_status.get(status, 0) + 1
            
            # Count by stage
            stage = app.stage.value if app.stage else 'unknown'
            stats.by_stage[stage] = stats.by_stage.get(stage, 0) + 1
            
            # Count by source
            source = app.source.value if app.source else 'unknown'
            stats.by_source[source] = stats.by_source.get(source, 0) + 1
            
            # Group by month
            if app.applied_at:
                month_key = app.applied_at.strftime('%Y-%m')
                stats.by_month[month_key] = stats.by_month.get(month_key, 0) + 1
        
        return stats
    
    def get_upcoming_activities(
        self,
        db: Session,
        user_id: UUID,
        days_ahead: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming activities related to applications.
        
        Args:
            db: Database session
            user_id: ID of the user
            days_ahead: Number of days to look ahead for activities
            limit: Maximum number of activities to return
            
        Returns:
            List of upcoming activities with application details
        """
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)
        
        # Get applications with upcoming interviews or follow-ups
        query = self._base_query.where(
            and_(
                Application.user_id == user_id,
                Application.status.notin_([
                    ApplicationStatus.REJECTED,
                    ApplicationStatus.WITHDRAWN,
                    ApplicationStatus.CLOSED,
                    ApplicationStatus.OFFER_DECLINED
                ])
            )
        ).options(
            joinedload(Application.internship).joinedload(Internship.company)
        )
        
        applications = db.execute(query).scalars().all()
        
        upcoming_activities = []
        
        for app in applications:
            # Check for upcoming interviews
            if app.activity_log:
                for activity in app.activity_log:
                    if activity.get('type') == 'interview_scheduled':
                        interview_time = datetime.fromisoformat(activity['details'].get('scheduled_time'))
                        if now <= interview_time <= end_date:
                            upcoming_activities.append({
                                'type': 'interview',
                                'application_id': str(app.id),
                                'internship_title': app.internship.title if app.internship else 'Untitled Internship',
                                'company_name': app.internship.company.name if app.internship and app.internship.company else 'Unknown Company',
                                'scheduled_time': interview_time,
                                'activity': activity,
                                'application': app
                            })
            
            # Check for follow-ups based on last activity
            if app.last_status_change:
                days_since_last_activity = (now - app.last_status_change).days
                if days_since_last_activity >= 7 and app.status == ApplicationStatus.APPLIED:
                    upcoming_activities.append({
                        'type': 'follow_up',
                        'application_id': str(app.id),
                        'internship_title': app.internship.title if app.internship else 'Untitled Internship',
                        'company_name': app.internship.company.name if app.internship and app.internship.company else 'Unknown Company',
                        'last_activity': app.last_status_change,
                        'status': app.status,
                        'application': app
                    })
        
        # Sort by date and limit results
        upcoming_activities.sort(key=lambda x: x.get('scheduled_time', x.get('last_activity', now)))
        return upcoming_activities[:limit]

# Create an instance of the CRUDApplication class
application = CRUDApplication(Application)
