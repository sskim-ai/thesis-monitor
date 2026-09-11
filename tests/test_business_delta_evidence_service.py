from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import pytest

from app.services.business_delta_evidence_service import (
    BusinessDeltaCapability,
    BusinessDeltaEvidenceRole,
    attach_business_delta_evidence_view,
    build_business_delta_evidence_view,
    build_business_delta_constrained_batch_schema,
    business_delta_property_enums,
    validate_business_delta_candidate,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialComparison,
    FinancialComparisonKind,
    FinancialContext,
    FinancialEvidenceQuality,
    FinancialEvidenceStatus,
    FinancialPeriod,
    FinancialPeriodType,
)
from app.services.direction_timing_ownership_service import (
    DirectionalCoreCandidate,
    EvidenceDomain,
    OwnedEvidencePacket,
    OwnedEvidenceRef,
)
from app.services.structured_autonomy_alias_service import (
    build_evidence_alias_catalog,
    compact_alias_ai_context,
)


FIXTURES = Path("tests/fixtures/business_delta_evidence_capability_m12ai.json")


def _ref(
    fixture_id: str,
    *,
    category: EvidenceCategory,
    statement: str,
    source_ref: str,
    financial_context: FinancialContext | None = None,
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=f"fixture:{fixture_id}",
        category=category,
        label=fixture_id,
        statement=statement,
        as_of="2026-09-11",
        source_ref=source_ref,
        financial_context=financial_context,
    )


def _comparison() -> FinancialContext:
    return FinancialContext(
        metric="operating_income",
        currency="USD",
        unit_scale=1,
        period=FinancialPeriod(
            type=FinancialPeriodType.QTD,
            start=date(2026, 4, 1),
            end=date(2026, 6, 30),
            duration_days=91,
        ),
        entity_scope="issuer_consolidated",
        statement_basis="official_filing_financial_statement",
        evidence_status=FinancialEvidenceStatus.DIRECT_REPORTED,
        quality=FinancialEvidenceQuality.VERIFIED,
        comparison=FinancialComparison(
            kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
            input_source_refs=("fixture:prior-period",),
        ),
    )


