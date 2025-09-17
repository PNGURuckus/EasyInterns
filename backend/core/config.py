"""
Configuration management for EasyInterns v2
"""
import os
from pydantic import Field, field_validator, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, List, Optional, Union
from pathlib import Path

_ALIAS_MAP: Dict[str, str] = {
    "database_url": "DATABASE_URL",
    "debug": "DEBUG",
    "environment": "ENVIRONMENT",
    "allowed_origins": "BACKEND_CORS_ORIGINS",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    # Application
    APP_NAME: str = "EasyInterns"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "insecure-secret-key")
    
    # API
    API_V1_STR: str = "/api/v1"
    SERVER_NAME: Optional[str] = None
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="ALLOWED_ORIGINS"
    )
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+pysqlite:///./easyintern_v2.db")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///./test_easyintern.db")
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").lower() in ("true", "1", "t")
    
    # JWT
    JWT_SECRET: str = os.getenv("SECRET_KEY", "insecure-jwt-secret")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Scraping
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    SCRAPER_TIMEOUT: int = 30
    
    # Feature Flags
    ENABLE_AI_FEATURES: bool = os.getenv("ENABLE_AI_FEATURES", "true").lower() in ("true", "1", "t")
    ENABLE_EMAIL_EXTRACTION: bool = os.getenv("ENABLE_EMAIL_EXTRACTION", "true").lower() in ("true", "1", "t")
    ENABLE_PDF_EXPORT: bool = True
    ENABLE_LINKEDIN_SCRAPER: bool = os.getenv("ENABLE_LINKEDIN_SCRAPER", "false").lower() in ("true", "1", "t")
    ENABLE_GLASSDOOR_SCRAPER: bool = os.getenv("ENABLE_GLASSDOOR_SCRAPER", "false").lower() in ("true", "1", "t")
    
    # Aggregator settings
    AGGREGATOR_ENABLED: bool = os.getenv("AGGREGATOR_ENABLED", "true").lower() in ("true", "1", "t")
    AGGREGATOR_INTERVAL_MINUTES: int = int(os.getenv("AGGREGATOR_INTERVAL_MINUTES", "240"))
    AGGREGATOR_QUERY: str = os.getenv("AGGREGATOR_QUERY", "intern")
    AGGREGATOR_LOCATION: str = os.getenv("AGGREGATOR_LOCATION", "Canada")
    AGGREGATOR_MAX_RESULTS: int = int(os.getenv("AGGREGATOR_MAX_RESULTS", "1500"))
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    STATIC_DIR: Path = BASE_DIR / "static"
    
    # External APIs
    CLEARBIT_API_KEY: str = os.getenv("CLEARBIT_API_KEY", "")
    
    # Validation
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Scoring Weights
    field_match_weight: float = Field(default=0.3)
    skill_overlap_weight: float = Field(default=0.25)
    recency_decay_weight: float = Field(default=0.2)
    location_distance_weight: float = Field(default=0.15)
    modality_match_weight: float = Field(default=0.05)
    salary_present_weight: float = Field(default=0.03)
    government_program_weight: float = Field(default=0.02)
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100)
    rate_limit_per_hour: int = Field(default=1000)
    rate_limit_burst: int = Field(default=20)
    
    # Email Extraction
    email_confidence_threshold: float = Field(default=0.5)
    email_display_threshold: float = Field(default=0.7)
    email_mx_lookup_enabled: bool = Field(default=True)
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None)
    log_level: str = Field(default="INFO")
    enable_telemetry: bool = Field(default=True)

    # Compatibility helpers -------------------------------------------------
    # Map legacy attribute names used elsewhere in the codebase to the new
    # uppercase settings introduced in this module.
    _aliases: Dict[str, str] = PrivateAttr(default_factory=lambda: dict(_ALIAS_MAP))

    def _get_alias_map(self) -> Dict[str, str]:
        try:
            return object.__getattribute__(self, "_aliases")
        except AttributeError:
            return _ALIAS_MAP

    def __getattr__(self, item):
        alias_map = self._get_alias_map()
        alias = alias_map.get(item)
        if alias is not None:
            return super().__getattribute__(alias)
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        alias_map = self._get_alias_map()
        alias = alias_map.get(key)
        if alias is not None:
            return super().__setattr__(alias, value)
        return super().__setattr__(key, value)


def load_scraper_config() -> dict:
    """Load scraper configuration from JSON file"""
    config_path = Path("config.example.json")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            return config.get("scraper_config", {})
    return {}


# Global settings instance
settings = Settings()
