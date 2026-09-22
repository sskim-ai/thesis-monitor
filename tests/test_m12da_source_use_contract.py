from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

from scripts.m12da_offline_proof import WC_RELATION_IDS, _subject_authorities
from scripts.m12da_source_use_contract import (
    DEFINITION_BINDING_CONTRACT,
    TRUSTED_AUTHORITY_ORIGIN,
    SourceUse,
    build_source_use_projection,
    canonical_sha256,
    freeze_security_identity_binding,
    frozen_source_authority,
    is_use_allowed,
    model_source_use_projection,
    validate_metric_definition_binding,
    validate_selected_refs,
)


def test_offline_proof_matches_canonical_working_capital_relation_identity() -> None:
    relation_id = WC_RELATION_IDS["000660"]
    source_authorities, claim_authorities = _subject_authorities(
        ticker="000660",
        context={"decision_evidence": []},
        catalog={"all_evidence_refs": [relation_id]},
        wc_periods={"000660": "2026-06-30"},
    )
    assert claim_authorities == []
    assert [row["ref_id"] for row in source_authorities] == [relation_id]
    assert source_authorities[0]["allowed_uses"] == [
        SourceUse.CONTEXT,
        SourceUse.EARNINGS_QUALITY_CONTEXT,
    ]


def _claim(
    claim_ref: str,
    parent_refs: list[str],
    *,
    polarity: str = "BEARISH",
) -> dict[str, object]:
    return {
        "claim_ref": claim_ref,
        "ticker": "RENAMED",
        "claim": {
            "text": "구조화된 근거 주장입니다.",
            "polarity": polarity,
            "logical_condition": None,
        },
        "parent_source_refs": parent_refs,
    }


def _catalog() -> dict[str, object]:
    claims = [
        _claim("claim:business", ["source:business"]),
        _claim("claim:working-capital", ["source:working-capital"]),
        _claim("claim:working-capital-positive", ["source:working-capital"], polarity="BULLISH"),
        _claim("claim:expectation", ["source:expectation"]),
        _claim("claim:mixed", ["source:business", "source:working-capital"]),
        _claim("claim:alias-one", ["source:wc-alias-one"]),
        _claim("claim:alias-two", ["source:wc-alias-two"]),
    ]
    return {
        "ticker": "RENAMED",
        "all_evidence_refs": [
            "source:business",
            "source:working-capital",
            "source:expectation",
            "source:wc-alias-one",
            "source:wc-alias-two",
            "canonical:valuation",
            "canonical:price",
        ],
        "claim_refs": [row["claim_ref"] for row in claims],
        "atomic_claims": claims,
        "valuation_evidence_refs": ["canonical:valuation"],
        "timing_evidence_refs": ["canonical:price"],
        "positive_quality_refs": [],
    }


def _restricted_authorities() -> list[dict[str, object]]:
    wc_allowed = [SourceUse.CONTEXT, SourceUse.EARNINGS_QUALITY_CONTEXT]
    wc_prohibited = [
        SourceUse.PASS_A_ARCHETYPE,
        SourceUse.PASS_A_VALUATION_TIER,
        SourceUse.OVERALL_DIRECTION,
        SourceUse.HOLDER_STANCE,
        SourceUse.NEW_BUYER_EXECUTION_RISK,
        SourceUse.VALUATION,
    ]
    return [
        frozen_source_authority(
            ticker="RENAMED",
            ref_id="source:working-capital",
            source_type="derived_working_capital_relation",
            source_scope="typed_relation_and_cautious_earnings_quality_context_only",
            allowed_uses=wc_allowed,
            prohibited_uses=wc_prohibited,
            denial_reasons=["working_capital_only_status_or_valuation_change"],
            authority_basis="canonical_working_capital_owner_contract",
            fact_kind="derived_relation",
        ),
        frozen_source_authority(
            ticker="RENAMED",
            ref_id="source:expectation",
            source_type="market_expectations",
            source_scope="expectations_price_confidence_entry_only",
            allowed_uses=[
                SourceUse.CONTEXT,
                SourceUse.EXPECTATIONS_CONTEXT,
                SourceUse.PRICE_ENTRY_CONTEXT,
                SourceUse.CONFIDENCE,
                SourceUse.ENTRY,
            ],
            prohibited_uses=[
                SourceUse.PASS_A_ARCHETYPE,
                SourceUse.PASS_A_VALUATION_TIER,
                SourceUse.OVERALL_DIRECTION,
                SourceUse.HOLDER_STANCE,
                SourceUse.NEW_BUYER_EXECUTION_RISK,
            ],
            denial_reasons=["expectation_reflection_not_independent_business_impairment"],
            authority_basis="structured_market_expectations_owner",
            fact_kind="hypothetical_scenario",
        ),
        *[
            frozen_source_authority(
                ticker="RENAMED",
                ref_id=ref_id,
                source_type="derived_working_capital_relation_alias",
                source_scope="context_only",
                allowed_uses=wc_allowed,
                prohibited_uses=wc_prohibited,
                denial_reasons=["working_capital_only_status_or_valuation_change"],
                authority_basis="canonical_working_capital_owner_contract",
                independence_group="same-restricted-relation",
                fact_kind="derived_relation",
            )
            for ref_id in ("source:wc-alias-one", "source:wc-alias-two")
        ],
    ]


