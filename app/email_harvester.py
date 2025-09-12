import asyncio, csv
from pathlib import Path
from typing import List, Dict
import httpx

from .models import Opportunity, CandidateProfile
from .pipeline import get_ranked
from .utils import find_emails_on_page, domain_from_url, guess_career_emails_from_domain
from .db import upsert_contacts

async def _harvest_one(client: httpx.AsyncClient, opp: Opportunity) -> Dict:
    emails = await find_emails_on_page(client, opp.apply_url)
    if not emails:
        domain = domain_from_url(opp.apply_url)
        emails = guess_career_emails_from_domain(domain)
    emails = sorted(set(emails))
    return {
        "company": opp.company,
        "title": opp.title,
        "location": opp.location or "",
        "apply_url": opp.apply_url,
        "source": opp.source,
        "emails": emails,
        "emails_csv": ",".join(emails)
    }

async def harvest_emails_for_opportunities(opps: List[Opportunity]) -> List[Dict]:
    results: List[Dict] = []
    async with httpx.AsyncClient() as client:
        for o in opps:
            try:
                results.append(await _harvest_one(client, o))
            except Exception:
                results.append({
                    "company": o.company, "title": o.title, "location": o.location or "",
                    "apply_url": o.apply_url, "source": o.source, "emails": [], "emails_csv": ""
                })
    return results

def export_emails_csv(rows: List[Dict], out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = ["company","title","location","apply_url","source","emails"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([r["company"], r["title"], r["location"], r["apply_url"], r["source"], r["emails_csv"]])

def build_email_list(profile: CandidateProfile, limit: int = 50, csv_path: Path = Path("exports/emails.csv")) -> Dict:
    triples = get_ranked(profile, limit=limit)
    opps = [t[0] for t in triples[:limit]]
    rows = asyncio.run(harvest_emails_for_opportunities(opps))
    export_emails_csv(rows, csv_path)
    upsert_contacts(rows)
    return {"count": len(rows), "path": str(csv_path), "rows": rows[:25]}  # preview first 25
