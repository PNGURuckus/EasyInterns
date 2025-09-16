from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class RankingPreference(str, Enum):
    STUDENT = "student"
    NEW_GRAD = "new_grad"
    CAREER_CHANGER = "career_changer"

class RankInternshipsRequest(BaseModel):
    """Request model for ranking internships"""
    internship_ids: List[str] = Field(
        ...,
        description="List of internship IDs to rank"
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user ID for personalized ranking"
    )
    preferences: Optional[RankingPreference] = Field(
        None,
        description="User preference profile for ranking"
    )
    custom_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom weights for ranking factors"
    )
    limit: Optional[int] = Field(
        None,
        description="Maximum number of results to return"
    )

class ScoreBreakdown(BaseModel):
    """Breakdown of scoring for a ranked internship"""
    keywords: float = 0.0
    skills: float = 0.0
    location: float = 0.0
    recency: float = 0.0
    internship_signal: float = 0.0
    salary: float = 0.0
    deadline: float = 0.0
    company_rating: float = 0.0
    custom_scores: Dict[str, float] = Field(default_factory=dict)

class RankedInternship(BaseModel):
    """A ranked internship with score and match details"""
    id: str
    title: str
    company: str
    location: str
    is_remote: bool = False
    score: float
    score_breakdown: ScoreBreakdown
    matched_keywords: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    posted_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    salary_range: Optional[str] = None
    source: Optional[str] = None

class RankInternshipsResponse(BaseModel):
    """Response model for ranked internships"""
    results: List[RankedInternship]
    total: int
    user_preferences: Optional[Dict] = None
    weights_used: Dict[str, float]

class RankingFeedback(BaseModel):
    """User feedback on ranking results"""
    internship_id: str
    was_relevant: bool
    feedback: Optional[str] = None
    suggested_improvements: Optional[List[str]] = None

class UpdateRankingWeightsRequest(BaseModel):
    """Request to update ranking weights"""
    weights: Dict[str, float]
    user_id: Optional[str] = None
    preference_profile: Optional[RankingPreference] = None
    is_global: bool = False