def _projection() -> dict[str, object]:
    return build_source_use_projection(
        ticker="RENAMED",
        input_generation_id="frozen-generation",
        catalog=_catalog(),
        source_authorities=_restricted_authorities(),
    )


def test_working_capital_relation_keeps_context_but_cannot_drive_any_decision_axis() -> None:
    projection = _projection()
    assert is_use_allowed(
        projection,
        ref_id="source:working-capital",
        use=SourceUse.EARNINGS_QUALITY_CONTEXT,
    )
    for ref_id in ("claim:working-capital", "claim:working-capital-positive"):
        for use in (
            SourceUse.PASS_A_ARCHETYPE,
            SourceUse.PASS_A_VALUATION_TIER,
            SourceUse.OVERALL_DIRECTION,
            SourceUse.HOLDER_STANCE,
            SourceUse.NEW_BUYER_EXECUTION_RISK,
        ):
            assert not is_use_allowed(projection, ref_id=ref_id, use=use)


def test_expectation_reflection_remains_entry_context_but_not_business_downgrade_support() -> None:
    projection = _projection()
    assert is_use_allowed(projection, ref_id="source:expectation", use=SourceUse.ENTRY)
    assert not is_use_allowed(
        projection,
        ref_id="claim:expectation",
        use=SourceUse.OVERALL_DIRECTION,
    )


def test_mixed_parent_claim_cannot_launder_restricted_proposition() -> None:
    projection = _projection()
    assert is_use_allowed(
        projection,
        ref_id="claim:business",
        use=SourceUse.OVERALL_DIRECTION,
    )
    assert not is_use_allowed(
        projection,
        ref_id="claim:mixed",
        use=SourceUse.OVERALL_DIRECTION,
    )


def test_restricted_aliases_do_not_become_independent_support_by_cardinality() -> None:
    projection = _projection()
    validation = validate_selected_refs(
        projection,
        refs=["claim:alias-one", "claim:alias-two"],
        use=SourceUse.OVERALL_DIRECTION,
        require_any=True,
    )
    assert validation["status"] == "FAIL"
    assert validation["error_count"] == 2


def test_unknown_and_cross_subject_authority_fail_closed() -> None:
    catalog = _catalog()
    forged = frozen_source_authority(
        ticker="OTHER",
        ref_id="source:business",
        source_type="model_asserted_permission",
        source_scope="untrusted",
        allowed_uses=[SourceUse.OVERALL_DIRECTION],
        authority_basis="model_output",
    )
    projection = build_source_use_projection(
        ticker="RENAMED",
        input_generation_id="frozen-generation",
        catalog=catalog,
        source_authorities=[forged],
    )
    assert projection["status"] == "FAIL"
    assert "source_authority_cross_subject:source:business" in projection["projection_errors"]
    validation = validate_selected_refs(
        projection,
        refs=["claim:not-present"],
        use=SourceUse.OVERALL_DIRECTION,
        require_any=True,
    )
    assert validation["errors"][0]["code"] == "SOURCE_USE_REF_UNKNOWN"


def test_same_subject_model_authored_authority_cannot_grant_permission() -> None:
    forged = {
        "ticker": "RENAMED",
        "ref_id": "source:business",
        "authority_origin": "MODEL_OUTPUT",
        "authority_state": "RESOLVED",
        "authority_basis": "model_authored_permission",
        "allowed_uses": [SourceUse.OVERALL_DIRECTION],
    }
    projection = build_source_use_projection(
        ticker="RENAMED",
        input_generation_id="frozen-generation",
        catalog=_catalog(),
        source_authorities=[forged],
    )
    assert projection["status"] == "FAIL"
    assert "source_authority_untrusted_origin:source:business" in projection["projection_errors"]


