import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import httpx

from .base import BaseScraper, ScrapeQuery, RawPosting
from ..config import settings

class LeverScraper(BaseScraper):
    """
    Scrapes job postings from Lever.co for configured companies.
    """
    
    name = "lever"
    description = "Lever.co job board scraper"
    base_url = "https://api.lever.co/v0/postings"
    requires_feature_flag = False
    
    # List of company names to scrape (can be overridden in scrape method)
    companies: List[str] = []
    
    async def _fetch_company(self, client: httpx.AsyncClient, company: str) -> List[RawPosting]:
        """Fetch jobs for a single company"""
        url = f"{self.base_url}/{company}?mode=json"
        
        try:
            response = await client.get(
                url,
                headers={"User-Agent": settings.USER_AGENT},
                timeout=15
            )
            
            if response.status_code != 200:
                return []
                
            jobs = response.json()
            if not isinstance(jobs, list):
                return []
                
            postings = []
            
            for job in jobs:
                title = job.get("text", "")
                if not self._is_internship(title):
                    continue
                    
                location = (job.get("categories") or {}).get("location")
                description = (job.get("descriptionPlain") or "")[:1000]  # Truncate long descriptions
                
                # Parse dates (Lever uses milliseconds since epoch)
                created_at = job.get("createdAt")
                posted_date = (
                    datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
                    if created_at
                    else datetime.now(timezone.utc)
                )
                
                # Check if position is remote
                is_remote = any([
                    "remote" in title.lower(),
                    location and "remote" in location.lower(),
                    any("remote" in (t.get("name") or "").lower() 
                        for t in job.get("tags", []) 
                        if isinstance(t, dict))
                ])
                
                # Get tags as a list of strings
                tags = [
                    t.get("name") for t in job.get("tags", [])
                    if isinstance(t, dict) and t.get("name")
                ]
                
                # Get department if available
                department = (job.get("categories") or {}).get("team")
                
                posting = RawPosting(
                    title=title,
                    company=company.title(),
                    location=location,
                    description=description,
                    apply_url=job.get("hostedUrl") or "",
                    external_id=job.get("id"),
                    posted_date=posted_date,
                    is_remote=is_remote,
                    source_metadata={
                        "scraper": "lever",
                        "department": department,
                        "company_id": company,
                        "tags": tags
                    }
                )
                postings.append(posting)
                
            return postings
            
        except Exception as e:
            print(f"Error fetching {company} jobs: {e}")
            return []
    
    async def scrape(self, query: ScrapeQuery = None) -> List[RawPosting]:
        """Scrape Lever for internship postings"""
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
