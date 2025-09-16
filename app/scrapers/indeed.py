import asyncio
import logging
from datetime import datetime, timezone

import cloudscraper
from bs4 import BeautifulSoup
from cloudscraper.exceptions import CloudflareChallengeError

from ..models import Opportunity
from ..config import settings

logger = logging.getLogger(__name__)

class IndeedScraper:
    """
    Scrapes Indeed.ca for internships in Canada.
    NOTE: Uses HTML parsing since Indeed has no free API.
    """
    def __init__(self, query="internship", location="Canada", max_pages=2):
        self.query = query
        self.location = location
        self.max_pages = max_pages
        self.base_url = "https://ca.indeed.com/jobs"
        self._proxy_url = settings.indeed_proxy_url
        self._scraper = self._build_scraper()

    def _build_scraper(self):
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False},
        )
        scraper.headers.update(
            {
                "User-Agent": settings.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Referer": "https://ca.indeed.com/",
            }
        )
        if self._proxy_url:
            scraper.proxies = {"http": self._proxy_url, "https": self._proxy_url}
        return scraper

    async def fetch_page(self, start):
        params = {"q": self.query, "l": self.location, "start": start}
        try:
            response = await asyncio.to_thread(
                self._scraper.get,
                self.base_url,
                params=params,
                timeout=settings.http_timeout_seconds,
            )
        except CloudflareChallengeError as exc:
            logger.warning("Indeed request blocked by Cloudflare challenge: %s", exc)
            return []
        except Exception as exc:
            logger.exception("Indeed request failed: %s", exc)
            return []

        if response.status_code != 200:
            logger.warning("Indeed request returned status %s", response.status_code)
            return []

        if self._is_blocked_html(response.text):
            logger.warning("Indeed responded with a block page; configure a proxy/anti-bot service for access")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        jobs = []
        for card in soup.select("div.job_seen_beacon"):
            title_el = card.select_one("h2 a")
            if not title_el: continue
            title = title_el.get("aria-label") or title_el.text.strip()
            link = "https://ca.indeed.com" + title_el.get("href", "")
            company = card.select_one("span.companyName")
            company = company.text.strip() if company else "Unknown"
            loc = card.select_one("div.companyLocation")
            loc = loc.text.strip() if loc else None
            snippet = card.select_one("div.job-snippet")
            desc = snippet.text.strip() if snippet else ""
            posted_at = datetime.now(timezone.utc)  # indeed hides exact date

            jobs.append(
                Opportunity(
                    source="indeed",
                    company=company,
                    title=title,
                    location=loc,
                    apply_url=link,
                    description_snippet=desc,
                    posted_at=posted_at,
                    remote_friendly="remote" in (loc or "").lower() or "remote" in desc.lower(),
                    job_id=link,
                    tags=["indeed"],
                )
            )
        return jobs

    async def fetch(self):
        opps = []
        for p in range(self.max_pages):
            opps.extend(await self.fetch_page(p * 10))
        return opps

    def _is_blocked_html(self, html: str) -> bool:
        block_tokens = [
            "Blocked - Indeed.com",
            "Our systems have detected unusual traffic",
            "cf-mitigated",
        ]
        return any(token in html for token in block_tokens)
