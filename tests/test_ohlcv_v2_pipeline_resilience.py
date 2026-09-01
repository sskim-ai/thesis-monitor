from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.jobs.accepted_decision_v2_runtime import prepare_context
from app.services.cross_market_decision_engine_service import (
    EvidenceCategory,
    build_decision_evidence_packet,
)
from app.services.kr_investor_flow_service import (
    serialize_price_context_with_reconciliation,
)
from app.services.ohlcv_client import OhlcvClient
from app.services.ohlcv_feature_engine_service import (
    build_multi_timeframe_feature_packet,
)
from app.services.ohlcv_resilience_service import (
    OhlcvServiceHealth,
    probe_ohlcv_service,
)
from app.services.packet_owned_technical_context_service import (
    TechnicalContextStatus,
    build_packet_owned_technical_context,
    packet_owned_context_for_stock,
)


def _bars(end: date, count: int = 40) -> list[dict[str, object]]:
    rows = []
    for index in range(count):
        current = end - timedelta(days=count - index - 1)
        close = 100 + index
        rows.append(
            {
                "date": current.isoformat(),
                "open": close - 1,
                "high": close + 2,
                "low": close - 2,
                "close": close,
                "volume": 1_000 + index,
            }
        )
    return rows


def _periods(end: date) -> dict[str, list[dict[str, object]]]:
    return {key: _bars(end) for key in ("daily", "weekly", "monthly")}


def _context(**overrides: object):
    values: dict[str, object] = {
        "ticker": "TEST",
        "market": "us",
        "session": "after_hours",
        "as_of": "2026-08-31T18:00:00-04:00",
        "periods": _periods(date(2026, 8, 31)),
        "cutoff": date(2026, 8, 31),
        "expected_daily_completed": "2026-08-31",
    }
    values.update(overrides)
    return build_packet_owned_technical_context(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "ticker",
    ("CORZ", "GOOGL", "MU", "TSLA", "CPNG", "000660", "047810"),
)
def test_packet_owned_context_preserves_exact_feature_engine_parity(
    ticker: str,
) -> None:
    periods = _periods(date(2026, 8, 31))
    expected = build_multi_timeframe_feature_packet(
        ticker=ticker,
        periods=periods,
        cutoff=date(2026, 8, 31),
    )

    context = _context(
        ticker=ticker,
        market="kr" if ticker.isdigit() else "us",
        periods=periods,
    )

    assert context.status == TechnicalContextStatus.FULL
    assert context.features == expected
    assert context.feature_fingerprint == expected.packet_sha256
    assert context.quality["D"].usable_for_current_reasoning is True


def test_stale_daily_is_partial_and_not_exposed_as_current_technical_evidence() -> None:
    context = _context(expected_daily_completed="2026-09-01")
    packet = {
        "packet_id": "packet-stale",
        "market": "us",
        "assessment_date": "2026-09-01",
    }
    stock = {"ticker": "TEST", "company_name": "Test", "thesis": {}}

    evidence = build_decision_evidence_packet(
        packet=packet,
        stock=stock,
        technical_context=context,
    )

    assert context.status == TechnicalContextStatus.PARTIAL_SAFE
    assert context.quality["D"].freshness_state == "STALE"
    assert not any(
        row.category == EvidenceCategory.TECHNICAL_FEATURE and row.source_ref.find(".daily.") >= 0
        for row in evidence.evidence
    )
    assert any(
        "technical_context_limit:PARTIAL_SAFE" in row for row in evidence.data_quality_cautions
    )


def test_malformed_single_subject_is_invalid_without_affecting_valid_peer() -> None:
    malformed = _periods(date(2026, 8, 31))
    malformed["daily"][5]["high"] = 1

    invalid = _context(ticker="BAD", periods=malformed)
    valid = _context(ticker="GOOD")

    assert invalid.status == TechnicalContextStatus.INVALID
    assert invalid.features is None
    assert "D:invalid_ohlc_relation" in invalid.cautions
    assert valid.status == TechnicalContextStatus.FULL


