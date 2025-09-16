from sqlmodel import Session, select, func, text
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import json

from .models import (
    User, Company, Internship, ContactEmail, Source, Bookmark, Resume, ClickLog,
    FieldTag, Modality
)
from .schemas import (
    InternshipSearchParams, SearchFacets, FacetCount, InternshipListResponse
)
from .db import engine

def get_session():
    return Session(engine)

class InternshipRepository:
    def __init__(self, session: Session):
        self.session = session

    def search_internships(self, params: InternshipSearchParams, user_id: Optional[int] = None) -> InternshipListResponse:
        """
        Search internships with faceted search using SQL CTEs
        """
        # Base query
        query = select(Internship).where(Internship.is_active == True)
        
        # Apply filters
        conditions = []
        
        if params.q:
            # Full-text search on title and description
            search_term = f"%{params.q.lower()}%"
            conditions.append(
                or_(
                    func.lower(Internship.title).contains(search_term),
                    func.lower(Internship.description).contains(search_term)
                )
            )
        
        if params.field_tags:
            conditions.append(Internship.field_tag.in_(params.field_tags))
        
        if params.modality:
            conditions.append(Internship.modality.in_(params.modality))
        
        if params.location:
            location_term = f"%{params.location.lower()}%"
            conditions.append(func.lower(Internship.location).contains(location_term))
        
        if params.min_salary:
            conditions.append(Internship.salary_min >= params.min_salary)
        
        if params.max_salary:
            conditions.append(Internship.salary_max <= params.max_salary)
        
        if params.is_government is not None:
            conditions.append(Internship.is_government == params.is_government)
        
        if params.posted_after:
            conditions.append(Internship.posting_date >= params.posted_after)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Add joins for related data
        query = query.join(Company, Internship.company_id == Company.id, isouter=True)
        query = query.join(Source, Internship.source_id == Source.id, isouter=True)
        
        # Count total results
        count_query = select(func.count(Internship.id)).select_from(query.subquery())
        total = self.session.exec(count_query).one()
        
        # Apply sorting
        if params.sort_by == "posting_date":
            order_col = Internship.posting_date
        elif params.sort_by == "salary":
            order_col = Internship.salary_max
        else:  # relevance
            order_col = Internship.relevance_score
        
        if params.sort_order == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))
        
        # Apply pagination
        offset = (params.page - 1) * params.limit
        query = query.offset(offset).limit(params.limit)
        
        # Execute main query
        internships = self.session.exec(query).all()
        
        # Calculate facets using CTEs
        facets = self._calculate_facets(params)
        
        pages = (total + params.limit - 1) // params.limit
        
        return InternshipListResponse(
            items=internships,
            total=total,
            page=params.page,
            limit=params.limit,
            pages=pages,
            facets=facets
        )
    
    def _calculate_facets(self, params: InternshipSearchParams) -> SearchFacets:
        """Calculate facet counts using SQL CTEs"""
        
        # Base conditions (same as main query but without the facet being calculated)
        base_conditions = [Internship.is_active == True]
        
        if params.q:
            search_term = f"%{params.q.lower()}%"
            base_conditions.append(
                or_(
                    func.lower(Internship.title).contains(search_term),
                    func.lower(Internship.description).contains(search_term)
                )
            )
        
        if params.posted_after:
            base_conditions.append(Internship.posting_date >= params.posted_after)
        
        if params.is_government is not None:
            base_conditions.append(Internship.is_government == params.is_government)
        
        # Field tags facet
        field_facet_query = select(
            Internship.field_tag,
            func.count().label('count')
        ).where(and_(*base_conditions))
        
        if params.modality:
            field_facet_query = field_facet_query.where(Internship.modality.in_(params.modality))
        if params.location:
            location_term = f"%{params.location.lower()}%"
            field_facet_query = field_facet_query.where(func.lower(Internship.location).contains(location_term))
        
        field_facet_query = field_facet_query.group_by(Internship.field_tag).order_by(desc('count'))
        
        field_results = self.session.exec(field_facet_query).all()
        field_facets = [
            FacetCount(value=str(field), count=count, label=field.replace('_', ' ').title() if field else 'Other')
            for field, count in field_results if field
        ]
        
        # Modality facet
        modality_facet_query = select(
            Internship.modality,
            func.count().label('count')
        ).where(and_(*base_conditions))
        
        if params.field_tags:
            modality_facet_query = modality_facet_query.where(Internship.field_tag.in_(params.field_tags))
        if params.location:
            location_term = f"%{params.location.lower()}%"
            modality_facet_query = modality_facet_query.where(func.lower(Internship.location).contains(location_term))
        
        modality_facet_query = modality_facet_query.group_by(Internship.modality).order_by(desc('count'))
        
        modality_results = self.session.exec(modality_facet_query).all()
        modality_facets = [
            FacetCount(value=str(modality), count=count, label=modality.title() if modality else 'Other')
            for modality, count in modality_results if modality
        ]
        
        # Location facet (top cities)
        location_facet_query = select(
            Internship.location,
            func.count().label('count')
        ).where(and_(*base_conditions))
        
        if params.field_tags:
            location_facet_query = location_facet_query.where(Internship.field_tag.in_(params.field_tags))
        if params.modality:
            location_facet_query = location_facet_query.where(Internship.modality.in_(params.modality))
        
        location_facet_query = location_facet_query.group_by(Internship.location).order_by(desc('count')).limit(10)
        
        location_results = self.session.exec(location_facet_query).all()
        location_facets = [
            FacetCount(value=location, count=count, label=location)
            for location, count in location_results if location
        ]
        
        # Source facet
        source_facet_query = select(
            Source.name,
            func.count().label('count')
        ).select_from(
            Internship.__table__.join(Source.__table__, Internship.source_id == Source.id)
        ).where(and_(*base_conditions))
        
        if params.field_tags:
            source_facet_query = source_facet_query.where(Internship.field_tag.in_(params.field_tags))
        if params.modality:
            source_facet_query = source_facet_query.where(Internship.modality.in_(params.modality))
        if params.location:
            location_term = f"%{params.location.lower()}%"
            source_facet_query = source_facet_query.where(func.lower(Internship.location).contains(location_term))
        
        source_facet_query = source_facet_query.group_by(Source.name).order_by(desc('count'))
        
        source_results = self.session.exec(source_facet_query).all()
        source_facets = [
            FacetCount(value=source, count=count, label=source.replace('_', ' ').title())
            for source, count in source_results if source
        ]
        
        return SearchFacets(
            field_tags=field_facets,
            modality=modality_facets,
            location=location_facets,
            sources=source_facets
        )
    
    def get_internship_by_id(self, internship_id: int) -> Optional[Internship]:
        """Get internship by ID with related data"""
        query = select(Internship).where(Internship.id == internship_id)
        return self.session.exec(query).first()
    
    def get_similar_internships(self, internship: Internship, limit: int = 5) -> List[Internship]:
        """Get similar internships based on field_tag and company"""
        query = select(Internship).where(
            and_(
                Internship.id != internship.id,
                Internship.is_active == True,
                or_(
                    Internship.field_tag == internship.field_tag,
                    Internship.company_id == internship.company_id
                )
            )
        ).order_by(desc(Internship.relevance_score)).limit(limit)
        
        return self.session.exec(query).all()

class UserRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_supabase_id(self, supabase_id: str) -> Optional[User]:
        query = select(User).where(User.supabase_id == supabase_id)
        return self.session.exec(query).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        return self.session.exec(query).first()
    
    def create_user(self, supabase_id: str, email: str, **kwargs) -> User:
        user = User(supabase_id=supabase_id, email=email, **kwargs)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def update_user(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

class BookmarkRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_user_bookmarks(self, user_id: int, page: int = 1, limit: int = 20) -> Tuple[List[Bookmark], int]:
        query = select(Bookmark).where(Bookmark.user_id == user_id)
        query = query.join(Internship).where(Internship.is_active == True)
        query = query.order_by(desc(Bookmark.created_at))
        
        # Count total
        count_query = select(func.count(Bookmark.id)).where(Bookmark.user_id == user_id)
        total = self.session.exec(count_query).one()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        bookmarks = self.session.exec(query).all()
        return bookmarks, total
    
    def create_bookmark(self, user_id: int, internship_id: int, notes: Optional[str] = None) -> Bookmark:
        bookmark = Bookmark(user_id=user_id, internship_id=internship_id, notes=notes)
        self.session.add(bookmark)
        self.session.commit()
        self.session.refresh(bookmark)
        return bookmark
    
    def delete_bookmark(self, user_id: int, internship_id: int) -> bool:
        query = select(Bookmark).where(
            and_(Bookmark.user_id == user_id, Bookmark.internship_id == internship_id)
        )
        bookmark = self.session.exec(query).first()
        if bookmark:
            self.session.delete(bookmark)
            self.session.commit()
            return True
        return False

class ResumeRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_user_resumes(self, user_id: int) -> List[Resume]:
        query = select(Resume).where(Resume.user_id == user_id).order_by(desc(Resume.updated_at))
        return self.session.exec(query).all()
    
    def get_resume_by_id(self, resume_id: int, user_id: int) -> Optional[Resume]:
        query = select(Resume).where(
            and_(Resume.id == resume_id, Resume.user_id == user_id)
        )
        return self.session.exec(query).first()
    
    def create_resume(self, user_id: int, name: str, template: str, content: Dict[str, Any]) -> Resume:
        resume = Resume(
            user_id=user_id,
            name=name,
            template=template,
            content=json.dumps(content)
        )
        self.session.add(resume)
        self.session.commit()
        self.session.refresh(resume)
        return resume
    
    def update_resume(self, resume: Resume, **kwargs) -> Resume:
        for key, value in kwargs.items():
            if key == 'content' and isinstance(value, dict):
                setattr(resume, key, json.dumps(value))
            elif hasattr(resume, key):
                setattr(resume, key, value)
        resume.updated_at = datetime.utcnow()
        self.session.add(resume)
        self.session.commit()
        self.session.refresh(resume)
        return resume

class ClickLogRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def log_action(self, user_id: int, internship_id: int, action: str, metadata: Optional[Dict[str, Any]] = None):
        click_log = ClickLog(
            user_id=user_id,
            internship_id=internship_id,
            action=action,
            metadata=json.dumps(metadata) if metadata else None
        )
        self.session.add(click_log)
        self.session.commit()

def get_repositories(session: Session = None):
    """Factory function to get all repositories"""
    if session is None:
        session = get_session()
    
    return {
        'internships': InternshipRepository(session),
        'users': UserRepository(session),
        'bookmarks': BookmarkRepository(session),
        'resumes': ResumeRepository(session),
        'click_logs': ClickLogRepository(session),
    }
