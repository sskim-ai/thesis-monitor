from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m12cq_two_pass_contract import build_pass_b_subject_context
from scripts.m12cv_pass_b_capability_contract import (
    build_pass_b_capability_catalog,
    validate_capability_selection,
)
from scripts.m12da_source_use_contract import (
    SourceUse,
    build_source_use_projection,
    build_trusted_source_authority_manifest,
    canonical_sha256,
    freeze_security_identity_binding,
    freeze_source_use_binding,
    freeze_source_use_input_expectation,
    frozen_source_authority,
    is_use_allowed,
    validate_security_identity_binding,
    validate_selected_refs,
    validate_source_use_projection_binding,
)


def _claim(claim_ref: str, parent: str, polarity: str) -> dict[str, object]:
    return {
        "claim_ref": claim_ref,
        "ticker": "RENAMED",
        "claim": {
            "text": "동결된 구조화 근거 주장입니다.",
            "polarity": polarity,
            "reason_role": "FUNDAMENTAL",
            "logical_condition": None,
        },
        "parent_source_refs": [parent],
    }


def _catalog() -> dict[str, object]:
    claims = [
        _claim("claim:bull", "source:business", "BULLISH"),
        _claim("claim:bear", "source:business", "BEARISH"),
        _claim("claim:wc", "canonical:working-capital-relation:new-id", "BEARISH"),
    ]
    return {
        "ticker": "RENAMED",
        "all_evidence_refs": [
            "source:business",
            "canonical:working-capital-relation:new-id",
            "canonical:working-capital-reported:new-id",
            "source:expectations",
            "canonical:valuation",
            "canonical:price",
            "canonical:security_basis:current",
        ],
        "core_evidence_refs": [
            "source:business",
            "canonical:working-capital-relation:new-id",
            "canonical:valuation",
        ],
        "timing_evidence_refs": ["canonical:price"],
        "valuation_evidence_refs": ["canonical:valuation"],
        "security_valuation_basis_refs": ["canonical:security_basis:current"],
        "positive_quality_refs": [],
        "claim_refs": [str(row["claim_ref"]) for row in claims],
        "atomic_claims": claims,
        "entry_catalog": {
            "ticker": "RENAMED",
            "current_price": {
                "value": 90.0,
                "as_of": "2026-09-18",
                "currency": "USD",
                "ref_id": "canonical:price",
            },
            "tactical_candidates": [],
            "unresolved_policy": {"tactical_unresolved_reason": "unavailable"},
        },
    }


def _metadata() -> list[dict[str, object]]:
    return [
        {
            "ref_id": "source:business",
            "category": "thesis",
            "label": "핵심 투자 논리",
            "as_of": "2026-09-18",
            "statement": "동결된 사업 근거",
        },
        {
            "ref_id": "canonical:working-capital-relation:new-id",
            "category": "earnings_quality",
            "label": "working_capital_inventory_relation",
            "as_of": "2026-06-30",
            "statement": {
                "relation_semantics_contract": "working-capital-relation-semantics-v1",
                "relation_id": "working-capital-relation:new-id",
                "semantic_scope": "exact_total_inventory",
            },
        },
        {
            "ref_id": "canonical:working-capital-reported:new-id",
            "category": "earnings_quality",
            "label": "working_capital_lineage_input",
            "as_of": "2026-06-30",
            "statement": {
                "relation_id": "working-capital-relation:new-id",
                "semantic_scope": "exact_total_inventory",
            },
        },
        {
            "ref_id": "source:expectations",
            "category": "expectations",
            "label": "시장 기대",
            "as_of": "2026-09-18",
            "statement": {"level": "high", "priced_in": "partly"},
        },
        {
            "ref_id": "canonical:valuation",
            "category": "valuation",
            "label": "valuation",
            "as_of": "2026-09-18",
            "statement": "동결된 밸류에이션 근거",
        },
        {
            "ref_id": "canonical:price",
            "category": "price_structure",
            "label": "price",
            "as_of": "2026-09-18",
            "statement": "동결된 가격 근거",
        },
        {
            "ref_id": "canonical:security_basis:current",
            "category": "quality",
            "label": "security_basis",
            "as_of": "2026-09-18",
            "statement": "동결된 증권 기준",
        },
    ]


