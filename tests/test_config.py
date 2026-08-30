from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.jobs.validate_env import main, validate_env_file


def _write_env(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_known_telegram_environment_settings_load(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path / ".env",
        [
            "NOTIFICATION_CHANNEL=telegram",
            "TELEGRAM_BOT_TOKEN=dummy-token",
            "TELEGRAM_CHAT_ID=123",
            "TELEGRAM_TEST_CHAT_ID=456",
        ],
    )

    settings = Settings(_env_file=env_file)

    assert settings.notification_channel == "telegram"
    assert settings.telegram_bot_token == "dummy-token"
    assert settings.telegram_chat_id == "123"
    assert settings.telegram_test_chat_id == "456"


def test_known_krx_environment_setting_loads(tmp_path: Path) -> None:
    env_file = _write_env(tmp_path / ".env", ["KRX_OPEN_API_KEY=dummy-key"])

    settings = Settings(_env_file=env_file)

    assert settings.krx_open_api_key == "dummy-key"


def test_known_market_cross_section_settings_load(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path / ".env",
        [
            "MASSIVE_API_KEY=dummy-key",
            "KIWOOM_GATEWAY_URL=https://gateway.example.test",
            "KIWOOM_GATEWAY_API_KEY=dummy-gateway-key",
        ],
    )

    settings = Settings(_env_file=env_file)

    assert settings.massive_api_key == "dummy-key"
    assert settings.kiwoom_gateway_url == "https://gateway.example.test"
    assert settings.kiwoom_gateway_api_key == "dummy-gateway-key"


def test_known_ai_review_environment_settings_load(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path / ".env",
        [
            "AI_REVIEW_MODE=shadow",
            "AI_REVIEW_CLAIM_LEASE_MINUTES=30",
            "AI_REVIEW_BACKUP_DELAY_MINUTES=40",
            "AI_REVIEW_CLAIM_SAFETY_MARGIN_MINUTES=5",
            "AI_REVIEW_SHADOW_CATCHUP_HOURS=24",
        ],
    )

    settings = Settings(_env_file=env_file)

    assert settings.ai_review_mode == "shadow"
    assert settings.free_analyst_adaptive_enabled is False
    assert settings.free_analyst_adaptive_mode == "current"
    assert settings.free_analyst_adaptive_canary_max_market == 1
    assert settings.free_analyst_adaptive_canary_max_stock == 2
    assert settings.free_analyst_adaptive_canary_max_total == 3
    assert settings.ai_review_claim_lease_minutes == 30
    assert settings.ai_review_backup_delay_minutes == 40
    assert settings.ai_review_claim_safety_margin_minutes == 5


def test_decision_canary_defaults_fail_closed_and_accepts_exact_two_plus_two(
    tmp_path: Path,
) -> None:
    defaults = Settings(_env_file=None)
    assert defaults.decision_engine_canary_enabled is False
    assert defaults.decision_engine_state == "test_sink_ready"

    env_file = _write_env(
        tmp_path / ".env",
        [
            "DECISION_ENGINE_CANARY_ENABLED=true",
            "DECISION_ENGINE_STATE=canary",
            "DECISION_ENGINE_CANARY_KR_SUBJECTS=003690,000660",
            "DECISION_ENGINE_CANARY_US_SUBJECTS=GOOGL,RXRX",
        ],
    )
    settings = Settings(_env_file=env_file)
    assert settings.decision_engine_canary_enabled is True
    assert settings.decision_engine_canary_kr_subjects == "003690,000660"
    assert settings.decision_engine_canary_us_subjects == "GOOGL,RXRX"


def test_enabled_decision_canary_rejects_incomplete_scope(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path / ".env",
        [
            "DECISION_ENGINE_CANARY_ENABLED=true",
            "DECISION_ENGINE_STATE=canary",
            "DECISION_ENGINE_CANARY_KR_SUBJECTS=003690",
            "DECISION_ENGINE_CANARY_US_SUBJECTS=GOOGL,RXRX",
        ],
    )

    with pytest.raises(ValidationError, match="exact unique 2\\+2 subjects"):
        Settings(_env_file=env_file)


def test_v2_accepted_production_selector_is_explicit_and_fail_closed(
    tmp_path: Path,
) -> None:
    defaults = Settings(_env_file=None)
    assert defaults.visible_stock_decision_engine == "v1_canary"
    assert defaults.v2_production_enabled is False
    assert defaults.v2_full_monitored_stock_coverage_target is False
    assert defaults.v1_decision_rollback_available is True

    invalid = _write_env(
        tmp_path / "invalid.env",
        ["VISIBLE_STOCK_DECISION_ENGINE=v2_accepted"],
    )
    with pytest.raises(ValidationError, match="Visible v2 accepted decisions require"):
        Settings(_env_file=invalid)

    valid = _write_env(
        tmp_path / "valid.env",
        [
            "VISIBLE_STOCK_DECISION_ENGINE=v2_accepted",
            "V2_PRODUCTION_ENABLED=true",
            "V2_FULL_MONITORED_STOCK_COVERAGE_TARGET=true",
            "V1_DECISION_ROLLBACK_AVAILABLE=true",
        ],
    )
    settings = Settings(_env_file=valid)
    assert settings.visible_stock_decision_engine == "v2_accepted"


def test_cash_flow_user_visible_mode_defaults_off_and_accepts_runtime_value(
    tmp_path: Path,
) -> None:
    assert Settings(_env_file=None).cash_flow_user_visible_mode == "OFF"
    env_file = _write_env(
        tmp_path / ".env",
        ["CASH_FLOW_USER_VISIBLE_MODE=SELECTIVE_CURRENT_FORMAL_FULL_FCF"],
    )

    assert (
        Settings(_env_file=env_file).cash_flow_user_visible_mode
        == "SELECTIVE_CURRENT_FORMAL_FULL_FCF"
    )


def test_ai_review_backup_must_run_after_lease_and_safety_margin(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path / ".env",
        [
            "AI_REVIEW_CLAIM_LEASE_MINUTES=30",
            "AI_REVIEW_BACKUP_DELAY_MINUTES=35",
            "AI_REVIEW_CLAIM_SAFETY_MARGIN_MINUTES=5",
        ],
    )

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=env_file)

    assert any("backup delay" in item["msg"] for item in exc_info.value.errors())


