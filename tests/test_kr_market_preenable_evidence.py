from __future__ import annotations

import json
from pathlib import Path

from scripts.kr_market_preenable_evidence import audit_test_sink


ROOT = Path(__file__).resolve().parents[1]


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


def test_fail_closed_preenable_artifacts_are_complete() -> None:
    reports = ROOT / "docs" / "reports"
    required = (
        "20260827-kr-preenable-target-session.md",
        "20260827-kr-preenable-data-collection.md",
        "20260827-kr-preenable-numeric-provenance.md",
        "20260827-kr-preenable-reconciliation.md",
        "20260827-kr-preenable-market-digest-plan.md",
        "20260827-kr-preenable-ai-fallback-parity.md",
        "20260827-kr-preenable-test-sink-safety.md",
        "20260827-kr-preenable-test-delivery.md",
        "20260827-kr-preenable-exact-test-message.md",
        "20260827-kr-preenable-message-quality.md",
        "20260827-kr-preenable-gate-matrix.md",
        "20260827-kr-size-sector-enablement-action.md",
        "20260827-kr-size-sector-post-enable-smoke.md",
        "20260827-kr-size-sector-natural-proof-status.md",
        "20260827-kr-preenable-safety-parity.md",
        "20260827-kr-preenable-artifact-index.md",
    )
    assert all((reports / name).exists() for name in required)
    provenance = (reports / "20260827-kr-preenable-numeric-provenance.md").read_text()
    assert provenance.count("market:cross-section:sector:") == 10

    evidence = json.loads(
        (reports / "20260827-kr-preenable-gate-matrix.json").read_text()
    )
    gates = evidence["gates"]
    assert gates["PREENABLE_DATA_COLLECTION"] == "PASS"
    assert gates["NUMERIC_GATE"] == "PASS"
    assert gates["AI_FALLBACK_SIZE_STYLE_PARITY"] == "PASS"
    assert gates["AI_FALLBACK_SECTOR_PARITY"] == "PASS"
    assert gates["TEST_SINK_AVAILABLE"] == "NO"
    assert gates["TEST_DELIVERY_COUNT"] == 0
    assert gates["PRODUCTION_DELIVERY_INTENT_CREATED"] == 0
    assert gates["ENABLEMENT_ACTION"] == "DO_NOT_ENABLE"
    assert gates["PRICE_STRUCTURE_RUNTIME_ARMED"] == 0
    assert evidence["open_p0"] == []
    assert evidence["open_material_p1"] == [
        "dedicated_test_sink_not_configured"
    ]
