from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = Field(default="EasyIntern")
    environment: str = Field(default="dev")
    database_url: str = Field(default="sqlite:///easyintern.db")
    user_agent: str = Field(default=(
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ))
    http_timeout_seconds: float = Field(default=20.0)
    max_concurrency: int = Field(default=10)
    enable_greenhouse: bool = Field(default=True)
    enable_lever: bool = Field(default=True)
    enable_rss: bool = Field(default=True)
    indeed_proxy_url: str | None = Field(default=None)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
