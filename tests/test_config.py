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
        ],
    )

    settings = Settings(_env_file=env_file)

    assert settings.notification_channel == "telegram"
    assert settings.telegram_bot_token == "dummy-token"
    assert settings.telegram_chat_id == "123"


def test_known_krx_environment_setting_loads(tmp_path: Path) -> None:
    env_file = _write_env(tmp_path / ".env", ["KRX_OPEN_API_KEY=dummy-key"])

    settings = Settings(_env_file=env_file)

    assert settings.krx_open_api_key == "dummy-key"


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
