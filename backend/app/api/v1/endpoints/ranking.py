from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.ranking import (
    RankInternshipsRequest,
    RankInternshipsResponse,
    RankedInternship,
    RankingFeedback,
    UpdateRankingWeightsRequest,
    RankingPreference,
)
from app.crud import internship as crud_internship
from app.ranking.engine import RankingEngine
from app.ranking.weights import get_weights_for_user, default_weights
from app.models.user import User
from app.api.deps import get_current_active_user

router = APIRouter()

@router.post("/rank", response_model=RankInternshipsResponse)
async def rank_internships(
    request: RankInternshipsRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Rank internships based on relevance to the user
    """
    try:
        # Get internships from database
        internships = await crud_internship.get_by_ids(
            db, 
            ids=request.internship_ids,
            include_company=True
        )
        
        if not internships:
            return RankInternshipsResponse(
                results=[],
                total=0,
                weights_used=default_weights.dict(),
            )
        
        # Initialize ranking engine with user preferences
        user_prefs = request.preferences or RankingPreference.STUDENT
        ranking_engine = RankingEngine(
            user=current_user,
            weights=get_weights_for_user(user_prefs.value)
        )
        
        # Apply custom weights if provided
        if request.custom_weights:
            ranking_engine.weights = ranking_engine.weights.copy(
                update=request.custom_weights
            )
        
        # Rank internships
        ranked_results = ranking_engine.rank_internships(
            internships,
            limit=request.limit
        )
        
        # Convert to response model
        ranked_internships = []
        for result in ranked_results:
            internship = result.internship
            ranked_internships.append(RankedInternship(
                id=str(internship.id),
                title=internship.title,
                company=internship.company.name if internship.company else "Unknown",
                location=internship.location,
                is_remote=internship.is_remote,
                score=result.score,
                score_breakdown=result.score_breakdown,
                matched_keywords=result.matched_keywords,
                matched_skills=result.matched_skills,
                posted_date=internship.posted_date,
                application_deadline=internship.application_deadline,
                salary_range=(
                    f"${internship.salary_min:,.2f} - ${internship.salary_max:,.2f} {internship.salary_currency}"
                    if internship.salary_min and internship.salary_max
                    else "Not specified"
                ) if internship.salary_min or internship.salary_max else None,
                source=internship.source,
            ))
        
        return RankInternshipsResponse(
            results=ranked_internships,
            total=len(ranked_internships),
            user_preferences={
                "preference_profile": user_prefs,
                "location": current_user.location if current_user and current_user.location else None,
                "skills": getattr(current_user, "skills", []) if current_user else [],
            },
            weights_used=ranking_engine.weights.dict(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ranking internships: {str(e)}",
        )

@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def submit_ranking_feedback(
    feedback: List[RankingFeedback],
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit feedback on ranking results to improve future rankings
    """
    try:
        # TODO: Store feedback in database for analysis
        # This could be used to retrain ranking models or adjust weights
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting feedback: {str(e)}",
        )

@router.get("/weights/{preference}")
async def get_ranking_weights(
    preference: RankingPreference,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the current ranking weights for a preference profile
    """
    try:
        weights = get_weights_for_user(preference.value)
        return weights.dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting ranking weights: {str(e)}",
        )

@router.put("/weights/{preference}")
async def update_ranking_weights(
    preference: RankingPreference,
    request: UpdateRankingWeightsRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update ranking weights for a preference profile
    """
    try:
        # TODO: Implement weight updates
        # This would typically be an admin-only endpoint
        if not current_user.is_superuser and request.is_global:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update global weights",
            )
            
        # TODO: Store updated weights in database
        return {"status": "success", "message": "Weights updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating weights: {str(e)}",
        )
