from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    data_dir: str = "./data"
    database_url: str = "sqlite:///./data/thesis_monitor.sqlite3"
    enable_live_providers: bool = False
    include_mock_provider: bool = True
    live_provider_timeout_seconds: float = 5.0
    naver_news_display: int = 10
    google_news_display: int = 10
    opendart_api_key: str | None = None
    newsapi_api_key: str | None = None
    finnhub_api_key: str | None = None
    alpha_vantage_api_key: str | None = None
    fred_api_key: str | None = None
    eia_api_key: str | None = None
    ecos_api_key: str | None = None
    naver_client_id: str | None = None
    naver_client_secret: str | None = None
    openai_api_key: str | None = None
    sec_user_agent: str | None = None
    action_api_key: str | None = None
    ohlcv_base_url: str = "http://127.0.0.1:8765"
    ohlcv_api_key: str | None = None
    ohlcv_timeout_seconds: float = 30.0
    monitor_lookback_days: int = 3
    monitor_retry_attempts: int = 3
    monitor_retry_base_seconds: float = 2.0
    macro_monitor_enabled: bool = True
    macro_provider_timeout_seconds: float = 20.0
    macro_briefing_send_no_change: bool = True
    macro_alert_min_magnitude: int = 3
    notification_dry_run: bool = True
    kakao_rest_api_key: str | None = None
    kakao_client_secret: str | None = None
    kakao_refresh_token: str | None = None
    kakao_web_url: str = "https://sskim-macmini.tailb44bb1.ts.net/thesis/health"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
