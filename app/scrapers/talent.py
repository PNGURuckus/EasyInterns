import asyncio
import json
import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

from ..config import settings
from ..models import Opportunity


class TalentScraper:
    """Scrape internship listings from Talent.com.

    Talent.com exposes its search results via a Next.js front-end. The HTML
    contains escaped JSON payloads that describe both the search results and
    individual job postings. We decode those payloads to reconstruct the job
    metadata without executing client-side JavaScript.
    """

    SEARCH_URL = "https://ca.talent.com/jobs"
    DETAIL_URL = "https://ca.talent.com/view"
    JSON_MARKER = '"type":"application/ld+json","children":"'

    def __init__(self, query: str = "internship", location: str = "Canada", max_pages: int = 2):
        self.query = query
        self.location = location
        self.max_pages = max_pages

    def _decode_json_payload(self, payload: str) -> dict | None:
        try:
            text = bytes(payload, "utf-8").decode("unicode_escape")
            return json.loads(unescape(text))
        except Exception:
            return None

    def _iter_embedded_json(self, html: str):
        marker = self.JSON_MARKER
        start = 0
        # Extract JSON payloads embedded as escaped strings
        while True:
            idx = html.find(marker, start)
            if idx == -1:
                break
            pos = idx + len(marker)
            end = pos
            while end < len(html):
                if end > pos and html[end] == '"' and html[end - 1] != '\\':
                    break
                end += 1
            encoded = html[pos:end]
            data = self._decode_json_payload(encoded)
            if data:
                yield data
            start = end + 1

        # Extract inline JSON payloads from <script type="application/ld+json">
        for match in re.finditer(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
            data = self._decode_json_payload(match.group(1))
            if data:
                yield data

    def _extract_job_ids(self, html: str) -> list[str]:
        job_ids: list[str] = []
        for data in self._iter_embedded_json(html):
            if data.get("@type") != "ItemList":
                continue
            for element in data.get("itemListElement", []):
                url = (element.get("item") or {}).get("url")
                if not url:
                    continue
                parsed = urlparse(url)
                job_id = parse_qs(parsed.query).get("id")
                if job_id:
                    job_ids.append(job_id[0])
            if job_ids:
                break
        return job_ids

    def _parse_job_posting(self, html: str) -> dict | None:
        for data in self._iter_embedded_json(html):
            if data.get("@type") == "JobPosting":
                return data
        return None

    async def _fetch_job(self, client: httpx.AsyncClient, job_id: str) -> Opportunity | None:
        try:
            resp = await client.get(
                self.DETAIL_URL,
                params={"id": job_id},
                headers={"User-Agent": settings.user_agent},
                timeout=settings.http_timeout_seconds,
            )
            if resp.status_code != 200:
                return None
        except Exception:
            return None

        payload = self._parse_job_posting(resp.text)
        if not payload:
            return None

        org = payload.get("hiringOrganization", {})
        address = (payload.get("jobLocation") or {}).get("address", {})
        location_parts = [
            address.get("addressLocality"),
            address.get("addressRegion"),
            address.get("addressCountry"),
        ]
        location = ", ".join([part for part in location_parts if part]) or None

        desc_html = payload.get("description") or ""
        desc = BeautifulSoup(desc_html, "html.parser").get_text(" ", strip=True)

        posted_at = None
        if payload.get("datePosted"):
            try:
                posted_at = datetime.fromisoformat(payload["datePosted"]).replace(tzinfo=timezone.utc)
            except Exception:
                posted_at = None

        employment_type = payload.get("employmentType", "")
        tags = ["talent"]
        if employment_type:
            tags.append(employment_type.lower())

        return Opportunity(
            source="talent",
            company=org.get("name", "Unknown"),
            title=payload.get("title", ""),
            location=location,
            apply_url=payload.get("url") or f"{self.DETAIL_URL}?id={job_id}",
            description_snippet=desc[:800],
            posted_at=posted_at,
            remote_friendly="remote" in (location or "").lower() or "remote" in desc.lower(),
            job_id=job_id,
            tags=tags,
            extra={
                "employmentType": employment_type,
                "industry": payload.get("industry", ""),
            },
        )

    async def fetch(self) -> list[Opportunity]:
        results: list[Opportunity] = []
        async with httpx.AsyncClient() as client:
            for page in range(self.max_pages):
                params = {"k": self.query, "l": self.location, "p": page + 1}
                try:
                    resp = await client.get(
                        self.SEARCH_URL,
                        params=params,
                        headers={"User-Agent": settings.user_agent},
                        timeout=settings.http_timeout_seconds,
                    )
                    if resp.status_code != 200:
                        continue
                except Exception:
                    continue

                job_ids = self._extract_job_ids(resp.text)
                if not job_ids:
                    continue

                detail_tasks = [self._fetch_job(client, job_id) for job_id in job_ids]
                detail_results = await asyncio.gather(*detail_tasks, return_exceptions=True)
                for job in detail_results:
                    if isinstance(job, Opportunity):
                        results.append(job)
        return results
