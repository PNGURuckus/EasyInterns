"""
Job Bank Canada scraper using Playwright
"""
import asyncio
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, urlparse

from backend.core.config import settings
from backend.data.models import FieldTag, Modality


class JobBankCanadaScraper:
    """Scraper for Job Bank Canada internships"""
    
    def __init__(self):
        self.base_url = "https://www.jobbank.gc.ca"
        self.search_url = f"{self.base_url}/jobsearch/jobsearch"
        self.cooldown = 2  # seconds between requests
        
    async def scrape_internships(self, max_pages: int = 5) -> List[Dict]:
        """Scrape internships from Job Bank Canada"""
        internships = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                # Search for internships
                await page.goto(self.search_url)
                await page.wait_for_load_state("networkidle")
                
                # Fill search form
                await page.fill('input[name="searchstring"]', "intern")
                await page.select_option('select[name="sort"]', "M")  # Most recent
                
                # Submit search
                await page.click('button[type="submit"]')
                await page.wait_for_load_state("networkidle")
                
                # Scrape multiple pages
                for page_num in range(1, max_pages + 1):
                    print(f"Scraping page {page_num}...")
                    
                    page_internships = await self._scrape_page(page)
                    internships.extend(page_internships)
                    
                    # Check for next page
                    next_button = await page.query_selector('a[aria-label="Next page"]')
                    if not next_button or page_num >= max_pages:
                        break
                        
                    await next_button.click()
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(self.cooldown)
                    
            except Exception as e:
                print(f"Error scraping Job Bank Canada: {e}")
            finally:
                await browser.close()
                
        return internships
    
    async def _scrape_page(self, page: Page) -> List[Dict]:
        """Scrape internships from current page"""
        internships = []
        
        # Get job listings
        job_elements = await page.query_selector_all('.resultJobItem')
        
        for job_element in job_elements:
            try:
                internship = await self._extract_job_data(page, job_element)
                if internship and self._is_internship(internship):
                    internships.append(internship)
            except Exception as e:
                print(f"Error extracting job data: {e}")
                continue
                
        return internships
    
    async def _extract_job_data(self, page: Page, job_element) -> Optional[Dict]:
        """Extract data from a single job element"""
        try:
            # Title and link
            title_element = await job_element.query_selector('.resultJobItemTitle a')
            if not title_element:
                return None
                
            title = await title_element.inner_text()
            job_url = await title_element.get_attribute('href')
            if job_url:
                job_url = urljoin(self.base_url, job_url)
            
            # Company
            company_element = await job_element.query_selector('.resultJobItemCompany')
            company = await company_element.inner_text() if company_element else "Unknown"
            
            # Location
            location_element = await job_element.query_selector('.resultJobItemLocation')
            location = await location_element.inner_text() if location_element else ""
            city, region = self._parse_location(location)
            
            # Salary
            salary_element = await job_element.query_selector('.resultJobItemWage')
            salary_text = await salary_element.inner_text() if salary_element else ""
            salary_min, salary_max = self._parse_salary(salary_text)
            
            # Posted date
            date_element = await job_element.query_selector('.resultJobItemDate')
            date_text = await date_element.inner_text() if date_element else ""
            posted_at = self._parse_date(date_text)
            
            # Get job details by visiting the job page
            description, skills, modality = await self._get_job_details(page, job_url)
            
            return {
                'title': title.strip(),
                'company_name': company.strip(),
                'description': description,
                'city': city,
                'region': region,
                'country': 'Canada',
                'modality': modality,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': 'CAD',
                'apply_url': job_url,
                'posted_at': posted_at,
                'skills_required': skills,
                'field_tag': self._classify_field(title, description),
                'source_name': 'job_bank_ca',
                'external_id': self._extract_job_id(job_url)
            }
            
        except Exception as e:
            print(f"Error extracting job data: {e}")
            return None
    
    async def _get_job_details(self, page: Page, job_url: str) -> tuple:
        """Get detailed job information"""
        if not job_url:
            return "", [], Modality.ON_SITE
            
        try:
            # Open job page in new tab
            new_page = await page.context.new_page()
            await new_page.goto(job_url)
            await new_page.wait_for_load_state("networkidle")
            
            # Description
            desc_element = await new_page.query_selector('.job-posting-detail-description')
            description = await desc_element.inner_text() if desc_element else ""
            
            # Skills (look for requirements section)
            skills = []
            requirements_element = await new_page.query_selector('.job-posting-detail-requirements')
            if requirements_element:
                req_text = await requirements_element.inner_text()
                skills = self._extract_skills(req_text)
            
            # Work modality
            modality = self._determine_modality(description)
            
            await new_page.close()
            await asyncio.sleep(self.cooldown)
            
            return description.strip(), skills, modality
            
        except Exception as e:
            print(f"Error getting job details: {e}")
            return "", [], Modality.ON_SITE
    
    def _is_internship(self, job_data: Dict) -> bool:
        """Check if job is an internship"""
        title = job_data.get('title', '').lower()
        description = job_data.get('description', '').lower()
        
        internship_keywords = [
            'intern', 'internship', 'co-op', 'coop', 'student', 
            'summer student', 'work term', 'placement'
        ]
        
        return any(keyword in title or keyword in description for keyword in internship_keywords)
    
    def _parse_location(self, location_text: str) -> tuple:
        """Parse location into city and region"""
        if not location_text:
            return None, None
            
        # Format: "City, Province" or "City, Province, Canada"
        parts = [part.strip() for part in location_text.split(',')]
        
        if len(parts) >= 2:
            city = parts[0]
            region = parts[1]
            return city, region
        elif len(parts) == 1:
            return parts[0], None
        
        return None, None
    
    def _parse_salary(self, salary_text: str) -> tuple:
        """Parse salary range"""
        if not salary_text:
            return None, None
            
        # Extract numbers from salary text
        numbers = re.findall(r'\$?([\d,]+)', salary_text)
        if not numbers:
            return None, None
            
        try:
            if len(numbers) >= 2:
                min_sal = int(numbers[0].replace(',', ''))
                max_sal = int(numbers[1].replace(',', ''))
                return min_sal, max_sal
            elif len(numbers) == 1:
                salary = int(numbers[0].replace(',', ''))
                return salary, None
        except ValueError:
            pass
            
        return None, None
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse posted date"""
        if not date_text:
            return None
            
        try:
            # Handle "X days ago" format
            if 'day' in date_text.lower():
                days_match = re.search(r'(\d+)', date_text)
                if days_match:
                    days_ago = int(days_match.group(1))
                    return datetime.now() - timedelta(days=days_ago)
            
            # Handle "today" or "yesterday"
            if 'today' in date_text.lower():
                return datetime.now()
            elif 'yesterday' in date_text.lower():
                return datetime.now() - timedelta(days=1)
                
        except Exception:
            pass
            
        return None
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from job description"""
        skills = []
        
        # Common tech skills
        tech_skills = [
            'Python', 'JavaScript', 'React', 'Node.js', 'Java', 'C++', 'C#',
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Git', 'Docker',
            'AWS', 'Azure', 'GCP', 'Kubernetes', 'Linux', 'HTML', 'CSS',
            'TypeScript', 'Vue.js', 'Angular', 'Django', 'Flask', 'Spring',
            'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn'
        ]
        
        text_lower = text.lower()
        for skill in tech_skills:
            if skill.lower() in text_lower:
                skills.append(skill)
                
        return skills[:10]  # Limit to 10 skills
    
    def _classify_field(self, title: str, description: str) -> FieldTag:
        """Classify internship field based on title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['software', 'developer', 'programming', 'coding', 'engineer']):
            return FieldTag.SOFTWARE_ENGINEERING
        elif any(word in text for word in ['data', 'analytics', 'machine learning', 'ai', 'scientist']):
            return FieldTag.DATA_SCIENCE
        elif any(word in text for word in ['product', 'pm', 'product manager']):
            return FieldTag.PRODUCT_MANAGEMENT
        elif any(word in text for word in ['design', 'ui', 'ux', 'designer']):
            return FieldTag.DESIGN_UX_UI
        elif any(word in text for word in ['marketing', 'digital marketing', 'content']):
            return FieldTag.MARKETING
        elif any(word in text for word in ['finance', 'financial', 'accounting']):
            return FieldTag.FINANCE
        elif any(word in text for word in ['sales', 'business development']):
            return FieldTag.SALES
        elif any(word in text for word in ['operations', 'ops', 'logistics']):
            return FieldTag.OPERATIONS
        else:
            return FieldTag.OTHER
    
    def _determine_modality(self, description: str) -> Modality:
        """Determine work modality from description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['remote', 'work from home', 'telecommute']):
            return Modality.REMOTE
        elif any(word in desc_lower for word in ['hybrid', 'flexible', 'remote and office']):
            return Modality.HYBRID
        else:
            return Modality.ON_SITE
    
    def _extract_job_id(self, job_url: str) -> Optional[str]:
        """Extract job ID from URL"""
        if not job_url:
            return None
            
        # Extract ID from URL pattern
        match = re.search(r'/jobposting/(\d+)', job_url)
        return match.group(1) if match else None


async def main():
    """Test the scraper"""
    scraper = JobBankCanadaScraper()
    internships = await scraper.scrape_internships(max_pages=2)
    
    print(f"Found {len(internships)} internships")
    for internship in internships[:3]:  # Show first 3
        print(f"- {internship['title']} at {internship['company_name']}")


if __name__ == "__main__":
    asyncio.run(main())
