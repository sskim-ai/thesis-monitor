"""Lossless chart facts through real B/B2/render builders; fictional offline data.

Only the accepted stock-plan lookup is replaced at rendering. Economics and B2
responses are explicit synthetic fixtures, not new model/source acceptances.
The tested frame facts, statement producer, source-use binding, B transformation,
B2 timing, and final renderer all use their production implementations.
"""
from copy import deepcopy
import json

import pytest

from app.services import new_buyer_base_contract as b1
from app.services import new_buyer_request_owner as b2
from app.services import production_message_renderer as renderer
from app.services.accepted_calibration_message_service import AcceptedDetailedCalibrationPlan
from app.services.ai_review_service import _chart_facts
from app.services.canonical_monitoring_input import b_input
from app.services.cross_market_decision_engine_service import (
    _compact, build_decision_evidence_packet, canonical_fact_statement,
)
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from app.services.new_buyer_input_owner import tactical_catalog
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.ohlcv_client import _chart_timeframe_context, _summarize_bars
from app.services.production_b2_execution import authorize_b2
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from scripts import r2b_r2_contract as b_contract
from scripts.kis_eps_wire_calibration import sealed
from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12co_entry_range_contract import build_subject_candidate_coverage
from scripts.m12da_source_use_contract import (
    build_source_use_projection, build_trusted_source_authority_manifest,
    freeze_source_use_binding, freeze_source_use_input_expectation,
)
from scripts.m12ds_r2_judgment_policy import frozen_fact_fields
from scripts.newbuyer_fper_prerequisite_scope import blocker_census
from tests.test_c44_renderer_replay import synthetic_renderer_case
from tests.test_m12ds_r4_r1_production_calibration import plan_for
from tests.test_newbuyer_b2_v2 import inputs as b2_inputs, outputs


SESSION = "2026-11-23"
BAR_DATES = dict(daily=SESSION, weekly="2026-11-20", monthly="2026-10-01")


def chart_input(support_timeframe):
    """Use the frame producer, including its genuine formula metadata.

    The completed weekly/monthly closes deliberately differ from the current
    daily close. Rich but ordinary indicator fields push each frame over 900.
    """
    timeframes = {}
    for timeframe, day in BAR_DATES.items():
        close = 10 if timeframe == "daily" else 9.5
        bars = [
            dict(date="2026-09-01", open=8, high=9, low=7.5, close=8.5, volume=20000000),
            dict(date=day, open=9.123456, high=10.234567, low=8.987654, close=close,
                 volume=44375551, value=441234567.89, RSI14=55.123456,
                 MACD=0.123456, MACD_SIGNAL=0.112233, MACD_HIST=0.011223,
                 VOLUME_RATIO_20=1.876543),
        ]
        frame = _chart_timeframe_context(timeframe, bars, _summarize_bars(2, bars)).model_dump(mode="json")
        frame.update(completed_bar_only=True, evaluation_as_of=SESSION, price_basis="adjusted")
        frame["indicator_source_semantics"]["volume_ratio_20"] = "volume / SMA(volume, 20)"
        timeframes[timeframe] = frame
    return dict(available=True, quality="fresh", as_of_date=SESSION,
        source="fictional-completed-ohlcv", timeframes=timeframes,
        stored_price_rules=dict(support_zone_low=1100, support_zone_high=1125),
        structure=dict(as_of_date=SESSION,
            nearest_supports=[dict(timeframe=support_timeframe, zone_low=9, zone_high=11)],
            invalidation=dict(available=True, timeframe=support_timeframe, price=8,
                support_low=9, status="intact", chart_only=True),
            risk_reward=dict(available=True, current_price=dict(entry=10, target=16,
                invalidation=8, ratio=3, scenario="current_price", classification="attractive"))))


