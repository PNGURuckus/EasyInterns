from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
import math
from dataclasses import dataclass

from ..models import Internship, User, FieldTag, Modality
from ..schemas import CandidateProfile

@dataclass
class ScoringWeights:
    """Configuration for scoring algorithm weights"""
    recency: float = 0.25
    relevance: float = 0.30
    quality: float = 0.20
    company: float = 0.15
    location: float = 0.10

@dataclass
class ScoringFactors:
    """Individual scoring factors for an internship"""
    recency_score: float
    relevance_score: float
    quality_score: float
    company_score: float
    location_score: float
    final_score: float

class InternshipScorer:
    """Comprehensive internship scoring and ranking system"""
    
    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()
        
        # Known high-quality companies (could be loaded from database)
        self.tier1_companies = {
            'google', 'microsoft', 'apple', 'amazon', 'meta', 'netflix', 'tesla',
            'shopify', 'uber', 'airbnb', 'stripe', 'palantir', 'databricks'
        }
        
        self.tier2_companies = {
            'ibm', 'oracle', 'salesforce', 'adobe', 'nvidia', 'intel', 'cisco',
            'rbc', 'td bank', 'bmo', 'scotiabank', 'cibc', 'deloitte', 'pwc',
            'kpmg', 'ey', 'mckinsey', 'bcg', 'bain'
        }
        
        # Government organizations
        self.government_orgs = {
            'government of canada', 'ontario public service', 'bc public service',
            'statistics canada', 'canada revenue agency', 'public health agency',
            'transport canada', 'innovation science'
        }
    
    def score_internship(self, internship: Internship, candidate_profile: Optional[CandidateProfile] = None) -> ScoringFactors:
        """Calculate comprehensive score for an internship"""
        
        # Calculate individual factor scores
        recency_score = self._calculate_recency_score(internship)
        relevance_score = self._calculate_relevance_score(internship, candidate_profile)
        quality_score = self._calculate_quality_score(internship)
        company_score = self._calculate_company_score(internship)
        location_score = self._calculate_location_score(internship, candidate_profile)
        
        # Calculate weighted final score
        final_score = (
            recency_score * self.weights.recency +
            relevance_score * self.weights.relevance +
            quality_score * self.weights.quality +
            company_score * self.weights.company +
            location_score * self.weights.location
        )
        
        return ScoringFactors(
            recency_score=recency_score,
            relevance_score=relevance_score,
            quality_score=quality_score,
            company_score=company_score,
            location_score=location_score,
            final_score=min(1.0, max(0.0, final_score))  # Clamp to [0, 1]
        )
    
    def _calculate_recency_score(self, internship: Internship) -> float:
        """Score based on how recently the internship was posted"""
        if not internship.posting_date:
            return 0.5  # Default score for unknown dates
        
        days_old = (datetime.utcnow() - internship.posting_date).days
        
        if days_old <= 1:
            return 1.0  # Posted today/yesterday
        elif days_old <= 7:
            return 0.9  # Within a week
        elif days_old <= 14:
            return 0.8  # Within two weeks
        elif days_old <= 30:
            return 0.6  # Within a month
        elif days_old <= 60:
            return 0.4  # Within two months
        elif days_old <= 90:
            return 0.2  # Within three months
        else:
            return 0.1  # Older than three months
    
    def _calculate_relevance_score(self, internship: Internship, candidate_profile: Optional[CandidateProfile]) -> float:
        """Score based on relevance to candidate profile and internship quality"""
        score = 0.5  # Base score
        
        # Title quality - prefer explicit internship titles
        title_lower = internship.title.lower()
        if any(keyword in title_lower for keyword in ['intern', 'internship', 'co-op', 'coop']):
            score += 0.2
        elif any(keyword in title_lower for keyword in ['student', 'entry level', 'junior']):
            score += 0.1
        elif any(keyword in title_lower for keyword in ['senior', 'lead', 'manager', 'director']):
            score -= 0.2  # Penalize senior roles
        
        # Field relevance
        if candidate_profile and candidate_profile.preferred_fields:
            if internship.field_tag in candidate_profile.preferred_fields:
                score += 0.3
        
        # Modality preference
        if candidate_profile and candidate_profile.preferred_modality:
            if internship.modality == candidate_profile.preferred_modality:
                score += 0.2
            elif candidate_profile.preferred_modality == Modality.HYBRID and internship.modality in [Modality.REMOTE, Modality.ONSITE]:
                score += 0.1  # Hybrid preference accepts both
        
        # Skills matching
        if candidate_profile and candidate_profile.skills:
            skill_matches = self._count_skill_matches(internship, candidate_profile.skills)
            score += min(0.3, skill_matches * 0.05)  # Up to 0.3 bonus for skills
        
        return min(1.0, max(0.0, score))
    
    def _calculate_quality_score(self, internship: Internship) -> float:
        """Score based on internship posting quality indicators"""
        score = 0.5  # Base score
        
        # Description quality
        if internship.description:
            desc_length = len(internship.description)
            if desc_length > 500:
                score += 0.2
            elif desc_length > 200:
                score += 0.1
            elif desc_length < 50:
                score -= 0.1
        
        # Salary information available
        if internship.salary_min or internship.salary_max:
            score += 0.15
            
            # Reasonable salary range
            if internship.salary_min and internship.salary_min >= 15:  # Minimum wage consideration
                score += 0.05
        
        # Requirements specified
        if internship.requirements and len(internship.requirements) > 50:
            score += 0.1
        
        # Benefits mentioned
        if internship.benefits:
            score += 0.05
        
        # Government positions (generally well-structured)
        if internship.is_government:
            score += 0.1
        
        # Deadline specified (shows organization)
        if internship.deadline:
            score += 0.05
        
        return min(1.0, max(0.0, score))
    
    def _calculate_company_score(self, internship: Internship) -> float:
        """Score based on company reputation and size"""
        if not internship.company:
            return 0.3  # Default for unknown companies
        
        company_name = internship.company.name.lower()
        
        # Tier 1 companies (FAANG, unicorns, etc.)
        if any(tier1 in company_name for tier1 in self.tier1_companies):
            return 1.0
        
        # Tier 2 companies (established tech, consulting, banking)
        if any(tier2 in company_name for tier2 in self.tier2_companies):
            return 0.8
        
        # Government organizations
        if any(gov in company_name for gov in self.government_orgs):
            return 0.7
        
        # Startups and scale-ups (heuristic based on name patterns)
        if any(indicator in company_name for indicator in ['technologies', 'labs', 'ai', 'tech']):
            return 0.6
        
        # Large corporations (heuristic)
        if any(indicator in company_name for indicator in ['inc', 'corp', 'ltd', 'limited']):
            return 0.5
        
        return 0.4  # Default for other companies
    
    def _calculate_location_score(self, internship: Internship, candidate_profile: Optional[CandidateProfile]) -> float:
        """Score based on location preferences and remote work"""
        if not internship.location:
            return 0.5  # Default for unknown locations
        
        location_lower = internship.location.lower()
        
        # Remote work gets high score
        if internship.modality == Modality.REMOTE:
            return 1.0
        
        # Hybrid work gets good score
        if internship.modality == Modality.HYBRID:
            return 0.8
        
        # Location matching
        if candidate_profile and candidate_profile.preferred_locations:
            for pref_location in candidate_profile.preferred_locations:
                if pref_location.lower() in location_lower:
                    return 0.9
        
        # Major tech hubs get higher scores
        tech_hubs = ['toronto', 'vancouver', 'montreal', 'ottawa', 'calgary', 'waterloo', 'kitchener']
        if any(hub in location_lower for hub in tech_hubs):
            return 0.7
        
        # Other Canadian cities
        if any(indicator in location_lower for indicator in ['canada', 'ontario', 'british columbia', 'quebec']):
            return 0.6
        
        return 0.4  # Default for other locations
    
    def _count_skill_matches(self, internship: Internship, candidate_skills: List[str]) -> int:
        """Count how many candidate skills match the internship description"""
        if not internship.description:
            return 0
        
        description_lower = internship.description.lower()
        matches = 0
        
        for skill in candidate_skills:
            skill_lower = skill.lower()
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(skill_lower) + r'\b', description_lower):
                matches += 1
        
        return matches
    
    def rank_internships(self, internships: List[Internship], candidate_profile: Optional[CandidateProfile] = None) -> List[Tuple[Internship, ScoringFactors]]:
        """Rank a list of internships by relevance score"""
        scored_internships = []
        
        for internship in internships:
            factors = self.score_internship(internship, candidate_profile)
            scored_internships.append((internship, factors))
        
        # Sort by final score (descending)
        scored_internships.sort(key=lambda x: x[1].final_score, reverse=True)
        
        return scored_internships
    
    def get_personalized_weights(self, user: User) -> ScoringWeights:
        """Get personalized scoring weights based on user preferences"""
        weights = ScoringWeights()
        
        # Adjust weights based on user profile
        # This could be enhanced with machine learning in the future
        
        # If user has strong location preferences, increase location weight
        if hasattr(user, 'preferred_locations') and user.preferred_locations:
            weights.location = 0.15
            weights.relevance = 0.25  # Reduce relevance slightly
        
        # If user is very focused on specific fields, increase relevance weight
        if hasattr(user, 'preferred_fields') and len(user.preferred_fields or []) <= 2:
            weights.relevance = 0.35
            weights.company = 0.10  # Reduce company weight slightly
        
        return weights

def calculate_internship_score(internship: Internship, candidate_profile: Optional[CandidateProfile] = None) -> float:
    """Convenience function to calculate a single internship score"""
    scorer = InternshipScorer()
    factors = scorer.score_internship(internship, candidate_profile)
    return factors.final_score

def rank_internships_for_user(internships: List[Internship], user: Optional[User] = None, candidate_profile: Optional[CandidateProfile] = None) -> List[Tuple[Internship, float]]:
    """Convenience function to rank internships for a user"""
    scorer = InternshipScorer()
    
    # Use personalized weights if user is provided
    if user:
        scorer.weights = scorer.get_personalized_weights(user)
    
    ranked = scorer.rank_internships(internships, candidate_profile)
    
    # Return simplified format with just scores
    return [(internship, factors.final_score) for internship, factors in ranked]
