from copy import deepcopy
import asyncio
from datetime import datetime
from hashlib import sha256
import json

import pytest

from app.macro.providers.market import MARKET_SYMBOLS
from scripts.m12ds_r6_r4_kiwoom_finality import (
    CONTRACT,
    cutoff_attempt,
    daily_observation,
    daily_request,
    extended_hours_finality,
    macro_information_block,
    qualified_universe,
    route_from_gateway,
    validate_routes,
)
from scripts.m12ds_r6_r4_cutoff_observer import load_routes, observe, plan
from tests.test_m12ds_r6_r3_source_qualification import macro


def route(symbol="SPY"):
    return dict(
        symbol=symbol,
        exchange="NY",
        security_identity=dict(code=symbol, exchange="NY"),
        identity_artifact_sha256="a" * 64,
        gateway_response_sha256="b" * 64,
    )


def envelope(payload, *, api="usa06012", symbol="SPY", at="2026-09-23T17:10:00+09:00"):
    raw = json.dumps(dict(return_code=0, **payload))
    return dict(
        api_id=api,
        endpoint="/api/us/chart" if api == "usa06012" else "/api/us/mrkcond",
        request=daily_request(route(symbol))
        if api == "usa06012"
        else dict(stex_tp="NY", stk_cd=symbol),
        started_at=at,
        received_at=at,
        raw_body=raw,
        raw_response_sha256=sha256(raw.encode()).hexdigest(),
        http_status=200,
    )


def daily(symbol="SPY", at="2026-09-23T17:10:00+09:00"):
    return envelope(
        dict(
            result_list=[
                dict(
                    dt=d,
                    open_pric="100",
                    high_pric="104",
                    low_pric="99",
                    cur_prc="102",
                    acc_trde_qty="1000",
                )
                for d in ("20260922", "20260921")
            ]
        ),
        symbol=symbol,
        at=at,
    )


def mutate_payload(e, mutation):
    p = json.loads(e["raw_body"])
    mutation(p)
    e["raw_body"] = json.dumps(p)
    e["raw_response_sha256"] = sha256(e["raw_body"].encode()).hexdigest()


def cross_context():
    d = [daily(at="2026-09-23T17:10:00+09:00"), daily(at="2026-09-23T17:12:00+09:00")]
    q = [
        envelope(dict(stk_cd="SPY", stex_tp="NY", cur_prc=v), api="usa20100", at=at)
        for v, at in [("103", "2026-09-23T17:10:10+09:00"), ("103.1", "2026-09-23T17:11:50+09:00")]
    ]
    return d, q


def test_routing_comes_from_successful_gateway_not_default_guess():
    e = dict(
        http_status=200,
        endpoint="/ohlcv",
        request_parameters=dict(symbol="SPY", market="US"),
        raw_response_sha256="f" * 64,
        response=dict(
            meta=dict(provider="kiwoom"),
            resolved_symbol=dict(
                code="SPY", market="US", exchange="NY", matched_by="us_stock_list_code"
            ),
        ),
    )
    assert route_from_gateway(e, symbol="SPY", artifact_sha256="e" * 64)["exchange"] == "NY"
    e["response"]["resolved_symbol"]["matched_by"] = "us_ticker"
    with pytest.raises(ValueError):
        route_from_gateway(e, symbol="SPY", artifact_sha256="e" * 64)
    e["http_status"] = 502
    with pytest.raises(ValueError):
        route_from_gateway(e, symbol="SPY", artifact_sha256="e" * 64)


@pytest.mark.parametrize(
    "mutation",
    [
        "hash",
        "quote",
        "route",
        "basis",
        "currency",
        "status",
        "time",
        "missing_date",
        "duplicate",
        "stale",
        "future",
        "enclosure",
    ],
)
def test_daily_negative_controls(mutation):
    e = daily()
    if mutation == "hash":
        e["raw_body"] += " "
    elif mutation == "quote":
        e.update(api_id="usa20100", endpoint="/api/us/mrkcond")
    elif mutation == "route":
        e["request"]["stex_tp"] = "NA"
    elif mutation == "basis":
        e["request"]["upd_stkpc_tp"] = "invalid"
    elif mutation == "currency":
        e["request"]["exrt_appl_tp"] = "1"
    elif mutation == "status":
        e["http_status"] = 503
    elif mutation == "time":
        e["started_at"] = "2026-09-23T17:10:00"
    elif mutation == "missing_date":
        mutate_payload(e, lambda p: p["result_list"][0].pop("dt"))
    elif mutation == "duplicate":
        mutate_payload(e, lambda p: p["result_list"].append(p["result_list"][0]))
    elif mutation == "stale":
        mutate_payload(e, lambda p: p["result_list"].pop(0))
    elif mutation == "future":
        mutate_payload(e, lambda p: p["result_list"][0].update(dt="20260924"))
    else:
        mutate_payload(e, lambda p: p["result_list"][0].update(cur_prc="999"))
    with pytest.raises((ValueError, KeyError)):
        daily_observation(e, route())


