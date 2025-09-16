from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math
import re
from difflib import SequenceMatcher
from collections import defaultdict

from pydantic import BaseModel
import numpy as np

from app.models.internship import Internship, InternshipPublic
from app.models.user import User
from .weights import RankingWeights, get_weights_for_user

class RankingResult(BaseModel):
    """Result of ranking a single internship"""
    internship: InternshipPublic
    score: float
    score_breakdown: Dict[str, float]
    matched_keywords: List[str]
    matched_skills: List[str]

class RankingEngine:
    """Engine for ranking internships based on various factors"""
    
    def __init__(self, user: Optional[User] = None, weights: Optional[RankingWeights] = None):
        self.user = user
        self.weights = weights or get_weights_for_user(
            user.user_type if user and hasattr(user, 'user_type') else None
        )
        self.user_skills = set(
            skill.lower() 
            for skill in (user.skills if user and hasattr(user, 'skills') else [])
        )
        self.user_location = user.location.lower() if user and user.location else None
        self.user_keywords = self._extract_keywords_from_user()
    
    def _extract_keywords_from_user(self) -> Dict[str, float]:
        """Extract keywords from user profile, resume, etc."""
        keywords = defaultdict(float)
        
        if not self.user:
            return keywords
        
        # Add skills as keywords
        for skill in self.user_skills:
            keywords[skill] = 1.0
        
        # Add education field keywords
        if hasattr(self.user, 'education') and self.user.education:
            for edu in self.user.education:
                if 'field' in edu:
                    keywords[edu['field'].lower()] = 1.5
                if 'degree' in edu:
                    keywords[edu['degree'].lower()] = 1.2
        
        # Add work experience keywords
        if hasattr(self.user, 'experience') and self.user.experience:
            for exp in self.user.experience:
                if 'title' in exp:
                    keywords[exp['title'].lower()] = 1.3
                if 'company' in exp:
                    keywords[exp['company'].lower()] = 0.8
        
        return keywords
    
    def _calculate_keyword_score(self, text: str) -> Tuple[float, List[str]]:
        """Calculate keyword match score for a text"""
        if not text or not self.user_keywords:
            return 0.0, []
        
        text_lower = text.lower()
        score = 0.0
        matched_keywords = []
        
        for keyword, weight in self.user_keywords.items():
            # Exact match
            if f' {keyword} ' in f' {text_lower} ':
                score += weight * self.weights.must_have_keywords
                matched_keywords.append(keyword)
            # Fuzzy match (using simple substring matching, could be improved with TF-IDF)
            elif keyword in text_lower:
                score += weight * self.weights.nice_have_keywords * 0.5
                matched_keywords.append(f"{keyword}*")
        
        return score, matched_keywords
    
    def _calculate_skills_match(self, internship: InternshipPublic) -> Tuple[float, List[str]]:
        """Calculate skills match score"""
        if not self.user_skills or not internship.skills:
            return 0.0, []
        
        matched_skills = []
        score = 0.0
        
        for skill in internship.skills:
            skill_lower = skill.lower()
            # Check for exact match
            if skill_lower in self.user_skills:
                score += self.weights.skills_match
                matched_skills.append(skill)
            # Check for partial match
            else:
                for user_skill in self.user_skills:
                    if user_skill in skill_lower or skill_lower in user_skill:
                        score += self.weights.skills_match * 0.5
                        matched_skills.append(f"{skill}~")
                        break
        
        # Normalize by number of skills in the internship
        if internship.skills:
            score = min(score / len(internship.skills), 1.0) * self.weights.skills_match
        
        return score, matched_skills
    
    def _calculate_location_score(self, internship: InternshipPublic) -> float:
        """Calculate location match score"""
        if not self.user_location or not internship.location:
            return 0.0
        
        # Check for remote work
        if internship.is_remote:
            return self.weights.remote_work
        
        # Check for exact location match
        if self.user_location.lower() in internship.location.lower():
            return self.weights.location_match
        
        # Check for same city (simple check, could be improved with geocoding)
        user_city = self.user_location.split(',')[0].strip().lower()
        if user_city and user_city in internship.location.lower():
            return self.weights.location_match * 0.7
        
        # Check for same province/state
        if ',' in self.user_location and ',' in internship.location:
            user_province = self.user_location.split(',')[-1].strip().lower()
            job_province = internship.location.split(',')[-1].strip().lower()
            if user_province and user_province in job_province:
                return self.weights.location_match * 0.3
        
        return 0.0
    
    def _calculate_recency_score(self, posted_date: datetime) -> float:
        """Calculate recency score (higher for more recent postings)"""
        if not posted_date:
            return 0.0
        
        days_old = (datetime.utcnow() - posted_date).days
        return max(0.0, 1.0 - (days_old * self.weights.recency_decay))
    
    def _calculate_internship_signal(self, title: str) -> float:
        """Check if the posting is specifically for internships/co-ops"""
        if not title:
            return 0.0
        
        internship_terms = ['intern', 'co-op', 'coop', 'co op', 'student', 'new grad', 'entry level']
        title_lower = title.lower()
        
        if any(term in title_lower for term in internship_terms):
            return self.weights.internship_signal
        
        return 0.0
    
    def _calculate_salary_score(self, internship: InternshipPublic) -> float:
        """Calculate normalized salary score (0-1)"""
        if not internship.salary_min and not internship.salary_max:
            return 0.0
        
        # Use average if both min and max are available
        if internship.salary_min is not None and internship.salary_max is not None:
            salary = (internship.salary_min + internship.salary_max) / 2
        else:
            salary = internship.salary_min or internship.salary_max or 0
        
        # Normalize salary (this is a simplified example)
        # In a real app, you'd want to normalize based on industry/role averages
        if salary > 100000:  # $100k+
            return 1.0 * self.weights.salary_weight
        elif salary > 70000:  # $70k-$100k
            return 0.8 * self.weights.salary_weight
        elif salary > 50000:  # $50k-$70k
            return 0.6 * self.weights.salary_weight
        elif salary > 30000:  # $30k-$50k
            return 0.4 * self.weights.salary_weight
        else:  # <$30k
            return 0.2 * self.weights.salary_weight
    
    def _calculate_deadline_urgency(self, deadline: Optional[datetime]) -> float:
        """Calculate urgency score based on application deadline"""
        if not deadline:
            return 0.0
        
        days_until_deadline = (deadline - datetime.utcnow()).days
        
        if days_until_deadline <= 1:  # Less than 24 hours
            return 1.0 * self.weights.deadline_urgency
        elif days_until_deadline <= 3:  # 1-3 days
            return 0.8 * self.weights.deadline_urgency
        elif days_until_deadline <= 7:  # 3-7 days
            return 0.5 * self.weights.deadline_urgency
        elif days_until_deadline <= 14:  # 1-2 weeks
            return 0.3 * self.weights.deadline_urgency
        elif days_until_deadline <= 30:  # 2-4 weeks
            return 0.1 * self.weights.deadline_urgency
        else:  # More than a month
            return 0.0
    
    def _calculate_company_rating_score(self, company_rating: Optional[float]) -> float:
        """Calculate score based on company rating (if available)"""
        if company_rating is None:
            return 0.0
        
        # Normalize to 0-1 range (assuming 5-star rating)
        normalized_rating = company_rating / 5.0
        return normalized_rating * self.weights.company_rating
    
    def rank_internships(
        self, 
        internships: List[InternshipPublic],
        limit: Optional[int] = None
    ) -> List[RankingResult]:
        """
        Rank a list of internships based on relevance to the user
        
        Args:
            internships: List of internships to rank
            limit: Maximum number of results to return (None for all)
            
        Returns:
            List of RankingResult objects, sorted by score (highest first)
        """
        ranked = []
        
        for internship in internships:
            score_breakdown = {}
            
            # Calculate keyword match score
            keyword_score, matched_keywords = self._calculate_keyword_score(
                f"{internship.title} {internship.description}"
            )
            score_breakdown["keywords"] = keyword_score
            
            # Calculate skills match
            skills_score, matched_skills = self._calculate_skills_match(internship)
            score_breakdown["skills"] = skills_score
            
            # Calculate location score
            location_score = self._calculate_location_score(internship)
            score_breakdown["location"] = location_score
            
            # Calculate recency score
            recency_score = self._calculate_recency_score(internship.posted_date)
            score_breakdown["recency"] = recency_score
            
            # Check for internship/co-op in title
            internship_score = self._calculate_internship_signal(internship.title)
            score_breakdown["internship_signal"] = internship_score
            
            # Calculate salary score
            salary_score = self._calculate_salary_score(internship)
            score_breakdown["salary"] = salary_score
            
            # Calculate deadline urgency
            deadline_score = self._calculate_deadline_urgency(internship.application_deadline)
            score_breakdown["deadline"] = deadline_score
            
            # Calculate company rating score
            company_rating = getattr(internship, 'company_rating', None)
            company_score = self._calculate_company_rating_score(company_rating)
            score_breakdown["company_rating"] = company_score
            
            # Calculate total score
            total_score = sum(score_breakdown.values())
            
            # Create result
            result = RankingResult(
                internship=internship,
                score=total_score,
                score_breakdown=score_breakdown,
                matched_keywords=matched_keywords,
                matched_skills=matched_skills,
            )
            
            ranked.append(result)
        
        # Sort by score (descending)
        ranked.sort(key=lambda x: x.score, reverse=True)
        
        # Apply limit if specified
        if limit is not None:
            ranked = ranked[:limit]
        
        return ranked