def test_empty_selection_and_unresolved_typed_authority_fail_closed() -> None:
    unresolved = {
        "ticker": "RENAMED",
        "ref_id": "source:business",
        "authority_origin": TRUSTED_AUTHORITY_ORIGIN,
        "source_type": "typed_source",
        "source_scope": "unresolved",
        "authority_state": "UNRESOLVED",
        "authority_basis": "missing_typed_permission",
        "allowed_uses": [SourceUse.CONTEXT, SourceUse.OVERALL_DIRECTION],
        "unresolved_cause": "typed_authority_missing",
    }
    projection = build_source_use_projection(
        ticker="RENAMED",
        input_generation_id="frozen-generation",
        catalog=_catalog(),
        source_authorities=[unresolved],
    )
    assert not is_use_allowed(
        projection,
        ref_id="source:business",
        use=SourceUse.OVERALL_DIRECTION,
    )
    assert not is_use_allowed(
        projection,
        ref_id="claim:business",
        use=SourceUse.OVERALL_DIRECTION,
    )
    validation = validate_selected_refs(
        projection,
        refs=[],
        use=SourceUse.OVERALL_DIRECTION,
        require_any=True,
    )
    assert validation["errors"] == [
        {
            "code": "SOURCE_USE_REQUIRED_REF_MISSING",
            "ref_id": None,
            "use": SourceUse.OVERALL_DIRECTION,
            "cause": "selected_ref_set_empty",
        }
    ]


def test_model_projection_contains_permissions_without_source_parser_noise() -> None:
    compact = model_source_use_projection(_projection())
    assert compact["contract"] == "m12da-shadow-source-use-projection-v1"
    assert "source_permissions" in compact
    assert "source_period" not in compact["source_permissions"][0]


def _binding(*, definition_id: str, value: str, value_type: str) -> dict[str, object]:
    identity = freeze_security_identity_binding(
        ticker="CPNG",
        issuer_id="sec:0001834584",
        venue="NYSE",
        security_type="common-stock",
        official_sources=[
            {
                "provider": "sec_edgar_submissions",
                "document_sha256": (
                    "d8e942a44d498b82f8348f95eb6742564a200cafcac3df02cd09d0bc77a53c5d"
                ),
                "locator": "tickers[0]/exchanges[0]",
                "assertion": "ticker=CPNG;exchange=NYSE",
            },
            {
                "provider": "sec_edgar_exhibit",
                "document_sha256": (
                    "5368db524a113b654d7b575c00b409f8866a153a71a2fb990d6fd031e595962f"
                ),
                "locator": "official exhibit issuer identity",
                "assertion": "NYSE: CPNG",
            },
        ],
    )
    return {
        "contract": DEFINITION_BINDING_CONTRACT,
        "binding_id": f"binding:{definition_id}",
        "ticker": "CPNG",
        "issuer_id": "sec:0001834584",
        "security_id": identity["security_id"],
        "security_identity": identity,
        "metric_id": "trailing_free_cash_flow",
        "definition_id": definition_id,
        "formula": (
            "OCF_MINUS_PPE_PURCHASES_PLUS_PPE_SALE_PROCEEDS"
            if definition_id == "management-defined-fcf"
            else "OCF_MINUS_PPE_PURCHASES"
        ),
        "period_start": "2025-07-01",
        "period_end": "2026-06-30",
        "duration_days": 365,
        "comparison_basis": "FY2025_PLUS_H1_2026_MINUS_H1_2025_COMPARABLE",
        "currency": "USD",
        "unit": "USD",
        "consolidation_scope": "issuer_consolidated",
        "value_type": value_type,
        "value": value,
        "component_refs": ["ocf:ttm", "ppe-purchases:ttm", "ppe-sale-proceeds:q2"],
        "source": {
            "provider": "sec_edgar",
            "accession": "0001834584-26-000070",
            "document_type": "8-K",
            "exhibit": "99.1",
            "row_locator": "Free Cash Flow table / TTM ended 2026-06-30",
            "document_sha256": "5368db524a113b654d7b575c00b409f8866a153a71a2fb990d6fd031e595962f",
            "publication_date": "2026-08-04",
            "retrieval_date": "2026-09-18",
        },
        "historical_packet_carried_evidence": False,
        "claim_scope": "EXACT_METRIC_ONLY",
    }


def _expected_security_identity() -> dict[str, object]:
    return {
        "venue": "NYSE",
        "ticker": "CPNG",
        "issuer_id": "sec:0001834584",
        "security_id": "nyse:CPNG:common-stock",
    }