def _fixture_rows(kind: str, fixture_id: str) -> list[tuple[DecisionEvidenceRef, EvidenceDomain]]:
    if kind == "stored_thesis":
        return [
            (
                _ref(
                    fixture_id,
                    category=EvidenceCategory.THESIS,
                    statement="Capital allocation discipline is a stored thesis driver.",
                    source_ref="stock.thesis.core_thesis",
                ),
                EvidenceDomain.BUSINESS_CURRENT,
            )
        ]
    if kind == "configured_condition":
        return [
            (
                _ref(
                    fixture_id,
                    category=EvidenceCategory.THESIS,
                    statement="A margin recovery would strengthen the configured thesis.",
                    source_ref="stock.thesis.strengthen_conditions",
                ),
                EvidenceDomain.BUSINESS_CURRENT,
            )
        ]
    if kind == "single_period_operating":
        return [
            (
                _ref(
                    fixture_id,
                    category=EvidenceCategory.EARNINGS,
                    statement="Current Q2 operating income is USD 40 million.",
                    source_ref="official.current.operating_income",
                ),
                EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
            )
        ]
    if kind == "verified_comparison":
        return [
            (
                _ref(
                    fixture_id,
                    category=EvidenceCategory.EARNINGS,
                    statement="Comparable-period operating income improved.",
                    source_ref="official.comparison.operating_income",
                    financial_context=_comparison(),
                ),
                EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
            )
        ]
    if kind == "dated_issuer_event":
        return [
            (
                _ref(
                    fixture_id,
                    category=EvidenceCategory.CATALYSTS,
                    statement=json.dumps(
                        {
                            "baseline_state": "authorized",
                            "current_state": "cancelled",
                            "event_date": "2026-09-11",
                        }
                    ),
                    source_ref="official.issuer.capital_allocation_event",
                ),
                EvidenceDomain.CAPITAL_ALLOCATION_CURRENT,
            )
        ]
    if kind == "price_transition":
        return [
            (
                _ref(
                    fixture_id,
                    category=EvidenceCategory.PRICE_STRUCTURE,
                    statement="Price confirmed above resistance.",
                    source_ref="stock.fact_catalog.monitoring:price_confirmation_transition",
                ),
                EvidenceDomain.PRICE_CONTEXT,
            )
        ]
    if kind == "market_expectation_change":
        return [
            (
                _ref(
                    fixture_id,
                    category=EvidenceCategory.EXPECTATIONS,
                    statement="Consensus expectations increased.",
                    source_ref="official.market_expectation_change",
                ),
                EvidenceDomain.MARKET_EXPECTATIONS,
            )
        ]
    if kind == "ambiguous_event":
        return [
            (
                _ref(
                    fixture_id,
                    category=EvidenceCategory.CATALYSTS,
                    statement="A business transition was reported without a comparable baseline.",
                    source_ref="official.issuer.business_transition",
                ),
                EvidenceDomain.BUSINESS_CURRENT,
            )
        ]
    if kind == "immaterial_positive_change":
        return [
            (
                _ref(
                    fixture_id,
                    category=EvidenceCategory.EARNINGS,
                    statement="Comparable operating result improved slightly.",
                    source_ref="fixture.immaterial-positive-change",
                ),
                EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
            )
        ]
    if kind == "conflicting_changes":
        return [
            (
                _ref(
                    fixture_id + ":positive",
                    category=EvidenceCategory.EARNINGS,
                    statement="Comparable operating profit improved.",
                    source_ref="fixture.conflict-positive",
                ),
                EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
            ),
            (
                _ref(
                    fixture_id + ":negative",
                    category=EvidenceCategory.EARNINGS_QUALITY,
                    statement="Comparable cash conversion deteriorated.",
                    source_ref="fixture.conflict-negative",
                ),
                EvidenceDomain.LIQUIDITY_CASHFLOW_CURRENT,
            ),
        ]
    raise AssertionError(f"unknown_fixture_kind:{kind}")


def _view(kind: str, fixture_id: str = "DELTA-CAP"):
    rows = _fixture_rows(kind, fixture_id)
    packet = DecisionEvidencePacket(
        packet_id=f"packet:{fixture_id}",
        ticker=fixture_id,
        company_name=fixture_id,
        market="us",
        assessment_date="2026-09-11",
        horizon="12m",
        evidence=tuple(ref for ref, _domain in rows),
        prohibited_claims=(),
        evidence_sha256=f"sha:{fixture_id}",
    )
    owned = OwnedEvidencePacket(
        source_packet=packet,
        evidence=tuple(
            OwnedEvidenceRef(ref=ref, domain=domain) for ref, domain in rows
        ),
    )
    catalog = build_evidence_alias_catalog(packet)
    context = compact_alias_ai_context(packet, catalog)
    return build_business_delta_evidence_view(
        owned,
        catalog,
        context=context,
    ), catalog, context


def _candidate(view, change: str, refs: list[str], text: str = "근거에 따른 판단입니다."):
    return {
        "ticker": view.ticker,
        "business_thesis_change": change,
        "business_thesis_context": {"text": text, "evidence_refs": refs},
    }


def test_required_ten_capability_fixtures() -> None:
    document = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert document["contract"] == "business-delta-evidence-capability-v1"
    assert len(document["fixtures"]) == 10
    for fixture in document["fixtures"]:
        view, _catalog, _context = _view(fixture["kind"], fixture["id"])
        assert view.capability.value == fixture["expected"], fixture


def test_baseline_and_current_single_point_never_become_delta_refs() -> None:
    thesis, _catalog, _context = _view("stored_thesis")
    current, _catalog, _context = _view("single_period_operating")
    assert thesis.items[0].role == BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT
    assert current.items[0].role == BusinessDeltaEvidenceRole.CURRENT_CONTEXT_ONLY
    assert not thesis.eligible_change_refs
    assert not current.eligible_change_refs


