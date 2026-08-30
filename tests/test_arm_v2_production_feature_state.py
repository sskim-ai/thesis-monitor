from __future__ import annotations

from pathlib import Path

from scripts.arm_v2_production_feature_state import (
    V2_PRODUCTION_FEATURE_STATE,
    arm_v2_production_feature_state,
)


def test_arm_v2_production_feature_state_changes_only_owned_keys(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "TELEGRAM_BOT_TOKEN=secret\n"
        "VISIBLE_STOCK_DECISION_ENGINE=v1_canary\n"
        "V2_PRODUCTION_ENABLED=false\n",
        encoding="utf-8",
    )

    updated = arm_v2_production_feature_state(env_file)
    result = env_file.read_text(encoding="utf-8")

    assert updated == tuple(V2_PRODUCTION_FEATURE_STATE)
    assert "TELEGRAM_BOT_TOKEN=secret" in result
    assert "VISIBLE_STOCK_DECISION_ENGINE=v2_accepted" in result
    assert "V2_PRODUCTION_ENABLED=true" in result
    assert "V2_FULL_MONITORED_STOCK_COVERAGE_TARGET=true" in result
    assert "V1_DECISION_ROLLBACK_AVAILABLE=true" in result
    assert result.count("VISIBLE_STOCK_DECISION_ENGINE=") == 1
