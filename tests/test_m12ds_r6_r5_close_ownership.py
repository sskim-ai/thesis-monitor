import asyncio
from copy import deepcopy
from datetime import date, datetime
import json

import pytest

from scripts.m12ds_r6_r5_close_ownership import (
    cross_context_alignment,
    later_historical_comparison,
    quote_observation,
    review_cutoff,
)
from scripts.m12ds_r6_r5_cutoff_observer import plan, window_gate, observe, sample
from tests.test_m12ds_r6_r4_kiwoom_finality import daily, envelope, mutate_payload, route, universe


def sample_three(symbol="SPY", at="2026-09-23T18:00:00+09:00", *, older=False):
    adjusted = daily(symbol, at=at)
    mutate_payload(
        adjusted,
        lambda p: p["result_list"][1].update(
            open_pric="90", high_pric="94", low_pric="89", cur_prc="92"
        ),
    )
    raw = deepcopy(adjusted)
    raw["request"]["upd_stkpc_tp"] = "0"
    values = (
        dict(pre_open_pric="90", pre_high_pric="94", pre_low_pric="89", base_close_pric="92")
        if older
        else dict(
            pre_open_pric="100", pre_high_pric="104", pre_low_pric="99", base_close_pric="102"
        )
    )
    q = envelope(
        dict(
            stk_cd=symbol,
            stex_tp="NY",
            curr_unit="USD",
            cur_prc="-101",
            pred_pre="9" if older else "-1",
            flu_rt="-0.98",
            **values,
        ),
        api="usa20100",
        symbol=symbol,
        at=at,
    )
    return q, raw, adjusted


def test_premarket_full_ohlc_alignment_is_not_production_authority():
    q, raw, adj = sample_three()
    receipt = cross_context_alignment(q, raw, adj, route())
    assert receipt["status"] == "EXACT_NUMERIC_ALIGNMENT"
    assert receipt["relation"] == "TARGET_VALUES"
    assert receipt["matched_dated_row"] == "2026-09-22"
    assert receipt["quote"]["current_price"] == "101"
    assert receipt["quote"]["provider_session_date"] is None
    assert receipt["provider_session_owner"] == "NOT_PROVEN_BY_NUMERIC_MATCH"
    assert not receipt["production_authority"] and not receipt["cutoff_proven"]


def test_afterhours_base_close_cannot_be_renamed_target_day():
    q, raw, adj = sample_three(at="2026-09-23T08:05:10+09:00", older=True)
    receipt = cross_context_alignment(q, raw, adj, route())
    assert receipt["relation"] == "PREVIOUS_SESSION_VALUES"
    assert receipt["matched_dated_row"] == "2026-09-21"
    assert receipt["target"] == "2026-09-22"
    assert not receipt["production_authority"]


@pytest.mark.parametrize(
    "mutation",
    [
        "currency",
        "symbol",
        "exchange",
        "api",
        "date_rollover",
        "hash",
        "nonfinite",
        "missing",
        "negative_base",
    ],
)
def test_quote_negative_controls(mutation):
    q, _, _ = sample_three()
    if mutation == "currency":
        mutate_payload(q, lambda p: p.update(curr_unit="KRW"))
    elif mutation == "symbol":
        mutate_payload(q, lambda p: p.update(stk_cd="OTHER"))
    elif mutation == "exchange":
        q["request"]["stex_tp"] = "NA"
    elif mutation == "api":
        q["api_id"] = "usa06012"
    elif mutation == "date_rollover":
        q["received_at"] = "2026-09-24T18:00:00+09:00"
    elif mutation == "hash":
        q["raw_body"] += " "
    elif mutation == "nonfinite":
        mutate_payload(q, lambda p: p.update(base_close_pric="NaN"))
    elif mutation == "missing":
        mutate_payload(q, lambda p: p.pop("pre_low_pric"))
    else:
        mutate_payload(q, lambda p: p.update(base_close_pric="-102"))
    with pytest.raises((KeyError, ValueError)):
        quote_observation(q, route())


@pytest.mark.parametrize("mutation", ["basis", "ohl_only", "delta", "ambiguous"])
def test_value_relation_requires_unique_full_tuple_and_basis(mutation):
    q, raw, adj = sample_three()
    if mutation == "basis":
        mutate_payload(adj, lambda p: p["result_list"][0].update(cur_prc="103"))
    elif mutation == "ohl_only":
        mutate_payload(q, lambda p: p.update(base_close_pric="103"))
    elif mutation == "delta":
        mutate_payload(q, lambda p: p.update(pred_pre="0"))
    else:
        for e in (raw, adj):
            mutate_payload(
                e,
                lambda p: p["result_list"][1].update(
                    {k: v for k, v in p["result_list"][0].items() if k != "dt"}
                ),
            )
    receipt = cross_context_alignment(q, raw, adj, route())
    assert receipt["status"] == "UNOWNED_ALIGNMENT" and receipt["matched_dated_row"] is None


