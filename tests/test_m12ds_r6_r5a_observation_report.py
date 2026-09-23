from datetime import date, datetime
import json

import pytest

from scripts.m12ds_r6_r5_cutoff_observer import plan, requests
from scripts.m12ds_r6_r5a_observation_report import build_report, changes, request_receipt
from tests.test_m12ds_r6_r4_kiwoom_finality import daily, mutate_payload, route, universe
from tests.test_m12ds_r6_r5_close_ownership import sample_three

CUTOFF = datetime.fromisoformat("2026-09-23T08:05:00+09:00")


def item():
    routes, _ = universe()
    return next(r for r in requests(routes) if r["symbol"] == "SPY" and r["mode"] == "adjusted")


def test_actual_dates_hashes_and_all_timezones_preserved():
    r = request_receipt(item(), daily(at="2026-09-23T08:05:12+09:00"), route(), CUTOFF)
    assert r["strict_valid"] and r["diagnostic_available"]
    assert r["target_row"]["date"] == "2026-09-22"
    assert r["previous_row"]["date"] == "2026-09-21"
    assert r["start_et"] == "2026-09-22T19:05:12-04:00"
    assert r["start_utc"] == "2026-09-22T23:05:12+00:00"
    assert len(r["request_sha256"]) == 64 and not r["production_authority"]


@pytest.mark.parametrize("mutation", ["minute", "hash", "request", "duplicate", "nan", "provider"])
def test_report_never_promotes_invalid_samples(mutation):
    e = daily(at="2026-09-23T08:05:12+09:00")
    if mutation == "minute":
        e["received_at"] = "2026-09-23T08:06:00+09:00"
    elif mutation == "hash":
        e["raw_body"] += " "
    elif mutation == "request":
        e["request"]["stex_tp"] = "ND"
    elif mutation == "duplicate":
        mutate_payload(e, lambda p: p["result_list"].append(p["result_list"][0]))
    elif mutation == "nan":
        mutate_payload(e, lambda p: p["result_list"][0].update(cur_prc="NaN"))
    else:
        mutate_payload(e, lambda p: p.update(return_code=7))
    r = request_receipt(item(), e, route(), CUTOFF)
    assert not r["diagnostic_available"] and not r["production_authority"]
    assert r["status"] == "FAILED"


def test_raw_diagnostic_is_not_strict_ohlc_acceptance():
    e = daily(at="2026-09-23T08:05:12+09:00")
    mutate_payload(e, lambda p: p["result_list"][0].update(cur_prc="105"))
    r = request_receipt(item(), e, route(), CUTOFF)
    assert r["diagnostic_available"] and not r["strict_valid"]
    assert r["strict_error"] == "ohlcv_enclosure_invalid"
    assert not r["production_authority"]


def test_missing_values_are_not_zero_changes():
    assert request_receipt(item(), None, route(), CUTOFF)["status"] == "MISSING"
    assert changes(None, None) == dict(status="UNAVAILABLE", changes=None)


def test_complete_observation_does_not_grant_finality(tmp_path):
    routes, _ = universe()
    frozen = plan(date(2026, 9, 23), routes)
    for cutoff in frozen["cutoffs"]:
        directory = tmp_path / datetime.fromisoformat(cutoff).strftime("%H%M")
        directory.mkdir()
        for r in frozen["requests"]:
            q, raw, adjusted = sample_three(r["symbol"], at=cutoff, older=True)
            e = dict(quote=q, raw=raw, adjusted=adjusted)[r["mode"]]
            (directory / (r["symbol"] + "-" + r["mode"] + ".json")).write_text(json.dumps(e))
    report = build_report(tmp_path, frozen, routes)
    assert report["classification"] == "CUTOFF_OBSERVATION_COMPLETE"
    assert all(w["full22_available"] == 22 for w in report["windows"])
    assert report["final_owner_decision"] is None and not report["production_authority"]
    assert report["windows"][0]["quote_relations"][0]["relation"] == "PREVIOUS_SESSION_VALUES"
    (tmp_path / "0805/SPY-adjusted.json").unlink()
    report = build_report(tmp_path, frozen, routes)
    assert report["classification"] == "CUTOFF_OBSERVATION_PARTIAL"
    spy = next(r for r in report["ohlc_change_matrix"] if r["symbol"] == "SPY")
    assert spy["transitions"][0]["changes"] is None


def test_missed_and_collection_failure_distinct(tmp_path):
    routes, _ = universe()
    frozen = plan(date(2026, 9, 23), routes)
    assert build_report(tmp_path, frozen, routes)["classification"] == "CUTOFF_WINDOW_MISSED"
    (tmp_path / "start.json").write_text("{}")
    assert (
        build_report(tmp_path, frozen, routes)["classification"] == "TECHNICAL_COLLECTION_FAILURE"
    )
    frozen["retries"] = 1
    with pytest.raises(ValueError, match="frozen_plan_mismatch"):
        build_report(tmp_path, frozen, routes)
