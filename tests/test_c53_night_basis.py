"""Synthetic provider-basis repair; no claim about the unavailable C52 raw rows."""
import asyncio
from copy import deepcopy
import json
import socket
from types import SimpleNamespace

import httpx
from pydantic import TypeAdapter
import pytest

from app.jobs.probe_krx_night_futures import (
    _product_statuses, expected_latest_completed_krx_session, fetch_live_probe,
    parse_krx_futures_payloads,
)
from app.macro.briefing import market_observation_to_dict
from app.macro.providers.base import MacroProviderResult
from app.macro.providers.krx import materialize_night_probe
from app.services.market_session import preceding_exchange_session_date
from app.services.night_futures import (
    NIGHT_COMPARISON_SEMANTIC, night_futures_context_row, summarize_night_futures,
)
from app.services.unified_snapshot_contract import encoded
from tests.test_c52_night_daily import AT, actual_market, summary
from tests.test_krx_night_futures_probe import _row


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("C53_BASIS_EXTERNAL_IO_DENIED")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)


def payloads(*, settlement="778.10", provider_change="-35.50"):
    # Dates use the established synthetic MARKET fixture, not a fabricated C52
    # capture. In particular, DAY close 778.20 is a test value, not a screenshot fact.
    night_date = expected_latest_completed_krx_session(AT.date())
    day_date = preceding_exchange_session_date("XKRX", night_date)
    day = _row("KOSPI 200 선물", "정규", "A016C000", "코스피200 F 202612",
               "778.20", day_date.strftime("%Y%m%d"))
    if settlement is not None:
        day["SETL_PRC"] = settlement
    night = _row("KOSPI 200 선물", "야간", "A016C000", "코스피200 F 202612 야간",
                 "742.60", night_date.strftime("%Y%m%d"), provider_change)
    night.update(TDD_OPNPRC="769.90", TDD_HGPRC="769.95", TDD_LWPRC="731.35")
    return {day_date: {"OutBlock_1": [day]}, night_date: {"OutBlock_1": [night]}}


def materialized(tmp_path):
    bodies = {day.strftime("%Y%m%d"): value for day, value in payloads().items()}
    def reply(request):
        return httpx.Response(200, content=encoded(
            bodies.get(request.url.params["basDd"], {"OutBlock_1": []})), request=request)
    probe = asyncio.run(fetch_live_probe(run_date=AT.date(), observation_time=AT,
        api_key="synthetic", transport=httpx.MockTransport(reply)))
    probe.live_source = True
    value = TypeAdapter(MacroProviderResult).dump_python(
        materialize_night_probe(probe, history_directory=tmp_path, night_end_dates=True), mode="json")
    return probe, value


def test_settlement_audit_reaches_briefing_and_real_renderer_without_changing_return(tmp_path):
    probe, value = materialized(tmp_path)
    observed = probe.observations[0]
    assert observed.session_date == probe.expected_reference_date
    assert observed.reference_price == observed.regular_close == 778.20
    assert observed.point_change == -35.60
    assert observed.provider_change_point == -35.50
    assert observed.provider_change_match is True
    assert observed.provider_change_basis == "PRECEDING_DAY_SETTLEMENT"
    assert observed.reference_settlement_price == 778.10
    assert observed.comparison_semantic == NIGHT_COMPARISON_SEMANTIC
    assert probe.product_statuses[0].readiness == "READY"
    assert probe.product_statuses[0].provider_change_crosscheck_status == "PASS"

    row = deepcopy(value["observations"][0])
    row["raw_payload"] = json.dumps(row["raw_payload"])
    brief = market_observation_to_dict(SimpleNamespace(**row,
        provider="krx_night_futures", retrieved_at=AT.isoformat()))
    assert brief["provider_change_basis"] == "PRECEDING_DAY_SETTLEMENT"
    assert brief["reference_settlement_price"] == 778.10
    from_brief = summarize_night_futures({"observations": [brief]})
    assert len(from_brief.items) == 1
    brief_context = night_futures_context_row(from_brief.items[0])
    direct_context = night_futures_context_row(summary(value).items[0])
    assert {key: brief_context[key] for key in (
        "value", "reference_price", "change_value", "change_pct", "session_date"
    )} == {key: direct_context[key] for key in (
        "value", "reference_price", "change_value", "change_pct", "session_date"
    )}

    projected, message = actual_market(probe, value)
    claims = [c for c in projected["context"]["numeric_catalog"]["claims"]
              if c["claim_type"] == "OFFICIAL_NIGHT"]
    assert len(claims) == 1
    assert "종가 742.60" in message["text"]
    assert "직전 정규장" in message["text"] and "778.20" in message["text"]
    assert "차이 -35.60pt / -4.57%" in message["text"]
    assert "-35.50" not in message["text"]


