# EasyInterns v2 Rebuild - Task Checklist

**Status**: 🚨 **CRITICAL REBUILD REQUIRED** 🚨

## Critical Issues Identified
- [ ] Backend+Frontend glue missing/confused
- [ ] package.json wired to Python processes with Python deps listed as npm deps  
- [ ] Insufficient Python dependencies in requirements.txt
- [ ] Config promises features not implemented
- [ ] No real scrapers, UI, or working architecture

## Phase 1: Foundation (Days 1-2)
- [ ] **Create /frontend Next.js app; remove misleading npm Python deps**
- [ ] **Fix requirements.txt with all necessary dependencies**
- [ ] **Restructure repo with proper /frontend and /backend separation**
- [ ] **Implement Supabase Auth + /api/internships (mocked) + Next.js shell**
- [ ] **Create Home/Browse scaffolds**

## Phase 2: Core Data & Scrapers (Days 3-5)  
- [ ] **Implement backend data models + indices; wire scoring.py to config weights**
- [ ] **Build search_internships with facets; paginate; return Pydantic DTOs**
- [ ] **Implement scrapers (Job Bank, Indeed, Talent.com, OPS, BCPS, Google Jobs, University boards)**
- [ ] **Feature-flag LinkedIn/Glassdoor scrapers**
- [ ] **Scrapers (Job Bank CA, Indeed, Talent.com) → DB → API → FE list**

## Phase 3: API Implementation (Days 5-7)
- [ ] **Implement /api/internships, /api/internships/{id}, /api/user, /api/resumes**
- [ ] **Implement /api/resumes/{id}/export, /api/scrape/***
- [ ] **Implement email extraction/validation w/ confidence scoring**
- [ ] **Build safe display defaults for contact emails**

## Phase 4: Resume Builder (Days 7-10)
- [ ] **Build 4 resume templates + AI features; export to Supabase Storage**
- [ ] **Resume builder MVP (1 template) + AI summary bullets + PDF export**
- [ ] **All 4 resume templates; Saved + Applications tabs**
- [ ] **Verified email pipeline with confidence badges**

## Phase 5: Frontend Pages (Days 8-12)
- [ ] **Next.js pages (Home, Browse, Detail, Resume, Saved, Applications, Profile)**
- [ ] **Implement Clearbit logos with fallbacks**
- [ ] **Add search functionality with filters and facets**
- [ ] **Implement infinite scroll and pagination**

## Phase 6: QA & Deploy (Days 10-14)
- [ ] **CI: unit/integration tests + Playwright E2E; coverage threshold 70%**
- [ ] **QA: unit, integration, Playwright E2E**
- [ ] **Deploy staging (Vercel FE, Fly.io BE, Supabase DB/Auth/Storage, Upstash Redis)**

## Acceptance Tests (Must Pass Before Ship)
- [ ] **Browse: ≥500 Canadian internships indexed in last 24h**
- [ ] **Filters (field, province, modality) update counts correctly**
- [ ] **Details: Apply URL valid; email shown with confidence badge**
- [ ] **50-sample audit yields 0 mismatches**
- [ ] **Resume: 4 templates export clean PDFs**
- [ ] **AI generates summary/bullets; tailoring injects keywords**
- [ ] **Every tab works: Home, Browse, Saved, Applications, Resume, Profile**
- [ ] **Perf: Lighthouse ≥85 desktop / ≥75 mobile**
- [ ] **No uncaught console errors**
- [ ] **Sentry logs tagged by source and job_id**
- [ ] **Tests: ≥70% coverage core modules; Playwright E2E green**

## File Structure (Target)
```
/frontend/                 # Next.js 14 app (brand-new)
  src/
    app/                   # App Router pages
    components/            # React components  
    lib/                   # Utilities
  package.json             # Next.js deps only
  
/backend/
  main.py
  /api/                    # FastAPI routers
    internships.py
    resumes.py
    users.py
    scrape.py
  /core/
    config.py
    security.py
    email_utils.py
    ai.py
  /data/
    models.py
    schemas.py
    db.py
    repositories.py
  /scrapers/
    base.py
    registry.py
    indeed.py
    talent.py
    jobbank_ca.py
    ontario_ps.py
    bc_ps.py
    google_jobs.py
    university_boards.py
    linkedin.py            # feature-flagged OFF
    glassdoor.py           # feature-flagged OFF
  /workers/
    queue.py
    tasks.py
  /ranking/
    scoring.py
  /resume/
    templates/
      ats_clean.html
      modern_two_col.html
      creative_accent.html
      compact_student.html
    builder.py
  /tests/
    unit/
    integration/
    e2e/
  requirements.txt         # Complete Python deps
```

## Tech Stack (Locked)
- **Frontend**: Next.js 14 (TS, App Router), Tailwind + shadcn/ui, TanStack Query, react-hook-form + zod, Zustand, Framer Motion
- **Backend**: FastAPI (Pydantic v2), SQLAlchemy/SQLModel, Postgres, Redis queue (RQ or Celery), Sentry, OpenTelemetry
- **Scrapers**: Playwright (stealth, headless Chromium), RSS/official APIs, Canada-first sources
- **Auth/Storage/DB**: Supabase (Auth, Postgres, Storage)
- **PDF**: Headless Chromium print to PDF
- **Logos**: Clearbit Logo → fallback (favicon → initials)
- **Hosting**: FE on Vercel; BE on Fly.io; DB/Auth/Storage on Supabase; Queue on Upstash Redis

## Single-Command Dev Scripts
```bash
# Backend dev
uvicorn backend.main:app --reload --port 8001

# Frontend dev  
cd frontend && pnpm dev

# Playwright setup
playwright install --with-deps
```

## Risk Mitigation
- **Source ToS**: Keep LinkedIn/Glassdoor OFF by default and behind flags
- **Email quality**: Display only confidence >= 0.5 by default
- **Chromium in CI**: Use Playwright's bundled Chromium for headless PDF
- **Auth drift**: Validate Supabase JWT on every write API; implement RLS

---

**⚠️ CRITICAL**: No reinterpretation allowed. This plan wins. Current state is not acceptable.
