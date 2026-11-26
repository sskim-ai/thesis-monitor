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
from app.services.ohlcv_structure_service import _candidate_scenario, calculate_invalidation
from app.services.production_monitoring_session import frozen_context_prompt
from app.services.production_model_transport import render_prompt
from app.services.unified_snapshot_contract import digest
from tests import test_c50_chart_statement as fixture
from tests.test_c51_invalidation import bars


def zone(low, high, frame="daily", pivot="2026-10-01"):
    return dict(timeframe=frame, pivot_type="low", pivot_dates=[pivot], pivot_prices=[low],
                zone_low=low, zone_high=high, strength="Strong")


def test_nearer_band_obstacle_and_same_low_identity():
    z, middle, far = zone(93, 99), zone(105, 107), zone(130, 131)
    inv, rr = dict(price=92, status="intact"), dict(current_price=dict(ratio=1.111111, classification="conditional"))
    result = _candidate_scenario(z, [z, middle, far], 110, far, inv, rr)
    assert (result["current_target"], result["current_rr"], result["band_target"]) == (130, 1.111111, 105)
    for distinct in (zone(93, 99, "weekly"), zone(93, 99, pivot="2026-10-05")):
        other = _candidate_scenario(z, [z, distinct, far], 110, far, inv, rr)
        assert other["band_overlap"] and "band_target" not in other
    inside = _candidate_scenario(z, [z, middle, far], 106, far, inv, rr)
    assert inside["active_obstacle"] and "current_rr" not in inside


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
def test_selected_source_scenario_to_renderer_and_denied_number(monkeypatch, market):
    chart = fixture.chart_input("daily")
    sc = dict(chart_only=True, reference_price=10, invalidation=7.846774, current_target=16,
              current_rr=2.78652, classification="attractive", band_target=16,
              status="wick_only_review", band_overlap=False, active_obstacle=False)
    chart["structure"]["nearest_supports"][0]["entry_scenario"] = sc
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
