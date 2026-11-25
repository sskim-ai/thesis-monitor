"""Real KR/US Source assembly from synthetic raw bars and financial responses.

No preassembled stock/catalog bypasses numeric registration. Trading-session
daily bars and their weekly/monthly aggregates exercise the completed-bar path
that the older weekend-filled fixtures could not reach in the US owner.
"""
from copy import deepcopy
from datetime import date, timedelta
import json
import math
import socket

import exchange_calendars
import pytest

from app.services import unified_stock_owner
from app.services.completed_price_state import bind_source
from app.services.fresh_financial_stock_owner import (
    BusinessMandatorySourceIncomplete, assemble_fresh_stock,
)
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import encoded
from app.services.unified_stock_anomaly_scope import materialize_source_components
from tests.completed_price_fixtures import source as completed_price_source
from tests.rev8_source_fixtures import fresh_inputs
from tests.rev10_source_fixtures import wire_clock
from tests.test_reported_business_native_projection import window
from tests.test_unified_stock_acquisition import plan as plan_fixture
from tests.test_unified_stock_owner import freeze_hashes


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("C56_SOURCE_EXTERNAL_IO_DENIED")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)


def _bars(market, target):
    calendar = exchange_calendars.get_calendar("XKRX" if market == "kr" else "XNYS")
    sessions = calendar.sessions_in_range("2023-01-01", target)[-600:]
    daily = []
    for index, session in enumerate(sessions):
        close = round(100 + 9 * math.sin(index * math.pi / 10), 4)
        daily.append(dict(date=session.date().isoformat(), open=close - 0.2,
            high=close + 1, low=close - 1, close=close,
            volume=1_000_000 + (index % 20) * 1000, value=100_000_000))

    def aggregate(key):
        groups = {}
        for row in daily:
            groups.setdefault(key(date.fromisoformat(row["date"])), []).append(row)
        return [dict(date=rows[0]["date"], open=rows[0]["open"],
            high=max(row["high"] for row in rows), low=min(row["low"] for row in rows),
            close=rows[-1]["close"], volume=sum(row["volume"] for row in rows),
            value=sum(row["value"] for row in rows)) for rows in groups.values()]

    weekly = aggregate(lambda day: day.isocalendar()[:2])
    return dict(adjusted_daily=daily, adjusted_weekly=weekly,
        adjusted_monthly=aggregate(lambda day: (day.year, day.month)),
        unadjusted_weekly_valuation=deepcopy(weekly))


def source_inputs(root, ticker):
    plan = plan_fixture.__wrapped__()
    with wire_clock(plan.frozen_at + timedelta(seconds=4)):
        inputs = fresh_inputs(root, ticker, plan=plan, verified_identity=True,
                              completed_price=False)
    technical = inputs["technical_inputs"]
    read = next(row for row in plan.reads if row.subject == ticker)
    roles = _bars(read.market, read.latest_completed_session)
    for role, rows in roles.items():
        receipt = technical["receipts"][role]
        raw, normalized = encoded(dict(return_code=0, result_list=rows)), encoded(rows)
        page = receipt["pages"][0]
        technical["artifacts"][page["artifact"]] = raw
        technical["artifacts"][receipt["normalized_artifact"]] = normalized
        page["source_sha256"] = sha256_bytes(raw)
        receipt["normalized_sha256"] = sha256_bytes(normalized)
    if read.market == "us":
        security = inputs["financial_inputs"]["plan"]["security"]
        price_source, artifacts = completed_price_source(plan, security,
            value=roles["adjusted_daily"][-1]["close"])
        technical = bind_source(technical, source=price_source, artifacts=artifacts,
                                security=security)
    else:
        technical["components"] = materialize_source_components(ticker=ticker,
            market=read.market, cutoff=date.fromisoformat(read.latest_completed_session),
            observed_at=plan.frozen_at.isoformat(), roles=roles, completed_session=True)
    inputs["technical_inputs"] = freeze_hashes(technical)
    return dict(inputs, reported_comparison_business=True, source_window=window(plan))


@pytest.mark.parametrize("market,ticker,currency", [("kr", "005930", "KRW"), ("us", "CORZ", "USD")])
def test_real_source_registers_both_closes_without_changing_their_dates(tmp_path, market, ticker, currency):
    inputs = source_inputs(tmp_path, ticker)
    before = deepcopy(inputs["technical_inputs"])
    result = assemble_fresh_stock(**inputs)
    assert result["status"] == "PASS" and result["mandatory_missing"] == []
    assert result["numeric_registry_unregistered"] == []
    assert inputs["technical_inputs"] == before
    stock = result["packet"]["stocks"][0]
    assert stock["chart_context"]["available"] is True
    fact = next(f for f in stock["fact_catalog"] if f["fact_type"] == "chart_invalidation")
    fields = fact["fields"]
    frames = stock["chart_context"]["timeframes"]
    assert fields["latest_daily_close"] == frames["daily"]["candle"]["close"]
    assert fields["weekly_close"] == frames["weekly"]["candle"]["close"]
    assert fields["evaluation_date"] == frames["daily"]["as_of_date"]
    assert fields["weekly_bar_date"] == frames["weekly"]["as_of_date"]
    assert fields["evaluation_date"] != fields["weekly_bar_date"]
    assert fields["comparison_basis"] == "CURRENT_SELECTED_SUPPORT"
    assert fields["historical_break_evidence"] == "NOT_ESTABLISHED"
    for flag in ("hard_daily", "hard_weekly", "accelerated", "wick_only", "chart_only"):
        assert isinstance(fields[flag], bool)
    for field in ("latest_daily_close", "weekly_close"):
        row = next(row for row in stock["numeric_registry"]
            if row["fact_id"] == fact["fact_id"] and row["field_path"] == "fields." + field)
        assert row["registered"] is True and row["prose_allowed"] is True
        assert (row["semantic_type"], row["unit"], row["value"]) == (
            "chart_close_price", currency, fields[field])
    evidence = next(row for row in result["evidence_packet"]["evidence"]
        if row["ref_id"] == "canonical:" + fact["fact_id"])
    assert json.loads(evidence["statement"]) == fields
    assert result["packet"]["market"] == market


@pytest.mark.parametrize("market,ticker", [("kr", "005930"), ("us", "CORZ")])
def test_other_unknown_number_still_blocks_real_source_with_its_identity(tmp_path, monkeypatch, market, ticker):
    inputs = source_inputs(tmp_path, ticker)
    original = unified_stock_owner.build_source_fact_catalog

    def future_field(**kwargs):
        facts = original(**kwargs)
        fact = next(row for row in facts if row["fact_type"] == "chart_invalidation")
        fact["fields"]["unregistered_future_close"] = 321.5
        return facts

    # Extend the actual producer, so every owner replay sees the same genuine
    # catalog plus one deliberately unsupported field. No acceptance is stubbed.
    monkeypatch.setattr(unified_stock_owner, "build_source_fact_catalog", future_field)
    with pytest.raises(BusinessMandatorySourceIncomplete) as failure:
        assemble_fresh_stock(**inputs)
    assert str(failure.value).startswith("business_mandatory_source_incomplete:")
    assert failure.value.source_context == dict(market=market, ticker=ticker,
        mandatory_missing=["numeric_registry:unregistered_fields"],
        unregistered_fields=[dict(fact_id="chart:structure:invalidation",
                                 field_path="fields.unregistered_future_close")])
