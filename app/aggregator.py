import os
import csv
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

from app.scrapers.registry import get_scraper_registry
from app.scrapers.base import ScrapeQuery
import re


def _ensure_exports_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _normalize(posting) -> Dict:
    return {
        "title": getattr(posting, "title", None),
        "company": getattr(posting, "company_name", None) or getattr(posting, "company", None),
        "location": getattr(posting, "location", None),
        "description": getattr(posting, "description", None),
        "apply_url": getattr(posting, "apply_url", None),
        "source": getattr(posting, "source", None),
        "external_id": getattr(posting, "external_id", None),
        "posted_date": getattr(posting, "posted_date", None).isoformat() if getattr(posting, "posted_date", None) else None,
        "application_deadline": _deadline_iso(getattr(posting, "application_deadline", None), getattr(posting, "description", None)),
        "salary_min": getattr(posting, "salary_min", None),
        "salary_max": getattr(posting, "salary_max", None),
    }


def _deadline_iso(dt: Optional[object], description: Optional[str]) -> Optional[str]:
    """Return ISO date string for deadline if present or parsed from description."""
    if dt is not None:
        try:
            return dt.date().isoformat() if hasattr(dt, 'date') else dt.isoformat()
        except Exception:
            pass
    text = (description or '').strip()
    if not text:
        return None
    m = re.search(r"(20\d{2})-(\d{1,2})-(\d{1,2})", text)
    if m:
        y, mo, d = map(int, m.groups())
        try:
            from datetime import date
            return date(y, mo, d).isoformat()
        except Exception:
            pass
    m = re.search(r"(?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:,\s*(\d{4}))?", text)
    if m:
        mon, day, year = m.groups()
        months = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'sept':9,'oct':10,'nov':11,'dec':12}
        mo = months.get(mon.lower(), 0)
        try:
            from datetime import date, datetime as _dt
            y = int(year) if year else _dt.utcnow().year
            return date(y, mo, int(day)).isoformat()
        except Exception:
            return None
    return None


async def run_ingest(query: str = "intern", location: str = "Canada", max_results: int = 1000, export_path: str = "exports/internships_latest.csv") -> Dict:
    registry = get_scraper_registry()
    sq = ScrapeQuery(query=query, location=location, max_results=max_results)
    postings = await registry.scrape_all_sources(sq)

    # Deduplicate by apply_url primarily
    seen = set()
    items: List[Dict] = []
    for p in postings:
        norm = _normalize(p)
        if not norm.get("title") or not norm.get("apply_url"):
            continue
        key = (norm.get("apply_url") or "").strip().lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(norm)

    # Sort by source then title for stable exports
    items.sort(key=lambda x: (x.get("source") or "", x.get("title") or ""))

    # Export CSV
    _ensure_exports_dir(export_path)
    tmp_path = export_path + ".tmp"
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "company",
                "location",
                "description",
                "apply_url",
                "source",
                "external_id",
                "posted_date",
                "application_deadline",
                "salary_min",
                "salary_max",
            ],
        )
        writer.writeheader()
        writer.writerows(items)
    os.replace(tmp_path, export_path)

    # Timestamped snapshot
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    snapshot = f"exports/internships_{stamp}.csv"
    try:
        import shutil
        shutil.copy(export_path, snapshot)
    except Exception:
        pass

    return {"count": len(items), "export": export_path, "snapshot": snapshot}
