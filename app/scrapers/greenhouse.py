import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapeQuery, RawPosting
from ..config import settings

class GreenhouseScraper(BaseScraper):
    """
    Scrapes job postings from Greenhouse.io for configured companies.
    """
    
    name = "greenhouse"
    description = "Greenhouse.io job board scraper"
    base_url = "https://boards-api.greenhouse.io"
    requires_feature_flag = False
    
    # List of company names to scrape (can be overridden in scrape method)
    companies: List[str] = []
    
    async def _fetch_company(self, client: httpx.AsyncClient, company: str) -> List[RawPosting]:
        """Fetch jobs for a single company"""
        url = f"{self.base_url}/v1/boards/{company}/jobs"
        
        try:
            response = await client.get(
                url,
                headers={"User-Agent": settings.USER_AGENT},
                timeout=15
            )
            
            if response.status_code != 200:
                return []
                
            jobs = response.json().get("jobs", [])
            postings = []
            
            for job in jobs:
                title = job.get("title", "")
                if not self._is_internship(title):
                    continue
                    
                location = (job.get("location") or {}).get("name")
                description = (job.get("content") or "")[:1000]  # Truncate long descriptions
                
                # Parse dates
                updated = job.get("updated_at")
                posted_date = self._parse_date(updated) if updated else datetime.now(timezone.utc)
                
                # Check if position is remote
                is_remote = any([
                    "remote" in title.lower(),
                    location and "remote" in location.lower(),
                    any(d.get("value", "").lower() == "remote" 
                        for d in job.get("metadata", []) 
                        if isinstance(d, dict))
                ])
                
                # Get department if available
                department = next(
                    (d.get("value") for d in job.get("metadata", []) 
                     if isinstance(d, dict) and d.get("name") == "Department"),
                    None
                )
                
                posting = RawPosting(
                    title=title,
                    company=company.title(),
                    location=location,
                    description=description,
                    apply_url=job.get("absolute_url"),
                    external_id=str(job.get("id")) if job.get("id") else None,
                    posted_date=posted_date,
                    is_remote=is_remote,
                    source_metadata={
                        "scraper": "greenhouse",
                        "department": department,
                        "company_id": company
                    }
                )
                postings.append(posting)
                
            return postings
            
        except Exception as e:
            print(f"Error fetching {company} jobs: {e}")
            return []
    
    async def scrape(self, query: ScrapeQuery = None) -> List[RawPosting]:
        """Scrape Greenhouse for internship postings"""
        query = query or ScrapeQuery()
        companies = self.companies or []
        
        # Add any companies from query keywords
        if query.keywords:
            companies.extend([k for k in query.keywords if k.isalpha()])
            
        if not companies:
            return []
            
        all_postings = []
        
        async with httpx.AsyncClient() as client:
            tasks = [self._fetch_company(client, c.lower().strip()) for c in set(companies)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                all_postings.extend(result)
                
        return all_postings[:query.max_results] if query and query.max_results else all_postings
    
    def _is_internship(self, title: str) -> bool:
        """Check if job title indicates an internship position"""
        if not title:
            return False
            
        title_lower = title.lower()
        return any(term in title_lower for term in ["intern", "co-op", "coop", "student"])
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string from Greenhouse API"""
        try:
            # Handle both with and without timezone
            if date_str.endswith("Z"):
                date_str = date_str[:-1] + "+00:00"
            return datetime.fromisoformat(date_str).astimezone(timezone.utc)
        except (ValueError, TypeError):
            return datetime.now(timezone.utc)