def _strict_projection() -> tuple[
    dict[str, object], dict[str, object], dict[str, object], dict[str, object]
]:
    catalog = _catalog()
    metadata = _metadata()
    business_row = metadata[0]
    manifest = build_trusted_source_authority_manifest(
        ticker="RENAMED",
        source_generation_id="source-generation",
        catalog=catalog,
        source_metadata=metadata,
        trusted_owner_overrides=[
            {
                "ref_id": "source:business",
                "catalog_sha256": canonical_sha256(catalog),
                "source_metadata_sha256": canonical_sha256(business_row),
                "source_type": "frozen_legacy_business_evidence",
                "source_scope": "exact_source_business_decision_owner",
                "authority_basis": "explicit_test_legacy_business_owner",
                "allowed_uses": [
                    SourceUse.CONTEXT,
                    SourceUse.BUSINESS_CONTEXT,
                    SourceUse.PASS_A_ARCHETYPE,
                    SourceUse.PASS_A_VALUATION_TIER,
                    SourceUse.OVERALL_DIRECTION,
                    SourceUse.HOLDER_STANCE,
                    SourceUse.NEW_BUYER_EXECUTION_RISK,
                ],
                "prohibited_uses": [SourceUse.VALUATION],
            }
        ],
    )
    expectation = freeze_source_use_input_expectation(
        ticker="RENAMED",
        source_generation_id="source-generation",
        execution_generation_id="execution-generation",
        catalog=catalog,
        source_metadata=metadata,
        authority_manifest=manifest,
    )
    projection = build_source_use_projection(
        ticker="RENAMED",
        input_generation_id="source-generation",
        execution_generation_id="execution-generation",
        catalog=catalog,
        authority_manifest=manifest,
        current_input_expectation=expectation,
    )
    binding = freeze_source_use_binding(
        projection=projection,
        authority_manifest=manifest,
        current_input_expectation=expectation,
    )
    return manifest, projection, binding, expectation


def _context() -> dict[str, object]:
    catalog = _catalog()
    return {
        "ticker": "RENAMED",
        "decision_evidence": deepcopy(_metadata()),
        "current_price": deepcopy(catalog["entry_catalog"]["current_price"]),
        "tactical_candidates": [],
        "security_valuation_basis_state": {
            "state": "RESOLVED",
            "new_buyer_price_resolution_use_allowed": True,
            "source_refs": ["canonical:security_basis:current"],
        },
    }


def _pass_a() -> dict[str, object]:
    return {"ticker": "RENAMED", "archetype": "DURABLE_FRANCHISE"}


def _option() -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "status": "RESOLVED",
        "low": 80.0,
        "high": 100.0,
        "currency": "USD",
        "evidence_refs": ["canonical:valuation"],
        "unresolved_reasons": [],
    }


def _output(*, support_ref: str = "claim:bull") -> dict[str, object]:
    return {
        "decisions": {
            "RENAMED": {
                "overall_direction": "BUY",
                "directional_buy_score": 6.0,
                "decision_confidence": "MEDIUM",
                "decisive_supporting_claim_refs": [support_ref],
                "decisive_contradicting_claim_refs": [],
                "thesis_state": "INTACT",
                "holder_decision": {
                    "holder": "HOLDABLE",
                    "reason_class": "NOT_APPLICABLE",
                    "reason": "핵심 논리를 훼손하는 근거가 없습니다.",
                    "evidence_refs": [],
                },
                "new_buyer_decision": {
                    "new_buyer": "ATTRACTIVE",
                    "reason_class": "ATTRACTIVE_WITHIN_RANGE",
                    "reason": "결정론적 범위 안입니다.",
                    "evidence_refs": ["canonical:valuation"],
                    "tactical_choice": "NOT_APPLICABLE",
                    "re_evaluate_conditions": [],
                },
                "policy_summary": "세 축을 분리해 판단했습니다.",
            }
        }
    }


