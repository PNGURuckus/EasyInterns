from typing import Dict, List
from pydantic import BaseModel, Field

class RankingWeights(BaseModel):
    """Weights for different ranking factors"""
    # Must-have keywords (exact matches)
    must_have_keywords: float = 2.0
    
    # Nice-to-have keywords (fuzzy matches)
    nice_have_keywords: float = 0.5
    
    # Skills match (from user profile)
    skills_match: float = 0.3
    
    # Location preference (exact match = 1.0, same city = 0.7, same province = 0.3)
    location_match: float = 1.0
    
    # Remote work preference
    remote_work: float = 0.8
    
    # Recency (decay over time, 0.1 per day)
    recency_decay: float = 0.1
    
    # Internship signal (title contains 'intern' or 'co-op')
    internship_signal: float = 1.5
    
    # Company rating (if available)
    company_rating: float = 0.5
    
    # Salary (normalized to range)
    salary_weight: float = 0.7
    
    # Application deadline (closer deadlines get higher scores)
    deadline_urgency: float = 0.3
    
    # Custom field weights (for dynamic fields)
    custom_weights: Dict[str, float] = Field(default_factory=dict)

# Default weights
default_weights = RankingWeights()

# Weights for different user types
weights_by_user_type = {
    "student": RankingWeights(
        must_have_keywords=2.0,
        nice_have_keywords=0.5,
        skills_match=0.4,
        location_match=1.2,  # Students may be more flexible with location
        remote_work=0.5,    # May prefer in-person experience
        internship_signal=2.0,  # Strong preference for internships
    ),
    "new_grad": RankingWeights(
        must_have_keywords=1.8,
        nice_have_keywords=0.7,
        skills_match=0.5,
        salary_weight=1.0,  # May prioritize salary more than students
        remote_work=0.7,
    ),
    "career_changer": RankingWeights(
        must_have_keywords=1.5,
        nice_have_keywords=0.8,
        skills_match=0.6,
        location_match=0.8,  # May be more flexible with location
        remote_work=1.0,    # May prefer remote opportunities
    )
}

def get_weights_for_user(user_type: str = None) -> RankingWeights:
    """Get ranking weights for a specific user type"""
    if user_type and user_type in weights_by_user_type:
        return weights_by_user_type[user_type]
    return default_weights
