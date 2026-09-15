from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.direction_timing_ownership_service import (
    EvidenceDomain,
    OwnedEvidencePacket,
    OwnedEvidenceRef,
)
from app.services.market_expectation_evidence_service import (
    MarketExpectationEvidenceRole,
    MarketExpectationStructuredBasis,
    attach_market_expectation_evidence_view,
    build_market_expectation_evidence_view,
    market_expectation_evidence_view_sha256,
    validate_market_expectation_candidate,
)
from app.services.structured_autonomy_alias_service import (
    build_evidence_alias_catalog,
    compact_alias_ai_context,
)
from app.services.two_stage_directional_service import (
    CORE_JUDGMENT_OUTPUT_CONTRACT,
    DirectionalCoreJudgment,
)
from scripts import business_delta_evidence_capability_m12ai as task
from scripts import directional_financial_context_m12 as m12


FIXTURES = Path("tests/fixtures/market_expectation_independence_m12ap.json")


def _ref(
    ref_id: str,
    *,
    category: EvidenceCategory,
    label: str,
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=category,
        label=label,
        statement=f"Structured fixture evidence for {label}.",
        as_of="2026-09-12",
        source_ref=f"fixture.{label}",
    )


def _fixture_view(
    *,
    basis_kind: str,
):
    expectation = _ref(
        "fixture:expectation",
        category=EvidenceCategory.EXPECTATIONS,
        label="market-expectation",
    )
    dependency = _ref(
        "fixture:dependency",
        category=EvidenceCategory.UNKNOWN,
        label="unresolved-condition",
    )
    operating = _ref(
        "fixture:operating",
        category=EvidenceCategory.EARNINGS,
        label="operating-evidence",
    )
    packet = DecisionEvidencePacket(
        packet_id="fixture:market-expectation",
        ticker="EXP-FIXTURE",
        company_name="Expectation Fixture",
        market="us",
        assessment_date="2026-09-12",
        horizon="12m",
        evidence=(expectation, dependency, operating),
        prohibited_claims=(),
        evidence_sha256="fixture-market-expectation-sha",
    )
    owned = OwnedEvidencePacket(
        source_packet=packet,
        evidence=(
            OwnedEvidenceRef(
                ref=expectation,
                domain=EvidenceDomain.MARKET_EXPECTATIONS,
            ),
            OwnedEvidenceRef(
                ref=dependency,
                domain=EvidenceDomain.DATA_QUALITY_LIMIT,
            ),
            OwnedEvidenceRef(
                ref=operating,
                domain=EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
            ),
        ),
    )
    catalog = build_evidence_alias_catalog(packet)
    if basis_kind == "conditional":
        bases = (
            MarketExpectationStructuredBasis(
                expectation_ref=expectation.ref_id,
                dependency_refs=(dependency.ref_id,),
            ),
        )
    elif basis_kind == "independent":
        bases = (
            MarketExpectationStructuredBasis(
                expectation_ref=expectation.ref_id,
                independently_observed=True,
                independence_basis_refs=(operating.ref_id,),
            ),
        )
    elif basis_kind == "unknown":
        bases = ()
    else:
        raise AssertionError(f"unknown basis kind: {basis_kind}")
    view = build_market_expectation_evidence_view(
        owned,
        catalog,
        structured_bases=bases,
    )
    aliases = {entry.canonical_ref: entry.alias for entry in catalog.entries}
    context = compact_alias_ai_context(packet, catalog)
    return view, catalog, context, aliases


def _expectation_item(view):
    assert len(view.expectation_items) == 1
    return view.expectation_items[0]


def test_fixture_inventory_covers_required_negative_and_positive_cases() -> None:
    document = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert document["contract"] == "market-expectation-independence-fixtures-v1"
    assert {row["id"] for row in document["fixtures"]} == {
        "EXP-INDEP-N01",
        "EXP-INDEP-N02",
        "EXP-INDEP-N03",
        "EXP-INDEP-N04",
        "EXP-INDEP-P01",
        "EXP-INDEP-P02",
        "EXP-INDEP-P03",
        "EXP-INDEP-P04",
        "EXP-INDEP-P05",
    }


def test_fictional_fic_fin_05_dependency_is_structured_before_model_use() -> None:
    _packets, owned, catalogs, _contexts = m12.fictional_inputs("m12ap-fixture")
    views = task._expectation_views(
        owned,
        catalogs,
        structured_bases=task._fictional_expectation_structured_bases(catalogs),
    )
    item = _expectation_item(views["FIC-FIN-05"])
    assert item.alias == "E07"
    assert item.role == MarketExpectationEvidenceRole.CONDITIONAL_CONTEXT_ONLY
    assert item.dependency_aliases == ("E08",)
    assert not item.material_anchor_eligible
    assert not item.dominant_evidence_eligible


def test_unspecified_expectation_independence_defaults_to_context_only() -> None:
    view, _catalog, _context, _aliases = _fixture_view(basis_kind="unknown")
    item = _expectation_item(view)
    assert item.role == MarketExpectationEvidenceRole.INDEPENDENCE_UNKNOWN
    assert not item.material_anchor_eligible
    assert not item.dominant_evidence_eligible


def test_source_category_alone_cannot_assert_independence() -> None:
    with pytest.raises(ValidationError, match="independence_basis_required"):
        MarketExpectationStructuredBasis(
            expectation_ref="fixture:expectation",
            independently_observed=True,
        )


