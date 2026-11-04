"""Synthetic legacy Core isolation tests, not real-source or judgment approval."""
from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import PriceDecisionContext
from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2ProductionContext,
    accepted_v2_fundamental_core_prompt,
    accepted_v2_fundamental_core_ref_catalog,
    accepted_v2_production_prompt,
    build_accepted_v2_production_context,
)
from app.services.ai_review_service import _stock_packet
from app.services.coldstart_source_assembly_service import (
    SourceAssemblyStatus,
    assemble_research_packet,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    build_decision_evidence_packet,
)
from app.services.direction_timing_ownership_service import (
    build_owned_evidence_packet,
    stage_alias_catalogs,
)
from tests.test_accepted_decision_v2_runtime import _fundamental_core
from tests.test_coldstart_source_assembly_service import (
    AS_OF,
    _PriceClient,
    _identity,
    _price_context,
    _unavailable_price_context,
)
from tests.test_financial_context_adapter_service import _row as financial_row


TICKER = "R21TEST"
PRICES = (987.654321, 876.543219)
FINANCIAL_VALUES = ("246813579.25", "357924680.50")
PREMISE = "A registered hypothesis about recurring customer adoption."
PROSPECTIVE = "Reevaluate only if a separately verified filing confirms adoption."


def _dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _unowned_text(price: float) -> str:
    return f'R21_UNOWNED_PRICE_MACD "OHLCV close {price}; prior BUY label"'