def test_completed_pair_does_not_need_next_day_or_quote():
    before = daily_observation(daily(), route())
    assert before["pair"][0]["date"] == "2026-09-22"
    assert not before["current_direction_eligible"]
    e = daily()
    mutate_payload(
        e, lambda p: p["result_list"].insert(0, dict(p["result_list"][0], dt="20260923"))
    )
    after = daily_observation(e, route())
    assert after["pair"] == before["pair"]
    assert after["excluded_provisional_dates"] == ["2026-09-23"]


def test_observed_movement_and_unchanged_daily_is_scoped_not_global():
    d, q = cross_context()
    receipt = extended_hours_finality(d, q, route())
    assert receipt["contract"] == CONTRACT and receipt["status"] == "PASS"
    assert receipt["scope"] == "OBSERVED_SYMBOL_SESSION_ONLY"
    assert not receipt["current_direction_eligible"] and not receipt["cutoff_proven"]


@pytest.mark.parametrize(
    "mutation",
    [
        "unchanged_quote",
        "daily_mutation",
        "wrong_quote",
        "non_extended",
        "unbracketed",
        "basis_mismatch",
    ],
)
def test_finality_requires_positive_evidence(mutation):
    d, q = cross_context()
    if mutation == "unchanged_quote":
        mutate_payload(q[1], lambda p: p.update(cur_prc="103"))
    elif mutation == "daily_mutation":
        mutate_payload(d[1], lambda p: p["result_list"][0].update(cur_prc="103"))
    elif mutation == "wrong_quote":
        mutate_payload(q[1], lambda p: p.update(stk_cd="QQQ"))
    elif mutation == "non_extended":
        q[1]["started_at"] = q[1]["received_at"] = "2026-09-23T14:00:00+09:00"
    elif mutation == "unbracketed":
        d[1]["started_at"] = d[1]["received_at"] = q[0]["started_at"]
    else:
        d[1]["request"]["upd_stkpc_tp"] = "0"
    with pytest.raises(ValueError):
        extended_hours_finality(d, q, route())


def universe():
    routes = {s: route(s) for s in MARKET_SYMBOLS}
    envelopes = {s: daily(s, at="2026-09-23T08:05:10+09:00") for s in routes}
    return routes, envelopes


def test_actual_cutoff_is_not_afternoon_or_group_mtime():
    routes, envelopes = universe()
    cutoff = "2026-09-23T08:05:00+09:00"
    receipt = cutoff_attempt(envelopes, routes, cutoff=cutoff)
    assert receipt["count"] == 22 and not receipt["finality_proven"]
    envelopes["SPY"] = daily()
    with pytest.raises(ValueError):
        cutoff_attempt(envelopes, routes, cutoff=cutoff)


@pytest.mark.parametrize(
    "mutation",
    ["missing_xlc", "extra", "wrong_route", "late_response", "wrong_slot", "mixed_basis"],
)
def test_full_cutoff_fail_closed(mutation):
    routes, envelopes = universe()
    cutoff = "2026-09-23T08:05:00+09:00"
    if mutation == "missing_xlc":
        envelopes.pop("XLC")
    elif mutation == "extra":
        routes["EXTRA"] = route("EXTRA")
    elif mutation == "wrong_route":
        routes["SPY"]["exchange"] = "NA"
    elif mutation == "late_response":
        envelopes["SPY"]["received_at"] = "2026-09-23T08:06:00+09:00"
    elif mutation == "wrong_slot":
        cutoff = "2026-09-23T08:08:00+09:00"
    else:
        envelopes["SPY"]["request"]["upd_stkpc_tp"] = "0"
    with pytest.raises(ValueError):
        cutoff_attempt(envelopes, routes, cutoff=cutoff)


def test_final_universe_exact_binding_no_spy_extrapolation_and_stable_sector_tie_break():
    routes, envelopes = universe()
    cutoff = cutoff_attempt(envelopes, routes, cutoff="2026-09-23T08:05:00+09:00")
    observations = cutoff["observations"]
    proofs = {
        s: dict(
            contract=CONTRACT,
            status="PASS",
            symbol=s,
            basis=o["basis"],
            session_date=o["pair"][0]["date"],
            daily_source_hashes=[o["source_sha256"]],
        )
        for s, o in observations.items()
    }
    result = qualified_universe(observations, proofs, cutoff)
    assert result["top3"] == result["bottom3"]
    assert [r["symbol"] for r in result["top3"]] == ["XLB", "XLC", "XLE"]
    with pytest.raises(ValueError):
        qualified_universe(observations, {"SPY": proofs["SPY"]}, cutoff)
    wrong = deepcopy(observations)
    wrong["SPY"]["pair"][0]["close"] = "200"
    with pytest.raises(ValueError):
        qualified_universe(wrong, proofs, cutoff)
    proofs["SPY"]["daily_source_hashes"] = ["c" * 64]
    with pytest.raises(ValueError):
        qualified_universe(observations, proofs, cutoff)