def test_generic_metadata_authority_survives_renamed_subject_and_new_relation_id() -> None:
    manifest, projection, binding, _ = _strict_projection()
    assert manifest["status"] == "PASS"
    assert projection["status"] == "PASS"
    assert validate_source_use_projection_binding(projection, binding)["status"] == "PASS"
    assert is_use_allowed(
        projection,
        binding=binding,
        ref_id="canonical:working-capital-relation:new-id",
        use=SourceUse.EARNINGS_QUALITY_CONTEXT,
    )
    assert not is_use_allowed(
        projection,
        binding=binding,
        ref_id="claim:wc",
        use=SourceUse.OVERALL_DIRECTION,
    )
    assert is_use_allowed(
        projection,
        binding=binding,
        ref_id="claim:bull",
        use=SourceUse.OVERALL_DIRECTION,
    )


def test_missing_metadata_never_inherits_legacy_decisive_permission() -> None:
    catalog = _catalog()
    metadata = [row for row in _metadata() if row["ref_id"] != "source:business"]
    manifest = build_trusted_source_authority_manifest(
        ticker="RENAMED",
        source_generation_id="source-generation",
        catalog=catalog,
        source_metadata=metadata,
    )
    assert manifest["status"] == "FAIL"
    with pytest.raises(ValueError, match="source_input_expectation_authority_status_not_pass"):
        freeze_source_use_input_expectation(
            ticker="RENAMED",
            source_generation_id="source-generation",
            execution_generation_id="execution-generation",
            catalog=catalog,
            source_metadata=metadata,
            authority_manifest=manifest,
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("ticker", "OTHER"),
        ("source_generation_id", "stale-source"),
        ("execution_generation_id", "other-execution"),
        ("catalog_sha256", "0" * 64),
    ],
)
def test_caller_binding_rejects_wrong_subject_generation_and_catalog(
    field: str,
    replacement: str,
) -> None:
    _, projection, binding, _ = _strict_projection()
    forged_binding = deepcopy(binding)
    forged_binding[field] = replacement
    forged_binding.pop("binding_sha256")
    forged_binding["binding_sha256"] = canonical_sha256(forged_binding)
    validation = validate_source_use_projection_binding(projection, forged_binding)
    assert validation["status"] == "FAIL"
    assert f"source_use_binding_identity_mismatch:{field}" in validation["errors"]


def test_recomputed_forged_projection_hash_does_not_replace_outer_binding() -> None:
    _, projection, binding, _ = _strict_projection()
    forged = deepcopy(projection)
    forged["source_records"]["source:expectations"]["allowed_uses"].append(
        SourceUse.OVERALL_DIRECTION
    )
    forged.pop("projection_sha256")
    forged["projection_sha256"] = canonical_sha256(forged)
    validation = validate_source_use_projection_binding(forged, binding)
    assert validation["status"] == "FAIL"
    assert "source_use_binding_identity_mismatch:projection_sha256" in validation["errors"]


def test_strict_capability_builder_requires_matching_outer_binding() -> None:
    _, projection, binding, expectation = _strict_projection()
    capability = build_pass_b_capability_catalog(
        context=_context(),
        catalog=_catalog(),
        pass_a=_pass_a(),
        policy_option=_option(),
        source_use_view=projection,
        source_use_binding=binding,
        source_use_expectation=expectation,
        source_generation_id="source-generation",
        execution_generation_id="execution-generation",
        require_source_use=True,
    )
    assert capability["source_use_binding_sha256"] == binding["binding_sha256"]
    with pytest.raises(ValueError, match="capability_source_use_current_input_invalid"):
        build_pass_b_capability_catalog(
            context=_context(),
            catalog=_catalog(),
            pass_a=_pass_a(),
            policy_option=_option(),
            source_use_view=projection,
            source_use_expectation=expectation,
            source_generation_id="source-generation",
            execution_generation_id="execution-generation",
            require_source_use=True,
        )