def test_management_and_ppe_only_fcf_remain_distinct_definition_bindings() -> None:
    management = _binding(
        definition_id="management-defined-fcf",
        value="105000000",
        value_type="REPORTED_NON_GAAP",
    )
    backend = _binding(
        definition_id="backend-ppe-only-fcf",
        value="99000000",
        value_type="DERIVED_METRIC",
    )
    backend["source"]["accession"] = "0001834584-26-000073"
    backend["source"]["document_type"] = "10-Q"
    backend["source"]["exhibit"] = "financial-statements"
    backend["source"]["row_locator"] = "cash-flow statement occurrences"
    assert (
        validate_metric_definition_binding(
            management,
            expected_security_identity=_expected_security_identity(),
        )["status"]
        == "PASS"
    )
    assert (
        validate_metric_definition_binding(
            backend,
            expected_security_identity=_expected_security_identity(),
        )["status"]
        == "PASS"
    )
    assert Decimal(management["value"]) - Decimal(backend["value"]) == Decimal("6000000")
    wrong_definition = validate_metric_definition_binding(
        management,
        expected={"definition_id": "backend-ppe-only-fcf"},
        expected_security_identity=_expected_security_identity(),
    )
    assert "definition_binding_expected_mismatch:definition_id" in wrong_definition["errors"]


def test_retrospective_binding_does_not_retroactively_source_historical_packet() -> None:
    binding = _binding(
        definition_id="management-defined-fcf",
        value="105000000",
        value_type="REPORTED_NON_GAAP",
    )
    validation = validate_metric_definition_binding(
        binding,
        expected_security_identity=_expected_security_identity(),
        replay_cutoff="2026-09-17",
        historical_use=True,
    )
    assert "historical_packet_did_not_carry_source_binding" in validation["errors"]


def test_definition_binding_requires_independent_expected_security_identity() -> None:
    binding = _binding(
        definition_id="management-defined-fcf",
        value="105000000",
        value_type="REPORTED_NON_GAAP",
    )
    missing_expected = validate_metric_definition_binding(binding)
    assert "definition_binding_expected_security_identity_missing" in missing_expected["errors"]

    forged = deepcopy(binding)
    forged["issuer_id"] = "sec:wrong"
    forged["security_identity"]["issuer_id"] = "sec:wrong"
    forged["security_identity"].pop("identity_sha256")
    forged["security_identity"]["identity_sha256"] = canonical_sha256(forged["security_identity"])
    validation = validate_metric_definition_binding(
        forged,
        expected_security_identity=_expected_security_identity(),
    )
    assert "security_identity_expected_mismatch:issuer_id" in validation["errors"]


def test_definition_binding_rejects_period_currency_issuer_cutoff_and_paragraph_laundering() -> (
    None
):
    binding = _binding(
        definition_id="management-defined-fcf",
        value="105000000",
        value_type="REPORTED_NON_GAAP",
    )
    binding["period_start"] = "2026-01-01"
    binding["currency"] = "KRW"
    binding["issuer_id"] = "sec:wrong"
    binding["claim_scope"] = "FULL_PARAGRAPH"
    binding["source"]["publication_date"] = "2026-09-18"
    validation = validate_metric_definition_binding(
        binding,
        expected={
            "period_start": "2025-07-01",
            "currency": "USD",
            "issuer_id": "sec:0001834584",
        },
        expected_security_identity=_expected_security_identity(),
        replay_cutoff="2026-09-17",
    )
    assert "partial_paragraph_laundering_blocked" in validation["errors"]
    assert "definition_binding_post_cutoff_source" in validation["errors"]
    assert "definition_binding_expected_mismatch:period_start" in validation["errors"]
    assert "definition_binding_expected_mismatch:currency" in validation["errors"]
    assert "definition_binding_expected_mismatch:issuer_id" in validation["errors"]


def test_claim_authority_cannot_expand_parent_permission() -> None:
    catalog = _catalog()
    claim_authority = {
        "ticker": "RENAMED",
        "claim_ref": "claim:working-capital",
        "authority_origin": TRUSTED_AUTHORITY_ORIGIN,
        "authority_state": "RESOLVED",
        "authority_basis": "forged_model_permission",
        "allowed_uses": [SourceUse.OVERALL_DIRECTION],
    }
    projection = build_source_use_projection(
        ticker="RENAMED",
        input_generation_id="frozen-generation",
        catalog=catalog,
        source_authorities=_restricted_authorities(),
        claim_authorities=[deepcopy(claim_authority)],
    )
    assert not is_use_allowed(
        projection,
        ref_id="claim:working-capital",
        use=SourceUse.OVERALL_DIRECTION,
    )
