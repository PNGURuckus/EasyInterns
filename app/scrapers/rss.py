import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

import feedparser
import httpx

from .base import BaseScraper, ScrapeQuery, RawPosting
from ..config import settings

# Regular expression for email extraction
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

class RSSScraper(BaseScraper):
    """
    Generic RSS scraper for job boards.
    Extracts titles, links, descriptions, dates, and emails.
    """
    
    name = "rss"
    description = "RSS feed scraper for job postings"
    requires_feature_flag = False
    
    # Default feeds to scrape (can be overridden in constructor or scrape method)
    feeds: Dict[str, str] = {
        # Example: "Remote OK": "https://remoteok.com/remote-jobs.rss",
        # Add more default feeds as needed
    }
    
    def __init__(self, feeds: Optional[Dict[str, str]] = None):
        if feeds:
            self.feeds = feeds
    
    async def _fetch_feed(self, client: httpx.AsyncClient, name: str, url: str) -> List[RawPosting]:
        """Fetch and parse a single RSS feed"""
        try:
            response = await client.get(
                url,
                headers={"User-Agent": settings.USER_AGENT},
                timeout=15
            )
            
            if response.status_code != 200:
                return []
                
            parsed = feedparser.parse(response.text)
            if not hasattr(parsed, 'entries') or not parsed.entries:
                return []
                
            postings = []
            
            for entry in parsed.entries:
                try:
                    title = entry.get("title", "")
                    if not self._is_internship(title):
                        continue
                        
                    link = entry.get("link", "")
                    description = (entry.get("summary") or entry.get("description") or "")[:1000]
                    
                    # Parse published date
                    if "published_parsed" in entry and entry.published_parsed:
                        posted_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif "updated_parsed" in entry and entry.updated_parsed:
                        posted_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    else:
                        posted_date = datetime.now(timezone.utc)
                    
                    # Extract location if available
                    location = None
                    if hasattr(entry, 'where'):
                        location = entry.where
                    
                    # Check if position is remote
                    is_remote = any([
                        "remote" in title.lower(),
                        location and "remote" in location.lower(),
                        "remote" in description.lower()
                    ])
                    
                    # Extract emails from description
                    emails = EMAIL_RE.findall(description)
                    
                    # Create posting
                    posting = RawPosting(
                        title=title,
                        company=name,
                        location=location,
                        description=description,
                        apply_url=link,
                        external_id=link,  # Use link as ID if no better ID is available
                        posted_date=posted_date,
                        is_remote=is_remote,
                        source_metadata={
                            "scraper": "rss",
                            "source_name": name,
                            "source_url": url,
                            "emails": emails[:3]  # Include first 3 emails if found
                        }
                    )
                    postings.append(posting)
                    
                except Exception as e:
                    print(f"Error processing RSS entry: {e}")
                    continue
                    
            return postings
            
        except Exception as e:
            print(f"Error fetching RSS feed {name} ({url}): {e}")
            return []
    
    async def scrape(self, query: ScrapeQuery = None) -> List[RawPosting]:
        """Scrape configured RSS feeds for job postings"""
        query = query or ScrapeQuery()
        all_postings = []
        
        # Use feeds from query if provided, otherwise use instance feeds
        feeds = query.source_metadata.get("feeds") if query and query.source_metadata else self.feeds
        
        if not feeds:
            return []
            
        async with httpx.AsyncClient() as client:
            tasks = [self._fetch_feed(client, name, url) for name, url in feeds.items()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                all_postings.extend(result)
        
        # Apply query filters
        if query.keywords:
            keyword_filter = '|'.join(re.escape(kw.lower()) for kw in query.keywords)
            all_postings = [
                p for p in all_postings 
                if re.search(keyword_filter, f"{p.title} {p.description}".lower())
            ]
                
        return all_postings[:query.max_results] if query and query.max_results else all_postings
    
    def _is_internship(self, title: str) -> bool:
        """Check if job title indicates an internship position"""
        if not title:
            return False
            
        title_lower = title.lower()
        return any(term in title_lower for term in ["intern", "co-op", "coop", "student"])
