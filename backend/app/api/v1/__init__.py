"""
API v1 Router
"""
from fastapi import APIRouter
from .endpoints import auth, internships, ranking

api_router = APIRouter()

# Include all available endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(internships.router, prefix="/internships", tags=["Internships"])
api_router.include_router(ranking.router, prefix="/ranking", tags=["Ranking"])