@pytest.mark.parametrize(
    "unknown_key",
    ["TELEGRAM_BOT_TOKN", "KAKAO_REFRESH_TOKEN", "KRX_OPEN_API_KE"],
)
def test_unknown_environment_key_fails_strict_validation(
    tmp_path: Path,
    unknown_key: str,
) -> None:
    env_file = _write_env(tmp_path / ".env", [f"{unknown_key}=dummy"])

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=env_file)

    assert any(item["type"] == "extra_forbidden" for item in exc_info.value.errors())


def test_startup_settings_fail_fast_for_unknown_dotenv_key(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = _write_env(tmp_path / ".env", ["TELEGRAM_BOT_TOKN=dummy"])
    monkeypatch.setenv("THESIS_MONITOR_ENV_FILE", str(env_file))
    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError):
            get_settings()
    finally:
        monkeypatch.setenv("THESIS_MONITOR_ENV_FILE", "")
        get_settings.cache_clear()


def test_env_example_contains_only_known_settings() -> None:
    env_example = Path(__file__).resolve().parents[1] / ".env.example"

    assert validate_env_file(env_example) == []


def test_env_validator_never_prints_secret_values(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    secret = "super-secret-value-123"
    env_file = _write_env(tmp_path / ".env", [f"TELEGRAM_BOT_TOKN={secret}"])
    monkeypatch.setattr(
        "sys.argv",
        ["validate_env", "--env-file", str(env_file)],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    output = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "TELEGRAM_BOT_TOKN" in output.out
    assert secret not in output.out
    assert secret not in output.err
