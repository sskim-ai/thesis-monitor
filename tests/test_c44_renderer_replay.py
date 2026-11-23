"""Synthetic accepted-input renderer replay, not saved Mac campaign evidence.

Only the already accepted stock-plan lookup is replaced. The detailed builders,
KR forward wrapper, B2 validation, and final production renderer remain real.
No provider, worker, database, or historical acceptance is invoked or rewritten.
"""
from copy import deepcopy
from datetime import date
import json
from types import SimpleNamespace

import pytest

from app.services import new_buyer_base_contract as b1
from app.services import new_buyer_request_owner as b2
from app.services import production_message_renderer as renderer
from app.services.accepted_calibration_message_service import AcceptedDetailedCalibrationPlan
from app.services.current_fresh_valuation import CurrentValuationView
from app.services.canonical_evidence_time_service import project_canonical_time
from app.services.cross_market_decision_engine_service import DecisionEvidenceRef
from app.services.kr_forward_valuation_context import KrForwardValuationView, calibration_context
from app.services.new_buyer_input_owner import tactical_catalog
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.production_b2_execution import authorize_b2
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from scripts.kis_eps_wire_calibration import sealed
from scripts.newbuyer_fper_prerequisite_scope import blocker_census
from tests.test_c43_offline import fixture as entry_fixture
from tests.test_kr_forward_valuation_integration import view as forward_fixture
from tests.test_m12ds_r4_r1_production_calibration import plan_for
from tests.test_newbuyer_b2_v2 import inputs as b2_inputs, outputs
from tests.test_r9_rev7_detailed_renderer import inputs as detailed_inputs


