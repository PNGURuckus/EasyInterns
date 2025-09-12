import asyncio
import httpx
from datetime import datetime
from ..models import Opportunity
from ..config import settings

class LeverScraper:
    """
    Scrapes ALL postings from Lever for the given companies, concurrently.
    """
    def __init__(self, companies):
        self.companies = [c.strip().lower() for c in (companies or []) if c]

    async def fetch_company(self, client: httpx.AsyncClient, company: str):
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        try:
            r = await client.get(url, headers={"User-Agent": settings.user_agent}, timeout=settings.http_timeout_seconds)
            if r.status_code != 200:
                return []
            data = r.json()
        except Exception:
            return []

        opps = []
        for item in data:
            title = item.get("text") or ""
            location = (item.get("categories") or {}).get("location")
            desc = (item.get("descriptionPlain") or "")[:800]
            created = item.get("createdAt")
            posted_at = datetime.fromtimestamp(created/1000) if created else None
            remote = "remote" in title.lower() or (location or "").lower().startswith("remote")
            tags = [t.get("name") for t in item.get("tags", [])] if item.get("tags") else []
            opps.append(
                Opportunity(
                    source="lever",
                    company=company,
                    title=title,
                    location=location,
                    apply_url=item.get("hostedUrl") or "",
                    description_snippet=desc,
                    posted_at=posted_at,
                    remote_friendly=remote,
                    job_id=item.get("id"),
                    tags=tags,
                )
            )
        return opps

    async def fetch(self):
        if not self.companies:
            return []
        opps = []
        async with httpx.AsyncClient() as client:
            tasks = [self.fetch_company(client, c) for c in self.companies]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                continue
            opps.extend(r)
        return opps
