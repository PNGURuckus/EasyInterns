from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.api import deps
from app.db.session import get_db
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[schemas.Internship])
async def read_internships(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve internships with optional filtering.
    """
    internships = await crud.internship.get_multi(db, skip=skip, limit=limit)
    return internships

@router.post("/", response_model=schemas.Internship)
async def create_internship(
    *,
    db: AsyncSession = Depends(get_db),
    internship_in: schemas.InternshipCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new internship.
    """
    # Check if company exists
    if internship_in.company_id:
        company = await crud.company.get(db, id=internship_in.company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The company with this ID does not exist.",
            )
    
    # Create the internship
    internship = await crud.internship.create_with_owner(
        db=db, 
        obj_in=internship_in, 
        owner_id=current_user.id,
        company_id=internship_in.company_id
    )
    return internship

@router.get("/{internship_id}", response_model=schemas.Internship)
async def read_internship(
    internship_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get internship by ID.
    """
    internship = await crud.internship.get(db, id=internship_id)
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship not found",
        )
    return internship

@router.put("/{internship_id}", response_model=schemas.Internship)
async def update_internship(
    *,
    db: AsyncSession = Depends(get_db),
    internship_id: UUID,
    internship_in: schemas.InternshipUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update an internship.
    """
    internship = await crud.internship.get(db, id=internship_id)
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship not found",
        )
    
    # Check if company exists if updating company_id
    if internship_in.company_id and internship_in.company_id != internship.company_id:
        company = await crud.company.get(db, id=internship_in.company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The company with this ID does not exist.",
            )
    
    internship = await crud.internship.update(db, db_obj=internship, obj_in=internship_in)
    return internship

@router.delete("/{internship_id}", response_model=schemas.Internship)
async def delete_internship(
    *,
    db: AsyncSession = Depends(get_db),
    internship_id: UUID,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete an internship.
    """
    internship = await crud.internship.get(db, id=internship_id)
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship not found",
        )
    
    internship = await crud.internship.remove(db, id=internship_id)
    return internship

@router.get("/search/", response_model=List[schemas.Internship])
async def search_internships(
    *,
    db: AsyncSession = Depends(get_db),
    query: Optional[str] = None,
    location: Optional[str] = None,
    locations: Optional[List[str]] = Query(None, description="List of exact locations to match"),
    is_remote: Optional[bool] = None,
    min_salary: Optional[float] = None,
    max_salary: Optional[float] = None,
    company_id: Optional[UUID] = None,
    posted_within_days: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Search internships with advanced filtering.
    """
    internships = await crud.internship.search(
        db=db,
        query=query,
        location=location,
        locations=locations,
        is_remote=is_remote,
        min_salary=min_salary,
        max_salary=max_salary,
        company_id=company_id,
        posted_within_days=posted_within_days,
        skip=skip,
        limit=limit,
    )
    return internships

@router.get("/company/{company_id}", response_model=List[schemas.Internship])
async def read_internships_by_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get internships by company ID.
    """
    # Check if company exists
    company = await crud.company.get(db, id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    
    internships = await crud.internship.get_multi_by_company(
        db, company_id=company_id, skip=skip, limit=limit
    )
    return internships

@router.get("/stats/", response_model=Dict[str, Any])
async def get_internship_stats(
    *,
    db: AsyncSession = Depends(get_db),
    company_id: Optional[UUID] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get statistics about internships.
    """
    return await crud.internship.get_stats(db, company_id=company_id)
