import os
from functools import lru_cache
from typing import Literal

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
    enable_newsapi_provider: bool = False
    finnhub_api_key: str | None = None
    alpha_vantage_api_key: str | None = None
    krx_open_api_key: str | None = None
    alpha_vantage_cache_hours: int = 24
    alpha_vantage_request_budget: int = 30
    alpha_vantage_consensus_discrepancy_pct: float = 20.0
    alpha_vantage_share_discrepancy_pct: float = 10.0
    openfigi_api_key: str | None = None
    fmp_api_key: str | None = None
    sharadar_api_key: str | None = None
    fred_api_key: str | None = None
    eia_api_key: str | None = None
    ecos_api_key: str | None = None
    naver_client_id: str | None = None
    naver_client_secret: str | None = None
    openai_api_key: str | None = None
    openai_narrative_model: str = "gpt-5.6-sol"
    openai_timeout_seconds: float = 60.0
    sec_user_agent: str | None = None
    action_api_key: str | None = None
    ohlcv_base_url: str = "http://127.0.0.1:8765"
    ohlcv_api_key: str | None = None
    ohlcv_timeout_seconds: float = 30.0
    monitor_lookback_days: int = 3
    monitor_retry_attempts: int = 3
    monitor_retry_base_seconds: float = 2.0
    assessment_distribution_warning_threshold: float = 0.7
    valuation_distribution_warning_threshold: float = 0.7
    valuation_snapshot_max_age_days: int = 7
    valuation_financial_max_age_days: int = 150
    valuation_provider_timeout_seconds: float = 15.0
    valuation_discrepancy_threshold_pct: float = 25.0
    valuation_model_min_quarters: int = 8
    valuation_model_growth_floor: float = -0.30
    valuation_model_growth_cap: float = 0.50
    valuation_history_sampling: str = "weekly"
    valuation_history_target_years: int = 5
    valuation_history_minimum_years: int = 3
    valuation_history_min_observations: int = 26
    valuation_history_min_days: int = 180
    valuation_history_max_pe: float = 200.0
    valuation_history_max_pb: float = 50.0
    valuation_history_cross_check_threshold_pct: float = 25.0
    valuation_history_discounted_percentile: float = 20.0
    valuation_history_somewhat_discounted_percentile: float = 40.0
    valuation_history_somewhat_premium_percentile: float = 60.0
    valuation_history_premium_percentile: float = 80.0
    capital_action_review_share_pct: float = 0.5
    capital_action_material_share_pct: float = 2.0
    capital_action_review_market_cap_pct: float = 0.5
    capital_action_material_market_cap_pct: float = 2.0
    macro_vix_material_pct: float = 5.0
    macro_real_yield_material_bp: float = 5.0
    macro_nominal_yield_material_bp: float = 7.0
    macro_credit_spread_material_bp: float = 10.0
    macro_other_material_pct: float = 1.0
    financial_operating_margin_upper_bound: float = 60.0
    financial_reporting_cadence_days: int = 160
    macro_monitor_enabled: bool = True
    macro_provider_timeout_seconds: float = 20.0
    macro_briefing_send_no_change: bool = True
    macro_alert_min_magnitude: int = 3
    notification_dry_run: bool = True
    notification_channel: str = "telegram"
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_message_max_chars: int = 3500
    telegram_retry_attempts: int = 3
    telegram_retry_base_seconds: float = 2.0
    ai_review_mode: Literal["off", "shadow", "assist"] = "shadow"
    ai_review_claim_lease_minutes: int = 30
    ai_review_shadow_catchup_hours: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )


def _settings_env_file() -> str | None:
    override = os.environ.get("THESIS_MONITOR_ENV_FILE")
    if override is None:
        return ".env"
    return override or None


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=_settings_env_file())
