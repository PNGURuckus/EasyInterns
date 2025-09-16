from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session
from typing import List, Dict, Any

from ..repositories import get_repositories, get_session
from ..schemas import (
    ResumeResponse, ResumeCreate, ResumeUpdate, AIResumeRequest,
    PDFExportResponse, AIResponse, SuccessResponse
)
from ..auth import get_current_user
from ..models import User
from ..core.ai import generate_resume_summary, generate_resume_bullets, tailor_resume_to_job
from ..resume.builder import generate_resume_pdf
import json

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

@router.get("", response_model=List[ResumeResponse])
async def get_user_resumes(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all resumes for current user"""
    repos = get_repositories(session)
    resumes = repos['resumes'].get_user_resumes(current_user.id)
    
    # Parse content JSON for each resume
    result = []
    for resume in resumes:
        resume_dict = resume.__dict__.copy()
        resume_dict['content'] = json.loads(resume.content) if resume.content else {}
        result.append(ResumeResponse(**resume_dict))
    
    return result

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get specific resume by ID"""
    repos = get_repositories(session)
    resume = repos['resumes'].get_resume_by_id(resume_id, current_user.id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_dict = resume.__dict__.copy()
    resume_dict['content'] = json.loads(resume.content) if resume.content else {}
    
    return ResumeResponse(**resume_dict)

@router.post("", response_model=ResumeResponse)
async def create_resume(
    resume_data: ResumeCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create new resume"""
    repos = get_repositories(session)
    
    resume = repos['resumes'].create_resume(
        user_id=current_user.id,
        name=resume_data.name,
        template=resume_data.template,
        content=resume_data.content
    )
    
    resume_dict = resume.__dict__.copy()
    resume_dict['content'] = json.loads(resume.content) if resume.content else {}
    
    return ResumeResponse(**resume_dict)

@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: int,
    resume_update: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update existing resume"""
    repos = get_repositories(session)
    resume = repos['resumes'].get_resume_by_id(resume_id, current_user.id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    update_data = resume_update.dict(exclude_none=True)
    updated_resume = repos['resumes'].update_resume(resume, **update_data)
    
    resume_dict = updated_resume.__dict__.copy()
    resume_dict['content'] = json.loads(updated_resume.content) if updated_resume.content else {}
    
    return ResumeResponse(**resume_dict)

@router.delete("/{resume_id}", response_model=SuccessResponse)
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete resume"""
    repos = get_repositories(session)
    resume = repos['resumes'].get_resume_by_id(resume_id, current_user.id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    session.delete(resume)
    session.commit()
    
    return SuccessResponse(message="Resume deleted successfully")

@router.post("/{resume_id}/export", response_model=PDFExportResponse)
async def export_resume_pdf(
    resume_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Export resume as PDF"""
    repos = get_repositories(session)
    resume = repos['resumes'].get_resume_by_id(resume_id, current_user.id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    try:
        # Generate PDF
        content = json.loads(resume.content) if resume.content else {}
        pdf_url = await generate_resume_pdf(
            content=content,
            template=resume.template,
            resume_id=resume_id
        )
        
        # Update resume with PDF URL
        repos['resumes'].update_resume(resume, pdf_url=pdf_url)
        
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        
        return PDFExportResponse(pdf_url=pdf_url, expires_at=expires_at)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.post("/{resume_id}/ai", response_model=AIResponse)
async def ai_enhance_resume(
    resume_id: int,
    ai_request: AIResumeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Use AI to enhance resume content"""
    repos = get_repositories(session)
    resume = repos['resumes'].get_resume_by_id(resume_id, current_user.id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    try:
        content = json.loads(resume.content) if resume.content else {}
        
        if ai_request.action == "generate_summary":
            # Get user profile for context
            user_skills = json.loads(current_user.skills) if current_user.skills else []
            user_interests = json.loads(current_user.interests) if current_user.interests else []
            
            profile = {
                'name': current_user.name or 'Student',
                'education_level': current_user.education_level,
                'skills': user_skills,
                'interests': user_interests,
                'location': current_user.location
            }
            
            result = await generate_resume_summary(profile)
            
        elif ai_request.action == "generate_bullets":
            if not ai_request.context or 'experience' not in ai_request.context:
                raise HTTPException(status_code=400, detail="Experience context required for bullet generation")
            
            result_list = await generate_resume_bullets(ai_request.context['experience'])
            result = '\n'.join(result_list)
            
        elif ai_request.action == "tailor_to_job":
            if not ai_request.internship_id:
                raise HTTPException(status_code=400, detail="Internship ID required for job tailoring")
            
            # Get internship details
            internship = repos['internships'].get_internship_by_id(ai_request.internship_id)
            if not internship:
                raise HTTPException(status_code=404, detail="Internship not found")
            
            job_description = f"{internship.title}\n{internship.description or ''}\n{internship.requirements or ''}"
            tailored_content = await tailor_resume_to_job(content, job_description)
            
            # Update resume with tailored content
            repos['resumes'].update_resume(resume, content=tailored_content)
            
            result = "Resume successfully tailored to job requirements"
            
        else:
            raise HTTPException(status_code=400, detail="Invalid AI action")
        
        return AIResponse(result=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI enhancement failed: {str(e)}")

@router.get("/templates/list")
async def get_resume_templates():
    """Get list of available resume templates"""
    templates = [
        {
            "id": "ats_clean",
            "name": "ATS Clean",
            "description": "Simple, ATS-friendly format optimized for applicant tracking systems",
            "preview_url": "/api/resumes/templates/ats_clean/preview"
        },
        {
            "id": "modern_two_col",
            "name": "Modern Two Column",
            "description": "Contemporary two-column layout with visual hierarchy",
            "preview_url": "/api/resumes/templates/modern_two_col/preview"
        },
        {
            "id": "creative_accent",
            "name": "Creative Accent",
            "description": "Professional design with subtle color accents and modern typography",
            "preview_url": "/api/resumes/templates/creative_accent/preview"
        },
        {
            "id": "compact_student",
            "name": "Compact Student",
            "description": "Optimized for students and new graduates with limited experience",
            "preview_url": "/api/resumes/templates/compact_student/preview"
        }
    ]
    
    return {"templates": templates}