def test_explicit_raw_request_required_not_same_adjusted_payload_twice():
    q, raw, adj = sample_three()
    with pytest.raises(ValueError):
        cross_context_alignment(q, adj, adj, route())
    q["started_at"] = q["received_at"] = "2026-09-24T18:00:00+09:00"
    with pytest.raises(ValueError):
        cross_context_alignment(q, raw, adj, route())


def test_cutoff_requires_full_universe_and_actual_quote_minute():
    routes, _ = universe()
    qs, raws, ds = {}, {}, {}
    for s in routes:
        q, r, d = sample_three(s, at="2026-09-23T08:05:10+09:00")
        ds[s] = d
        if s in ("SPY", "SOXX", "XLC"):
            qs[s], raws[s] = q, r
    receipt = review_cutoff(ds, raws, qs, routes, cutoff="2026-09-23T08:05:00+09:00")
    assert receipt["availability"]["count"] == 22
    assert receipt["final_decision"] is None
    qs["SPY"]["received_at"] = "2026-09-23T08:06:00+09:00"
    with pytest.raises(ValueError):
        review_cutoff(ds, raws, qs, routes, cutoff="2026-09-23T08:05:00+09:00")
    qs.pop("SPY")
    with pytest.raises(ValueError):
        review_cutoff(ds, raws, qs, routes, cutoff="2026-09-23T08:05:00+09:00")


def test_later_historical_equality_is_qualification_only_and_keeps_prior_drift():
    early = daily(at="2026-09-23T08:05:10+09:00")
    late = daily(at="2026-09-23T18:00:00+09:00")
    receipt = later_historical_comparison(early, late, route())
    assert receipt["close_equal"] and not receipt["prior_drift_erased"]
    assert not receipt["production_lookahead_dependency"] and not receipt["production_authority"]
    mutate_payload(early, lambda p: p["result_list"][0].update(cur_prc="103"))
    receipt = later_historical_comparison(early, late, route())
    assert not receipt["close_equal"]
    late["started_at"] = late["received_at"] = "2026-09-23T08:10:00+09:00"
    with pytest.raises(ValueError):
        later_historical_comparison(early, late, route())


def test_plan_has_bounded_readonly_calls_and_no_automation():
    routes, _ = universe()
    p = plan(date(2026, 9, 24), routes)
    assert p["target"] == "2026-09-23"
    assert p["request_count_per_sample"] == 28
    assert p["maximum_cutoff_data_calls"] == 112 and p["maximum_later_data_calls"] == 28
    assert p["model_calls"] == p["sends"] == p["retries"] == 0
    assert not p["scheduler_registration"] and not p["authority_promotion"]
    assert set(r["api_id"] for r in p["requests"]) == {"usa06012", "usa20100"}


@pytest.mark.parametrize("at", ["2026-09-23T12:00:00+09:00", "2026-09-23T08:08:00+09:00"])
def test_delayed_comparison_rejects_non_cutoff_sample(at):
    with pytest.raises(ValueError, match="actual_configured_cutoff"):
        later_historical_comparison(daily(at=at), daily(at="2026-09-23T18:00:00+09:00"), route())


def test_delayed_comparison_rejects_response_outside_acquisition_minute():
    early = daily(at="2026-09-23T08:05:30+09:00")
    early["received_at"] = "2026-09-23T08:06:01+09:00"
    with pytest.raises(ValueError, match="actual_configured_cutoff"):
        later_historical_comparison(early, daily(at="2026-09-23T18:00:00+09:00"), route())


def test_preflight_missed_and_wrong_window_fail_before_network(tmp_path):
    routes, _ = universe()
    day = date(2000, 1, 1)
    with pytest.raises(ValueError):
        asyncio.run(
            observe(
                day,
                routes,
                tmp_path / "out",
                mode="cutoff",
                env_file=tmp_path / "missing",
                frozen_plan=plan(day, routes),
            )
        )
    assert not (tmp_path / "out").exists()
    with pytest.raises(ValueError):
        window_gate(
            datetime.fromisoformat("2026-09-23T18:00:00+09:00"), day=date(2026, 9, 24), mode="later"
        )
    window_gate(
        datetime.fromisoformat("2026-09-24T18:00:00+09:00"), day=date(2026, 9, 24), mode="later"
    )


def test_observer_raw_payloads_are_never_retried_or_replaced(tmp_path, monkeypatch):
    from scripts import m12ds_r6_r5_cutoff_observer as observer

    calls = []

    async def fetch(client, token, item):
        calls.append(item["symbol"])
        if item["symbol"] == "SPY":
            raise ValueError("synthetic failure")
        return daily("XLC")

    async def sleep(seconds):
        pass

    monkeypatch.setattr(observer, "fetch", fetch)
    monkeypatch.setattr(observer.asyncio, "sleep", sleep)
    items = [dict(symbol=s, mode="adjusted") for s in ("SPY", "XLC")]
    collected, errors = asyncio.run(sample(None, None, items, tmp_path))
    assert calls == ["SPY", "XLC"] and len(errors) == 1
    assert list(collected) == ["XLC-adjusted"]
    assert json.loads((tmp_path / "XLC-adjusted.json").read_text()) == collected["XLC-adjusted"]
