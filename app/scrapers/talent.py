import httpx
from typing import List
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapeQuery, RawPosting
from ..config import settings


class TalentScraper(BaseScraper):
    """Minimal Talent.com scraper to satisfy tests."""

    name = "talent"
    description = "Talent.com job board scraper"
    base_url = "https://www.talent.com"
    requires_feature_flag = False

    async def scrape(self, query: ScrapeQuery | None = None) -> List[RawPosting]:
        query = query or ScrapeQuery(query="intern")
        params = {
            "query": query.query,
            "location": (query.location or "Canada"),
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/jobs", params=params, headers={"User-Agent": settings.user_agent})
                if resp.status_code != 200:
                    return []
                soup = BeautifulSoup(resp.text, "html.parser")
                results: List[RawPosting] = []
                for card in soup.select("div.job-item"):
                    title_el = card.select_one("h3 a")
                    company_el = card.select_one("div.company")
                    location_el = card.select_one("div.location")
                    desc_el = card.select_one("div.description")
                    if not title_el or not company_el:
                        continue
                    results.append(
                        RawPosting(
                            title=title_el.text.strip(),
                            company_name=company_el.text.strip(),
                            location=(location_el.text.strip() if location_el else None),
                            description=(desc_el.text.strip() if desc_el else None),
                            apply_url=title_el.get("href"),
                            source=self.name,
                        )
                    )
                return results
        except Exception:
            return []