def produced_case(market, support_timeframe):
    session, ticker, _, _, _ = synthetic_renderer_case(market)
    source = session.fresh_stocks[ticker]
    stock = source["packet"]["stocks"][0]
    currency = source["valuation_view"]["currency"]
    stock["chart_context"] = chart_input(support_timeframe)
    price = stock["fact_catalog"][0]
    price["fields"].update(price_basis="adjusted_close", price_as_of=SESSION)
    stock["fact_catalog"] = [price, *_chart_facts(stock["chart_context"], currency)]
    stock["thesis"] = dict(core_thesis="Synthetic business context for renderer plumbing.")
    stock["numeric_registry"] = build_numeric_registry(stock["fact_catalog"])
    source["packet"].update(packet_id="source-one", market=market, assessment_date="2026-11-24",
                            generated_at="2026-11-24T00:30:00+00:00")
    packet = build_decision_evidence_packet(packet=source["packet"], stock=stock)
    owned = build_owned_evidence_packet(packet, stock=stock)
    source.update(evidence_packet=packet.model_dump(mode="json"), ownership=owned.model_dump(mode="json"),
        packet_sha256=digest(source["packet"]),
        source_graph={fact["fact_id"]: dict(ticker=ticker, fact_sha256=digest(fact))
                      for fact in stock["fact_catalog"]})
    return session, ticker, source, stock, packet, owned


def bound_b_input(case):
    session, ticker, source, _, packet, owned = case
    rows = packet.model_dump(mode="json")["evidence"]
    ownership = dict(ticker=ticker, core_ref_ids=sorted(owned.core_refs),
                     timing_ref_ids=sorted(owned.timing_refs))
    catalog = build_subject_catalog(context=dict(evidence_packets=[packet.model_dump(mode="json")],
        evidence_ownership=[ownership]), ticker=ticker, atomic_claims=[])
    # Match bound_chain: a subject context contains only its catalog's sources.
    rows = [row for row in rows if row["ref_id"] in catalog["all_evidence_refs"]]
    subject = build_subject_candidate_coverage(market=session.market,
        packet=packet.model_dump(mode="json"), ownership=ownership)
    subject.update(decision_evidence=deepcopy(rows), security_valuation_basis_state=dict(state="UNRESOLVED"))
    manifest = build_trusted_source_authority_manifest(ticker=ticker,
        source_generation_id=session.source_gen, catalog=catalog, source_metadata=rows)
    expectation = freeze_source_use_input_expectation(ticker=ticker,
        source_generation_id=session.source_gen, execution_generation_id=session.gen,
        catalog=catalog, source_metadata=rows, authority_manifest=manifest)
    projection = build_source_use_projection(ticker=ticker, input_generation_id=session.source_gen,
        execution_generation_id=session.gen, catalog=catalog, authority_manifest=manifest,
        current_input_expectation=expectation)
    binding = freeze_source_use_binding(projection=projection, authority_manifest=manifest,
                                         current_input_expectation=expectation)
    chain = dict(projection=projection, binding=binding, expectation=expectation,
                 source_generation_id=session.source_gen, execution_generation_id=session.gen)
    capability = dict(positive=["claim:one"], negative=[], holder_support=["claim:one"],
        holder_risk=[], holder_reduce=[], confidence=[], quality=[], condition=[], risk_triggers={},
        sell_eligible=[], current_stress=[])
    classification = dict(ticker=ticker, archetype="DURABLE_FRANCHISE", valuation_regime_tier="BASE")
    session.arows[ticker] = classification
    context, entries, valuation = b_input(source, catalog, subject, chain, classification, capability)
    session.bctx[ticker] = context
    return context, entries, b_contract.decision_schema("EVIDENCE_BASED", capability, valuation, entries, {})


