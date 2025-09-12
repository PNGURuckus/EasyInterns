import re
from typing import List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import httpx

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def domain_from_url(url: str) -> Optional[str]:
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return None
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None

def guess_career_emails_from_domain(domain: Optional[str]) -> List[str]:
    if not domain:
        return []
    prefixes = ["careers", "hr", "recruiting", "talent", "jobs", "people", "university", "campus", "internships"]
    return [f"{p}@{domain}" for p in prefixes]

async def find_emails_on_page(client: httpx.AsyncClient, url: str) -> List[str]:
    try:
        r = await client.get(url, timeout=25)
        r.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    emails = set()

    for a in soup.select("a[href^=mailto]"):
        href = a.get("href", "")
        for e in EMAIL_REGEX.findall(href):
            emails.add(e.lower())

    text = soup.get_text(" ", strip=True)
    for e in EMAIL_REGEX.findall(text):
        emails.add(e.lower())

    return sorted(emails)
