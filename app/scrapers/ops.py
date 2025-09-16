import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapeQuery, RawPosting
from ..config import settings

class OPSScraper(BaseScraper):
    """
    Scrapes Ontario Public Service (OPS) careers site for government internships.
    """
    
    name = "ops"
    description = "Ontario Public Service careers scraper"
    base_url = "https://www.gojobs.gov.on.ca"
    requires_feature_flag = False
    

    async def _fetch_page(self, client: httpx.AsyncClient, query: str, page: int) -> List[RawPosting]:
        """Fetch a single page of results"""
        params = {
            "keywords": f"{query} student internship" if query else "student internship",
            "page": page,
            "jobtype": "Student"
        }
        
        try:
            response = await client.get(
                f"{self.base_url}/Jobs.aspx",
                params=params,
                headers={"User-Agent": settings.USER_AGENT},
                timeout=15
            )
            
            if response.status_code != 200:
                return []
                
        except Exception as e:
            print(f"Error fetching OPS page: {e}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        postings = []
        
        # OPS uses specific selectors for job listings
        for card in soup.select(".job-listing, .job-item"):
            try:
                # Extract title and link
                title_el = card.select_one("h3 a, .job-title a")
                if not title_el:
                    continue
                    
                title = title_el.text.strip()
                relative_url = title_el.get("href", "")
                apply_url = urljoin(self.base_url, relative_url)
                
                # Extract department (acts as company for government)
                dept_el = card.select_one(".department, .ministry")
                company = dept_el.text.strip() if dept_el else "Ontario Public Service"
                
                # Extract location
                location_el = card.select_one(".location, .job-location")
                location_text = location_el.text.strip() if location_el else "Ontario, Canada"
                
                # Extract description snippet
                snippet_el = card.select_one(".job-summary, .description")
                description = snippet_el.text.strip() if snippet_el else ""
                
                # Extract salary if available
                salary_el = card.select_one(".salary, .compensation")
                salary_text = salary_el.text.strip() if salary_el else None
                salary_min, salary_max = self._parse_salary(salary_text)
                
                # Extract posting date
                date_el = card.select_one(".posted-date, .date-posted")
                posted_date = self._parse_date(date_el.text.strip() if date_el else None)
                
                # Extract deadline if available
                deadline_el = card.select_one(".deadline, .closing-date")
                deadline = self._parse_date(deadline_el.text.strip() if deadline_el else None)
                
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
                    is_government=True,  # OPS is government
                    source_metadata={
                        "scraper": "ops",
                        "page": page,
                        "deadline": deadline.isoformat() if deadline else None
                    }
                )
                
                postings.append(posting)
                
            except Exception as e:
                print(f"Error parsing OPS job card: {e}")
                continue
        
        return postings

    async def scrape(self, query: ScrapeQuery = None) -> List[RawPosting]:
        """Scrape OPS for internship postings"""
        query = query or ScrapeQuery()
        max_results = min(query.max_results or 100, 150)
        all_postings = []
        
        async with httpx.AsyncClient() as client:
            for page in range(1, (max_results // 20) + 2):
                page_postings = await self._fetch_page(
                    client, 
                    query=" ".join(query.keywords) if query.keywords else "",
                    page=page
                )
                
                if not page_postings:
                    break
                    
                all_postings.extend(page_postings)
                if len(all_postings) >= max_results:
                    break
                    
                await asyncio.sleep(2)  # Reduced delay
        
        return all_postings[:max_results]
    
    def _parse_salary(self, salary_text: str) -> Tuple[Optional[float], Optional[float]]:
        if not salary_text:
            return None, None
            
        clean_text = re.sub(r'[^\d\.,\-\s]', '', salary_text)
        
        patterns = [
            # Salary range (e.g., $45,000 - $55,000)
            (r'([\d,]+)\s*-\s*([\d,]+)', 
             lambda m: (float(m[1].replace(',', '')), float(m[2].replace(',', '')))),
            # Single value (e.g., $50,000)
            (r'([\d,]+)', 
             lambda m: (float(m[1].replace(',', '')),) * 2)
        ]
        
        for pattern, converter in patterns:
            match = re.search(pattern, clean_text)
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
            
        # Common date patterns
        patterns = [
            # YYYY-MM-DD
            (r'(\d{4})-(\d{2})-(\d{2})', 
             lambda m: datetime(int(m[0]), int(m[1]), int(m[2]), tzinfo=timezone.utc)),
            # MM/DD/YYYY
            (r'(\d{2})/(\d{2})/(\d{4})', 
             lambda m: datetime(int(m[2]), int(m[0]), int(m[1]), tzinfo=timezone.utc)),
            # DD Month YYYY
            (r'(\d{1,2})\s+(\w+)\s+(\d{4})',
             lambda m: datetime(int(m[2]), 
                              datetime.strptime(m[1][:3], "%b").month, 
                              int(m[0]), 
                              tzinfo=timezone.utc))
        ]
        
        for pattern, converter in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    return converter(match.groups())
                except (ValueError, IndexError):
                    continue
                    
        return now
    
    def _extract_job_id(self, url: str) -> str:
        """Extract job ID from OPS URL"""
        match = re.search(r'jobid=(\d+)', url)
        if match:
            return match.group(1)
        
        # Fallback to URL path
        return url.split('/')[-1]
    
    async def is_available(self) -> bool:
        """Check if OPS is accessible"""
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
