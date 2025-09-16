import asyncio
import re
from datetime import datetime, timezone
from typing import List
from urllib.parse import urljoin, parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapeQuery, RawPosting
from ..config import settings

class JobBankScraper(BaseScraper):
    """
    Scrapes Job Bank Canada (jobbank.gc.ca) for government and private internships.
    """
    
    name = "job_bank"
    description = "Job Bank Canada government job board scraper"
    base_url = "https://www.jobbank.gc.ca"
    requires_feature_flag = False
    

    async def _fetch_page(self, client: httpx.AsyncClient, query: str, location: str, page: int) -> List[RawPosting]:
        """Fetch a single page of results"""
        
        params = {
            "searchstring": f"{query} internship" if query else "internship",
            "locationstring": location or "Canada",
            "page": page
        }
        search_url = f"{self.base_url}/jobsearch/jobsearch"
        
        try:
            response = await client.get(
                search_url,
                params=params,
                headers={"User-Agent": settings.USER_AGENT},
                timeout=15
            )
            
            if response.status_code != 200:
                return []
                
        except Exception as e:
            print(f"Error fetching Job Bank page: {e}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        postings = []
        
        # Job Bank uses specific selectors
        for card in soup.select("article.resultJobItem"):
            try:
                # Extract title and link
                title_el = card.select_one("h3 a")
                if not title_el:
                    continue
                    
                title = title_el.text.strip()
                relative_url = title_el.get("href", "")
                apply_url = urljoin(self.base_url, relative_url)
                
                # Extract company
                company_el = card.select_one(".resultJobItemCompany")
                company = company_el.text.strip() if company_el else "Unknown Company"
                
                # Extract location
                location_el = card.select_one(".resultJobItemLocation")
                location_text = location_el.text.strip() if location_el else None
                
                # Extract description snippet
                snippet_el = card.select_one(".resultJobItemSummary")
                description = snippet_el.text.strip() if snippet_el else ""
                
                # Extract salary if available
                salary_el = card.select_one(".resultJobItemWage")
                salary_text = salary_el.text.strip() if salary_el else None
                salary_min, salary_max = self._parse_salary(salary_text)
                
                # Extract posting date
                date_el = card.select_one(".resultJobItemDatePosted")
                posted_date = self._parse_date(date_el.text.strip() if date_el else None)
                
                # Create external ID from URL
                external_id = self._extract_job_id(apply_url)
                
                posting = RawPosting(
                    title=title,
                    company=company,
                    location=location_text,
                    description=description,
                    apply_url=apply_url,
                    external_id=external_id,
                    posted_date=posted_date,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    is_government=True,  # Job Bank is government
                    source_metadata={
                        "scraper": "job_bank",
                        "page": page
                    }
                )
                
                postings.append(posting)
                
            except Exception as e:
                print(f"Error parsing Job Bank job card: {e}")
                continue
        
        return postings

    async def scrape(self, query: ScrapeQuery = None) -> List[RawPosting]:
        """Scrape Job Bank for internship postings"""
        query = query or ScrapeQuery()
        max_results = min(query.max_results or 100, 200)
        all_postings = []
        
        async with httpx.AsyncClient() as client:
            for page in range(1, (max_results // 25) + 2):
                page_postings = await self._fetch_page(
                    client, 
                    query=" ".join(query.keywords) if query.keywords else "",
                    location=query.location,
                    page=page
                )
                
                if not page_postings:
                    break
                    
                all_postings.extend(page_postings)
                if len(all_postings) >= max_results:
                    break
                    
                await asyncio.sleep(1.5)  # Reduced delay between requests
        
        return all_postings[:max_results]
    
    def _parse_salary(self, salary_text: str) -> tuple[float, float]:
        if not salary_text:
            return None, None
            
        clean_text = re.sub(r'[^\d\.,\-\s]', '', salary_text)
        
        # Try different salary patterns
        patterns = [
            # Hourly rate (e.g., $15.50/hour)
            (r'(\d+\.?\d*)\s*(?:to|-)?\s*(\d+\.?\d*)?\s*(?:per|/)\s*hour', 
             lambda m: (float(m[1]) * 2080, float(m[2]) * 2080 if m[2] else float(m[1]) * 2080)),
            # Yearly range (e.g., $50,000 - $60,000)
            (r'([\d,]+)\s*-\s*([\d,]+)', 
             lambda m: (float(m[1].replace(',', '')), float(m[2].replace(',', '')))),
            # Single value (e.g., $45,000)
            (r'([\d,]+)', 
             lambda m: (float(m[1].replace(',', '')),) * 2)
        ]
        
        for pattern, converter in patterns:
            match = re.search(pattern, salary_text.lower() if 'hour' in pattern else clean_text)
            if match:
                try:
                    return converter(match.groups())
                except (ValueError, IndexError):
                    continue
                    
        return None, None
    
    def _parse_date(self, date_text: str) -> datetime:
        if not date_text:
            return datetime.now(timezone.utc)
            
        date_text = date_text.lower()
        now = datetime.now(timezone.utc)
        
        if "today" in date_text:
            return now
        if "yesterday" in date_text:
            return now.replace(day=now.day - 1)
            
        days_ago = re.search(r'(\d+)\s*days?\s*ago', date_text)
        if days_ago:
            days = int(days_ago.group(1))
            return now.replace(day=now.day - days)
        
        return datetime.now(timezone.utc)
    
    def _extract_job_id(self, url: str) -> str:
        """Extract job ID from Job Bank URL"""
        parsed = urlparse(url)
        if parsed.query:
            params = parse_qs(parsed.query)
            if 'jobid' in params:
                return params['jobid'][0]
        
        # Fallback to URL path
        return url.split('/')[-1]
    
    async def is_available(self) -> bool:
        """Check if Job Bank is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers={"User-Agent": settings.USER_AGENT},
                    timeout=10
                )
                return response.status_code == 200
        except Exception:
            return False