def synthetic_renderer_case(market, *, target_session="2026-11-23", include_support=False,
                            support_timeframe="daily"):
    """Compose existing fictional fixtures into one frozen renderer input."""
    ticker = "123456" if market == "kr" else "C44_SYNTHETIC"
    currency = "KRW" if market == "kr" else "USD"
    security = "SYNTHETIC:" + ticker
    setup = detailed_inputs.__wrapped__()
    packet = setup["packet"].model_copy(update={
        "ticker": ticker, "market": market, "assessment_date": "2026-11-24",
    })
    source, core, pass_a = setup["source_stock"], setup["core"], setup["pass_a"]
    source.update(ticker=ticker, evidence_packet=packet.model_dump(mode="json"))
    pass_a["ticker"] = ticker
    stock = source["packet"]["stocks"][0]
    stock["ticker"] = ticker
    stock["chart_context"] = {}
    quote = stock["current_price_context"]
    quote.update(current_price=10, currency=currency, as_of_date="2026-11-23",
                 price_basis="adjusted_close")
    fact = stock["fact_catalog"][0]
    fact.update(ticker=ticker, as_of_date="2026-11-23")
    fact["fields"].update(current_price=10, currency=currency)
    stock["numeric_registry"] = build_numeric_registry(stock["fact_catalog"])
    source["source_graph"][fact["fact_id"]]["fact_sha256"] = digest(fact)
    support_ref = "canonical:chart:structure:nearest_supports:1"
    if include_support:
        support = dict(fact_id=support_ref.removeprefix("canonical:"),
            fact_type="chart_support_zone", ticker=ticker, as_of_date="2026-11-23",
            source="deterministic_ohlcv_structure",
            fields=dict(timeframe=support_timeframe, zone_low=9, zone_high=11, currency=currency))
        stock["fact_catalog"].append(support)
        stock["numeric_registry"] = build_numeric_registry(stock["fact_catalog"])
        source["source_graph"][support["fact_id"]] = dict(ticker=ticker, fact_sha256=digest(support))
        stock["chart_context"] = dict(timeframes=dict(daily=dict(timeframe="daily",
            quality="available", as_of_date="2026-11-23", price_basis="adjusted", candle=dict(close=10))))
        if support_timeframe == "weekly":
            stock["chart_context"]["timeframes"]["weekly"] = dict(timeframe="weekly",
                quality="available", as_of_date="2026-11-20", price_basis="adjusted", candle=dict(close=9.5),
                completed_bar_only=True, evaluation_as_of="2026-11-23")
        evidence = DecisionEvidenceRef(ref_id=support_ref, category="price_structure",
            label="chart_support_zone", statement=json.dumps(support["fields"]), as_of="2026-11-23",
            source_ref="stock.fact_catalog." + support["fact_id"],
            source_time=project_canonical_time(support, ticker=ticker, projection_at="2026-11-24"))
        packet = packet.model_copy(update={"evidence": (*packet.evidence, evidence)})
        source["evidence_packet"] = packet.model_dump(mode="json")
    valuation = setup["valuation"].model_copy(update={
        "ticker": ticker, "security_id": security, "currency": currency,
        "price": 10, "price_session": date(2026, 11, 23), "price_basis": "adjusted_close",
        "price_context_sha256": digest(quote),
        "metrics": tuple(m.model_copy(update={"numerator": 10}) for m in setup["valuation"].metrics),
    })
    valuation = CurrentValuationView.model_validate(valuation.model_dump(mode="json"))
    source["valuation_view"] = valuation.model_dump(mode="json")
    # The renderer consumes the previously source-bound identity and target;
    # this compact synthetic projection does not purport to prove acquisition.
    source["completed_session_current_price"] = dict(
        contract="completed-session-current-price-v1", generation_id="source-one",
        ticker=ticker, market=market, canonical_security_id=security,
        target_session=target_session, availability="AVAILABLE", price_as_of=target_session,
        current_price=10, adjustment_basis="adjusted_close", currency=currency,
    )
    source["packet_sha256"] = digest(source["packet"])
    baseline = plan_for(packet)
    if include_support:
        decision = dict(baseline.decision, tactical_choice="watch")
        entries = dict(tactical_watch_status="RESOLVED", tactical_watch_low=9,
            tactical_watch_high=11, tactical_currency=currency, tactical_watch_basis=[support_ref])
        receipt = dict(baseline.acceptance, decision_sha256=digest(decision), entries_sha256=digest(entries))
        baseline = baseline.model_copy(update=dict(decision=decision, entries=entries,
            acceptance=receipt, acceptance_sha256=digest(receipt)))
    provenance = dict(core_sha256=digest(core), pass_a_sha256=digest(pass_a),
        pass_b_sha256=digest(baseline.decision), pass_b_input_sha256=digest("synthetic B"),
        fresh_stock_sha256=digest(source))
    receipt = dict(baseline.acceptance, stage_provenance_sha256=digest(provenance))
    accepted = AcceptedDetailedCalibrationPlan(**dict(baseline.model_dump(mode="json"),
        stage_provenance=provenance, acceptance=receipt, acceptance_sha256=digest(receipt)))

    context = entry_fixture()
    context["ticker"] = ticker
    context["source_evidence_binding"]["source_generation_id"] = "source-one"
    context["current_price"]["currency"] = currency
    for row in context["decision_evidence"]:
        row["statement"]["currency"] = currency
    for candidate in context["r2_eligible_range_catalog"]["tactical_candidates"]:
        candidate["currency"] = currency
    if include_support and support_timeframe == "weekly":
        context["decision_evidence"][2]["statement"]["timeframe"] = "weekly"
        context["decision_evidence"][3]["statement"]["timeframe"] = "weekly"
        context["decision_evidence"].append(dict(ref_id="canonical:chart:weekly", as_of="2026-11-20",
            label="weekly", statement=dict(timeframe="weekly", quality="available", currency=currency,
                price_basis="adjusted", candle=dict(close=9.5), completed_bar_only=True, evaluation_as_of="2026-11-23")))
        context["source_use_projection"]["source_permissions"].append(
            dict(ref_id="canonical:chart:weekly", allowed_uses=["ENTRY"]))

    data = b2_inputs(legacy=False)
    subject = data["v1_request"]["subject"]
    subject.update(ticker=ticker, security_id=security, source_generation_id="source-one",
        frozen_authority=dict(core=digest(core), pass_a=digest(pass_a),
            accepted_b=digest(baseline.decision), context=digest(context)),
        current_price=deepcopy(context["current_price"]), selected_tactical_candidate="watch",
        tactical_catalog=tactical_catalog(context, ticker, security))
    for valuation_fact in subject["facts"].values():
        valuation_fact.update(ticker=ticker, security_id=security)
    data["v1_request"]["output_schema"] = b1.output_schema(subject)
    data["v1_request"]["request_sha256"] = digest({
        key: value for key, value in data["v1_request"].items() if key != "request_sha256"})
    coverage_row = {key: value for key, value in data["coverage"]["rows"][0].items()
                    if key != "receipt_sha256"}
    coverage_row.update(ticker=ticker, canonical_security_id=security, source_generation="source-one")
    coverage_row = sealed(coverage_row)
    coverage = {key: value for key, value in data["coverage"].items() if key != "receipt_sha256"}
    data["coverage"] = sealed(dict(coverage, rows=[coverage_row]))
    data["census"] = blocker_census([coverage_row], expected_subjects=[ticker])
    data.update(coverage_sha=data["coverage"]["receipt_sha256"], census_sha=data["census"]["receipt_sha256"])
    request = b2.build_request(**data)
    output = {"new_buyer_shadow": next(row for row in outputs(request) if row["new_buyer"] == "ATTRACTIVE")}
    auth = authorize_b2(request, generation_id="exec-one", source_generation_id="source-one",
        source_envelope_sha256=digest("synthetic envelope"), owner_sha256=digest("synthetic owner"),
        core_sha256=digest(core), pass_a_sha256=digest(pass_a),
        pass_b_sha256=digest(baseline.decision), execution_profile=SOL_HIGH_V1)
    result = dict(contract="production-b2-accepted-result-v1", generation_id="exec-one",
        ticker=ticker, security_id=security, request_sha256=auth.request_sha256,
        authorization_sha256=digest(auth.model_dump(mode="json")), output=output,
        output_sha256=digest(output), status="PASS", attempts=[], semantic_retries=0)
    source_envelope = dict(source_generation_id="source-one")
    if market == "kr":
        forward = forward_fixture(missing=True).model_dump(mode="json")
        forward["native"] = valuation.model_dump(mode="json")
        forward["kis"]["security_code"] = ticker
        forward = KrForwardValuationView.model_validate(forward).model_dump(mode="json")
        source_envelope["forward_views"] = {ticker: forward}
    session = SimpleNamespace(market=market, gen="exec-one", source_gen="source-one",
        source=source_envelope, fresh_stocks={ticker: source}, cores={ticker: core},
        arows={ticker: pass_a}, brows={ticker: baseline.decision}, bctx={ticker: context},
        b2_request=lambda key: request,
        valuation_context=lambda key: calibration_context(source_envelope["forward_views"][key]))
    return session, ticker, accepted, dict(result=result, authorization=auth.model_dump(mode="json")), request


