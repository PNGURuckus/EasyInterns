# EasyInterns Deployment Guide

This guide covers deploying the EasyInterns platform to production using Vercel (frontend), Fly.io (backend), and Supabase (database/auth).

## Prerequisites

- [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) installed
- [Vercel CLI](https://vercel.com/cli) installed (optional)
- [Supabase CLI](https://supabase.com/docs/guides/cli) installed (optional)
- Docker installed for local testing

## 1. Supabase Setup

### Create Supabase Project

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Create a new project
3. Note down your project URL and anon key
4. Go to Authentication > Settings and configure:
   - Enable email auth
   - Set site URL to your frontend domain
   - Add redirect URLs for auth callbacks

### Database Schema

Run the following SQL in the Supabase SQL editor:

```sql
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    location TEXT,
    school TEXT,
    degree TEXT,
    graduation_year INTEGER,
    gpa DECIMAL(3,2),
    skills TEXT[],
    interests TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);
```

## 2. Backend Deployment (Fly.io)

### Initial Setup

```bash
# Navigate to project root
cd /path/to/EasyInterns-1

# Login to Fly.io
flyctl auth login

# Create Fly.io app (if not already created)
flyctl apps create easyinterns-api --org personal

# Set secrets
flyctl secrets set \
  SUPABASE_URL="https://your-project.supabase.co" \
  SUPABASE_SERVICE_KEY="your-service-role-key" \
  SUPABASE_JWT_SECRET="your-jwt-secret" \
  OPENAI_API_KEY="your-openai-key" \
  CLEARBIT_API_KEY="your-clearbit-key" \
  REDIS_URL="redis://localhost:6379" \
  DATABASE_URL="postgresql://..." \
  SECRET_KEY="your-secret-key"
```

### Deploy

```bash
# Deploy to Fly.io
flyctl deploy

# Check deployment status
flyctl status

# View logs
flyctl logs
```

### Scale and Monitor

```bash
# Scale app
flyctl scale count 2

# Monitor metrics
flyctl dashboard

# SSH into machine for debugging
flyctl ssh console
```

## 3. Frontend Deployment (Vercel)

### Setup Environment Variables

In Vercel dashboard or CLI, set:

```bash
# Using Vercel CLI
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY  
vercel env add NEXT_PUBLIC_API_URL

# Or in Vercel dashboard:
# NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
# NEXT_PUBLIC_API_URL=https://easyinterns-api.fly.dev
```

### Deploy

```bash
# Navigate to frontend directory
cd frontend-next

# Install dependencies (if not done)
npm install

# Deploy to Vercel
vercel --prod

# Or connect GitHub repo in Vercel dashboard for auto-deploy
```

## 4. Domain Configuration

### Custom Domain (Optional)

1. **Backend**: Add custom domain in Fly.io dashboard
2. **Frontend**: Add custom domain in Vercel dashboard
3. **Update Environment Variables**: Update API_URL to use custom domain

### SSL Certificates

Both Fly.io and Vercel provide automatic SSL certificates.

## 5. Environment Variables Reference

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://localhost:6379

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# AI Services
OPENAI_API_KEY=sk-...
CLEARBIT_API_KEY=sk-...

# App Configuration
SECRET_KEY=your-secret-key
ENVIRONMENT=production
DEBUG=false

# Feature Flags
ENABLE_LINKEDIN_SCRAPER=false
ENABLE_GLASSDOOR_SCRAPER=false
ENABLE_AI_FEATURES=true
ENABLE_EMAIL_EXTRACTION=true
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=https://easyinterns-api.fly.dev
```

## 6. Monitoring and Maintenance

### Health Checks

- Backend: `https://easyinterns-api.fly.dev/health`
- Frontend: Built-in Vercel monitoring

### Logging

```bash
# Backend logs
flyctl logs -a easyinterns-api

# Error tracking (recommended)
# Set up Sentry for both frontend and backend
```

### Database Backups

Supabase provides automatic backups. For additional safety:

```bash
# Manual backup
supabase db dump --db-url "postgresql://..." > backup.sql

# Restore
psql "postgresql://..." < backup.sql
```

### Scaling

```bash
# Scale backend
flyctl scale count 3 -a easyinterns-api

# Frontend scales automatically on Vercel
```

## 7. CI/CD Pipeline

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
```

## 8. Post-Deployment Checklist

- [ ] Backend health check passes
- [ ] Frontend loads correctly
- [ ] Authentication flow works
- [ ] Database connections established
- [ ] Scraping jobs can be created
- [ ] Resume generation works
- [ ] Email extraction functions
- [ ] Search and filtering work
- [ ] All API endpoints respond correctly

## 9. Troubleshooting

### Common Issues

1. **CORS Errors**: Update CORS settings in backend config
2. **Auth Issues**: Verify Supabase JWT secret and URLs
3. **Database Connection**: Check DATABASE_URL and network access
4. **Scraping Failures**: Verify Playwright installation in Docker
5. **PDF Generation**: Ensure Chrome is installed in container

### Debug Commands

```bash
# Check backend logs
flyctl logs -a easyinterns-api

# Test API endpoints
curl https://easyinterns-api.fly.dev/health

# Check database connection
flyctl ssh console -a easyinterns-api
python -c "from app.database import engine; print(engine.execute('SELECT 1'))"
```

## 10. Security Considerations

- All secrets stored in environment variables
- HTTPS enforced on all endpoints
- JWT tokens for API authentication
- Rate limiting enabled
- Input validation on all endpoints
- SQL injection protection via SQLModel
- XSS protection headers set

### Admin Access Hardening

Protect admin UI and ingest APIs at the edge with IP allowlists. Example NGINX config:

```nginx
server {
  # ...
  location ^~ /admin {
    allow 203.0.113.4;        # office/VPN IP
    allow 10.0.0.0/8;         # private network
    deny all;
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }

  location ^~ /api/ingest/ {
    allow 203.0.113.4;
    allow 10.0.0.0/8;
    deny all;
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
}
```

Application-level controls are also in place:
- Basic auth on `/admin` via `ADMIN_USER`/`ADMIN_PASSWORD`
- Header token required for admin APIs via `ADMIN_TOKEN`
- Optional in-app IP allowlist via `ADMIN_IP_ALLOWLIST`
- In-app rate limiting on admin operations

## Support

For deployment issues:
- Check Fly.io status page
- Check Vercel status page  
- Review application logs
- Contact support if needed
