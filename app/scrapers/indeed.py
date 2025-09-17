import logging
from datetime import datetime, timezone
from typing import Iterable

import httpx
from bs4 import BeautifulSoup

from ..config import settings
from ..models import Opportunity

logger = logging.getLogger(__name__)


class IndeedScraper:
    """Fetch internship listings using the Remotive public jobs API.

    Indeed aggressively blocks automated requests behind Cloudflare which
    prevents reliable scraping without an anti-bot proxy. To keep this
    project functional in a sandboxed environment we use the public Remotive
    API as a data source for remote internships. Results are filtered to
    Canada (or the requested location).
    """

    REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
    GLOBAL_KEYWORDS = {"anywhere", "global", "worldwide", "international"}

    def __init__(self, query: str = "intern", location: str = "Canada", max_results: int = 200):
        self.query = query
        self.location = location
        self.max_results = max_results

    async def _fetch_jobs(self) -> Iterable[dict]:
        params = {"search": self.query}
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            try:
                resp = await client.get(self.REMOTIVE_URL, params=params)
                resp.raise_for_status()
            except Exception as exc:
                logger.exception("Remotive API request failed: %s", exc)
                return []
        data = resp.json()
        return data.get("jobs", [])

    def _location_matches(self, location_text: str) -> bool:
        if not self.location:
            return True
        if not location_text:
            return False
        lt = location_text.lower()
        if self.location.lower() in lt:
            return True
        return any(token in lt for token in self.GLOBAL_KEYWORDS)

    def _parse_posted_at(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    async def fetch(self) -> list[Opportunity]:
        jobs = await self._fetch_jobs()
        opps: list[Opportunity] = []
        for job in jobs:
            if len(opps) >= self.max_results:
                break

            location_text = job.get("candidate_required_location", "")
            if self.location and not self._location_matches(location_text):
                continue

            desc_html = job.get("description") or ""
            desc = BeautifulSoup(desc_html, "html.parser").get_text(" ", strip=True)
            posted_at = self._parse_posted_at(job.get("publication_date"))
            remote = True  # Remotive only lists remote jobs

            opps.append(
                Opportunity(
                    source="indeed",  # keep the historic source label
                    company=job.get("company_name", "Unknown"),
                    title=job.get("title", ""),
                    location=location_text or self.location,
                    apply_url=job.get("url", ""),
                    description_snippet=desc[:800],
                    posted_at=posted_at,
                    remote_friendly=remote,
                    job_id=str(job.get("id")),
                    salary_min=None,
                    salary_max=None,
                    tags=["remotive"] + job.get("tags", []),
                    extra={
                        "job_type": job.get("job_type", ""),
                        "category": job.get("category", ""),
                    },
                )
            )

        return opps
