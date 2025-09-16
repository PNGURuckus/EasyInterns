# EasyInterns v2 - Canadian Internship Platform

**Status**: 🚨 **CRITICAL REBUILD IN PROGRESS** 🚨

A production-grade internship finder platform connecting Canadian students with opportunities from top companies, government programs, and university partnerships.

## ⚠️ Current State

**The existing codebase requires a complete rebuild.** See [TASKS.md](TASKS.md) for the comprehensive rebuild plan.

### Critical Issues Identified
- Backend+Frontend glue missing/confused
- package.json incorrectly wired to Python processes
- Insufficient dependencies in requirements.txt
- Config promises features not implemented
- No working scrapers, authentication, or real UI

## 🎯 Target Architecture (v2)

### Tech Stack (Locked)
- **Frontend**: Next.js 14 (TypeScript, App Router), Tailwind + shadcn/ui, TanStack Query, Zustand
- **Backend**: FastAPI (Pydantic v2), SQLModel, PostgreSQL, Redis queue, Playwright scrapers
- **Auth/Storage**: Supabase (Auth, Postgres, Storage)
- **Hosting**: Vercel (FE) + Fly.io (BE) + Supabase (DB/Auth) + Upstash Redis

### Repository Structure (Target)
```
/frontend/                 # Next.js 14 app (brand-new)
  src/app/                 # App Router pages
  src/components/          # React components
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
    ai.py
  /data/
    models.py
    schemas.py
    repositories.py
  /scrapers/
    indeed.py
    jobbank_ca.py
    talent.py
    ontario_ps.py
    bc_ps.py
  /resume/
    templates/             # 4 HTML templates
    builder.py
  requirements.txt         # Complete Python deps
```

## 🚀 Quick Start

Two modes are available:

- Demo (12 items):
  ```bash
  pip install -r requirements.txt
  python3 simple_api.py
  # Visit http://127.0.0.1:8001 (limited sample list)
  ```

- Full data (CSV/DB-backed):
  ```bash
  pip install -r requirements.txt
  uvicorn main:app --reload --port 8001
  # Visit http://127.0.0.1:8001
  # Admin: http://127.0.0.1:8001/admin (upload CSV or index to DB)
  ```

To expose more positions:
- Upload your spreadsheet in the Admin page (protected by Basic auth and token), or
- Place it at `exports/internships_latest.csv` with headers: `title,company,location,description,apply_url,source,external_id` and click “Re-index CSV”.

## 📋 Rebuild Progress

See [TASKS.md](TASKS.md) for the complete task checklist and progress tracking.

### Phase 1: Foundation (Days 1-2)
- [ ] Create proper Next.js frontend
- [ ] Fix requirements.txt with all dependencies
- [ ] Implement Supabase Auth + basic API

### Phase 2: Core Features (Days 3-7)
- [ ] Build working Canadian scrapers (Job Bank, Indeed, Talent.com)
- [ ] Implement search API with facets
- [ ] Create resume builder with AI features

### Phase 3: Production (Days 8-14)
- [ ] Complete all frontend pages
- [ ] Comprehensive testing suite
- [ ] Deploy to staging environment

## 🎯 Target Features (v2)

### For Students
- **Search**: 500+ Canadian internships updated daily
- **Filters**: Field, location, modality, salary, posting date
- **Resume Builder**: 4 professional templates with AI enhancement
- **Applications**: Save, track, and manage applications
- **Contact Discovery**: Verified hiring manager emails with confidence scores

### Data Sources (Canada-First)
- Job Bank Canada (official government portal)
- Indeed Canada
- Talent.com
- Ontario Public Service
- BC Public Service
- Google Jobs API
- University career boards
- LinkedIn* (feature-flagged)
- Glassdoor* (feature-flagged)

## 🔧 Configuration

All configuration is managed through structured JSON files:

- `config.example.json` - Complete configuration template
- `scrape_config.json` - Source registry with cooldowns and feature flags
- Environment variables for secrets (Supabase, OpenAI, etc.)

## 📊 Acceptance Criteria

Before v2 ships, these must pass:

- [ ] ≥500 Canadian internships indexed in last 24h
- [ ] Search filters update counts correctly
- [ ] 4 resume templates export clean PDFs
- [ ] AI generates relevant summaries and bullets
- [ ] All pages work: Home, Browse, Detail, Resume, Saved, Profile
- [ ] Lighthouse ≥85 desktop / ≥75 mobile
- [ ] ≥70% test coverage with Playwright E2E
- [ ] Sentry monitoring with proper tagging

## 🚨 Development Commands

```bash
# Backend development
uvicorn main:app --reload --port 8001

# Frontend development (when ready)
cd frontend && pnpm dev

# Setup Playwright
playwright install --with-deps

# Run tests (when implemented)
pytest backend/tests/
cd frontend && pnpm test
```

## 📈 Roadmap

### Immediate (v2.0)
- Complete rebuild per TASKS.md
- Canadian internship aggregation
- Resume builder with AI
- Production deployment

### Future (v2.1+)
- Application tracking system
- Email notifications
- Company profiles
- Analytics dashboard
- Mobile app

## 🤝 Contributing

**Current Focus**: Complete the v2 rebuild per [TASKS.md](TASKS.md)

1. Check TASKS.md for current priorities
2. Follow the locked tech stack
3. No deviations from the rebuild plan
4. All PRs must pass acceptance tests

## 📄 License

MIT License

---

**⚠️ Important**: The current demo at http://127.0.0.1:8001 is temporary. The real platform is being built according to the specifications in [TASKS.md](TASKS.md).
