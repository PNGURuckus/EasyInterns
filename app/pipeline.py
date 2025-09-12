import asyncio, csv
from pathlib import Path
from .models import CandidateProfile, Opportunity
from .scoring import score_opportunity
from .db import init_db, upsert_opportunities, fetch_all
from .scrapers.lever import LeverScraper
from .scrapers.greenhouse import GreenhouseScraper
from .scrapers.rss import RSSScraper
from .scrapers.indeed import IndeedScraper
from .scrapers.talent import TalentScraper


def build_scrapers(config):
    scrapers = []
    if config.get("lever_companies"):
        scrapers.append(LeverScraper(config["lever_companies"]))
    if config.get("greenhouse_companies"):
        scrapers.append(GreenhouseScraper(config["greenhouse_companies"]))
    if config.get("rss_feeds"):
        scrapers.append(RSSScraper(config["rss_feeds"]))
    if config.get("indeed", False):
        scrapers.append(IndeedScraper())
    if config.get("talent", False):
        scrapers.append(TalentScraper())
    return scrapers


async def run_scrapers(scrapers):
    results = []
    for s in scrapers:
        part = await s.fetch()
        results.extend(part)
    # de-dupe by unique key
    seen, uniq = set(), []
    for o in results:
        k = o.key()
        if k not in seen:
            uniq.append(o)
            seen.add(k)
    return uniq


def rank_opportunities(profile, opportunities):
    triples = []
    for o in opportunities:
        score, comps = score_opportunity(profile, o)
        triples.append((o, score, comps))
    return sorted(triples, key=lambda x: x[1], reverse=True)


def export_to_csv(triples, out_path: Path, top_k=100):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "score", "company", "title", "location", "apply_url"])
        for i, (o, s, _) in enumerate(triples[:top_k], 1):
            w.writerow([i, round(s, 2), o.company, o.title, o.location or "", o.apply_url])


async def scrape_and_store(config):
    init_db()
    scrapers = build_scrapers(config)
    opps = await run_scrapers(scrapers)
    inserted = upsert_opportunities(opps)
    print(
        f"[scrape] companies(L={len(config.get('lever_companies', []))}, "
        f"GH={len(config.get('greenhouse_companies', []))}, "
        f"RSS={len(config.get('rss_feeds', {}))}, "
        f"Indeed={config.get('indeed', False)}, "
        f"Talent={config.get('talent', False)}) "
        f"fetched={len(opps)} inserted={inserted}"
    )
    return {"fetched": len(opps), "inserted": inserted}


def get_ranked(profile: CandidateProfile, limit=200):
    rows = fetch_all(limit=limit * 2)  # pull more than we rank
    opps = [
        Opportunity(
            source=r.source,
            company=r.company,
            title=r.title,
            location=r.location,
            apply_url=r.apply_url,
            description_snippet=r.description_snippet,
            posted_at=r.posted_at,
            remote_friendly=r.remote_friendly,
            job_id=r.job_id,
            salary_min=r.salary_min,
            salary_max=r.salary_max,
            tags=r.tags.split(",") if r.tags else [],
        )
        for r in rows
    ]
    return rank_opportunities(profile, opps)[:limit]

