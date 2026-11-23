"""Synthetic source replay through the real stock assembler and fact catalog."""

from copy import deepcopy
from datetime import date
from decimal import Decimal
import json

from app.services import unified_stock_owner as owner
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import encoded
from app.services.unified_stock_anomaly_scope import materialize_source_components
from tests.test_unified_stock_owner import freeze_hashes, source as _source_fixture


source = _source_fixture


def _rebind_rows(inputs, changes):
    roles = {role: json.loads(inputs["artifacts"][receipt["normalized_artifact"]])
             for role, receipt in inputs["receipts"].items()}
    changes(roles)
    for role, rows in roles.items():
        receipt = inputs["receipts"][role]
        raw, normalized = encoded({"return_code": 0, "result_list": rows}), encoded(rows)
        inputs["artifacts"][receipt["pages"][0]["artifact"]] = raw
        inputs["artifacts"][receipt["normalized_artifact"]] = normalized
        receipt["pages"][0]["source_sha256"] = sha256_bytes(raw)
        receipt["normalized_sha256"] = sha256_bytes(normalized)
    read = next(r for r in inputs["plan"].reads if r.subject == inputs["ticker"])
    inputs["components"] = materialize_source_components(
        ticker=inputs["ticker"], market=read.market,
        cutoff=date.fromisoformat(read.latest_completed_session),
        observed_at=inputs["plan"].frozen_at.isoformat(), roles=roles)
    freeze_hashes(inputs)


def _assemble_observed(inputs, monkeypatch):
    observed = {}
    analyze = owner.analyze_chart_structure

    def trace(periods, **kwargs):
        observed["periods"] = deepcopy(periods)
        observed["timeframes"] = deepcopy(kwargs["timeframe_contexts"])
        return analyze(periods, **kwargs)

    monkeypatch.setattr(owner, "analyze_chart_structure", trace)
    result = owner.assemble_stock(**inputs)
    stock = result["packet"]["stocks"][0]
    facts = {fact["fact_id"]: fact for fact in stock["fact_catalog"]}
    return result, stock, facts, observed


def test_completed_frames_and_owned_volume_reach_structure_and_source_facts(source, monkeypatch):
    def add_raw_indicator(roles):
        # This provider value is deliberately incompatible with the owned ratio.
        for row in roles["adjusted_daily"]:
            row["VOLUME_RATIO_20"] = 999
    _rebind_rows(source, add_raw_indicator)
    before = deepcopy(source)
    result, stock, facts, observed = _assemble_observed(source, monkeypatch)
    assert result["status"] == "PASS"
    assert source == before

    # September is unfinished on this fixture's September 25 completed session.
    assert any(row["bar_state"] == "PARTIAL" for row in
               source["components"]["analysis_view_finality"]["monthly"]["rows"])
    assert observed["periods"]["monthly"][-1]["date"] == "2026-08-31"
    assert all(row["bar_state"] == "COMPLETE" for rows in observed["periods"].values()
               for row in rows)
    assert stock["chart_context"]["timeframes"]["monthly"]["candle"]["close"] == 11.0
    for tf in ("daily", "weekly", "monthly"):
        frame = facts["chart:" + tf]
        assert frame["as_of_date"] == observed["periods"][tf][-1]["date"]
        assert frame["fields"]["completed_bar_only"] is True
        assert frame["fields"]["evaluation_as_of"] == "2026-09-25"
    assert facts["chart:monthly"]["as_of_date"] != facts["chart:daily"]["as_of_date"]

    feature = next(f for f in stock["technical_context"]["features"]["daily"]["facts"]
                   if f["semantic"] == "volume_ratio_20")
    expected = Decimal("1.019408")  # 499 / mean(480, ..., 499), existing six-place fact.
    assert Decimal(feature["value"]) == expected
    assert observed["timeframes"]["daily"]["volume_ratio_20"] == float(expected)
    assert facts["chart:daily"]["fields"]["volume_ratio_20"] == float(expected)
    assert facts["chart:daily"]["fields"]["indicator_source_semantics"]["volume_ratio_20"] == feature["formula"]
    assert feature["formula"] == "volume / SMA(volume, 20)"


def test_unavailable_owned_volume_is_not_replaced_by_provider_indicator(source, monkeypatch):
    def missing_volume(roles):
        roles["adjusted_daily"][-2]["volume"] = None
        roles["adjusted_daily"][-1]["VOLUME_RATIO_20"] = 999
    _rebind_rows(source, missing_volume)
    _, stock, facts, observed = _assemble_observed(source, monkeypatch)
    assert not any(f["semantic"] == "volume_ratio_20"
                   for f in stock["technical_context"]["features"]["daily"]["facts"])
    assert observed["timeframes"]["daily"]["volume_ratio_20"] is None
    assert "volume_ratio_20" not in facts["chart:daily"]["fields"]


def test_partial_only_timeframe_has_no_completed_fact(source, monkeypatch):
    def partial_month_only(roles):
        roles["adjusted_monthly"] = [row for row in roles["adjusted_monthly"]
                                     if row["date"] >= "2026-09-01"]
    _rebind_rows(source, partial_month_only)
    before = deepcopy(source["artifacts"])
    _, stock, facts, observed = _assemble_observed(source, monkeypatch)
    assert observed["periods"]["monthly"] == []
    assert stock["chart_context"]["timeframes"]["monthly"]["quality"] == "unavailable"
    assert "chart:monthly" not in facts
    assert source["artifacts"] == before


def test_completed_window_does_not_cross_a_previously_unconsumed_bad_row(source, monkeypatch):
    def older_bad_volume(roles):
        # Outside the original monthly tail of 60; inside the tail after the
        # unfinished September rows are excluded. Keep its explicit finality.
        roles["adjusted_monthly"][-61].update(volume=-1, bar_state="COMPLETE")
    _rebind_rows(source, older_bad_volume)
    legacy = {"legacy_local_pivots", "legacy_major_swings_atr", "legacy_boxes"}
    assert all(c["eligible"] for rows in source["components"]["role_consumer_matrix"].values()
               for c in rows if c["consumer"] in legacy)
    before = deepcopy(source["artifacts"])
    _, stock, facts, observed = _assemble_observed(source, monkeypatch)
    assert observed == {}  # The real structure calculator never consumes the widened bad span.
    assert stock["chart_context"]["structure"] == {}
    assert not any(key.startswith("chart:structure:") for key in facts)
    assert source["artifacts"] == before
