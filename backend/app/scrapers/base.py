from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ScrapeQuery(BaseModel):
    """Query parameters for scraping jobs"""
    keywords: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    radius: int = 25  # in miles/kilometers
    max_results: int = 100
    days_old: int = 30  # max age of postings in days
    skip_duplicates: bool = True
    full_descriptions: bool = True

class RawPosting(BaseModel):
    """Raw job posting data from a scraper"""
    # Required fields
    title: str
    company: str
    location: str
    description: str
    source: str
    source_id: str  # Unique ID from the source
    posted_date: datetime
    url: str
    
    # Optional fields
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "CAD"
    salary_period: Optional[str] = None  # year, month, hour, etc.
    
    # Metadata
    is_remote: bool = False
    job_type: Optional[str] = None  # full-time, part-time, contract, etc.
    industry: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    
    # Internal use
    raw_data: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    
    class Config:
        arbitrary_types_allowed = True

class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.name = self.__class__.__name__.replace("Scraper", "").lower()
        self.base_url = ""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.rate_limit = 2.0  # seconds between requests
        self.last_request = 0
        
    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = asyncio.get_event_loop().time() - self.last_request
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self.last_request = asyncio.get_event_loop().time()
    
    @abstractmethod
    async def scrape(self, query: ScrapeQuery) -> List[RawPosting]:
        """
        Scrape job postings based on the query
        
        Args:
            query: Parameters for the search query
            
        Returns:
            List of raw job postings
        """
        pass
    
    async def process_results(self, postings: List[RawPosting], query: ScrapeQuery) -> List[RawPosting]:
        """
        Process and filter raw postings
        """
        # Filter out old postings
        if query.days_old > 0:
            min_date = datetime.utcnow() - timedelta(days=query.days_old)
            postings = [p for p in postings if p.posted_date >= min_date]
        
        # Filter by keywords if provided
        if query.keywords:
            keyword_set = set(k.lower() for k in query.keywords)
            filtered = []
            for posting in postings:
                content = f"{posting.title} {posting.description}".lower()
                if any(keyword in content for keyword in keyword_set):
                    filtered.append(posting)
            postings = filtered
        
        # Limit results
        if query.max_results > 0:
            postings = postings[:query.max_results]
            
        return postings
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        import re
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_regex, text)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove non-printable characters
        import string
        printable = set(string.printable)
        text = ''.join(filter(lambda x: x in printable, text))
        
        return text.strip()
    
    def parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object"""
        from dateutil import parser
        try:
            return parser.parse(date_str, fuzzy=True)
        except (ValueError, OverflowError):
            return datetime.utcnow()
