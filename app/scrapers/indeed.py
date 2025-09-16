import asyncio
import httpx
import re
from datetime import datetime, timezone
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .base import BaseScraper, ScrapeQuery, RawPosting
from ..config import settings

class IndeedScraper(BaseScraper):
    """
    Scrapes Indeed.ca for internships in Canada.
    NOTE: Uses HTML parsing since Indeed has no free API.
    """
    
    name = "indeed"
    description = "Indeed Canada job board scraper"
    base_url = "https://ca.indeed.com"
    requires_feature_flag = False
    
    # Remove redundant __init__ - use settings directly

    async def _fetch_page(self, client: httpx.AsyncClient, query: str, location: str, start: int) -> List[RawPosting]:
        """Fetch a single page of results with improved error handling and performance"""
        params = {
            "q": f"{query} intern OR internship OR co-op" if not any(term in query.lower() for term in ["intern", "coop", "co-op"]) else query,
            "l": location,
            "start": start,
            "fromage": 7,  # Last 7 days
            "sort": "date"  # Most recent first
        }
        
        try:
            response = await client.get(
                f"{self.base_url}/jobs",
                params=params,
                headers={"User-Agent": settings.user_agent},
                timeout=15,
                follow_redirects=True
            )
            
            if response.status_code != 200:
                print(f"Indeed returned status {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Check for rate limiting or captcha
            if "unusual traffic" in response.text.lower() or "captcha" in response.text.lower():
                print("Warning: Potential rate limiting or captcha detected")
                return []
                
            postings = []
            job_cards = soup.select("div.job_seen_beacon")
            
            if not job_cards:
                print("No job cards found on page")
                return []
            
            for card in job_cards:
                try:
                    # Extract title and link
                    title_el = card.select_one("h2 a[data-jk]")
                    if not title_el:
                        continue
                        
                    title = (title_el.get("aria-label") or title_el.text).strip()
                    job_id = title_el.get("data-jk")
                    if not job_id:
                        continue
                        
                    apply_url = f"{self.base_url}/viewjob?jk={job_id}"
                    
                    # Extract company with better error handling
                    company_el = card.select_one("span[data-testid=company-name]")
                    company = company_el.text.strip() if company_el else "Unknown Company"
                    
                    # Extract location with better handling
                    location_el = card.select_one("div[data-testid=text-location]")
                    location_text = location_el.text.strip() if location_el else "Remote"
                    
                    # Extract description with better fallbacks
                    snippet_el = card.select_one("div.job-snippet")
                    description = " ".join(li.text.strip() for li in snippet_el.select("li")) if snippet_el else ""
                    
                    # Extract salary with better parsing
                    salary_el = card.select_one("div.metadata div:first-child")
                    salary_text = salary_el.text.strip() if salary_el else None
                    salary_min, salary_max = self._parse_salary(salary_text)
                    
                    # Check if remote
                    is_remote = any(term in location_text.lower() for term in ["remote", "work from home", "wfh"])
                    
                    # Get posting date if available
                    posted_date = self._parse_posted_date(card)
                    
                    posting = RawPosting(
                        title=title,
                        company_name=company,
                        location=location_text,
                        description=description,
                        apply_url=apply_url,
                        source=self.name,
                        external_id=job_id,
                        posted_date=posted_date,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        source_metadata={
                            "scraper": "indeed",
                            "page": (start // 10) + 1,
                            "search_query": query,
                            "location": location
                        }
                    )
                    
                    postings.append(posting)
                    
                except Exception as e:
                    print(f"Error parsing Indeed job card: {e}")
                    continue
            
            return postings
                
        except httpx.RequestError as e:
            print(f"Request error fetching Indeed page: {e}")
        except Exception as e:
            print(f"Unexpected error in _fetch_page: {e}")
            
        return []

    async def scrape(self, query: ScrapeQuery | None = None) -> List[RawPosting]:
        """Scrape Indeed for internship postings with improved concurrency and error handling"""
        base_query = (query.query if query else "")
        # Build search query with internship terms if not already present
        search_terms = [base_query] if base_query else []
        if not any(term in base_query.lower() for term in ["intern", "internship", "co-op", "coop"]):
            search_terms.append("intern OR internship OR co-op")

        search_query = " ".join(search_terms)
        location = (query.location if query else None) or "Canada"
        # Allow large result sets (up to ~1500) while keeping reasonable caps
        max_results = min(((query.max_results if query else 1000) or 1000), 1500)
        
        # Calculate number of pages needed
        per_page = 15  # Indeed shows ~15 results per page
        # Cap pages to avoid being too aggressive in a single run
        max_pages = min((max_results + per_page - 1) // per_page, 100)
        
        all_postings = []
        seen_ids = set()
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=True
        ) as client:
            tasks = []
            
            # Create tasks for all pages
            for page in range(max_pages):
                start = page * per_page
                tasks.append(self._fetch_page(client, search_query, location, start))
                
                # Small delay between creating tasks to avoid overwhelming
                if page > 0 and page % 3 == 0:
                    await asyncio.sleep(0.35)
            
            # Process results as they complete
            for task in asyncio.as_completed(tasks):
                try:
                    page_postings = await task
                    
                    # Deduplicate and add to results
                    for posting in page_postings:
                        if posting.external_id not in seen_ids:
                            seen_ids.add(posting.external_id)
                            all_postings.append(posting)
                            
                            if len(all_postings) >= max_results:
                                return all_postings[:max_results]
                                
                except Exception as e:
                    print(f"Error in scrape task: {e}")
                    continue
                
                # Small delay between processing pages
                await asyncio.sleep(0.25)
        
        return all_postings[:max_results]
    
    def _parse_salary(self, salary_text: str) -> tuple[float, float]:
        """Parse salary information from text with improved accuracy"""
        if not salary_text or not isinstance(salary_text, str):
            return None, None
        
        # Common salary patterns
        patterns = [
            # $100,000 - $150,000 a year
            (r'\$?([\d,]+)\s*-\s*\$?([\d,]+)\s*(?:a year|yr|yearly|annually)', 1.0),
            # $50 - $60 an hour
            (r'\$?([\d.]+)\s*-\s*\$?([\d.]+)\s*(?:an hour|hr|hourly)', 2080),  # Approx hours in work year
            # $100,000 a year
            (r'\$?([\d,]+)\s*(?:a year|yr|yearly|annually)', 1.0),
            # $50 an hour
            (r'\$?([\d.]+)\s*(?:an hour|hr|hourly)', 2080),
            # $25/hour or $25/hr
            (r'\$?([\d.]+)\s*/\s*(?:hour|hr)', 2080),
            # Simple number range (fallback)
            (r'([\d,]+)\s*-\s*([\d,]+)', 1.0),
            # Single number (fallback)
            (r'([\d,]+)', 1.0)
        ]
        
        # Clean and normalize the text (preserve spaces for patterns)
        clean_text = salary_text.lower()
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 2:  # Range
                        min_val = float(groups[0].replace(',', '')) * multiplier
                        max_val = float(groups[1].replace(',', '')) * multiplier
                        return min_val, max_val
                    else:  # Single value
                        val = float(groups[0].replace(',', '')) * multiplier
                        return val, val
                except (ValueError, IndexError) as e:
                    continue
        
        return None, None
    
    def _parse_posted_date(self, card) -> datetime:
        """Parse the posted date from the job card"""
        try:
            date_el = card.select_one("span.date")
            if not date_el:
                return datetime.now(timezone.utc)
                
            date_text = date_el.text.strip().lower()
            now = datetime.now(timezone.utc)
            
            if "just posted" in date_text or "today" in date_text:
                return now
            elif "yesterday" in date_text:
                return now.replace(day=now.day-1)
            elif "days ago" in date_text:
                days = int(re.search(r'(\d+)\s+days?', date_text).group(1))
                return now.replace(day=now.day-days)
            elif "week" in date_text:
                weeks = int(re.search(r'(\d+)\s+weeks?', date_text).group(1))
                return now.replace(day=now.day-(weeks*7))
            else:
                return now
                
        except Exception:
            return datetime.now(timezone.utc)
    
    async def is_available(self) -> bool:
        """Check if Indeed is accessible and not blocking requests"""
        try:
            async with httpx.AsyncClient() as client:
                # First check basic connectivity
                response = await client.head(
                    self.base_url,
                    headers={"User-Agent": settings.user_agent},
                    timeout=10,
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    return False
                
                # Then check if we're getting rate limited
                test_response = await client.get(
                    f"{self.base_url}/jobs",
                    params={"q": "test", "l": "Canada"},
                    headers={"User-Agent": settings.user_agent},
                    timeout=10
                )
                
                # Check for rate limiting or captcha
                if any(term in test_response.text.lower() for term in ["unusual traffic", "captcha"]):
                    print("Warning: Indeed is rate limiting requests")
                    return False
                    
                return True
                
        except httpx.RequestError as e:
            print(f"Request error checking Indeed availability: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error checking Indeed availability: {e}")
            return False
