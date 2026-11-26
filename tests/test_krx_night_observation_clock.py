"""The probe and the US consumer must use the same instant. Synthetic HTTP only."""
import asyncio
from datetime import date, datetime, timedelta
from hashlib import sha256

import httpx
import pytest
from pydantic import TypeAdapter

from app.jobs.probe_krx_night_futures import fetch_live_probe
from app.macro.providers.base import MacroProviderResult
from app.macro.providers.krx import materialize_night_probe
from app.services.canonical_market_projection import project_optional_night
from tests.test_c52_night_daily import bound_value
from tests.test_krx_night_futures_probe import _row


def night_input(tmp_path, at, last_returned):
    def reply(request):
        day = request.url.params["basDd"]
        rows = [] if not last_returned or day > last_returned else [
            _row("KOSPI 200 선물", "정규", "A016C000", "코스피200 F 202612", "100", day),
            _row("KOSPI 200 선물", "야간", "A016C000", "코스피200 F 202612 야간", "101", day, "1"),
        ]
        return httpx.Response(200, json={"OutBlock_1": rows})

    probe = asyncio.run(fetch_live_probe(observation_time=at, api_key="synthetic",
        transport=httpx.MockTransport(reply), max_lookback_days=4))
    assert probe.fetched_at == at and probe.queried_dates[0] == date(2026, 11, 27)
    value = TypeAdapter(MacroProviderResult).dump_python(
        materialize_night_probe(probe, history_directory=tmp_path, night_end_dates=True), mode="json")
    night, _ = bound_value(probe, value, at=at)
    seed = dict(parent_run_id=night["original_run_id"], started_at=at.isoformat(),
        run_acquisitions={"night": night["value_sha256"]})
    return night, seed


@pytest.mark.parametrize("instant,last_returned,expected,state", [
    ("2026-11-26T15:47:07.017313Z", "20261125", "2026-11-26", "UNAVAILABLE_BEFORE_FINALITY"),
    ("2026-11-27T05:59:59.999999+09:00", "20261127", "2026-11-26", "UNAVAILABLE_BEFORE_FINALITY"),
    ("2026-11-27T06:00:00+09:00", "20261127", "2026-11-27", "AVAILABLE_FINAL"),
    ("2026-11-27T06:00:00+09:00", "20261125", "2026-11-27", "UNAVAILABLE_NO_CURRENT_FINAL_ROW"),
    ("2026-11-27T06:00:00+09:00", None, "2026-11-27", "UNAVAILABLE_NO_CURRENT_FINAL_ROW"),
])
def test_observed_clock_to_optional_market_coverage(tmp_path, instant, last_returned, expected, state):
    at = datetime.fromisoformat(instant)
    night, seed = night_input(tmp_path, at, last_returned)
    telemetry = night["value"]["telemetry"]
    assert telemetry["expected_latest_session_date"] == telemetry["expected_reference_date"] == expected
    eligible, receipt = project_optional_night(night, seed=seed, cutoff=at+timedelta(minutes=1))
    assert receipt["state"] == state and receipt["optional"] and receipt["coverage_resolved"]
    assert receipt["current_consumer_eligible_count"] == len(eligible) == int(state == "AVAILABLE_FINAL")
    assert not receipt["stale_promoted"]
    if not eligible:
        assert receipt["value"] is None


def test_unchanged_seal_rejects_edited_expected_date(tmp_path):
    at = datetime.fromisoformat("2026-11-27T00:47:07+09:00")
    night, seed = night_input(tmp_path, at, "20261125")
    night["value"]["telemetry"]["expected_reference_date"] = "2026-11-27"
    with pytest.raises(ValueError, match="night_authority_mismatch"):
        project_optional_night(night, seed=seed, cutoff=at+timedelta(minutes=1))


def test_exact_probe_uses_receipt_instant_not_query_day_at_eight():
    received = datetime.fromisoformat("2026-11-26T15:47:07.017313Z")
    def reply(request):
        day = request.url.params["basDd"]
        row = _row("KOSPI 200 선물", "정규", "A016C000", "코스피200 F 202612", "100", day)
        return httpx.Response(200, json={"OutBlock_1": [row]})

    class Observer:
        async def get(self, client, url, *, params, response_secrets):
            response = await client.get(url, params=params)
            response.extensions["unified_source_receipt"] = ("test", {
                "received_at": received.isoformat(), "artifact_sha256": sha256(response.content).hexdigest()})
            return response

    probe = asyncio.run(fetch_live_probe(observation_time=received-timedelta(seconds=1),
        exact_dates=(date(2026, 11, 26),), api_key="synthetic", source_observer=Observer(),
        transport=httpx.MockTransport(reply), hard_stop_on_error=True))
    assert probe.fetched_at == received and probe.finality_valid is False
    assert probe.expected_reference_date == probe.expected_latest_session_date == date(2026, 11, 26)
