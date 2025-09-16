from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session
from typing import Optional, List, Dict, Any
import uuid
import asyncio
from datetime import datetime

from ..repositories import get_repositories, get_session
from ..schemas import ScrapeJobResponse, ScrapeJobStatus, SuccessResponse
from ..auth import get_current_user
from ..models import User
from ..scrapers.registry import get_scraper_registry
from ..workers.tasks import run_scrape_job
import json

router = APIRouter(prefix="/api/scrape", tags=["scraping"])

# In-memory job storage (in production, use Redis)
active_jobs: Dict[str, Dict[str, Any]] = {}

@router.post("/run", response_model=ScrapeJobResponse)
async def start_scrape_job(
    background_tasks: BackgroundTasks,
    source: Optional[str] = None,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Start a scraping job for specified source or all sources"""
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Get available scrapers
    registry = get_scraper_registry()
    
    if source:
        if source not in registry.get_enabled_sources():
            raise HTTPException(status_code=400, detail=f"Source '{source}' not available or disabled")
        sources_to_scrape = [source]
    else:
        sources_to_scrape = registry.get_enabled_sources()
    
    if not sources_to_scrape:
        raise HTTPException(status_code=400, detail="No enabled sources available for scraping")
    
    # Initialize job status
    job_status = {
        "job_id": job_id,
        "status": "pending",
        "source": source,
        "sources_to_scrape": sources_to_scrape,
        "progress": {
            "total_sources": len(sources_to_scrape),
            "completed_sources": 0,
            "current_source": None,
            "total_internships": 0,
            "new_internships": 0,
            "errors": []
        },
        "result": None,
        "error": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "user_id": current_user.id
    }
    
    active_jobs[job_id] = job_status
    
    # Start background task
    background_tasks.add_task(run_scrape_job, job_id, sources_to_scrape, force)
    
    return ScrapeJobResponse(
        job_id=job_id,
        message=f"Scraping job started for {len(sources_to_scrape)} source(s)"
    )

@router.get("/status/{job_id}", response_model=ScrapeJobStatus)
async def get_scrape_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a scraping job"""
    
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = active_jobs[job_id]
    
    # Check if user owns this job (or is admin)
    if job.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ScrapeJobStatus(
        job_id=job["job_id"],
        status=job["status"],
        source=job.get("source"),
        progress=job.get("progress"),
        result=job.get("result"),
        error=job.get("error"),
        created_at=job["created_at"],
        updated_at=job["updated_at"]
    )

@router.get("/jobs", response_model=List[ScrapeJobStatus])
async def get_user_scrape_jobs(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get recent scraping jobs for current user"""
    
    user_jobs = []
    for job in active_jobs.values():
        if job.get("user_id") == current_user.id:
            user_jobs.append(ScrapeJobStatus(
                job_id=job["job_id"],
                status=job["status"],
                source=job.get("source"),
                progress=job.get("progress"),
                result=job.get("result"),
                error=job.get("error"),
                created_at=job["created_at"],
                updated_at=job["updated_at"]
            ))
    
    # Sort by created_at descending and limit
    user_jobs.sort(key=lambda x: x.created_at, reverse=True)
    return user_jobs[:limit]

@router.delete("/jobs/{job_id}", response_model=SuccessResponse)
async def cancel_scrape_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a running scraping job"""
    
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = active_jobs[job_id]
    
    # Check if user owns this job
    if job.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if job["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Job already finished")
    
    # Mark job as cancelled
    job["status"] = "cancelled"
    job["updated_at"] = datetime.utcnow()
    
    return SuccessResponse(message="Job cancelled successfully")

@router.get("/sources")
async def get_available_sources():
    """Get list of available scraping sources"""
    
    registry = get_scraper_registry()
    sources = []
    
    for source_name in registry.get_all_sources():
        scraper_class = registry.get_scraper(source_name)
        is_enabled = source_name in registry.get_enabled_sources()
        
        sources.append({
            "name": source_name,
            "enabled": is_enabled,
            "description": getattr(scraper_class, 'description', f'{source_name} scraper'),
            "requires_feature_flag": getattr(scraper_class, 'requires_feature_flag', False),
            "last_scraped": None  # TODO: Get from database
        })
    
    return {"sources": sources}

@router.post("/sources/{source_name}/toggle", response_model=SuccessResponse)
async def toggle_source(
    source_name: str,
    enabled: bool,
    current_user: User = Depends(get_current_user)
):
    """Enable or disable a scraping source (admin only)"""
    
    # TODO: Add admin check
    # For now, any authenticated user can toggle
    
    registry = get_scraper_registry()
    
    if source_name not in registry.get_all_sources():
        raise HTTPException(status_code=404, detail="Source not found")
    
    # TODO: Update source status in database
    # For now, just return success
    
    action = "enabled" if enabled else "disabled"
    return SuccessResponse(message=f"Source {source_name} {action} successfully")

@router.get("/stats")
async def get_scraping_stats(
    session: Session = Depends(get_session)
):
    """Get scraping statistics"""
    
    from sqlmodel import select, func
    from ..models import Internship, Source
    from datetime import timedelta
    
    # Total internships
    total_internships = session.exec(
        select(func.count(Internship.id))
    ).one()
    
    # Active internships
    active_internships = session.exec(
        select(func.count(Internship.id)).where(Internship.is_active == True)
    ).one()
    
    # Recent internships (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_internships = session.exec(
        select(func.count(Internship.id)).where(Internship.created_at >= week_ago)
    ).one()
    
    # Internships by source
    source_stats = session.exec(
        select(Source.name, func.count(Internship.id))
        .select_from(Source.__table__.join(Internship.__table__, Source.id == Internship.source_id))
        .group_by(Source.name)
    ).all()
    
    # Active jobs
    active_job_count = len([job for job in active_jobs.values() if job["status"] == "running"])
    
    return {
        "total_internships": total_internships,
        "active_internships": active_internships,
        "recent_internships": recent_internships,
        "active_jobs": active_job_count,
        "sources": [{"name": name, "count": count} for name, count in source_stats]
    }

# Helper function to update job status (used by background tasks)
def update_job_status(job_id: str, **updates):
    """Update job status in memory store"""
    if job_id in active_jobs:
        active_jobs[job_id].update(updates)
        active_jobs[job_id]["updated_at"] = datetime.utcnow()

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status from memory store"""
    return active_jobs.get(job_id)
