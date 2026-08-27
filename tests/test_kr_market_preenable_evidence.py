from __future__ import annotations

from scripts.kr_market_preenable_evidence import audit_test_sink


def test_missing_dedicated_sink_fails_closed() -> None:
    result = audit_test_sink(
        {
            "TELEGRAM_BOT_TOKEN": "secret",
            "TELEGRAM_CHAT_ID": "production-chat",
        }
    )

    assert result["available"] is False
    assert result["reason"] == "dedicated_test_sink_not_configured"
    assert result["test_sink_alias"] == "NOT_CONFIGURED"
    assert result["production_collision"] == 0
    assert result["production_intent_collision"] == 0


def test_production_recipient_cannot_be_used_as_test_sink() -> None:
    result = audit_test_sink(
        {
            "TELEGRAM_CHAT_ID": "same-chat",
            "TELEGRAM_TEST_CHAT_ID": "same-chat",
        }
    )

    assert result["available"] is False
    assert result["reason"] == "test_sink_matches_production_sink"
    assert result["production_collision"] == 1


def test_distinct_explicit_test_sink_is_eligible_without_exposing_ids() -> None:
    result = audit_test_sink(
        {
            "TELEGRAM_CHAT_ID": "production-chat",
            "TELEGRAM_TEST_CHAT_ID": "developer-test-chat",
        }
    )

    assert result["available"] is True
    assert result["reason"] == "safe_dedicated_test_sink"
    assert result["selected_test_key_name"] == "TELEGRAM_TEST_CHAT_ID"
    assert result["test_sink_alias"] != result["production_sink_alias"]
    assert "production-chat" not in str(result)
    assert "developer-test-chat" not in str(result)


def test_multiple_test_sink_keys_are_ambiguous() -> None:
    result = audit_test_sink(
        {
            "TELEGRAM_CHAT_ID": "production-chat",
            "TELEGRAM_TEST_CHAT_ID": "test-chat-one",
            "TELEGRAM_STAGING_CHAT_ID": "test-chat-two",
        }
    )

    assert result["available"] is False
    assert result["reason"] == "multiple_test_sinks_ambiguous"
