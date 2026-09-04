import os
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
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
    krx_open_api_base_url: str = "https://data-dbg.krx.co.kr/svc/apis"
    massive_api_key: str | None = None
    massive_base_url: str = "https://api.massive.com"
    massive_cache_dir: str = "./data/cache/massive"
    massive_requests_per_minute: int = 5
    kiwoom_gateway_url: str | None = None
    kiwoom_gateway_api_key: str | None = None
    kiwoom_gateway_timeout_seconds: float = 15.0
    kiwoom_app_key: str | None = None
    kiwoom_secret_key: str | None = None
    kiwoom_rest_base_url: str = "https://api.kiwoom.com"
    kiwoom_rest_timeout_seconds: float = 30.0
    kiwoom_rest_request_interval_seconds: float = 0.2
    kiwoom_rest_max_retries: int = 3
    kiwoom_rest_max_pages: int = 50
    kiwoom_kr_market_context_enabled: bool = False
    nasdaq_us_exchange_breadth_enabled: bool = False
    nasdaq_trader_base_url: str = "https://www.nasdaqtrader.com"
    nasdaq_trader_timeout_seconds: float = 20.0
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
    onboarding_reconciler_enabled: bool = True
    onboarding_retry_base_minutes: int = 30
    onboarding_retry_max_minutes: int = 720
    onboarding_immediate_timeout_seconds: float = 45.0
    onboarding_background_timeout_seconds: float = 900.0
    onboarding_preflight_timeout_seconds: float = 8.0
    onboarding_pending_sla_hours: int = 24
    onboarding_repeated_failure_warning_threshold: int = 5
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
    notification_recipient_class: Literal["production", "test"] = "production"
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_test_chat_id: str | None = None
    telegram_message_max_chars: int = 3500
    telegram_retry_attempts: int = 3
    telegram_retry_base_seconds: float = 2.0
    ai_review_mode: Literal["off", "shadow", "assist"] = "shadow"
    ai_review_claim_lease_minutes: int = 30
    ai_review_claim_heartbeat_seconds: int = 60
    ai_review_backup_delay_minutes: int = 40
    ai_review_claim_safety_margin_minutes: int = 5
    ai_review_shadow_catchup_hours: int = 24
    ai_review_pilot_enabled: bool = False
    ai_review_pilot_target_success_days: int = 5
    ai_review_pilot_us_fallback_time: str = "08:40"
    ai_review_pilot_kr_fallback_time: str = "17:10"
    free_analyst_adaptive_enabled: bool = False
    free_analyst_adaptive_mode: Literal[
        "current", "free_analyst_adaptive_canary", "free_analyst_adaptive"
    ] = "current"
    free_analyst_adaptive_canary_max_market: int = 1
    free_analyst_adaptive_canary_max_stock: int = 2
    free_analyst_adaptive_canary_max_total: int = 3
    decision_engine_canary_enabled: bool = False
    decision_engine_state: Literal["test_sink_ready", "canary"] = "test_sink_ready"
    decision_engine_canary_kr_subjects: str = ""
    decision_engine_canary_us_subjects: str = ""
    visible_stock_decision_engine: Literal["v1_canary", "v2_accepted"] = "v1_canary"
    v2_production_enabled: bool = False
    v2_full_monitored_stock_coverage_target: bool = False
    v1_decision_rollback_available: bool = True
    cash_flow_runtime_shadow_canary_enabled: bool = True
    working_capital_runtime_shadow_canary_enabled: bool = True
    cash_flow_user_visible_mode: str = "OFF"
    working_capital_user_visible_mode: str = "OFF"
    kr_market_sector_top3_enabled: bool = False
    kr_price_structure_v3_enabled: bool = False
    us_price_structure_v3_enabled: bool = False

    @model_validator(mode="after")
    def validate_ai_review_schedule(self) -> "Settings":
        if self.ai_review_claim_heartbeat_seconds < 1:
            raise ValueError("AI review claim heartbeat must be positive")
        if self.onboarding_retry_base_minutes < 1:
            raise ValueError("Onboarding retry base must be at least one minute")
        if self.onboarding_retry_max_minutes < self.onboarding_retry_base_minutes:
            raise ValueError("Onboarding retry maximum must not be below its base")
        if min(
            self.onboarding_immediate_timeout_seconds,
            self.onboarding_background_timeout_seconds,
            self.onboarding_preflight_timeout_seconds,
        ) <= 0:
            raise ValueError("Onboarding timeouts must be positive")
        if self.onboarding_pending_sla_hours < 1:
            raise ValueError("Onboarding pending SLA must be positive")
        if self.onboarding_repeated_failure_warning_threshold < 1:
            raise ValueError("Onboarding retry warning threshold must be positive")
        if self.ai_review_backup_delay_minutes <= (
            self.ai_review_claim_lease_minutes + self.ai_review_claim_safety_margin_minutes
        ):
            raise ValueError("AI review backup delay must exceed claim lease plus safety margin")
        if not 0 <= self.free_analyst_adaptive_canary_max_market <= 1:
            raise ValueError("Free Analyst canary market limit must be 0 or 1")
        if not 0 <= self.free_analyst_adaptive_canary_max_stock <= 2:
            raise ValueError("Free Analyst canary stock limit must be between 0 and 2")
        if not 0 <= self.free_analyst_adaptive_canary_max_total <= 3:
            raise ValueError("Free Analyst canary total limit must be between 0 and 3")
        kr_subjects = tuple(
            item.strip().upper()
            for item in self.decision_engine_canary_kr_subjects.split(",")
            if item.strip()
        )
        us_subjects = tuple(
            item.strip().upper()
            for item in self.decision_engine_canary_us_subjects.split(",")
            if item.strip()
        )
        if len(kr_subjects) != len(set(kr_subjects)) or len(us_subjects) != len(
            set(us_subjects)
        ):
            raise ValueError("Decision canary subjects must be unique")
        if self.decision_engine_canary_enabled and (
            self.decision_engine_state != "canary"
            or len(kr_subjects) != 2
            or len(us_subjects) != 2
            or len(set((*kr_subjects, *us_subjects))) != 4
        ):
            raise ValueError(
                "Enabled decision canary requires state=canary and exact unique 2+2 subjects"
            )
        if self.visible_stock_decision_engine == "v2_accepted" and (
            not self.v2_production_enabled
            or not self.v2_full_monitored_stock_coverage_target
            or not self.v1_decision_rollback_available
        ):
            raise ValueError(
                "Visible v2 accepted decisions require production enablement, "
                "full monitored-stock coverage target, and v1 rollback availability"
            )
        return self

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
