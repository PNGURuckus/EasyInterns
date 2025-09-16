from typing import List, Dict, Any, Protocol, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from html import unescape
from urllib.parse import urlparse
import re

@dataclass
class ScrapeQuery:
    """Query parameters for scraping (test-friendly)."""
    query: str
    location: Optional[str] = None
    max_results: int = 100
    posted_after: Optional[datetime] = None

@dataclass
class RawPosting:
    """Raw job posting data from scraper (test-friendly)."""
    title: str
    company_name: str
    location: Optional[str] = None
    description: Optional[str] = None
    apply_url: Optional[str] = None
    source: Optional[str] = None
    external_id: Optional[str] = None
    posted_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    is_government: bool = False
    source_metadata: Optional[Dict[str, Any]] = None

class SourceScraper(Protocol):
    """Protocol for internship scrapers"""
    
    name: str
    description: str
    base_url: str
    requires_feature_flag: bool = False
    
    async def scrape(self, query: ScrapeQuery = None) -> List[RawPosting]:
        """Scrape internships and return raw postings"""
        ...
    
    async def is_available(self) -> bool:
        """Check if scraper is available and working"""
        ...

class BaseScraper:
    """Base class for scrapers with common functionality"""
    
    name: str = "base"
    description: str = "Base scraper"
    base_url: str = ""
    requires_feature_flag: bool = False
    
    async def scrape(self, query: ScrapeQuery = None) -> List[RawPosting]:
        """Scrape internships and return raw postings"""
        raise NotImplementedError
    
    async def is_available(self) -> bool:
        """Default availability check"""
        return True
    
    def normalize_posting(self, raw_data: Dict[str, Any]) -> RawPosting:
        """Normalize raw scraping data to RawPosting format"""
        return RawPosting(
            title=raw_data.get("title", ""),
            company_name=raw_data.get("company_name", raw_data.get("company", "")),
            location=raw_data.get("location"),
            description=raw_data.get("description"),
            apply_url=raw_data.get("apply_url"),
            source=raw_data.get("source"),
            external_id=raw_data.get("external_id"),
            posted_date=raw_data.get("posted_date"),
            application_deadline=raw_data.get("application_deadline"),
            salary_min=raw_data.get("salary_min"),
            salary_max=raw_data.get("salary_max"),
            requirements=raw_data.get("requirements"),
            benefits=raw_data.get("benefits"),
            is_government=raw_data.get("is_government", False),
            source_metadata=raw_data.get("metadata", {}),
        )

    def _clean_text(self, text: str) -> str:
        """Strip HTML tags and normalize whitespace."""
        if not text:
            return ""
        # Remove tags crudely
        no_tags = re.sub(r"<[^>]+>", " ", text)
        # Unescape entities and collapse whitespace
        cleaned = " ".join(unescape(no_tags).split())
        # Remove space before punctuation like !, ., , etc.
        cleaned = re.sub(r"\s+([?!.,;:])", r"\1", cleaned)
        return cleaned

    def _extract_domain(self, url: str) -> str:
        """Extract domain from a URL, preserving subdomains."""
        try:
            parsed = urlparse(url)
            host = parsed.netloc or ""
            if host.startswith("www."):
                host = host[4:]
            return host
        except Exception:
            return ""

    def _parse_posting_date(self, text: str):
        """Parse relative date strings like '2 days ago' or 'today' to a date."""
        if not text:
            return None
        s = text.strip().lower()
        now = datetime.now()
        if "today" in s:
            return now.date()
        m = re.search(r"(\d+)\s+days?\s+ago", s)
        if m:
            days = int(m.group(1))
            return (now - timedelta(days=days)).date()
        return None