def test_dynamic_schema_makes_unchanged_structurally_mandatory() -> None:
    view, catalog, _context = _view("stored_thesis")
    schema = build_business_delta_constrained_batch_schema(
        candidate_schema=DirectionalCoreCandidate.model_json_schema(),
        contract="directional-core-batch-v1",
        packet_id="packet",
        aliases_by_ticker={view.ticker: tuple(catalog.by_alias)},
        views={view.ticker: view},
    )
    candidate = schema["properties"]["candidates"]["items"]["anyOf"][0]
    assert candidate["properties"]["business_thesis_change"]["enum"] == [
        "UNCHANGED"
    ]


def test_dynamic_schema_preserves_all_choices_for_ai_judgment() -> None:
    view, catalog, _context = _view("verified_comparison")
    schema = build_business_delta_constrained_batch_schema(
        candidate_schema=DirectionalCoreCandidate.model_json_schema(),
        contract="directional-core-batch-v1",
        packet_id="packet",
        aliases_by_ticker={view.ticker: tuple(catalog.by_alias)},
        views={view.ticker: view},
    )
    candidate = schema["properties"]["candidates"]["items"]["anyOf"][0]
    assert candidate["properties"]["business_thesis_change"]["enum"] == [
        "STRENGTHENED",
        "UNCHANGED",
        "WEAKENED",
        "UNRESOLVED",
    ]


def test_ambiguous_input_hard_stops_before_schema_generation() -> None:
    view, _catalog, _context = _view("ambiguous_event")
    assert view.capability == BusinessDeltaCapability.INPUT_AMBIGUOUS
    with pytest.raises(ValueError, match="business_delta_input_ambiguous_pre_model"):
        business_delta_property_enums({view.ticker: view})


def test_changed_output_requires_an_eligible_delta_ref() -> None:
    view, _catalog, _context = _view("verified_comparison")
    result = validate_business_delta_candidate(
        _candidate(view, "STRENGTHENED", []),
        view,
    )
    assert result["status"] == "FAIL"
    assert "BUSINESS_DELTA_CHANGED_WITHOUT_ELIGIBLE_REF" in result["errors"]


def test_ai_judgment_can_remain_unchanged_for_immaterial_change() -> None:
    view, _catalog, _context = _view("immaterial_positive_change")
    result = validate_business_delta_candidate(
        _candidate(view, "UNCHANGED", [view.eligible_change_refs[0]]),
        view,
    )
    assert result["status"] == "PASS"


def test_unresolved_requires_real_eligible_conflict() -> None:
    conflict, _catalog, _context = _view("conflicting_changes")
    accepted = validate_business_delta_candidate(
        _candidate(conflict, "UNRESOLVED", list(conflict.eligible_change_refs)),
        conflict,
    )
    assert accepted["status"] == "PASS"

    one_sided, _catalog, _context = _view("verified_comparison")
    rejected = validate_business_delta_candidate(
        _candidate(one_sided, "UNRESOLVED", list(one_sided.eligible_change_refs)),
        one_sided,
    )
    assert rejected["status"] == "FAIL"
    assert "BUSINESS_DELTA_UNRESOLVED_WITHOUT_ELIGIBLE_AMBIGUITY" in rejected["errors"]


def test_unchanged_context_cannot_claim_that_the_thesis_strengthened() -> None:
    view, _catalog, _context = _view("stored_thesis")
    result = validate_business_delta_candidate(
        _candidate(
            view,
            "UNCHANGED",
            [view.baseline_context_refs[0]],
            "저장된 논리가 강화된 것으로 판단합니다.",
        ),
        view,
    )
    assert result["status"] == "FAIL"
    assert "BUSINESS_DELTA_UNCHANGED_CONTEXT_ASSERTS_CHANGE" in result["errors"]


def test_model_view_is_attached_without_removing_absolute_core_evidence() -> None:
    view, _catalog, context = _view("stored_thesis")
    enriched = attach_business_delta_evidence_view(context, view)
    assert enriched["evidence"] == context["evidence"]
    assert enriched["business_delta_evidence_view"]["capability"] == "UNCHANGED_ONLY"
    assert enriched["business_delta_evidence_view"]["eligible_change_refs"] == []