def test_pass_b_model_context_requires_binding_for_v2_projection() -> None:
    _, projection, binding, expectation = _strict_projection()
    context = {
        "evidence_packets": [{"ticker": "RENAMED", "evidence": _metadata()}],
        "decision_evidence": _metadata(),
    }
    result = build_pass_b_subject_context(
        context=context,
        ticker="RENAMED",
        catalog=_catalog(),
        pass_a=_pass_a(),
        policy_option=_option(),
        source_use_view=projection,
        source_use_binding=binding,
        source_use_expectation=expectation,
        source_generation_id="source-generation",
        execution_generation_id="execution-generation",
        require_source_use=True,
    )
    assert result["source_use_projection"]["binding_sha256"] == binding["binding_sha256"]
    with pytest.raises(ValueError, match="pass_b_source_use_current_input_invalid"):
        build_pass_b_subject_context(
            context=context,
            ticker="RENAMED",
            catalog=_catalog(),
            pass_a=_pass_a(),
            policy_option=_option(),
            source_use_view=projection,
            source_use_expectation=expectation,
            source_generation_id="source-generation",
            execution_generation_id="execution-generation",
            require_source_use=True,
        )


def test_direct_final_gate_rejects_restricted_ref_and_missing_view() -> None:
    _, projection, binding, expectation = _strict_projection()
    permissive_capability = build_pass_b_capability_catalog(
        context=_context(),
        catalog=_catalog(),
        pass_a=_pass_a(),
        policy_option=_option(),
    )
    restricted = validate_capability_selection(
        _output(support_ref="claim:wc"),
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
        capabilities={"RENAMED": permissive_capability},
        source_use_views={"RENAMED": projection},
        source_use_bindings={"RENAMED": binding},
        source_use_expectations={"RENAMED": expectation},
        source_metadata_by_ticker={"RENAMED": _metadata()},
        source_generation_id="source-generation",
        execution_generation_id="execution-generation",
        require_source_use=True,
    )
    assert restricted["status"] == "FAIL"
    assert any("SOURCE_USE_REF_FORBIDDEN" in error for error in restricted["errors"])

    omitted = validate_capability_selection(
        _output(),
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
        capabilities={"RENAMED": permissive_capability},
        require_source_use=True,
    )
    assert omitted["status"] == "FAIL"
    assert any("PB_SOURCE_USE_CURRENT_INPUT_INVALID" in error for error in omitted["errors"])


def test_legacy_projection_cannot_claim_new_binding_evidence() -> None:
    catalog = _catalog()
    legacy = build_source_use_projection(
        ticker="RENAMED",
        input_generation_id="source-generation",
        catalog=catalog,
        source_authorities=[
            frozen_source_authority(
                ticker="RENAMED",
                ref_id="source:business",
                source_type="legacy_business",
                source_scope="legacy_only",
                allowed_uses=[SourceUse.OVERALL_DIRECTION],
                authority_basis="frozen_legacy_fixture",
            )
        ],
    )
    _, _, binding, _ = _strict_projection()
    validation = validate_selected_refs(
        legacy,
        binding=binding,
        refs=["claim:bull"],
        use=SourceUse.OVERALL_DIRECTION,
        require_any=True,
    )
    assert validation["status"] == "FAIL"
    assert any(row["code"] == "SOURCE_USE_LEGACY_BINDING_FORBIDDEN" for row in validation["errors"])


def test_cpng_nyse_identity_is_versioned_and_wrong_components_fail() -> None:
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
    assert identity["security_id"] == "nyse:CPNG:common-stock"
    assert validate_security_identity_binding(identity)["status"] == "PASS"
    for field, replacement in (
        ("venue", "NASDAQ"),
        ("issuer_id", "sec:wrong"),
        ("security_id", "nasdaq:CPNG:common-stock"),
    ):
        forged = deepcopy(identity)
        forged[field] = replacement
        forged.pop("identity_sha256")
        forged["identity_sha256"] = canonical_sha256(forged)
        validation = validate_security_identity_binding(
            forged,
            expected={
                "venue": "NYSE",
                "issuer_id": "sec:0001834584",
                "security_id": "nyse:CPNG:common-stock",
            },
        )
        assert validation["status"] == "FAIL"
