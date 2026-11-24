"""Daily night prices survive absent optional periods; synthetic source bytes only."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta
import json
import socket
from types import SimpleNamespace

import httpx
import pytest
from pydantic import TypeAdapter

from app.jobs.probe_krx_night_futures import KRX_FUTURES_DAILY_URL, fetch_live_probe
from app.macro.providers.base import MacroProviderResult
from app.macro.providers.krx import materialize_night_probe
from app.services import krx_night_history_service as history
from app.services import production_message_renderer as renderer
from app.services.market_session import is_exchange_session_date
from app.services.night_futures import (
    night_futures_context_row, night_futures_timeframe_facts, summarize_night_futures,
)
from app.services.official_night_market_eligibility_service import night_market_eligibility
from app.services.unified_sealed_context import replay_night
from app.services.unified_snapshot_contract import digest, encoded
from tests.test_c47_optional_night_market import parts, project, reseal, decision
from tests.test_krx_night_futures_probe import _row


AT = datetime.fromisoformat("2026-09-27T08:00:00+00:00")


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("C52_NIGHT_EXTERNAL_IO_DENIED")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)


def original_probe(*, ohlc=True, at=AT):
    def reply(request):
        day = request.url.params["basDd"]
        day_date = datetime.strptime(day, "%Y%m%d").date()
        rows = []
        for session, close in (("정규", "100"), ("야간", "101")):
            if not is_exchange_session_date("XKRX", day_date-timedelta(days=int(session == "야간"))):
                continue
            row = _row("KOSPI 200 선물", session, "A016C000",
                "코스피200 F 202612" + (" 야간" if session == "야간" else ""),
                close, day, "1" if session == "야간" else None)
            if ohlc:
                row.update(TDD_OPNPRC="100", TDD_HGPRC="102", TDD_LWPRC="99")
            rows.append(row)
        return httpx.Response(200, content=encoded({"OutBlock_1": rows}), request=request)
    probe = asyncio.run(fetch_live_probe(run_date=at.astimezone(history.KST).date(),
        observation_time=at, api_key="synthetic", transport=httpx.MockTransport(reply)))
    probe.live_source = True
    return probe


def materialize(tmp_path, *, ohlc=True, at=AT):
    probe = original_probe(ohlc=ohlc, at=at)
    value = TypeAdapter(MacroProviderResult).dump_python(
        materialize_night_probe(probe, history_directory=tmp_path, night_end_dates=True), mode="json")
    return probe, value


def summary(value):
    return summarize_night_futures({"observations": [
        {**row, **row["raw_payload"]} for row in value["observations"]
    ]})


def bound_value(probe, value, *, at=AT):
    receipts, bodies, hashes = [], {}, {}
    for index, status in enumerate(probe.date_statuses):
        artifact = status.query_date.isoformat() + ".json"
        bodies[artifact] = probe.source_response_bodies_by_date[status.query_date]
        hashes[artifact] = status.raw_payload_sha256
        receipts.append(dict(run_id="test", acquisition_id="test:night", provider="krx_night_futures",
            artifact=artifact, artifact_sha256=hashes[artifact], http_status=200, outcome="HTTP_RESPONSE",
            requested_at=(at+timedelta(seconds=index)).isoformat(),
            received_at=(at+timedelta(seconds=index+1)).isoformat(),
            request=dict(method="GET", route=KRX_FUTURES_DAILY_URL,
                params={"basDd":status.query_date.strftime("%Y%m%d")})))
    return dict(observed_at=at.isoformat(), original_run_id="test", original_acquisition_id="test:night",
        original_receipts=receipts, source_hashes=hashes, value=value, value_sha256=digest(value)), bodies


def actual_market(probe, value):
    packet, seed, graph = parts()
    night, _ = bound_value(probe, value)
    seed["run_acquisitions"]["night"] = night["value_sha256"]
    graph["night"] = packet["night_and_publication_context"] = night
    reseal(packet, seed, graph)
    projected = project((packet, seed, graph))
    output = decision(projected["context"])
    message = renderer.market_message(SimpleNamespace(market="us", gen="C52-synthetic",
        projected={"us":projected}, markets={"us":output}, fresh_stocks={}))
    return projected, message


@pytest.mark.parametrize("missing", [("weekly",), ("monthly",), ("weekly", "monthly")])
def test_empty_period_does_not_remove_valid_daily_pair(tmp_path, monkeypatch, missing):
    session_dates = history._session_dates
    def calendar(start, end, **kwargs):
        period = "weekly" if (end-start).days == 6 else "monthly"
        return () if period in missing else session_dates(start, end, **kwargs)
    monkeypatch.setattr(history, "_session_dates", calendar)
    probe, value = materialize(tmp_path)
    raw = value["observations"][0]["raw_payload"]
    frames = raw["night_timeframes"]
    assert frames["daily"]["close"] == raw["night_close"] == 101
    assert frames["daily"]["return_pct"] == 1
    assert frames["unavailable_timeframes"] == {
        name:f"same_contract_{name}_constituents_unavailable" for name in missing}
    assert all((frames[name] is None) == (name in missing) for name in ("weekly", "monthly"))
    item = summary(value).items[0]
    assert len(night_futures_timeframe_facts(item)) == 3-len(missing)
    projected, message = actual_market(probe, value)
    official = [claim for claim in projected["context"]["numeric_catalog"]["claims"]
                if claim["claim_type"] == "OFFICIAL_NIGHT"]
    assert len(official) == 1
    assert "한국 야간선물" in message["text"] and "종가 101.00" in message["text"]
    for name, label in (("weekly", "주봉"), ("monthly", "월봉")):
        if name in missing:
            assert label+": 자료 부족 (동일 만기 이력 미확보)" in message["text"]
            assert not any("night_futures:"+name in component["source_fact_ref"]
                for component in official[0]["components"])


def test_complete_timeframes_keep_existing_wire_shape(tmp_path):
    _, value = materialize(tmp_path)
    raw = value["observations"][0]["raw_payload"]
    frames = raw["night_timeframes"]
    assert frames["weekly"] is not None and frames["monthly"] is not None
    assert "unavailable_timeframes" not in frames and "night_price_basis" not in raw
    assert "night_price_basis" not in night_futures_context_row(summary(value).items[0])
    assert history.KrxNightTimeframes.model_validate(frames).model_dump(mode="json") == frames


def test_unexpected_aggregate_error_is_not_disguised_as_missing_history(tmp_path, monkeypatch):
    def invalid(**kwargs):
        raise ValueError("unexpected_history_conflict")
    monkeypatch.setattr(history, "_aggregate", invalid)
    with pytest.raises(ValueError, match="unexpected_history_conflict"):
        materialize(tmp_path)


@pytest.mark.parametrize("change", ["missing_reason", "unavailable_with_frame"])
def test_optional_period_absence_cannot_be_ambiguous(tmp_path, change):
    _, value = materialize(tmp_path)
    frames = value["observations"][0]["raw_payload"]["night_timeframes"]
    if change == "missing_reason":
        frames["weekly"] = None
    else:
        frames["unavailable_timeframes"] = {"weekly":"same_contract_weekly_constituents_unavailable"}
    with pytest.raises(ValueError, match="night_timeframe_absence_reason_mismatch"):
        history.KrxNightTimeframes.model_validate(frames)


def test_close_pair_without_ohlc_reaches_real_market_renderer(tmp_path):
    probe, value = materialize(tmp_path, ohlc=False)
    before = deepcopy(value)
    raw = value["observations"][0]["raw_payload"]
    assert raw["night_timeframes"] is None
    assert raw["night_price_basis"] == history.KRX_NIGHT_CLOSE_PAIR_ONLY
    assert raw["night_close"] == 101 and raw["regular_close"] == 100
    assert not night_futures_timeframe_facts(summary(value).items[0])
    projected, message = actual_market(probe, value)
    official = [claim for claim in projected["context"]["numeric_catalog"]["claims"]
                if claim["claim_type"] == "OFFICIAL_NIGHT"]
    assert len(official) == 1
    assert "일별 종가: 101.00 · +1.00pt (+1.00%)" in message["text"]
    assert "직전 정규장(2026-09-23) 종가 100.00 대비" in message["text"]
    assert "주봉: 자료 부족" in message["text"] and "월봉: 자료 부족" in message["text"]
    assert "시가" not in official[0]["rendered_text"]
    assert value == before


@pytest.mark.parametrize("change", ["marker", "raw_id", "date", "arithmetic", "expired", "malformed_frame"])
def test_close_only_preserves_original_pair_requirements(tmp_path, change):
    _, value = materialize(tmp_path, ohlc=False)
    row = json.loads(json.dumps(night_futures_context_row(summary(value).items[0]), default=str))
    if change == "marker": row.pop("night_price_basis")
    elif change == "raw_id": row["reference_source_record_id"] = "another-contract"
    elif change == "date": row["session_date"] = "2026-09-25"
    elif change == "arithmetic": row["change_pct"] = 2
    elif change == "expired": row["contract_maturity"] = "2026-08"
    else: row["night_timeframes"] = {"daily":{"close":101}}
    gate = night_market_eligibility(row, market="us", assessment_date="2026-09-27",
        completed_session_date="2026-09-25")
    assert not gate["eligible"], gate


def test_close_only_sealed_replay_reproduces_original_materialization(tmp_path):
    from app.services.production_source_context import POLICY
    probe, value = materialize(tmp_path, ohlc=False)
    night, bodies = bound_value(probe, value)
    replayed = replay_night(receipts=night["original_receipts"], bodies=bodies,
        body_hashes=night["source_hashes"], observed_at=AT, run_id="test", acquisition_id="test:night",
        expected_value_sha256=digest(value), policy=POLICY, run_started_at=AT,
        acquisition_cutoff=AT+timedelta(minutes=2), night_end_dates=True)
    assert replayed["value"] == value and replayed["network_calls"] == 0