def renderer_case(case, context, candidate):
    """Attach explicit synthetic accepted economics to the real generated context."""
    session, ticker, source, _, packet, _ = case
    security = source["valuation_view"]["security_id"]
    core, pass_a = session.cores[ticker], session.arows[ticker]
    business_ref = next(ref.ref_id for ref in packet.evidence if ref.source_ref == "stock.thesis.core_thesis")
    core["atomic_claims"][0]["parent_source_refs"] = [business_ref]
    core["binding_sha256"] = digest(dict(atomic=core["atomic_claims"], effects=core["effects"]))
    baseline = plan_for(packet)
    decision = dict(baseline.decision, tactical_choice=candidate["candidate_id"])
    session.brows[ticker] = decision
    entries = dict(tactical_watch_status="RESOLVED", tactical_watch_low=candidate["low"],
        tactical_watch_high=candidate["high"], tactical_currency=candidate["currency"],
        tactical_watch_basis=candidate["evidence_refs"])
    lineage = {"claim:one": (business_ref,)}
    provenance = dict(core_sha256=digest(core), pass_a_sha256=digest(pass_a),
        pass_b_sha256=digest(decision), pass_b_input_sha256=digest(context), fresh_stock_sha256=digest(source))
    receipt = dict(baseline.acceptance, decision_sha256=digest(decision), entries_sha256=digest(entries),
        claim_lineage_sha256=digest(lineage), stage_provenance_sha256=digest(provenance))
    accepted = AcceptedDetailedCalibrationPlan(**dict(baseline.model_dump(mode="json"),
        decision=decision, entries=entries, claim_lineage=lineage, stage_provenance=provenance,
        acceptance=receipt, acceptance_sha256=digest(receipt)))

    data = b2_inputs(legacy=False)
    subject = data["v1_request"]["subject"]
    subject.update(ticker=ticker, security_id=security, source_generation_id=session.source_gen,
        frozen_authority=dict(core=digest(core), pass_a=digest(pass_a), accepted_b=digest(decision),
                              context=digest(context)), current_price=deepcopy(context["current_price"]),
        selected_tactical_candidate=candidate["candidate_id"],
        tactical_catalog=tactical_catalog(context, ticker, security, source_generation_id=session.source_gen))
    for valuation_fact in subject["facts"].values():
        valuation_fact.update(ticker=ticker, security_id=security)
    data["v1_request"]["output_schema"] = b1.output_schema(subject)
    data["v1_request"]["request_sha256"] = digest({
        key: value for key, value in data["v1_request"].items() if key != "request_sha256"})
    coverage_row = {key: value for key, value in data["coverage"]["rows"][0].items()
                    if key != "receipt_sha256"}
    coverage_row = sealed(dict(coverage_row, ticker=ticker, canonical_security_id=security,
                              source_generation=session.source_gen))
    coverage = {key: value for key, value in data["coverage"].items() if key != "receipt_sha256"}
    data["coverage"] = sealed(dict(coverage, rows=[coverage_row]))
    data["census"] = blocker_census([coverage_row], expected_subjects=[ticker])
    data.update(coverage_sha=data["coverage"]["receipt_sha256"], census_sha=data["census"]["receipt_sha256"])
    request = b2.build_request(**data)
    output = dict(new_buyer_shadow=next(row for row in outputs(request) if row["new_buyer"] == "ATTRACTIVE"))
    auth = authorize_b2(request, generation_id=session.gen, source_generation_id=session.source_gen,
        source_envelope_sha256=digest("synthetic envelope"), owner_sha256=digest("synthetic owner"),
        core_sha256=digest(core), pass_a_sha256=digest(pass_a), pass_b_sha256=digest(decision),
        execution_profile=SOL_HIGH_V1)
    result = dict(contract="production-b2-accepted-result-v1", generation_id=session.gen,
        ticker=ticker, security_id=security, request_sha256=auth.request_sha256,
        authorization_sha256=digest(auth.model_dump(mode="json")), output=output,
        output_sha256=digest(output), status="PASS", attempts=[], semantic_retries=0)
    session.b2_request = lambda key: request
    return accepted, dict(result=result, authorization=auth.model_dump(mode="json")), request


