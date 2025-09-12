import asyncio
import httpx
from datetime import datetime, timezone
from ..models import Opportunity
from ..config import settings

class GreenhouseScraper:
    """
    Scrapes ALL postings from Greenhouse for the given companies, concurrently.
    """
    def __init__(self, companies):
        self.companies = [c.strip().lower() for c in (companies or []) if c]

    async def fetch_company(self, client: httpx.AsyncClient, company: str):
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
        try:
            r = await client.get(url, headers={"User-Agent": settings.user_agent}, timeout=settings.http_timeout_seconds)
            if r.status_code != 200:
                return []
            jobs = r.json().get("jobs", [])
        except Exception:
            return []

        opps = []
        for j in jobs:
            title = j.get("title","")
            location = (j.get("location") or {}).get("name")
            desc = (j.get("content") or "")[:800]
            updated = j.get("updated_at")
            posted_at = None
            if updated:
                try:
                    posted_at = datetime.fromisoformat(updated.replace("Z","+00:00")).astimezone(timezone.utc)
                except Exception:
                    posted_at = None
            remote = "remote" in title.lower() or (location or "").lower().startswith("remote")
            opps.append(
                Opportunity(
                    source="greenhouse",
                    company=company,
                    title=title,
                    location=location,
                    apply_url=j.get("absolute_url"),
                    description_snippet=desc,
                    posted_at=posted_at,
                    remote_friendly=remote,
                    job_id=str(j.get("id")) if j.get("id") else None,
                    tags=[],
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
