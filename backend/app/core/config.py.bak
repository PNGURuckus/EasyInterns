from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "EasyInterns"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "insecure-secret-key")
    
    # API
    API_V1_STR: str = "/api/v1"
    SERVER_NAME: Optional[str] = None
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    ASYNC_DATABASE_URL: str = os.getenv("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///./sql_app.db")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_sql_app.db")
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "False").lower() in ("true", "1", "t")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Scraping
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    SCRAPER_TIMEOUT: int = 30
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    STATIC_DIR: Path = BASE_DIR / "static"
    
    # Aggregator settings
    AGGREGATOR_ENABLED: bool = os.getenv("AGGREGATOR_ENABLED", "false").lower() in ("true", "1", "t")
    AGGREGATOR_INTERVAL_MINUTES: int = int(os.getenv("AGGREGATOR_INTERVAL_MINUTES", "240"))
    AGGREGATOR_QUERY: str = os.getenv("AGGREGATOR_QUERY", "intern")
    AGGREGATOR_LOCATION: str = os.getenv("AGGREGATOR_LOCATION", "Canada")
    AGGREGATOR_MAX_RESULTS: int = int(os.getenv("AGGREGATOR_MAX_RESULTS", "1500"))
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        
settings = Settings()
