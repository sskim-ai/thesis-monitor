from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "sqlite:///./thesis_monitor.sqlite3"
    enable_live_providers: bool = False
    include_mock_provider: bool = True
    live_provider_timeout_seconds: float = 5.0
    naver_news_display: int = 10
    google_news_display: int = 10
    opendart_api_key: str | None = None
    newsapi_api_key: str | None = None
    finnhub_api_key: str | None = None
    alpha_vantage_api_key: str | None = None
    naver_client_id: str | None = None
    naver_client_secret: str | None = None
    openai_api_key: str | None = None
    sec_user_agent: str | None = None
    action_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
