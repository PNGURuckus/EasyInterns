import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, RawPosting, ScrapeQuery
from ..core.config import settings

logger = logging.getLogger(__name__)

@scraper_registry.register
class JobBankScraper(BaseScraper):
    """Scraper for Job Bank Canada (https://www.jobbank.gc.ca/)"""
    
    def __init__(self):
        super().__init__()
        self.name = "jobbank"
        self.base_url = "https://www.jobbank.gc.ca"
        self.search_url = f"{self.base_url}/jobbank/jobsearch"
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-CA,en-US;q=0.7,en;q=0.3",
            "Referer": f"{self.base_url}/",
        }
        self.rate_limit = 1.5  # Be respectful of their servers
    
    async def _fetch_search_page(self, client: httpx.AsyncClient, query: ScrapeQuery, page: int = 1) -> Optional[str]:
        """Fetch a search results page"""
        params = {
            "searchstring": " ".join(query.keywords) if query.keywords else "internship",
            "locationstring": query.location or "",
            "sort": "D",  # Sort by date
            "page": page,
            "fprov": "ON",  # Default to Ontario
            "fd": "",  # Job posting date (empty for all)
        }
        
        try:
            await self._rate_limit()
            response = await client.get(
                self.search_url,
                params=params,
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True
            )
            response.raise_for_status()
            return response.text
        except (httpx.HTTPError, asyncio.TimeoutError) as e:
            logger.error(f"Error fetching JobBank search page: {str(e)}")
            return None
    
    async def _parse_search_results(self, html: str) -> List[Dict[str, str]]:
        """Parse job listing URLs from search results"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        jobs = []
        
        for article in soup.select('article.result'):
            try:
                title_elem = article.select_one('span.noctitle')
                if not title_elem or not title_elem.find('a'):
                    continue
                    
                job = {
                    'title': self.clean_text(title_elem.get_text(strip=True)),
                    'url': self.base_url + title_elem.find('a')['href'],
                    'company': self.clean_text(article.select_one('li.business').get_text(strip=True)) if article.select_one('li.business') else "",
                    'location': self.clean_text(article.select_one('li.location').get_text(strip=True)) if article.select_one('li.location') else "",
                    'date': article.select_one('span.date').get_text(strip=True) if article.select_one('span.date') else "",
                }
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing job listing: {str(e)}")
                continue
                
        return jobs
    
    async def _fetch_job_details(self, client: httpx.AsyncClient, job_url: str) -> Optional[Dict]:
        """Fetch and parse detailed job posting"""
        try:
            await self._rate_limit()
            response = await client.get(job_url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract job details
            job_details = {
                'description': "",
                'salary': "",
                'employment_type': "",
                'start_date': "",
                'skills': [],
                'requirements': [],
            }
            
            # Main job description
            description_section = soup.select_one('div.job-posting-details')
            if description_section:
                job_details['description'] = self.clean_text(description_section.get_text())
            
            # Salary information
            salary_section = soup.select_one('div.salary')
            if salary_section:
                job_details['salary'] = self.clean_text(salary_section.get_text())
            
            # Employment type and other metadata
            for item in soup.select('div.job-posting-brief'):
                label = item.select_one('span.attribute-label')
                if label and 'employment type' in label.text.lower():
                    job_details['employment_type'] = self.clean_text(item.get_text())
                elif label and 'start date' in label.text.lower():
                    job_details['start_date'] = self.clean_text(item.get_text())
            
            # Skills and requirements
            for section in soup.select('div.profile-content'):
                heading = section.select_one('h4')
                if not heading:
                    continue
                    
                heading_text = heading.get_text(strip=True).lower()
                if 'skills' in heading_text:
                    job_details['skills'] = [
                        self.clean_text(li.get_text())
                        for li in section.select('li')
                    ]
                elif 'requirements' in heading_text:
                    job_details['requirements'] = [
                        self.clean_text(li.get_text())
                        for li in section.select('li')
                    ]
            
            return job_details
            
        except (httpx.HTTPError, asyncio.TimeoutError) as e:
            logger.error(f"Error fetching job details from {job_url}: {str(e)}")
            return None
    
    def _parse_salary(self, salary_text: str) -> tuple[Optional[float], Optional[float], str]:
        """Parse salary information from text"""
        if not salary_text:
            return None, None, "CAD"
        
        # Simple salary parsing - this can be enhanced based on actual formats
        import re
        
        # Look for hourly rates
        hourly_match = re.search(r'\$([\d,.]+)(?:\s*to\s*\$?([\d,.]+))?\s*per hour', salary_text, re.IGNORECASE)
        if hourly_match:
            min_sal = float(hourly_match.group(1).replace(',', ''))
            max_sal = float(hourly_match.group(2).replace(',', '')) if hourly_match.group(2) else min_sal
            return min_sal, max_sal, "CAD/hour"
        
        # Look for annual salaries
        annual_match = re.search(r'\$([\d,.]+)(?:\s*to\s*\$?([\d,.]+))?\s*(?:per year|annually|/year)', salary_text, re.IGNORECASE)
        if annual_match:
            min_sal = float(annual_match.group(1).replace(',', ''))
            max_sal = float(annual_match.group(2).replace(',', '')) if annual_match.group(2) else min_sal
            return min_sal, max_sal, "CAD/year"
        
        return None, None, "CAD"
    
    async def scrape(self, query: ScrapeQuery) -> List[RawPosting]:
        """Scrape job postings from Job Bank Canada"""
        if not query.keywords and not query.location:
            logger.warning("No keywords or location provided for JobBank search")
            return []
        
        all_postings = []
        
        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
            http2=True
        ) as client:
            # Get first page of results
            html = await self._fetch_search_page(client, query, page=1)
            if not html:
                return []
            
            # Parse job listings from first page
            jobs = await self._parse_search_results(html)
            
            # Process each job listing
            for job in jobs:
                try:
                    # Get job details
                    details = await self._fetch_job_details(client, job['url'])
                    if not details:
                        continue
                    
                    # Parse salary
                    salary_min, salary_max, salary_period = self._parse_salary(details.get('salary', ''))
                    
                    # Create RawPosting
                    posting = RawPosting(
                        title=job['title'],
                        company=job['company'],
                        location=job['location'],
                        description=details.get('description', ''),
                        source=self.name,
                        source_id=job['url'].split('/')[-1],  # Use job ID from URL
                        posted_date=self.parse_date(job['date']),
                        url=job['url'],
                        salary_min=salary_min,
                        salary_max=salary_max,
                        salary_currency="CAD",
                        salary_period=salary_period,
                        is_remote=any(term in job['location'].lower() for term in ['remote', 'work from home', 'telecommute']),
                        job_type=details.get('employment_type', ''),
                        skills=details.get('skills', []),
                        requirements=details.get('requirements', []),
                        raw_data={
                            'job': job,
                            'details': details
                        }
                    )
                    
                    all_postings.append(posting)
                    
                    # Respect max_results
                    if query.max_results and len(all_postings) >= query.max_results:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing job listing: {str(e)}")
                    continue
        
        return all_postings
