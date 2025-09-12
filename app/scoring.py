from datetime import datetime, timezone
from .models import Opportunity, CandidateProfile

INTERN_HINTS = [
    "intern", "internship", "co-op", "co op", "coop",
    "summer", "campus", "university", "new grad", "apprentice"
]

def _kw_score(text, keywords, weight):
    if not text or not keywords:
        return 0.0
    t = text.lower()
    return sum(weight for k in keywords if k.lower() in t)

def _contains_any(text, words):
    text = (text or "").lower()
    return any(w in text for w in words)

def score_opportunity(profile: CandidateProfile, opp: Opportunity):
    components = {}
    score = 0.0

    # 1) Strong boost if it looks like an internship
    blob_title = (opp.title or "")
    blob_all = " ".join(filter(None, [opp.title, opp.description_snippet or "", " ".join(opp.tags or [])]))
    if _contains_any(blob_title, INTERN_HINTS) or _contains_any(blob_all, INTERN_HINTS):
        score += 8.0
        components["intern_signal"] = 8.0

    # 2) Recency (updated recently)
    if opp.posted_at:
        days = max(0, (datetime.now(timezone.utc) - opp.posted_at.replace(tzinfo=timezone.utc)).days)
        rec = max(0.0, 4.0 - 0.12 * days)  # up to 4 pts, decays ~0.12/day
        score += rec
        components["recency"] = rec

    # 3) Remote / location
    if profile.remote_ok and opp.remote_friendly:
        score += 2.0
        components["remote_match"] = 2.0
    if profile.location_preference and opp.location and profile.location_preference.lower() in opp.location.lower():
        score += 2.0
        components["location_match"] = 2.0

    # 4) Textual match on must-have / skills / interests
    mh = _kw_score(blob_all, profile.must_have_keywords, 1.2)
    sk = _kw_score(blob_all, profile.skills, 0.7)
    it = _kw_score(blob_all, profile.interests, 0.5)
    score += mh + sk + it
    if mh: components["must_have"] = mh
    if sk: components["skills"] = sk
    if it: components["interests"] = it

    return score, components
