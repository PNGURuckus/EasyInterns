import httpx
import re
from datetime import datetime, timezone

import feedparser

from ..config import settings
from ..models import Opportunity

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

class RSSScraper:
    """
    Generic RSS scraper for job boards.
    Extracts titles, links, descriptions, dates, and emails.
    """
    def __init__(self, feeds: dict):
        # feeds = { "name": "url", ... }
        self.feeds = feeds or {}

    async def fetch_feed(self, client, name, url):
        try:
            r = await client.get(
                url,
                headers={"User-Agent": settings.user_agent, "Accept": "application/rss+xml"},
                timeout=settings.http_timeout_seconds,
            )
            if r.status_code != 200:
                return []
            parsed = feedparser.parse(r.content)
        except Exception:
            return []

        opps = []
        for entry in parsed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            desc = entry.get("summary", "")[:800]
            posted_at = None
            if getattr(entry, "published_parsed", None):
                posted_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif getattr(entry, "updated_parsed", None):
                posted_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            emails = EMAIL_RE.findall(desc)
            tags = [name]  # tag it with the feed name
            
            opps.append(
                Opportunity(
                    source="rss",
                    company=name,
                    title=title,
                    location=None,
                    apply_url=link,
                    description_snippet=desc,
                    posted_at=posted_at,
                    remote_friendly="remote" in title.lower() or "remote" in desc.lower(),
                    job_id=link,
                    tags=tags,
                )
            )
        return opps

    async def fetch(self):
        if not self.feeds:
            return []
        opps = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for name, url in self.feeds.items():
                part = await self.fetch_feed(client, name, url)
                opps.extend(part)
        return opps