@pytest.fixture(autouse=True)
def _isolated_data(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("ENABLE_LIVE_PROVIDERS", "false")
    monkeypatch.setenv("NOTIFICATION_DRY_RUN", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _daily_stock(*, relevance: int = 40, thesis_changes=None) -> dict[str, Any]:
    fields = {
        "ticker": TICKER,
        "version": 1,
        "core_thesis": PREMISE,
        "time_horizon": "12-24 months",
        "strengthen_signals": json.dumps([PROSPECTIVE]),
    }
    for key, value in (thesis_changes or {}).items():
        fields[key] = value if isinstance(value, str) else json.dumps(value)
    thesis = InvestmentThesis(**fields)
    item = WatchlistItem(
        ticker=TICKER,
        company_name="Synthetic R21 Company",
        active=False,
        production_eligible=False,
        monitoring_requested=False,
    )
    event = {
        "fingerprint": "r21-synthetic-event-stable-fingerprint",
        "title": "Synthetic reported business event, not real issuer evidence",
        "date": AS_OF.date().isoformat(),
        "event_type": "financial_report",
        "materiality": "material",
        "direction": "positive",
        "relevance_score": relevance,
    }
    assessment = ThesisAssessment(
        ticker=TICKER,
        thesis_version=1,
        assessment_date=AS_OF.date(),
        status="strengthened",
        score=80,
        summary="R21_DAILY_TRIAGE_ONLY",
        new_buyer_view="SYNTHETIC_ONLY",
        holder_view="SYNTHETIC_ONLY",
        price_view="SYNTHETIC_ONLY",
        risk_level="normal",
        evidence=json.dumps([event]),
    )
    engine = create_engine("sqlite://")
    try:
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            session.add(thesis)
            session.commit()
            stock = _stock_packet(session, item, assessment)
            assert stock is not None
            assert thesis.core_thesis == fields["core_thesis"]
            assert json.loads(assessment.evidence) == [event]
            return stock
    finally:
        engine.dispose()


def _financial_stock(value: str = FINANCIAL_VALUES[0]) -> dict[str, Any]:
    # Reuse the canonical financial fixture's exact period/basis vocabulary.
    fact = financial_row(
        "r21:ocf:current",
        "cash_flow_ocf",
        value,
        period_type="QTD",
        fiscal_year=2026,
        fiscal_quarter=2,
        attribution_basis="total",
    )
    return {
        "ticker": TICKER,
        "company_name": "Synthetic R21 Company",
        "thesis": {},
        "fact_catalog": [fact],
        "unknowns": [],
        "data_cautions": [],
    }


def _packet(stock: dict[str, Any]) -> dict[str, Any]:
    return {
        "packet_id": "r21-isolation-fixed-outer-packet",
        "market": "us",
        "assessment_date": AS_OF.date().isoformat(),
        "generated_at": AS_OF.isoformat(),
        "stocks": [stock],
    }


@dataclass(frozen=True)
class NativeView:
    evidence: DecisionEvidencePacket
    context: AcceptedV2ProductionContext
    prompt: str
    payload: list[dict[str, Any]]


def _native(packet, *, evidence=None) -> NativeView:
    before = deepcopy(packet)
    evidence = evidence or build_decision_evidence_packet(
        packet=packet, stock=packet["stocks"][0]
    )
    context = build_accepted_v2_production_context(
        packet=packet,
        claim_id="r21-source-isolation-fixed-claim",
        evidence_packets=(evidence,),
        prepared_at=AS_OF,
        authority_native_v2=False,
    )
    prompt = accepted_v2_fundamental_core_prompt(context)
    marker = "\nFUNDAMENTAL_CORE_CONTEXT:\n"
    assert prompt.count(marker) == 1
    payload = json.loads(prompt.split(marker, 1)[1])
    assert packet == before, "Core projection must not edit the producer packet"
    return NativeView(evidence, context, prompt, payload)


def _core_rows(view: NativeView):
    allowed = set(accepted_v2_fundamental_core_ref_catalog(view.context))
    return [
        ref
        for packet in view.context.evidence_packets
        for ref in packet.evidence
        if ref.ref_id in allowed
    ]


def _assert_unowned_absent(view: NativeView) -> None:
    assert "R21_UNOWNED_PRICE_MACD" not in view.prompt
    for price in PRICES:
        assert str(price) not in view.prompt
    assert all(not row.source_ref.startswith("stock.thesis.") for row in _core_rows(view))


def _semantic_payload(view: NativeView):
    payload = deepcopy(view.payload)
    # Coldstart binds its raw price packet into this documented outer identifier.
    # No evidence IDs, statements, numeric fields, cautions or hashes are masked.
    for subject in payload:
        subject["fundamental_core_evidence"].pop("packet_id", None)
    return payload


def test_actual_stock_packet_score_pair_preserves_triage_but_not_core_influence():
    stocks = [_daily_stock(relevance=score) for score in (40, 99)]
    for stock, score in zip(stocks, (40, 99), strict=True):
        assert stock["evidence"][0]["relevance_score"] == score
        assert any(
            fact["fields"].get("relevance_score") == score
            for fact in stock["fact_catalog"]
        )
        assert stock["deterministic_assessment"]["summary"] == "R21_DAILY_TRIAGE_ONLY"
        assert stock["thesis"]["core_thesis"] == PREMISE
    views = [_native(_packet(stock)) for stock in stocks]
    assert views[0].context.source_packet_sha256 != views[1].context.source_packet_sha256
    assert views[0].payload == views[1].payload
    assert views[0].prompt == views[1].prompt
    assert "relevance_score" not in _dump(views[0].payload)
    assert "R21_DAILY_TRIAGE_ONLY" not in views[0].prompt


@pytest.mark.parametrize(
    "channel",
    (
        "core_thesis",
        "strengthen_signals",
        "weaken_signals",
        "invalidation_signals",
        "market_expectations",
        "macro_exposures",
        "time_horizon",
    ),
)
def test_stored_user_thesis_variants_never_become_core_current_facts(channel):
    views = []
    for price in PRICES:
        text = _unowned_text(price)
        if channel == "core_thesis":
            value = json.dumps({"quoted": {"statement": text, "price": price}})
        elif channel == "time_horizon":
            value = f"12-24 months; {text}"
        elif channel == "market_expectations":
            value = {"as_of_date": "2026-09-06", "summary": text, "nested": {"MACD": price}}
        else:
            value = [{"condition": {"statement": text, "expected_price": price}}]
        stock = _daily_stock(thesis_changes={channel: value})
        assert stock["thesis"][channel] == value
        assert str(price) in _dump(stock["thesis"])
        view = _native(_packet(stock))
        _assert_unowned_absent(view)
        views.append(view)
    assert views[0].payload == views[1].payload
    assert views[0].prompt == views[1].prompt


def test_registered_business_premise_and_future_condition_remain_in_original_stock():
    stock = _daily_stock()
    view = _native(_packet(stock))
    assert stock["thesis"]["core_thesis"] == PREMISE
    assert stock["thesis"]["strengthen_signals"] == [PROSPECTIVE]
    assert all(not row.source_ref.startswith("stock.thesis.") for row in _core_rows(view))
    assert all(PROSPECTIVE not in row.statement for row in _core_rows(view))


def test_qualified_canonical_financial_value_survives_and_changes_core_prompt():
    views = []
    for value in FINANCIAL_VALUES:
        stock = _financial_stock(value)
        fact = stock["fact_catalog"][0]
        assert fact["source"] == "canonical_cash_flow_fact"
        assert fact["fields"]["period_start"] == "2026-04-01"
        assert fact["fields"]["period_end"] == "2026-06-30"
        view = _native(_packet(stock))
        matches = [row for row in _core_rows(view) if row.ref_id == "canonical:r21:ocf:current"]
        assert len(matches) == 1, "Dropping all evidence cannot pass source isolation"
        assert value in matches[0].statement
        assert value in view.prompt
        assert matches[0].financial_context is not None
        assert matches[0].financial_context.period.end.isoformat() == "2026-06-30"
        views.append(view)
    assert views[0].payload != views[1].payload
    assert views[0].prompt != views[1].prompt


@pytest.mark.parametrize("channel", ("data_cautions", "unknowns"))
@pytest.mark.parametrize("shape", ("prose", "nested"))
def test_free_quality_prose_and_nested_numbers_do_not_enter_core(channel, shape):
    views = []
    for price in PRICES:
        stock = _financial_stock()
        text = _unowned_text(price)
        unowned = text if shape == "prose" else {"statement": text, "details": {"current_price": price}}
        stock[channel] = [unowned]
        view = _native(_packet(stock))
        assert stock[channel] == [unowned]
        _assert_unowned_absent(view)
        assert FINANCIAL_VALUES[0] in view.prompt
        views.append(view)
    assert views[0].payload == views[1].payload
    assert views[0].prompt == views[1].prompt


def test_typed_evidence_technical_quality_cannot_bypass_native_prompt_boundary():
    packet = _packet(_financial_stock())
    evidence = build_decision_evidence_packet(packet=packet, stock=packet["stocks"][0])
    views = []
    for price in PRICES:
        raw = evidence.model_dump(mode="json")
        raw["technical_context_quality"] = {
            "daily": {"status": "UNAVAILABLE", "statement": _unowned_text(price), "close": price}
        }
        supplied = DecisionEvidencePacket.model_validate(raw)
        assert str(price) in _dump(supplied.technical_context_quality)
        view = _native(packet, evidence=supplied)
        _assert_unowned_absent(view)
        assert FINANCIAL_VALUES[0] in view.prompt
        views.append(view)
    assert views[0].payload == views[1].payload
    assert views[0].prompt == views[1].prompt


def test_raw_quality_dictionary_cannot_self_label_as_current_business_evidence():
    stock = _financial_stock()
    stock["fact_catalog"].append({
        "fact_id": "r21:unowned-quality",
        "fact_type": "quality",
        "evidence_family": "BUSINESS_CURRENT",
        "source": "caller_quality_dictionary",
        "as_of_date": AS_OF.date().isoformat(),
        "fields": {"statement": _unowned_text(PRICES[0]), "nested": {"current_price": PRICES[0]}},
    })
    view = _native(_packet(stock))
    _assert_unowned_absent(view)
    assert "canonical:r21:unowned-quality" not in accepted_v2_fundamental_core_ref_catalog(view.context)
    assert FINANCIAL_VALUES[0] in view.prompt
    assert stock["fact_catalog"][1]["fields"]["nested"]["current_price"] == PRICES[0]


@pytest.mark.parametrize("availability", ("ready", "price_only", "unavailable"))
def test_actual_coldstart_availability_branches_keep_price_out_of_native_core(availability):
    views = []
    for price in PRICES:
        price_context = (
            _price_context("AAPL")
            if availability == "ready"
            else _unavailable_price_context("AAPL")
        )
        if availability != "unavailable":
            price_context.available = True
            price_context.decision = PriceDecisionContext(
                current_price=price,
                currency="USD",
                price_as_of="2026-09-04",
                exchange_trade_date="2026-09-04",
                latest_completed_regular_session_date="2026-09-04",
                price_basis="close",
                market_session="closed",
                assessment_state="final",
            )
        price_context.warnings = [*price_context.warnings, _unowned_text(price)]
        result = asyncio.run(assemble_research_packet(
            "AAPL", AS_OF, identity=_identity(), price_client=_PriceClient(price_context),
        ))
        assert result.status == SourceAssemblyStatus.ASSEMBLED
        assert result.validation_errors == ()
        assert result.packet is not None
        stock = result.packet["stocks"][0]
        current = stock["current_price_context"]
        assert current["availability"] == availability
        assert current["current_price"] == (None if availability == "unavailable" else price)
        assert _unowned_text(price) in stock["data_cautions"]
        view = _native(result.packet, evidence=result.decision_evidence_packet())
        _assert_unowned_absent(view)
        core_ids = set(accepted_v2_fundamental_core_ref_catalog(view.context))
        assert "canonical:price:current" not in core_ids
        assert all(not ref.startswith("technical-feature:") for ref in core_ids)
        if availability != "unavailable":
            price_ref = next(row for row in view.evidence.evidence if row.ref_id == "canonical:price:current")
            assert str(price) in price_ref.statement
            assert price_ref.ref_id in view.context.evidence_ownership[0].timing_ref_ids
        views.append(view)
    assert views[0].context.packet_id != views[1].context.packet_id
    assert _semantic_payload(views[0]) == _semantic_payload(views[1])


def test_price_timing_binding_relabelled_earnings_never_enters_native_core():
    stock = _financial_stock()
    stock["current_price_context"] = {
        "availability": "price_only", "current_price": PRICES[0], "currency": "USD",
    }
    packet = _packet(stock)
    baseline = _native(packet)
    assert FINANCIAL_VALUES[0] in baseline.prompt
    raw = baseline.evidence.model_dump(mode="json")
    row = next(ref for ref in raw["evidence"] if ref["source_ref"] == "stock.current_price_context")
    assert row["source_use"]["source_class"] == "PRICE_TIMING"
    assert row["source_use"]["core_current_fact"] is False
    ref_id = row["ref_id"]
    row.update(category="earnings", label=_unowned_text(PRICES[0]), statement=_unowned_text(PRICES[0]))
    try:
        supplied = DecisionEvidencePacket.model_validate(raw)
        view = _native(packet, evidence=supplied)
    except ValueError as exc:
        assert "fundamental_" in str(exc), "Only a source-boundary rejection satisfies this control"
        return
    assert ref_id not in accepted_v2_fundamental_core_ref_catalog(view.context)
    assert ref_id not in view.context.evidence_ownership[0].core_ref_ids
    _assert_unowned_absent(view)
    assert FINANCIAL_VALUES[0] in view.prompt


@pytest.mark.parametrize("sibling", ("label", "value", "owner_ref"))
def test_quality_ref_arbitrary_siblings_are_rejected_or_closed_projected(sibling):
    stock = _financial_stock()
    stock["current_price_context"] = {"availability": "price_only"}
    packet = _packet(stock)
    baseline = _native(packet)
    assert FINANCIAL_VALUES[0] in baseline.prompt
    raw = baseline.evidence.model_dump(mode="json")
    row = next(ref for ref in raw["evidence"] if ref["ref_id"] == "quality:current_price_context")
    assert row["source_use"]["source_class"] == "QUALITY_LIMIT"
    original_statement = row["statement"]
    if sibling == "owner_ref":
        row["source_use"]["owner_ref"] = _unowned_text(PRICES[0])
    else:
        row[sibling] = _unowned_text(PRICES[0])
    assert row["statement"] == original_statement
    assert "R21_UNOWNED_PRICE_MACD" in _dump(row)
    try:
        supplied = DecisionEvidencePacket.model_validate(raw)
        view = _native(packet, evidence=supplied)
    except ValueError as exc:
        assert "fundamental_" in str(exc), "Unrelated fixture errors are not admission rejections"
        return
    _assert_unowned_absent(view)
    assert FINANCIAL_VALUES[0] in view.prompt
    assert view.payload == baseline.payload
    assert view.prompt == baseline.prompt


@pytest.mark.parametrize("surface", ("catalog_fields", "typed_ref"))
def test_financial_raw_siblings_never_enter_core_alias_or_stage2_fundamental_evidence(surface):
    stock = _financial_stock()
    # Keep a real timing channel so both stage alias catalogs are nonempty.
    stock["current_price_context"] = {
        "availability": "price_only", "current_price": 123.45, "currency": "USD",
    }
    if surface == "catalog_fields":
        stock["fact_catalog"][0]["fields"]["unadmitted_sibling"] = {
            "statement": _unowned_text(PRICES[0]), "price": PRICES[0],
        }
    packet = _packet(stock)
    raw_before = deepcopy(packet)
    evidence = build_decision_evidence_packet(packet=packet, stock=stock)
    ref_id = "canonical:r21:ocf:current"
    if surface == "typed_ref":
        raw = evidence.model_dump(mode="json")
        row = next(ref for ref in raw["evidence"] if ref["ref_id"] == ref_id)
        row.update(label=_unowned_text(PRICES[0]), statement=_unowned_text(PRICES[0]), value=str(PRICES[0]))
        evidence = DecisionEvidencePacket.model_validate(raw)
    original = next(ref for ref in evidence.evidence if ref.ref_id == ref_id)
    assert original.financial_context is not None
    if surface == "catalog_fields":
        assert "R21_UNOWNED_PRICE_MACD" in _dump(stock["fact_catalog"][0]["fields"])
    else:
        assert "R21_UNOWNED_PRICE_MACD" in original.statement
    view = _native(packet, evidence=evidence)
    _assert_unowned_absent(view)
    assert ref_id in accepted_v2_fundamental_core_ref_catalog(view.context)
    assert FINANCIAL_VALUES[0] in view.prompt

    owned = build_owned_evidence_packet(evidence, stock=stock)
    core_aliases, _ = stage_alias_catalogs(owned)
    assert ref_id in core_aliases.by_ref
    alias_payload = core_aliases.model_dump(mode="json")
    assert "R21_UNOWNED_PRICE_MACD" not in _dump(alias_payload)
    assert str(PRICES[0]) not in _dump(alias_payload)
    assert FINANCIAL_VALUES[0] in core_aliases.by_ref[ref_id].statement

    # Existing synthetic Core fixture exercises transport only, not accepted judgment.
    stage2_prompt = accepted_v2_production_prompt(
        view.context, fundamental_cores=(_fundamental_core(TICKER, ref_id),),
    )
    marker = "\nPRODUCTION_V2_CONTEXT:\n"
    assert stage2_prompt.count(marker) == 1
    stage2 = json.loads(stage2_prompt.split(marker, 1)[1])
    fundamental = stage2[0]["fundamental_core_evidence"]
    projected = next(row for row in fundamental["evidence"] if row["ref_id"] == ref_id)
    assert "R21_UNOWNED_PRICE_MACD" not in _dump(fundamental)
    assert str(PRICES[0]) not in _dump(fundamental)
    assert FINANCIAL_VALUES[0] in projected["statement"]
    assert packet == raw_before