def test_structured_independent_expectation_is_anchor_eligible() -> None:
    view, _catalog, _context, aliases = _fixture_view(basis_kind="independent")
    item = _expectation_item(view)
    expectation_alias = aliases["fixture:expectation"]
    assert item.role == MarketExpectationEvidenceRole.INDEPENDENT_DIRECTIONAL_SUPPORT
    assert item.material_anchor_eligible
    assert item.dominant_evidence_eligible
    candidate = {
        "ticker": view.ticker,
        "material_directional_anchor_basis": ["fixture:expectation"],
        "dominant_evidence": {"evidence_refs": ["fixture:expectation"]},
    }
    assert validate_market_expectation_candidate(candidate, view)["status"] == "PASS"
    assert expectation_alias in view.material_anchor_eligible_aliases


def test_context_attachment_preserves_existing_business_delta_view() -> None:
    view, _catalog, context, _aliases = _fixture_view(basis_kind="conditional")
    enriched = attach_market_expectation_evidence_view(
        {**context, "business_delta_evidence_view": {"capability": "UNCHANGED_ONLY"}},
        view,
    )
    assert enriched["business_delta_evidence_view"]["capability"] == "UNCHANGED_ONLY"
    assert enriched["market_expectation_evidence_view"]["expectations"]


def test_dynamic_schema_limits_only_anchor_and_dominant_fields() -> None:
    _packets, owned, catalogs, contexts = m12.fictional_inputs("m12ap-schema")
    delta_views = task._views(owned, catalogs, contexts)
    expectation_views = task._expectation_views(
        owned,
        catalogs,
        structured_bases=task._fictional_expectation_structured_bases(catalogs),
    )
    tickers = m12.CONTEXTS[1]
    schema = task._batch_schema(
        model=DirectionalCoreJudgment,
        contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
        packet_id="m12ap-schema",
        tickers=tickers,
        catalogs=catalogs,
        views=delta_views,
        expectation_views=expectation_views,
    )
    choice = schema["properties"]["candidates"]["items"]["anyOf"][0]
    properties = choice["properties"]
    anchor_name = properties["material_directional_anchor_basis"]["items"]["$ref"].split("/")[-1]
    dominant_name = properties["dominant_evidence"]["$ref"].split("/")[-1]
    dominant_alias_name = schema["$defs"][dominant_name]["properties"]["evidence_refs"]["items"]["$ref"].split("/")[-1]
    assert "E07" not in schema["$defs"][anchor_name]["enum"]
    assert "E07" not in schema["$defs"][dominant_alias_name]["enum"]
    assert "E07" in schema["$defs"]["T1_EvidenceAlias"]["enum"]
    assert properties["market_expectation_context"]["$ref"] == (
        "#/$defs/T1_DirectionalClaim"
    )


def test_context_only_expectation_anchor_and_dominant_are_rejected() -> None:
    view, _catalog, _context, _aliases = _fixture_view(basis_kind="conditional")
    anchor = validate_market_expectation_candidate(
        {
            "ticker": view.ticker,
            "material_directional_anchor_basis": ["fixture:expectation"],
        },
        view,
    )
    dominant = validate_market_expectation_candidate(
        {
            "ticker": view.ticker,
            "dominant_evidence": {"evidence_refs": ["fixture:expectation"]},
        },
        view,
    )
    assert anchor["status"] == "FAIL"
    assert anchor["context_only_expectation_material_anchor_violation_count"] == 1
    assert dominant["status"] == "FAIL"
    assert dominant["context_only_expectation_dominant_evidence_violation_count"] == 1


def test_context_only_expectation_driver_requires_other_evidence() -> None:
    view, _catalog, _context, _aliases = _fixture_view(basis_kind="conditional")
    rejected = validate_market_expectation_candidate(
        {
            "ticker": view.ticker,
            "sell_drivers": [
                {
                    "classification": "CONFIRMED_DOWNSIDE",
                    "evidence_refs": ["fixture:expectation"],
                }
            ],
        },
        view,
    )
    accepted = validate_market_expectation_candidate(
        {
            "ticker": view.ticker,
            "sell_drivers": [
                {
                    "classification": "OTHER_EVIDENCE",
                    "evidence_refs": ["fixture:expectation"],
                }
            ],
            "market_expectation_context": {
                "evidence_refs": ["fixture:expectation"]
            },
        },
        view,
    )
    assert rejected["status"] == "FAIL"
    assert rejected[
        "context_only_expectation_driver_classification_violation_count"
    ] == 1
    assert accepted["status"] == "PASS"


def test_non_expectation_anchors_support_direction_with_conditional_context() -> None:
    view, _catalog, _context, _aliases = _fixture_view(basis_kind="conditional")
    result = validate_market_expectation_candidate(
        {
            "ticker": view.ticker,
            "material_directional_anchor_basis": ["fixture:operating"],
            "dominant_evidence": {"evidence_refs": ["fixture:operating"]},
            "market_expectation_context": {
                "evidence_refs": ["fixture:expectation"]
            },
        },
        view,
    )
    assert result["status"] == "PASS"


def test_unknown_independence_is_context_not_negative_evidence() -> None:
    view, _catalog, _context, _aliases = _fixture_view(basis_kind="unknown")
    result = validate_market_expectation_candidate(
        {
            "ticker": view.ticker,
            "market_expectation_context": {
                "evidence_refs": ["fixture:expectation"]
            },
        },
        view,
    )
    assert result["status"] == "PASS"
    assert not result["errors"]


def test_pre_post_view_hash_mismatch_is_rejected() -> None:
    view, _catalog, _context, _aliases = _fixture_view(basis_kind="conditional")
    actual = market_expectation_evidence_view_sha256(view)
    result = validate_market_expectation_candidate(
        {"ticker": view.ticker},
        view,
        pre_model_view_sha256="0" * 64,
    )
    assert actual != "0" * 64
    assert result["status"] == "FAIL"
    assert result["pre_post_expectation_view_identity_mismatch_count"] == 1
