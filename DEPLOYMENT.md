# EasyInterns Deployment Guide

Complete deployment guide for the EasyInterns platform.

## Quick Start

1. **Setup Development Environment**
   ```bash
   ./scripts/setup-dev.sh
   ```

2. **Test Locally**
   ```bash
   ./scripts/test-local.sh
   ```

3. **Deploy Backend**
   ```bash
   ./scripts/deploy-backend.sh
   ```

4. **Deploy Frontend**
   ```bash
   ./scripts/deploy-frontend.sh
   ```

## Prerequisites

### Required Tools
- Python 3.11+
- Node.js 18+
- Docker (for local testing)
- [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/)
- [Vercel CLI](https://vercel.com/cli) (optional)

### Required Services
- [Supabase](https://supabase.com) account and project
- [OpenAI](https://openai.com) API key
- [Clearbit](https://clearbit.com) API key (optional)

## Step-by-Step Deployment

### 1. Environment Setup

Run the setup script:
```bash
./scripts/setup-dev.sh
```

Configure environment variables:
```bash
# Edit backend .env
cp .env.example .env
# Add your actual values

# Edit frontend .env.local
cd frontend-next
cp .env.example .env.local
# Add your actual values
```

### 2. Database Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run the database initialization script in Supabase SQL editor:
   ```sql
   -- Copy contents from scripts/init-database.sql
   ```
3. Note your project URL and keys from Supabase dashboard

### 3. Local Testing

Test the complete application locally:
```bash
./scripts/test-local.sh
```

Run comprehensive tests:
```bash
./scripts/run-tests.sh
```

### 4. Backend Deployment

Deploy to Fly.io:
```bash
./scripts/deploy-backend.sh
```

Set required secrets:
```bash
flyctl secrets set \
  SUPABASE_URL="https://your-project.supabase.co" \
  SUPABASE_SERVICE_KEY="your-service-role-key" \
  SUPABASE_JWT_SECRET="your-jwt-secret" \
  OPENAI_API_KEY="sk-your-openai-key" \
  SECRET_KEY="your-secret-key" \
  -a easyinterns-api
```

### 5. Frontend Deployment

Deploy to Vercel:
```bash
cd frontend-next
./scripts/deploy-frontend.sh
```

Or connect GitHub repository to Vercel for automatic deployments.

### 6. Post-Deployment

1. Test the deployed application
2. Set up monitoring and alerts
3. Configure custom domains (optional)
4. Set up CI/CD pipelines (optional)

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
OPENAI_API_KEY=sk-...
CLEARBIT_API_KEY=sk-...
SECRET_KEY=your-secret-key
ENVIRONMENT=production
DEBUG=false
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=https://easyinterns-api.fly.dev
```

## Monitoring

### Health Checks
- Backend: `https://easyinterns-api.fly.dev/health`
- Frontend: Built-in Vercel monitoring

### Logs
```bash
# Backend logs
flyctl logs -a easyinterns-api

# Frontend logs
vercel logs
```

### Metrics
- Fly.io Dashboard: `flyctl dashboard easyinterns-api`
- Vercel Dashboard: `https://vercel.com/dashboard`

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Verify DATABASE_URL is correct
   - Check Supabase project status
   - Ensure RLS policies are set correctly

2. **Authentication Issues**
   - Verify Supabase JWT secret matches
   - Check CORS settings in Supabase
   - Ensure redirect URLs are configured

3. **Scraping Issues**
   - Verify Playwright is installed in Docker
   - Check rate limiting settings
   - Review scraper logs

4. **Build Issues**
   - Clear node_modules and reinstall
   - Check TypeScript errors
   - Verify environment variables

### Debug Commands

```bash
# Test backend locally
python main.py

# Test frontend locally
cd frontend-next && npm run dev

# Check backend health
curl https://easyinterns-api.fly.dev/health

# View backend logs
flyctl logs -a easyinterns-api

# SSH into backend container
flyctl ssh console -a easyinterns-api
```

## Security

- All secrets stored as environment variables
- HTTPS enforced on all endpoints
- JWT authentication for protected routes
- Rate limiting enabled
- Input validation on all endpoints
- Row Level Security (RLS) enabled in database

## Scaling

### Backend Scaling
```bash
# Scale to multiple instances
flyctl scale count 3 -a easyinterns-api

# Scale machine resources
flyctl scale memory 2gb -a easyinterns-api
```

### Frontend Scaling
Vercel automatically scales based on traffic.

## Backup and Recovery

### Database Backups
Supabase provides automatic backups. For manual backups:
```bash
# Export database
supabase db dump --db-url "postgresql://..." > backup.sql

# Import database
psql "postgresql://..." < backup.sql
```

### Application Backups
- Code: Version controlled in Git
- Environment variables: Documented and stored securely
- Database: Automatic Supabase backups

## Support

For deployment issues:
- Check service status pages (Fly.io, Vercel, Supabase)
- Review application logs
- Contact platform support if needed

## Next Steps

After successful deployment:
1. Set up monitoring and alerting
2. Configure custom domains
3. Implement CI/CD pipelines
4. Set up error tracking (Sentry)
5. Configure analytics
6. Plan for scaling and optimization