@pytest.mark.parametrize("market", ["kr", "us"])
@pytest.mark.parametrize("support_timeframe", ["daily", "weekly", "monthly"])
def test_long_dwm_facts_reach_bound_b_b2_and_full_renderer(monkeypatch, market, support_timeframe):
    case = produced_case(market, support_timeframe)
    session, ticker, source, stock, packet, _ = case
    before = deepcopy((stock, packet.model_dump(mode="json")))
    context, entries, schema = bound_b_input(case)
    facts = {"canonical:" + fact["fact_id"]: fact for fact in stock["fact_catalog"]}
    rows = {row["ref_id"]: row for row in context["decision_evidence"]}
    original_rows = {row.ref_id: row for row in packet.evidence}
    fields = frozen_fact_fields(source["packet"], ticker, packet.model_dump(mode="json")["evidence"])
    for timeframe in BAR_DATES:
        ref = "canonical:chart:" + timeframe
        assert len(rows[ref]["statement"]) > 900
        assert rows[ref]["statement"] == original_rows[ref].statement
        assert json.loads(rows[ref]["statement"]) == fields[ref]["fields"] == facts[ref]["fields"]
        assert rows[ref]["as_of"] == BAR_DATES[timeframe]
        assert fields[ref]["fields"]["evaluation_as_of"] == SESSION
        assert fields[ref]["fields"]["completed_bar_only"] is True
    assert (stock, packet.model_dump(mode="json")) == before
    assert len(entries["tactical_candidates"]) == 1
    candidate = entries["tactical_candidates"][0]
    assert candidate["source_label"] == "chart_support_zone" and candidate["eligible"]
    assert schema["properties"]["tactical_choice"]["enum"] == [candidate["candidate_id"]]
    permissions = {row["ref_id"]: row["allowed_uses"]
                   for row in context["source_use_projection"]["source_permissions"]}
    required = [context["current_price"]["ref_id"], "canonical:chart:daily",
                "canonical:chart:" + support_timeframe, *candidate["evidence_refs"]]
    assert all("ENTRY" in permissions[ref] for ref in required)
    assert any("STORED_PRICE_RULE_REFERENCE_ONLY" in row["failure_reasons"]
               for row in context["entry_candidate_diagnostics"])
    accepted, b2_row, request = renderer_case(case, context, candidate)
    timing = request["provider_request"]["input"]["timing_context"]
    assert (timing["state"], timing["relation"]) == ("FAVORABLE_NOW", "INSIDE")
    assert timing["evidence_refs"] == sorted([context["current_price"]["ref_id"], *candidate["evidence_refs"]])
    before_render = deepcopy((source, context, b2_row, request))
    monkeypatch.setattr(renderer, "stock_plan", lambda *args: accepted)
    message = renderer.stock_message(session, ticker, b2_row, execution_profile=SOL_HIGH_V1)
    assert message["NO_SEND"] is True
    assert "지지 구간 안" in message["text"] and "신규 매수 검토 가능" in message["text"]
    label = {"daily": "일봉", "weekly": "주봉 완료봉", "monthly": "월봉 완료봉"}[support_timeframe]
    assert f"{BAR_DATES[support_timeframe]} {label}" in message["text"]
    assert message["text"].count("진입 관찰 지지 구간(") == 1
    assert all(value not in message["text"] for value in ("UNRESOLVED", "FAVORABLE_NOW", "SMA(volume"))
    assert (source, context, b2_row, request) == before_render


@pytest.mark.parametrize("mutation", ["old_truncation", "changed_tail"])
def test_frozen_fact_comparison_rejects_truncated_or_changed_complete_statement(mutation):
    _, ticker, source, stock, packet, _ = produced_case("us", "weekly")
    rows = packet.model_dump(mode="json")["evidence"]
    daily = next(row for row in rows if row["ref_id"] == "canonical:chart:daily")
    if mutation == "old_truncation":
        fields = next(fact["fields"] for fact in stock["fact_catalog"] if fact["fact_id"] == "chart:daily")
        daily["statement"] = _compact(fields)
        assert len(daily["statement"]) == 900 and daily["statement"].endswith("…")
    else:
        fields = json.loads(daily["statement"])
        fields["volume_ratio_20"] = 99
        daily["statement"] = json.dumps(fields, ensure_ascii=False, sort_keys=True, default=str)
    before = deepcopy((source, rows))
    with pytest.raises(ValueError, match="frozen_fact_projection_mismatch"):
        frozen_fact_fields(source["packet"], ticker, rows)
    assert (source, rows) == before


def test_non_frame_facts_and_prose_keep_existing_compact_bytes():
    _, _, source, stock, _, _ = produced_case("us", "daily")
    long_text = "A fictional long source explanation. " * 40
    stock["thesis"]["core_thesis"] = long_text
    financial = dict(fact_id="earnings:2026-09-30", fact_type="earnings",
        as_of_date="2026-09-30", source="fictional-financial-fixture", fields=dict(note=long_text))
    stock["fact_catalog"].append(financial)
    packet = build_decision_evidence_packet(packet=source["packet"], stock=stock)
    rows = {row.ref_id: row for row in packet.evidence}
    assert rows["canonical:" + financial["fact_id"]].statement == _compact(financial["fields"])
    prose = next(row for row in packet.evidence if row.source_ref == "stock.thesis.core_thesis")
    assert prose.statement == _compact(long_text) and len(prose.statement) == 900
    frozen_fact_fields(source["packet"], stock["ticker"], packet.model_dump(mode="json")["evidence"])
    # Neither a similarly named family nor an unsupported timeframe widens the exception.
    for fact_id, fact_type in [("chart:daily", "chart_price_rules"),
                               ("chart:hourly", "chart_timeframe"),
                               ("chart:stored_price_rules", "chart_price_rules")]:
        fact = dict(fact_id=fact_id, fact_type=fact_type, fields=dict(note=long_text))
        assert canonical_fact_statement(fact) == _compact(fact["fields"])
