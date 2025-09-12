from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict

@dataclass
class CandidateProfile:
    name: str
    email: Optional[str] = None
    education_level: Optional[str] = None
    location_preference: Optional[str] = None
    remote_ok: bool = True
    visa_requirement: Optional[str] = None
    interests: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    must_have_keywords: List[str] = field(default_factory=list)
    nice_to_have_keywords: List[str] = field(default_factory=list)

@dataclass
class Opportunity:
    source: str
    company: str
    title: str
    location: Optional[str]
    apply_url: str
    description_snippet: Optional[str] = None
    posted_at: Optional[datetime] = None
    remote_friendly: Optional[bool] = None
    job_id: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    extra: Dict[str, str] = field(default_factory=dict)

    def key(self) -> str:
        return f"{self.company}|{self.title}|{self.apply_url}".lower()

    def is_intern_role(self) -> bool:
        t = self.title.lower()
        return any(k in t for k in ["intern", "co-op", "summer student", "apprentice"])