@pytest.mark.parametrize("market", ["kr", "us"])
@pytest.mark.parametrize("target_session", ["2026-11-23", "2026-11-24"])
def test_real_renderer_keeps_completed_session_separate_from_assessment(monkeypatch, market, target_session):
    session, ticker, accepted, row, request = synthetic_renderer_case(market, target_session=target_session)
    before = deepcopy((session.bctx, session.fresh_stocks, row, request))
    monkeypatch.setattr(renderer, "stock_plan", lambda current, symbol, packet: accepted)
    message = renderer.stock_message(session, ticker, row, execution_profile=SOL_HIGH_V1)
    text = message["text"]
    assert message["message_id"] == ticker
    assert "판단 기준일: 2026-11-24" in text
    assert all(raw not in text for raw in (
        "FAVORABLE_NOW", "UNRESOLVED", "EXACT_SELECTED_ZONE_RELATION",
        "QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE",
    ))
    if target_session == "2026-11-23":
        assert "신규 매수 검토 가능" in text
        assert "현재가 기준 손익비 근거가 지지함" in text
    else:
        assert "완료 거래일과 가격·차트 세션 불일치" in text
        assert "신규 매수 검토 가능" not in text
    assert (session.bctx, session.fresh_stocks, row, request) == before
    assert row["result"]["output"]["new_buyer_shadow"]["timing_context"]["state"] == "FAVORABLE_NOW"