@pytest.mark.parametrize("provider_change", ["-35.60", None])
def test_existing_close_basis_has_no_new_serialized_fields(provider_change):
    result = parse_krx_futures_payloads(payloads(provider_change=provider_change), fetched_at=AT)
    assert result.night_session_usable
    row = result.observations[0].model_dump(mode="json")
    assert "provider_change_basis" not in row and "reference_settlement_price" not in row
    assert row["reference_price"] == 778.20 and row["point_change"] == -35.60
    assert row["provider_change_match"] is (None if provider_change is None else True)


@pytest.mark.parametrize("settlement", [None, "0", "-778.10", "nan", "777.95"])
def test_unmatched_or_invalid_settlement_cannot_explain_conflicting_provider_delta(settlement):
    result = parse_krx_futures_payloads(payloads(settlement=settlement), fetched_at=AT)
    assert not result.night_session_usable
    assert not result.observations
    assert any("provider change conflicts" in warning for warning in result.warnings)


@pytest.mark.parametrize("change", ["other_contract", "same_date_day"])
def test_settlement_from_another_day_or_contract_cannot_make_pair_eligible(change):
    values = payloads()
    day_date, night_date = sorted(values)
    day = values[day_date]["OutBlock_1"][0]
    if change == "other_contract":
        day["ISU_CD"] = "OTHER"
    else:
        day["BAS_DD"] = night_date.strftime("%Y%m%d")
    result = parse_krx_futures_payloads(values, fetched_at=AT)
    assert not result.night_session_usable and not result.observations


def test_rejected_current_row_keeps_its_date_when_parser_falls_back_to_older_pair():
    values = payloads(settlement="777.95")
    day_date, night_date = sorted(values)
    prior_day = preceding_exchange_session_date("XKRX", day_date)
    values[day_date]["OutBlock_1"].append(_row(
        "KOSPI 200 선물", "야간", "A016C000", "코스피200 F 202612 야간",
        "777.95", day_date.strftime("%Y%m%d"), "1"))
    values[prior_day] = {"OutBlock_1": [_row(
        "KOSPI 200 선물", "정규", "A016C000", "코스피200 F 202612",
        "776.95", prior_day.strftime("%Y%m%d"))]}
    result = parse_krx_futures_payloads(values, fetched_at=AT)
    assert result.source_date == day_date
    status = _product_statuses(values, night_date, result, finality_valid=True)[0]
    assert status.returned_night_bas_dd == status.provider_raw_bas_dd == night_date
    assert status.reference_date_relation == "DATE_MATCH" and status.reference_date_match
    assert status.readiness == "NOT_READY"
    assert status.rejection_reason == "provider_change_conflict"
    assert status.provider_change_crosscheck_status == "FAILED"


@pytest.mark.parametrize("change", ["unknown_basis", "missing_basis", "missing_settlement", "wrong_settlement"])
def test_summary_recomputes_explicit_basis_instead_of_trusting_match_flag(tmp_path, change):
    _, value = materialized(tmp_path)
    row = value["observations"][0]
    fields = row["raw_payload"]
    if change == "unknown_basis":
        fields["provider_change_basis"] = "UNVERIFIED"
    elif change == "missing_basis":
        fields.pop("provider_change_basis")
    elif change == "missing_settlement":
        fields.pop("reference_settlement_price")
    else:
        fields["reference_settlement_price"] = 777.95
    assert fields["provider_change_match"] is True
    assert summarize_night_futures({"observations": [{**row, **fields}]}).items == []
