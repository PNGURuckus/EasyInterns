from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, users, internships, companies, 
    resumes, scrapers, ranking, applications, bookmarks
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(internships.router, prefix="/internships", tags=["Internships"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(scrapers.router, prefix="/scrapers", tags=["Scrapers"])
api_router.include_router(ranking.router, prefix="/ranking", tags=["Ranking"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(bookmarks.router, prefix="/bookmarks", tags=["Bookmarks"])