def test_partial_weekly_monthly_keeps_safe_daily_features_only() -> None:
    context = _context(periods={"daily": _bars(date(2026, 8, 31)), "weekly": [], "monthly": []})
    evidence = build_decision_evidence_packet(
        packet={
            "packet_id": "packet-partial",
            "market": "us",
            "assessment_date": "2026-09-01",
        },
        stock={"ticker": "TEST", "company_name": "Test", "thesis": {}},
        technical_context=context,
    )

    assert context.status == TechnicalContextStatus.PARTIAL_SAFE
    assert context.quality["D"].usable_for_current_reasoning is True
    assert context.quality["W"].status == TechnicalContextStatus.UNAVAILABLE
    technical = [
        row for row in evidence.evidence if row.category == EvidenceCategory.TECHNICAL_FEATURE
    ]
    assert technical
    assert all(".daily." in row.source_ref for row in technical)


def test_missing_legacy_packet_context_fails_closed_but_builds_decision_packet() -> None:
    packet = {
        "packet_id": "legacy-run-49-copy",
        "market": "us",
        "assessment_date": "2026-09-01",
        "generated_at": "2026-09-01T00:00:00+00:00",
    }
    stock = {"ticker": "CPNG", "company_name": "Coupang", "thesis": {}}

    context = packet_owned_context_for_stock(packet=packet, stock=stock)
    evidence = build_decision_evidence_packet(
        packet=packet,
        stock=stock,
        technical_context=context,
    )

    assert context.status == TechnicalContextStatus.UNAVAILABLE
    assert evidence.technical_context_status == "UNAVAILABLE"
    assert any("packet_technical_context_missing" in row for row in evidence.data_quality_cautions)


@pytest.mark.anyio
async def test_source_client_recovers_after_connect_error_and_freezes_internal_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ConnectError("service restart", request=request)
        period = request.url.params["periods"]
        return httpx.Response(200, json={"periods": {period: _bars(date(2026, 8, 31))}})

    client = OhlcvClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(client.settings, "monitor_retry_attempts", 3)
    monkeypatch.setattr(client.settings, "monitor_retry_base_seconds", 0)
    context = await client.fetch_price_context(
        "CPNG",
        as_of=datetime(2026, 8, 31, 18, 0, tzinfo=ZoneInfo("America/New_York")),
    )
    stored = json.loads(serialize_price_context_with_reconciliation(context))

    assert "technical_context" not in context.model_dump(mode="json")
    assert stored["technical_context"]["status"] == "FULL"
    assert stored["technical_context"]["acquisition"]["retry_count"] == 1
    assert stored["technical_context"]["acquisition"]["connection_error_count"] == 1


