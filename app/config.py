from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra='ignore', case_sensitive=False)
    # Core App Settings
    app_name: str = Field(default="EasyIntern")
    environment: str = Field(default="dev")
    debug: bool = Field(default=False)
    
    # Database
    database_url: str = Field(default="sqlite:///easyintern.db")
    
    # Supabase
    supabase_url: Optional[str] = Field(default=None)
    supabase_anon_key: Optional[str] = Field(default=None)
    supabase_service_key: Optional[str] = Field(default=None)
    supabase_jwt_secret: Optional[str] = Field(default=None)
    
    # AI Provider
    ai_provider: str = Field(default="openai")
    openai_api_key: Optional[str] = Field(default=None)
    
    # External APIs
    clearbit_api_base: str = Field(default="https://logo.clearbit.com")
    clearbit_api_key: Optional[str] = Field(default=None)
    
    # Redis/Queue
    redis_url: Optional[str] = Field(default=None)
    
    # Scraping
    user_agent: str = Field(default=(
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ))
    http_timeout_seconds: float = Field(default=20.0)
    max_concurrency: int = Field(default=10)
    
    # Feature Flags
    enable_greenhouse: bool = Field(default=True)
    enable_lever: bool = Field(default=True)
    enable_rss: bool = Field(default=True)
    enable_linkedin: bool = Field(default=False)
    enable_glassdoor: bool = Field(default=False)
    enable_linkedin_scraper: bool = Field(default=False)
    enable_glassdoor_scraper: bool = Field(default=False)
    enable_ai_features: bool = Field(default=True)
    enable_email_extraction: bool = Field(default=True)
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=30)
    # Admin access
    admin_token: Optional[str] = Field(default=None, description="Static admin token for protected endpoints")
    admin_user: Optional[str] = Field(default=None, description="Admin basic auth username for /admin UI")
    admin_password: Optional[str] = Field(default=None, description="Admin basic auth password for /admin UI")
    admin_ip_allowlist: Optional[List[str]] = Field(default=None, description="List of allowed CIDRs/IPs for admin endpoints")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100)
    
    # Logging
    log_level: str = Field(default="INFO")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None)
    
    # File Storage
    upload_max_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    allowed_file_types: list[str] = Field(default=["pdf", "doc", "docx"])
    storage_backend: str = Field(default="local", description="local or supabase")
    storage_bucket: Optional[str] = Field(default=None)
    storage_prefix: Optional[str] = Field(default="exports")

    # Aggregation / Ingestion
    aggregator_enabled: bool = Field(default=False)
    aggregator_interval_minutes: int = Field(default=240)  # every 4 hours
    aggregator_query: str = Field(default="intern")
    aggregator_location: str = Field(default="Canada")
    aggregator_max_results: int = Field(default=1000)
    aggregator_nightly_enabled: bool = Field(default=False)
    aggregator_nightly_hour_local: int = Field(default=3, description="Local hour [0-23] to run nightly ingest")

    # No inner Config; handled by model_config

settings = Settings()


def get_settings() -> Settings:
    """Return application settings instance (for test patching)."""
    return settings
