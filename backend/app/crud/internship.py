from typing import List, Optional, Union, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.internship import Internship, InternshipCreate, InternshipUpdate, InternshipPublic
from app.models.base import WorkLocation
from app.crud.base import CRUDBase

class CRUDInternship(CRUDBase[Internship, InternshipCreate, InternshipUpdate]):
    """CRUD operations for Internship model"""
    
    async def get_multi_by_company(
        self, db: AsyncSession, *, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Internship]:
        """Get multiple internships by company ID"""
        result = await db.execute(
            select(self.model)
            .filter(Internship.company_id == company_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_multi_by_ids(
        self, 
        db: AsyncSession, 
        *, 
        ids: List[Union[str, UUID]],
        include_company: bool = False,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Internship]:
        """Get multiple internships by their IDs"""
        if not ids:
            return []
            
        # Convert string IDs to UUID objects if needed
        uuids = [UUID(str(id_)) if isinstance(id_, str) else id_ for id_ in ids]
        
        query = select(self.model).filter(Internship.id.in_(uuids))
        
        if include_company:
            query = query.options(selectinload(Internship.company))
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def search(
        self,
        db: AsyncSession,
        *,
        query: Optional[str] = None,
        location: Optional[str] = None,
        locations: Optional[List[str]] = None,
        is_remote: Optional[bool] = None,
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,
        company_id: Optional[UUID] = None,
        posted_within_days: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Internship]:
        """Search internships with filters"""
        stmt = select(self.model)
        
        # Apply filters
        filters = []
        
        if query:
            search_terms = f"%{query.lower()}%"
            filters.extend([
                Internship.title.ilike(search_terms),
                Internship.description.ilike(search_terms),
            ])
        
        def _normalize(value: str) -> str:
            return " ".join(value.lower().split())

        if locations:
            normalized_locations = [_normalize(loc) for loc in locations if loc]
            if normalized_locations:
                normalized_column = func.lower(func.trim(Internship.location))
                filters.append(normalized_column.in_(normalized_locations))
        elif location:
            normalized_column = func.lower(func.trim(Internship.location))
            filters.append(normalized_column == _normalize(location))

        if is_remote is not None:
            if is_remote:
                filters.append(Internship.work_location == WorkLocation.REMOTE)
            else:
                filters.append(Internship.work_location != WorkLocation.REMOTE)
            
        if min_salary is not None:
            filters.append(Internship.salary_min >= min_salary)
            
        if max_salary is not None:
            filters.append(Internship.salary_max <= max_salary)
            
        if company_id:
            filters.append(Internship.company_id == company_id)
            
        if posted_within_days:
            from datetime import datetime, timedelta
            from sqlalchemy import func
            
            cutoff_date = datetime.utcnow() - timedelta(days=posted_within_days)
            filters.append(Internship.posted_date >= cutoff_date)
        
        if filters:
            stmt = stmt.filter(and_(*filters))
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def create_with_company(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: InternshipCreate,
        company_id: UUID
    ) -> Internship:
        """Create a new internship with a company"""
        db_obj = Internship(
            **obj_in.dict(exclude={"company"}),
            company_id=company_id,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_stats(
        self, 
        db: AsyncSession,
        *,
        company_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get statistics about internships"""
        from sqlalchemy import func, select
        
        # Base query
        stmt = select(
            func.count(Internship.id).label("total"),
            func.avg(Internship.salary_min).label("avg_min_salary"),
            func.avg(Internship.salary_max).label("avg_max_salary"),
            func.max(Internship.posted_date).label("newest_posting"),
        )
        
        if company_id:
            stmt = stmt.filter(Internship.company_id == company_id)
        
        result = await db.execute(stmt)
        stats = result.first()
        
        # Get count by location
        location_stmt = select(
            Internship.location,
            func.count(Internship.id).label("count")
        )
        
        if company_id:
            location_stmt = location_stmt.filter(Internship.company_id == company_id)
            
        location_stmt = location_stmt.group_by(Internship.location)
        location_result = await db.execute(location_stmt)
        locations = [{"location": loc, "count": cnt} for loc, cnt in location_result]
        
        return {
            "total": stats.total or 0,
            "avg_min_salary": float(stats.avg_min_salary) if stats.avg_min_salary else None,
            "avg_max_salary": float(stats.avg_max_salary) if stats.avg_max_salary else None,
            "newest_posting": stats.newest_posting,
            "locations": locations,
        }

# Create a singleton instance
internship = CRUDInternship(Internship)