@pytest.mark.anyio
@pytest.mark.parametrize("error_type", [httpx.ConnectTimeout, httpx.ReadTimeout])
async def test_source_client_timeout_is_bounded_and_subject_safe(
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[httpx.TimeoutException],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error_type("timeout", request=request)

    client = OhlcvClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(client.settings, "monitor_retry_attempts", 2)
    monkeypatch.setattr(client.settings, "monitor_retry_base_seconds", 0)
    context = await client.fetch_price_context(
        "CPNG",
        as_of=datetime(2026, 8, 31, 18, 0, tzinfo=ZoneInfo("America/New_York")),
    )
    technical = context.technical_context_payload()

    assert technical["status"] == "UNAVAILABLE"
    assert technical["acquisition"]["request_count"] == 6
    assert technical["acquisition"]["timeout_count"] == 6


@pytest.mark.anyio
async def test_source_client_caps_excessive_retry_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unreachable", request=request)

    client = OhlcvClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(client.settings, "monitor_retry_attempts", 50)
    monkeypatch.setattr(client.settings, "monitor_retry_base_seconds", 0)
    context = await client.fetch_price_context(
        "CPNG",
        as_of=datetime(2026, 8, 31, 18, 0, tzinfo=ZoneInfo("America/New_York")),
    )
    technical = context.technical_context_payload()

    assert technical["status"] == "UNAVAILABLE"
    assert technical["acquisition"]["request_count"] == 15
    assert technical["acquisition"]["connection_error_count"] == 15


@pytest.mark.anyio
async def test_service_health_distinguishes_transport_and_data_freshness() -> None:
    def healthy(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(
            200,
            json={"periods": {"daily": [{"date": "2026-08-31"}]}},
        )

    ready = await probe_ohlcv_service(
        base_url="http://ohlcv.test",
        api_key="",
        symbol="CPNG",
        expected_daily_bar="2026-08-31",
        attempts=1,
        transport=httpx.MockTransport(healthy),
    )
    stale = await probe_ohlcv_service(
        base_url="http://ohlcv.test",
        api_key="",
        symbol="CPNG",
        expected_daily_bar="2026-09-01",
        attempts=1,
        transport=httpx.MockTransport(healthy),
    )

    assert ready.state == OhlcvServiceHealth.READY
    assert ready.data_endpoint_functional is True
    assert stale.state == OhlcvServiceHealth.DEGRADED
    assert stale.latest_expected_completed_bar_available is False


@pytest.mark.anyio
async def test_accepted_v2_prepare_consumes_only_packet_owned_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    root = tmp_path / "ai_review"
    (root / "claims").mkdir(parents=True)
    (root / "outbox").mkdir(parents=True)
    context = _context(ticker="CPNG")
    packet = {
        "packet_id": "packet-owned-v2",
        "market": "us",
        "assessment_date": "2026-09-01",
        "generated_at": "2026-09-01T00:00:00+00:00",
        "stocks": [
            {
                "ticker": "CPNG",
                "company_name": "Coupang",
                "thesis": {},
                "technical_context": context.model_dump(mode="json"),
            }
        ],
    }
    packet_path = root / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    (root / "claims" / "packet-owned-v2.json").write_text(
        json.dumps(
            {
                "packet_id": "packet-owned-v2",
                "claim_id": "claim-owned-v2",
                "packet_path": str(packet_path),
                "final_output_path": str(root / "outbox" / "review.json"),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("app.jobs.accepted_decision_v2_runtime._root", lambda: root)
    monkeypatch.setattr(
        "app.jobs.accepted_decision_v2_runtime.v2_accepted_production_armed",
        lambda: True,
    )

    result = await prepare_context("packet-owned-v2", "claim-owned-v2")
    prepared = json.loads(
        (root / "claims" / "review--claim-owned-v2.decision-v2-context.json").read_text()
    )

    assert result["status"] == "CONTEXT_READY"
    assert result["technical_context_counts"]["FULL"] == 1
    assert prepared["evidence_packets"][0]["technical_context_id"] == context.technical_context_id


@pytest.mark.anyio
async def test_systemic_missing_packet_context_does_not_abort_cohort_prepare(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    root = tmp_path / "ai_review"
    (root / "claims").mkdir(parents=True)
    (root / "outbox").mkdir(parents=True)
    packet = {
        "packet_id": "legacy-systemic-outage",
        "market": "us",
        "assessment_date": "2026-09-01",
        "generated_at": "2026-09-01T00:00:00+00:00",
        "stocks": [
            {"ticker": ticker, "company_name": ticker, "thesis": {}} for ticker in ("CPNG", "GOOGL")
        ],
    }
    packet_path = root / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    (root / "claims" / "legacy-systemic-outage.json").write_text(
        json.dumps(
            {
                "packet_id": "legacy-systemic-outage",
                "claim_id": "claim-systemic",
                "packet_path": str(packet_path),
                "final_output_path": str(root / "outbox" / "review.json"),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("app.jobs.accepted_decision_v2_runtime._root", lambda: root)
    monkeypatch.setattr(
        "app.jobs.accepted_decision_v2_runtime.v2_accepted_production_armed",
        lambda: True,
    )

    result = await prepare_context("legacy-systemic-outage", "claim-systemic")

    assert result["status"] == "CONTEXT_READY"
    assert result["subjects"] == ["CPNG", "GOOGL"]
    assert result["technical_context_counts"]["UNAVAILABLE"] == 2
