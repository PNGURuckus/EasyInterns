from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
from pathlib import Path

from .config import settings
from .models import CandidateProfile
from .pipeline import scrape_and_store, get_ranked, export_to_csv
from .email_harvester import build_email_list
from .db import fetch_all

DEFAULT_LEVER = [
    "stripe","databricks","square","robinhood","affirm","brex",
    "ramp","notion","airtable","discord","doordash"
]
DEFAULT_GREENHOUSE = [
    "shopify","doordash","snowflake","roblox","instacart",
    "palantir","datadog","cloudflare","neo4j","snap"
]

class ProfileIn(BaseModel):
    name: str
    email: Optional[str] = None
    education_level: Optional[str] = None
    location_preference: Optional[str] = None
    remote_ok: bool = True
    visa_requirement: Optional[str] = None
    interests: List[str] = []
    skills: List[str] = []
    must_have_keywords: List[str] = []
    nice_to_have_keywords: List[str] = []

class QuickstartIn(BaseModel):
    use_defaults: bool = True
    fast: bool = True               # NEW: fast limits the curated list to speed up first-run
    extra_lever: List[str] = []
    extra_greenhouse: List[str] = []
    rss_feeds: Dict[str, str] = {}

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# serve simple frontend
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")

EXPORTS_DIR = Path("exports"); EXPORTS_DIR.mkdir(exist_ok=True)

@app.get("/ping")
def ping(): return {"ok": True}

@app.get("/")
def root(): return {"message": "EasyIntern API running. See /docs."}

@app.post("/scrape_quickstart")
async def scrape_quickstart(cfg: QuickstartIn):
    lever = DEFAULT_LEVER[:] if cfg.use_defaults else []
    gh = DEFAULT_GREENHOUSE[:] if cfg.use_defaults else []
    if cfg.fast:
        lever = lever[:4]   # keep it snappy on first run
        gh = gh[:4]
    lever += [c.strip().lower() for c in cfg.extra_lever]
    gh += [c.strip().lower() for c in cfg.extra_greenhouse]

    # de-dup while keeping order
    def dedupe(seq):
        seen=set(); out=[]
        for s in seq:
            if s and s not in seen:
                out.append(s); seen.add(s)
        return out

    lever, gh = dedupe(lever), dedupe(gh)
    summary = await scrape_and_store({"lever_companies": lever, "greenhouse_companies": gh, "rss_feeds": cfg.rss_feeds or {}})
    return {"lever_used": lever, "greenhouse_used": gh, **summary}

@app.post("/rank")
def rank(profile: ProfileIn, limit: int = Query(200, ge=1, le=2000), min_score: float = Query(0.0), remote_only: bool = Query(False)):
    p = CandidateProfile(**profile.dict())
    triples = get_ranked(p, limit=limit)
    results = []
    for i, (o, s, comps) in enumerate(triples, start=1):
        if remote_only and not (o.remote_friendly or (o.location or "").lower().startswith("remote")):
            continue
        if s < min_score: continue
        results.append({
            "rank": i, "score": round(s, 2), "components": comps,
            "opportunity": {
                "source": o.source, "company": o.company, "title": o.title,
                "location": o.location, "apply_url": o.apply_url,
                "posted_at": o.posted_at.isoformat() if o.posted_at else None,
                "remote_friendly": o.remote_friendly, "job_id": o.job_id, "tags": o.tags,
            }
        })
    return {"results": results}

@app.post("/export_csv")
def export_csv(profile: ProfileIn, top_k: int = Query(100, ge=1, le=1000)):
    p = CandidateProfile(**profile.dict())
    triples = get_ranked(p, limit=top_k*3)
    out_path = EXPORTS_DIR / "easyintern_results.csv"
    export_to_csv(triples, out_path, top_k=top_k)
    return {"path": str(out_path)}

@app.get("/download/results")
def download_results():
    path = EXPORTS_DIR / "easyintern_results.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No results export found.")
    return FileResponse(str(path), media_type="text/csv", filename="results.csv")

@app.post("/harvest_emails")
def harvest_emails(profile: ProfileIn, limit: int = Query(50, ge=1, le=500)):
    p = CandidateProfile(**profile.dict())
    info = build_email_list(p, limit=limit, csv_path=EXPORTS_DIR / "emails.csv")
    return info

@app.get("/download/emails")
def download_emails():
    path = EXPORTS_DIR / "emails.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No emails export found.")
    return FileResponse(str(path), media_type="text/csv", filename="emails.csv")

@app.get("/stats")
def stats():
    total = len(fetch_all(limit=10000))
    return {"opportunities_in_db": total}
