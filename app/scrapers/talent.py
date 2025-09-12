import httpx
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from ..models import Opportunity
from ..config import settings

class TalentScraper:
    """
    Scrapes Talent.com for internships in Canada.
    """
    def __init__(self, query="internship", location="Canada", max_pages=2):
        self.query = query
        self.location = location
        self.max_pages = max_pages
        self.base_url = "https://ca.talent.com/jobs"

    async def fetch_page(self, client, page):
        params = {"k": self.query, "l": self.location, "p": page+1}
        try:
            r = await client.get(self.base_url, params=params, headers={"User-Agent": settings.user_agent}, timeout=15)
            if r.status_code != 200:
                return []
        except Exception:
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        jobs = []
        for card in soup.select("article.job-card"):
            title_el = card.select_one("h2 a")
            if not title_el: continue
            title = title_el.text.strip()
            link = "https://ca.talent.com" + title_el.get("href", "")
            company = card.select_one("span.card__company")
            company = company.text.strip() if company else "Unknown"
            loc = card.select_one("span.card__location")
            loc = loc.text.strip() if loc else None
            snippet = card.select_one("p.card__description")
            desc = snippet.text.strip() if snippet else ""
            posted_at = datetime.now(timezone.utc)

            jobs.append(
                Opportunity(
                    source="talent",
                    company=company,
                    title=title,
                    location=loc,
                    apply_url=link,
                    description_snippet=desc,
                    posted_at=posted_at,
                    remote_friendly="remote" in (loc or "").lower() or "remote" in desc.lower(),
                    job_id=link,
                    tags=["talent"],
                )
            )
        return jobs

    async def fetch(self):
        opps = []
        async with httpx.AsyncClient() as client:
            for p in range(self.max_pages):
                opps.extend(await self.fetch_page(client, p))
        return opps