def test_manual_observer_plan_hash_and_no_production_side_effects(tmp_path):
    routes, _ = universe()
    validate_routes(routes)
    p = tmp_path / "routes.json"
    p.write_text(json.dumps(dict(routes=routes)))
    assert load_routes(p, sha256(p.read_bytes()).hexdigest()) == routes
    with pytest.raises(ValueError):
        load_routes(p, "a" * 64)
    result = plan(datetime(2026, 9, 24).date(), routes)
    assert result["max_daily_calls"] == 88 and result["retries"] == 0
    assert result["model_calls"] == result["sends"] == result["scheduler_mutations"] == 0
    assert len(result["cutoffs"]) == 4 and not result["finality_promotion"]


def test_observer_rejects_old_date_before_network(tmp_path):
    routes, _ = universe()
    with pytest.raises(ValueError, match="start_manually"):
        asyncio.run(
            observe(
                datetime(2000, 1, 1).date(),
                routes,
                tmp_path / "output",
                env_file=tmp_path / "absent",
            )
        )
    assert not (tmp_path / "output").exists()


def test_unconsumed_old_adjustment_marker_does_not_reject_current_pair():
    e = daily()
    mutate_payload(
        e,
        lambda p: p["result_list"].append(
            dict(p["result_list"][0], dt="20260501", upd_stkpc_tp="1f")
        ),
    )
    assert len(daily_observation(e, route())["pair"]) == 2
    mutate_payload(e, lambda p: p["result_list"][0].update(upd_stkpc_tp="1f"))
    with pytest.raises(ValueError, match="adjustment_basis_mismatch"):
        daily_observation(e, route())


def test_lagged_macro_rendered_with_date_without_direction_or_currency_conversion():
    at = datetime.fromisoformat("2026-09-23T16:05:00+09:00")
    block = macro_information_block({"DCOILWTICO": macro()}, as_of=at)
    assert block["text"] == "WTI 64.50 USD/배럴 · 최신 확인값 (기준 2026-09-21)"
    assert not block["current_direction_eligible"] and block["direction_fact_refs"] == []
    bad = macro()
    bad["raw_body"] += " "
    with pytest.raises(ValueError):
        macro_information_block({"DCOILWTICO": bad}, as_of=at)


def test_manual_observer_complete_attempt_stops_without_waiting_later_slots(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from scripts import m12ds_r6_r4_cutoff_observer as observer
    import app.config
    import app.providers.kiwoom_rest_client

    routes, envelopes = universe()
    calls = []
    sleeps = []
    now = datetime.fromisoformat("2026-09-23T08:05:10+09:00")

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz)

    class Owner:
        base_url = "https://api.kiwoom.com"

        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0

        async def _access_token(self, client):
            calls.append("AUTH")
            return "synthetic-token"

    class Client:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == 10

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    async def fetch(client, token, route):
        calls.append(route["symbol"])
        return envelopes[route["symbol"]]

    async def sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(observer, "datetime", Clock)
    monkeypatch.setattr(observer.httpx, "AsyncClient", Client)
    monkeypatch.setattr(observer, "fetch_daily", fetch)
    monkeypatch.setattr(observer.asyncio, "sleep", sleep)
    monkeypatch.setattr(app.providers.kiwoom_rest_client, "KiwoomRestClient", Owner)
    monkeypatch.setattr(
        app.config,
        "Settings",
        lambda **kwargs: SimpleNamespace(
            kiwoom_app_key="fixture",
            kiwoom_secret_key="fixture",
            kiwoom_rest_base_url=Owner.base_url,
        ),
    )
    output = tmp_path / "observer"
    asyncio.run(observe(now.date(), routes, output, env_file=tmp_path / "fixture"))
    result = json.loads((output / "result.json").read_text())
    assert result["status"] == "PASS" and len(result["attempts"]) == 1
    assert calls[0] == "AUTH" and calls[1:] == list(routes)
    assert result["regular_session_finality"] == "NOT_PROMOTED"
    assert result["model_calls"] == result["sends"] == 0
    assert max(sleeps) == 0.6
