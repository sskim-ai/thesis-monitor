"""Synthetic C60 source, selected candidate, numeric rights and wire boundaries."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from app.services import detailed_stock_message_v2 as msg
from app.services import new_buyer_base_contract as base
from app.services import production_message_renderer as renderer
from app.services.entry_candidate_basis import selected_entry_scenario
from app.services.entry_price_basis import scenario_for_fact
from app.services.ohlcv_structure_service import (
    _candidate_scenario, _entry_role, calculate_invalidation, project_entry_scenarios,
)
from app.services.production_monitoring_session import frozen_context_prompt
from app.services.production_model_transport import render_prompt
from app.services.unified_snapshot_contract import digest
from tests import test_c50_chart_statement as fixture
from tests.test_c51_invalidation import bars


def zone(low, high, frame="daily", pivot="2026-10-01"):
    return dict(timeframe=frame, pivot_type="low", pivot_dates=[pivot], pivot_prices=[low],
                zone_low=low, zone_high=high, strength="Strong")


def test_nearer_band_obstacle_and_same_low_identity():
    z = zone(93, 99)
    middle = dict(zone(105, 107, pivot="2026-10-05"), pivot_type="high")
    far = dict(zone(130, 131, pivot="2026-10-09"), pivot_type="high")
    inv = dict(available=True, price=92, status="intact")
    result = _candidate_scenario(z, [z, middle, far], 110, far, inv, {})
    assert (result["current_target"], result["current_rr"], result["band_target"]) == (130, 1.111111, 105)
    assert result["band_target_assumption"] == "HYPOTHETICAL_REAPPROACH"
    for distinct in (zone(93, 100, "weekly"), zone(93, 100, pivot="2026-10-05")):
        other = _candidate_scenario(z, [z, distinct, far], 110, far, inv, {})
        assert not other["band_overlap"] and other["band_target"] == 130
        opposing = dict(distinct, pivot_type="high", entry_role="resistance")
        other = _candidate_scenario(z, [z, opposing, far], 110, far, inv, {})
        assert other["band_overlap"] and "band_target" not in other
        assert other["current_rr"] == result["current_rr"]
    inside = _candidate_scenario(z, [z, middle, far], 106, far, inv, {})
    assert inside["active_obstacle"] and "current_rr" not in inside
    support = dict(zone(104, 107, pivot="2026-10-05"), entry_role="support")
    other = _candidate_scenario(z, [z, support, far], 110, far, inv, {})
    assert not other["active_obstacle"] and not other["band_overlap"]
    assert other["band_reason"] == "INTERMEDIATE_ROLE_UNCONFIRMED"
    assert other["current_rr"] == result["current_rr"]


def test_role_transition_requires_observed_retest_not_location():
    z = dict(zone(9, 11), confirmation_bar="2026-11-16")
    assert _entry_role(z, (), 8)[0] == "unresolved"
    history = bars(("2026-11-17", 8), ("2026-11-18", 8))
    # Use a real subsequent high touching the former support from below.
    from dataclasses import replace
    history[-1] = replace(history[-1], high=10)
    assert _entry_role(z, history, 8)[0] == "resistance"
    assert _entry_role(dict(z, confirmation_bar="2026-11-18"), history, 8)[0] == "unresolved"


def test_v3_original_anchor_projection_and_current_vs_band_targets():
    from decimal import Decimal
    from app.services.price_structure_wave_fibonacci_v3_service import entry_zone_proposals
    from app.services.ai_review_service import _compact_chart_structure

    def raw_zone(identifier, kind, low, high, day):
        pivot = SimpleNamespace(pivot_id=identifier, status="CONFIRMED", timeframe="daily",
            bar_date=day, confirmation_date="2026-11-16", kind=kind, price=Decimal(str(low)))
        src = SimpleNamespace(source_id=identifier, evidence_type="PIVOT", status="CONFIRMED")
        value = SimpleNamespace(zone_id="v3:"+identifier, sources=[src], low=Decimal(str(low)),
            high=Decimal(str(high)), center=(Decimal(str(low))+Decimal(str(high)))/2,
            confirmation_quality=Decimal(1), structural_importance=11,
            current_role="SUPPORT" if kind == "LOW" else "RESISTANCE")
        return pivot, value
    pv, sv = raw_zone("p1", "LOW", 9, 10, "2026-11-10")
    pr, sr = raw_zone("p2", "HIGH", 12, 12.5, "2026-11-11")
    result = SimpleNamespace(pivots={"daily":[pv,pr]}, sr_maps={"daily":[sv,sr]},
        deterministic_sr_maps={}, timeframe_zone_maps={})
    proposals = entry_zone_proposals(result)
    assert len(proposals) == 2 and all(p["price_anchor_refs"] for p in proposals)
    chart = fixture.chart_input("daily")
    original = dict(as_of_date=fixture.SESSION, price_basis="adjusted_close",
        atr={"daily":{"value":1,"available":True}}, all_zones=[
            dict(zone(16,17,pivot="2026-11-12"),pivot_type="high")])
    periods = {"daily":[dict(date=fixture.SESSION,open=10,high=10.5,low=9.5,close=10,volume=100)]}
    quote = dict(value=10,currency="USD",basis="adjusted_close",as_of=fixture.SESSION)
    projected = project_entry_scenarios(original, periods=periods, timeframes=chart["timeframes"],
        quote=quote, session=fixture.SESSION, v3_proposals=proposals)
    assert len(projected["entry_supports"]) == 1
    selected = projected["entry_supports"][0]
    assert selected["source"] == "price_structure_wave_fibonacci_v3"
    assert selected["entry_scenario"]["current_target"] == 12
    assert projected["entry_resistances"][0]["zone_low"] == 12
    chart["structure"] = _compact_chart_structure(projected)
    from app.services.ai_review_service import _chart_facts
    from app.services.cross_market_decision_engine_service import canonical_fact_statement
    support = next(f for f in _chart_facts(chart,"USD") if f["fact_type"]=="chart_support_zone")
    assert support["source"] == "price_structure_wave_fibonacci_v3"
    assert json.loads(canonical_fact_statement(support)) == support["fields"]


@pytest.mark.parametrize("frame,confirmation", [("daily", "2026-11-23"), ("weekly", "2026-11-16")])
def test_only_post_confirmation_bars_count(frame, confirmation):
    result = calculate_invalidation(dict(zone(9, 11, frame), confirmation_bar=confirmation),
        current_price=7, daily_atr=2, weekly_atr=2, daily_bars=bars(("2026-11-20", 7), ("2026-11-23", 7)),
        weekly_bars=bars(("2026-11-20", 7)), volume_ratio=1, supply_classification="mixed")
    assert not result["hard_daily"] and not result["hard_weekly"] and result["trigger_dates"] == []
    assert result["price"] == 8 and result["price"] > 7


@pytest.mark.parametrize("low,kind", [(96, "DISPLAYABLE"), (98.661, "BELOW_DISPLAY_PRECISION"), (99, "EMPTY")])
def test_price_fact_has_inward_numbers_not_exactness_claims(low, kind):
    z = dict(zone(low, 101), entry_scenario=dict(chart_only=True, invalidation=93, band_target=110))
    value = scenario_for_fact(z, "USD")
    assert value["rr2_intersection"] == kind and value["rr2_ceiling_inward"] == 98.66
    assert ("rr2_low" in value) == (kind == "DISPLAYABLE")
    assert json.loads(json.dumps(value)) == value


def test_b_wire_is_lossless_and_old_prompt_unchanged():
    ctx = {"XYZ": {"native_technical_context": {"comparison_version": 1}, "evidence": ["one", "two"]}}
    text = frozen_context_prompt("pass-b", "prefix", ctx)
    legacy = "prefix\nFROZEN_CONTEXT:\n" + json.dumps(ctx, ensure_ascii=False, sort_keys=True) + "\n"
    assert len(text) < len(legacy) and frozen_context_prompt("pass-a", "prefix", ctx) == legacy
    assert render_prompt(dict(prompt=text, input=ctx, response_schema={}), "B") == text.encode()


@pytest.mark.parametrize("market", ["us", "kr"])
@pytest.mark.parametrize("v3", [False, True])
def test_selected_source_scenario_to_renderer_and_denied_number(monkeypatch, market, v3):
    chart = fixture.chart_input("daily")
    sc = dict(chart_only=True, reference_price=10, invalidation=7.846774, current_target=16,
              current_rr=2.78652, classification="attractive", band_target=16,
              status="wick_only_review", band_overlap=False, active_obstacle=False)
    chart["structure"]["nearest_supports"][0]["entry_scenario"] = sc
    if v3:
        chart["structure"]["nearest_supports"][0].update(
            source="price_structure_wave_fibonacci_v3", zone_id="v3:fixture",
            source_refs=["pivot:fixture"], price_anchor_refs=["pivot:fixture"],
            confirmation_bar="2026-11-16", entry_role="support", entry_role_basis="ORIGINAL_SUPPORT")
    # This global hard-invalid fact is for a different support.
    chart["structure"]["invalidation"].update(support_low=4, price=3, status="hard_invalid")
    monkeypatch.setattr(fixture, "chart_input", lambda _: deepcopy(chart))
    case = fixture.produced_case(market, "daily")
    session, ticker, source, stock, _, _ = case
    ctx, entries, _ = fixture.bound_b_input(case)
    candidate, = entries["tactical_candidates"]
    selected = selected_entry_scenario(ctx, candidate)
    assert selected and selected["evidence_ref"] in candidate["evidence_refs"]
    assert selected_entry_scenario(ctx, dict(candidate, low=5)) is None
    assert selected_entry_scenario(ctx, dict(candidate, eligible=False)) is None
    assert selected_entry_scenario(dict(ctx, current_price=dict(ctx["current_price"], as_of="2026-01-01")), candidate) is None
    build = fixture.b2.build_request
    def synthetic_first_request(**args):
        v1 = args["v1_request"]
        v1["subject"]["selected_entry_scenario"] = selected
        v1["output_schema"] = base.output_schema(v1["subject"])
        v1["request_sha256"] = digest({k:v for k,v in v1.items() if k != "request_sha256"})
        return build(**args)
    monkeypatch.setattr(fixture.b2, "build_request", synthetic_first_request)
    accepted, row, request = fixture.renderer_case(case, ctx, candidate)
    data = request["provider_request"]["input"]
    assert data["selected_entry_scenario"] == selected
    shadow = row["result"]["output"]["new_buyer_shadow"]
    assessment = msg._entry_assessment(data, shadow["timing_context"], ctx, market, fixture.SESSION)
    assert assessment.quality == "SUPPORTED" and assessment.invalidation_ref == selected["evidence_ref"]
    assert assessment.invalidation_price == base.number(7.846774) and assessment.warnings
    with pytest.raises(ValueError, match="selected_scenario_mismatch"):
        msg._entry_assessment(dict(data, selected_entry_scenario=dict(selected, current_target=600)),
                              shadow["timing_context"], ctx, market, fixture.SESSION)
    monkeypatch.setattr(renderer, "stock_plan", lambda *args: accepted)
    text = renderer.stock_message(session, ticker, row, execution_profile=fixture.SOL_HIGH_V1)["text"]
    assert "선택 지지 무효화선" in text and "가까운 저항 하단" in text and "손익비 2배 상한" in text
    assert "2회 연속" in text
    assert len(text.encode("utf-16-le")) // 2 <= 4096
    reg = next(r for r in stock["numeric_registry"] if r["fact_id"] == selected["evidence_ref"].removeprefix("canonical:")
               and r["field_path"] == "fields.entry_scenario.invalidation")
    reg["prose_allowed"] = False
    assert msg._entry_invalidation_row(SimpleNamespace(ticker=ticker, market=market),
        SimpleNamespace(source_stock=source), assessment, fixture.SESSION) is None


def test_below_is_a_location_not_a_historical_crossing():
    assessment = SimpleNamespace(scenario={"status": "intact"})
    assert "이탈" not in msg._buyer_action("ATTRACTIVE", "BELOW", "BLOCKED", assessment=assessment)
    assert "가치평가" in msg._buyer_action("WAIT", "BELOW", "BLOCKED", assessment=assessment,
                                     reason_class="VALUATION_UNRESOLVED")


def test_b_wire_ref_lists_round_trip_without_changing_backend_or_other_stages():
    from app.services.production_monitoring_session import model_wire_context
    ids = ["source:z", "source:a"]
    row = dict(native_technical_context={"comparison_version": 1},
        decision_evidence=[{"ref_id": k, "statement": k} for k in ids],
        source_evidence_binding=dict(emitted_ref_ids=ids[:], ordered_retained_refs=ids[:],
                                     emitted_evidence_sha256="retained"))
    ctx = {"X": row, "Y": dict(row, native_technical_context={})}
    before = deepcopy(ctx)
    projected = model_wire_context("pass-b", ctx)
    assert ctx == before and projected["Y"] is ctx["Y"]
    assert model_wire_context("pass-a", ctx) is ctx and model_wire_context("B2", ctx) is ctx
    recovered = deepcopy(projected)
    for k in ("emitted_ref_ids", "ordered_retained_refs"):
        assert recovered["X"]["source_evidence_binding"][k] == {"same_ordered_values_as": "decision_evidence[].ref_id"}
        recovered["X"]["source_evidence_binding"][k] = [v["ref_id"] for v in recovered["X"]["decision_evidence"]]
    assert recovered == before
    ctx["X"]["source_evidence_binding"]["ordered_retained_refs"].reverse()
    assert model_wire_context("pass-b", ctx) == ctx
