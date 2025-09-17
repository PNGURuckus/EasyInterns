"""
EasyInterns v2 Backend
FastAPI application with proper structure
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.core.config import settings
from backend.core.database import create_db_and_tables
from backend.api import internships, users, resumes, scrape


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting EasyInterns v2 Backend - {settings.ENVIRONMENT}")
    create_db_and_tables()
    yield
    # Shutdown
    print("Shutting down EasyInterns v2 Backend")


app = FastAPI(
    title="EasyInterns v2 API",
    description="Canadian Internship Platform - Production Grade",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(internships.router, prefix="/api", tags=["internships"])
app.include_router(resumes.router, prefix="/api", tags=["resumes"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(scrape.router, prefix="/api", tags=["scraping"])


@app.get("/")
def root():
    return {
        "message": "EasyInterns v2 API",
        "version": "2.0.0",
        "environment": settings.environment,
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        log_level="info"
    )
