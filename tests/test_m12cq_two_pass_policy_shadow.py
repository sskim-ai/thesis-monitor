from __future__ import annotations

from copy import deepcopy

from scripts.m12cq_two_pass_contract import (
    PASS_A_CONTRACT,
    PASS_B_CONTRACT,
    DecisionRuleId,
    PassABatchOutput,
    PassAClassification,
    PassBBatchOutput,
    PassBDecision,
    build_pass_a_subject_context,
    generic_control_matrix,
    materialize_policy_entry_range,
    pass_a_batch_schema,
    pass_a_leakage_scan,
    pass_b_batch_schema,
    schema_preflight,
    select_matrix_option,
    validate_new_buyer_consistency,
    validate_pass_a_batch,
    validate_pass_b_batch,
)
from scripts.m12da_source_use_contract import (
    SourceUse,
    build_source_use_projection,
    frozen_source_authority,
)


def _atomic_claim(
    claim_ref: str,
    parent_ref: str,
    *,
    polarity: str = "BULLISH",
    text: str = "검증된 사업 성과가 구조적 경쟁력을 지지합니다.",
) -> dict[str, object]:
    return {
        "claim_ref": claim_ref,
        "ticker": "RENAMED",
        "claim": {
            "text": text,
            "polarity": polarity,
            "logical_condition": None,
        },
        "parent_source_refs": [parent_ref],
    }


def _context() -> dict[str, object]:
    return {
        "evidence_packets": [
            {
                "ticker": "RENAMED",
                "company_name": "Hidden",
                "evidence": [
                    {
                        "ref_id": "core:thesis",
                        "category": "thesis",
                        "label": "핵심 투자 논리",
                        "statement": {"state": "verified"},
                        "as_of": "2026-09-17",
                    },
                    {
                        "ref_id": "core:quality",
                        "category": "quality",
                        "label": "data_quality",
                        "statement": {"state": "provider_limited"},
                        "as_of": "2026-09-17",
                    },
                    {
                        "ref_id": "canonical:valuation:current",
                        "category": "valuation",
                        "label": "valuation",
                        "statement": {"current_percentile": 90},
                        "as_of": "2026-09-17",
                    },
                    {
                        "ref_id": "canonical:price:current",
                        "category": "price_structure",
                        "label": "price",
                        "statement": {"current_price": 120.0},
                        "as_of": "2026-09-17",
                    },
                    {
                        "ref_id": "timing:support",
                        "category": "price_structure",
                        "label": "chart_support_zone",
                        "statement": {"zone_low": 90.0, "zone_high": 110.0},
                        "as_of": "2026-09-17",
                    },
                ],
            }
        ]
    }


def _catalog() -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "all_evidence_refs": [
            "core:thesis",
            "core:quality",
            "canonical:valuation:current",
            "canonical:price:current",
            "timing:support",
        ],
        "core_evidence_refs": [
            "core:thesis",
            "core:quality",
            "canonical:valuation:current",
        ],
        "timing_evidence_refs": ["canonical:price:current", "timing:support"],
        "valuation_evidence_refs": ["canonical:valuation:current"],
        "material_disclosure_failure_refs": [],
        "positive_quality_refs": [],
        "claim_refs": ["claim:bull", "claim:bear"],
        "atomic_claims": [
            _atomic_claim("claim:bull", "core:thesis"),
            _atomic_claim(
                "claim:bear",
                "core:thesis",
                polarity="BEARISH",
                text="실행 성과가 약화되면 장기 논리를 재검토해야 합니다.",
            ),
        ],
        "entry_catalog": {
            "ticker": "RENAMED",
            "current_price": {
                "value": 120.0,
                "as_of": "2026-09-17",
                "ref_id": "canonical:price:current",
            },
            "tactical_candidates": [
                {
                    "ticker": "RENAMED",
                    "candidate_id": "tactical:one",
                    "low": 90.0,
                    "high": 110.0,
                    "currency": "USD",
                    "evidence_refs": ["timing:support"],
                }
            ],
            "unresolved_policy": {"tactical_unresolved_reason": "tactical unavailable"},
        },
    }


def _restricted_source_use() -> dict[str, object]:
    catalog = _catalog()
    authority = frozen_source_authority(
        ticker="RENAMED",
        ref_id="core:thesis",
        source_type="derived_relation",
        source_scope="context_only",
        allowed_uses=[SourceUse.CONTEXT, SourceUse.EARNINGS_QUALITY_CONTEXT],
        prohibited_uses=[
            SourceUse.PASS_A_ARCHETYPE,
            SourceUse.PASS_A_VALUATION_TIER,
            SourceUse.OVERALL_DIRECTION,
            SourceUse.HOLDER_STANCE,
            SourceUse.NEW_BUYER_EXECUTION_RISK,
        ],
        denial_reasons=["source_scope_does_not_authorize_decision"],
        authority_basis="deterministic_test_authority",
    )
    return build_source_use_projection(
        ticker="RENAMED",
        input_generation_id="generation",
        catalog=catalog,
        source_authorities=[authority],
    )


def _pass_a_context() -> dict[str, object]:
    return build_pass_a_subject_context(
        context=_context(),
        ticker="RENAMED",
        catalog=_catalog(),
    )


def _pass_a(*, tier: str = "BASE") -> PassAClassification:
    return PassAClassification.model_validate(
        {
            "ticker": "RENAMED",
            "archetype": "DURABLE_FRANCHISE",
            "archetype_confidence": "HIGH",
            "archetype_supporting_claim_refs": ["claim:bull"],
            "archetype_rationale": "검증된 사업 성과가 장기 경쟁력을 지지합니다.",
            "valuation_regime_tier": tier,
            "tier_supporting_claim_refs": ["claim:bull"] if tier != "UNRESOLVED" else [],
            "tier_rationale": "비가격 구조 개선 근거를 사용했습니다.",
            "data_quality_effect": "CONFIDENCE_ONLY",
            "data_quality_reason_class": "PROVIDER_LIMITATION",
            "data_quality_reason": "일부 제공자 범위가 제한됩니다.",
            "data_quality_evidence_refs": ["core:quality"],
            "classification_summary": "가격과 무관하게 사업 분류를 완료했습니다.",
        }
    )


def _matrix() -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "options": [
            {
                "ticker": "RENAMED",
                "archetype": "DURABLE_FRANCHISE",
                "valuation_regime_tier": "BASE",
                "status": "RESOLVED",
                "option_id": "policy-option:one",
                "low": 80.0,
                "high": 100.0,
                "currency": "USD",
                "method_family": "HISTORICAL_TRAILING_PE_QUANTILE",
                "selection_basis": "DURABLE_PRIMARY_TRAILING_PE",
                "evidence_refs": ["canonical:valuation:current"],
                "unresolved_reasons": [],
            },
            {
                "ticker": "RENAMED",
                "archetype": "DURABLE_FRANCHISE",
                "valuation_regime_tier": "UNRESOLVED",
                "status": "UNRESOLVED",
                "option_id": None,
                "low": None,
                "high": None,
                "currency": None,
                "method_family": None,
                "selection_basis": None,
                "evidence_refs": [],
                "unresolved_reasons": ["VALUATION_REGIME_TIER_UNRESOLVED"],
            },
        ],
    }


def _identity(contract: str) -> dict[str, object]:
    return {
        "contract": contract,
        "generation_id": "generation",
        "packet_id": "packet",
        "market": "us",
        "assessment_date": "2026-09-17",
        "expected_subjects": ["RENAMED"],
    }


def _pass_b(
    *,
    overall: str = "BUY",
    new_buyer: str = "WAIT",
    holder: str = "HOLDABLE",
    reason_class: str = "FUNDAMENTAL_RANGE_POSITION",
    tactical_choice: str = "tactical:one",
) -> PassBDecision:
    return PassBDecision.model_validate(
        {
            "ticker": "RENAMED",
            "overall_direction": overall,
            "new_buyer": new_buyer,
            "holder": holder,
            "directional_balance": {"buy": 6.0, "sell": 4.0},
            "decision_confidence": "MEDIUM",
            "decisive_supporting_claim_refs": ["claim:bull"],
            "decisive_contradicting_claim_refs": ["claim:bear"],
            "thesis_state": "INTACT",
            "holder_reason_class": "NOT_APPLICABLE"
            if holder == "HOLDABLE"
            else "THESIS_UNCERTAINTY",
            "holder_reason": "장기 논리를 훼손하는 근거가 없습니다.",
            "holder_reason_evidence_refs": ["core:thesis"],
            "new_buyer_reason_class": reason_class,
            "new_buyer_reason": "현재 가격은 허용된 기본 범위보다 높습니다.",
            "new_buyer_reason_refs": ["canonical:price:current"],
            "tactical_choice": tactical_choice,
            "re_evaluate_conditions": ["가격이 기본 범위에 진입하는지 확인"]
            if new_buyer == "WAIT"
            else [],
            "valuation_affects": ["NEW_BUYER"],
            "rule_trace": [
                DecisionRuleId.ARCHETYPE_REGIME_FREEZE,
                DecisionRuleId.THESIS_ENTRY_SEPARATION,
                DecisionRuleId.HOLDER_VALUATION_SEPARATION,
                DecisionRuleId.EVIDENCE_OWNERSHIP,
                DecisionRuleId.DETERMINISTIC_FUNDAMENTAL_OPTION,
                DecisionRuleId.TACTICAL_SELECTION_ONLY,
                DecisionRuleId.NEW_BUYER_CONSISTENCY,
            ],
            "policy_summary": "장기 논리는 유효하지만 현재 진입은 기다립니다.",
        }
    )


def test_pass_a_filters_price_valuation_and_technical_context() -> None:
    payload = _pass_a_context()

    refs = {row["ref_id"] for row in payload["eligible_non_price_evidence"]}
    assert refs == {"core:thesis", "core:quality"}
    assert payload["eligible_claim_refs"] == ["claim:bull", "claim:bear"]
    assert pass_a_leakage_scan([payload])["status"] == "PASS"


def test_pass_a_leakage_scan_rejects_current_price() -> None:
    payload = _pass_a_context()
    payload["current_price"] = 120.0

    proof = pass_a_leakage_scan([payload])

    assert proof["status"] == "FAIL"
    assert proof["current_price_leak_count"] > 0


def test_pass_a_schema_is_recursive_strict_and_exact_scope() -> None:
    schema = pass_a_batch_schema(
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _pass_a_context()},
    )

    assert schema["title"] == "m12cq-pass-a-response-schema-v1"
    assert schema_preflight(schema)["status"] == "PASS"
    assert schema["properties"]["classifications"]["minItems"] == 1


def test_pass_b_schema_excludes_runtime_owned_price_fields() -> None:
    schema = pass_b_batch_schema(
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )
    rendered = str(schema)

    assert schema_preflight(schema)["status"] == "PASS"
    assert "preferred_entry_low" not in rendered
    assert "fundamental_choice" not in rendered
    assert "distance_to_band_pct" not in rendered


def test_pass_a_validation_requires_premium_structural_ref() -> None:
    output = PassABatchOutput(
        contract=PASS_A_CONTRACT,
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        classifications=(_pass_a(tier="PREMIUM"),),
    )

    result = validate_pass_a_batch(
        output,
        expected_identity=_identity(PASS_A_CONTRACT),
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _pass_a_context()},
    )

    assert result["status"] == "PASS"


def test_pass_a_validation_rejects_premium_without_eligible_ref() -> None:
    context = _pass_a_context()
    context["premium_eligible_claim_refs"] = []
    output = PassABatchOutput(
        contract=PASS_A_CONTRACT,
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        classifications=(_pass_a(tier="PREMIUM"),),
    )

    result = validate_pass_a_batch(
        output,
        expected_identity=_identity(PASS_A_CONTRACT),
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": context},
    )

    assert "RENAMED:premium_without_structural_improvement_ref" in result["errors"]


def test_matrix_selection_is_exact_and_price_independent() -> None:
    first = select_matrix_option(_matrix(), _pass_a())
    renamed = deepcopy(_matrix())
    renamed["ticker"] = "OTHER"
    for option in renamed["options"]:
        option["ticker"] = "OTHER"
    second = select_matrix_option(
        renamed,
        {"archetype": "DURABLE_FRANCHISE", "valuation_regime_tier": "BASE"},
    )

    assert first["option_id"] == "policy-option:one"
    assert first["low"] == second["low"]
    assert first["high"] == second["high"]


def test_runtime_materializer_intersects_fundamental_and_tactical() -> None:
    entry = materialize_policy_entry_range(
        ticker="RENAMED",
        new_buyer="WAIT",
        policy_option=select_matrix_option(_matrix(), _pass_a()),
        entry_catalog=_catalog()["entry_catalog"],
        tactical_choice="tactical:one",
        re_evaluate_conditions=("가격 범위 진입 여부 확인",),
    )

    assert entry["entry_range_status"] == "ENTRY_RANGE_RESOLVED"
    assert entry["preferred_entry_low"] == 90.0
    assert entry["preferred_entry_high"] == 100.0
    assert entry["combination_rule"] == "OVERLAP_INTERSECTION"
    assert entry["distance_to_band_pct"] < 0


def test_runtime_materializer_preserves_unresolved_fundamental() -> None:
    entry = materialize_policy_entry_range(
        ticker="RENAMED",
        new_buyer="WAIT",
        policy_option=select_matrix_option(_matrix(), _pass_a(tier="UNRESOLVED")),
        entry_catalog=_catalog()["entry_catalog"],
        tactical_choice="tactical:one",
        re_evaluate_conditions=("가치평가 근거 확보",),
    )

    assert entry["entry_range_status"] == "ENTRY_RANGE_UNRESOLVED"
    assert entry["preferred_entry_low"] is None
    assert entry["tactical_entry_band"]["status"] == "RESOLVED"


def test_pass_b_semantics_accept_buy_wait_holdable() -> None:
    decision = _pass_b()
    output = PassBBatchOutput(
        contract=PASS_B_CONTRACT,
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        decisions=(decision,),
    )

    result = validate_pass_b_batch(
        output,
        expected_identity=_identity(PASS_B_CONTRACT),
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
        pass_a_by_ticker={"RENAMED": _pass_a().model_dump(mode="json")},
    )

    assert result["status"] == "PASS"


def test_pass_a_final_gate_rejects_restricted_selected_claims() -> None:
    classification = _pass_a()
    output = PassABatchOutput(
        contract=PASS_A_CONTRACT,
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        classifications=(classification,),
    )
    result = validate_pass_a_batch(
        output,
        expected_identity=_identity(PASS_A_CONTRACT),
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _pass_a_context()},
        source_use_views={"RENAMED": _restricted_source_use()},
    )
    assert result["status"] == "FAIL"
    assert any("source_use_pass_a_archetype" in row for row in result["errors"])
    assert any("source_use_pass_a_tier" in row for row in result["errors"])


def test_pass_b_final_gate_rejects_restricted_selected_claims() -> None:
    output = PassBBatchOutput(
        contract=PASS_B_CONTRACT,
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        decisions=(_pass_b(),),
    )
    result = validate_pass_b_batch(
        output,
        expected_identity=_identity(PASS_B_CONTRACT),
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
        pass_a_by_ticker={"RENAMED": _pass_a().model_dump(mode="json")},
        source_use_views={"RENAMED": _restricted_source_use()},
    )
    assert result["status"] == "FAIL"
    assert any("source_use_overall" in row for row in result["errors"])


def test_holder_review_requires_nonvaluation_evidence() -> None:
    catalog = _catalog()
    candidate = _pass_b(holder="REVIEW")
    payload = candidate.model_dump(mode="json")
    payload["holder_reason_evidence_refs"] = ["canonical:valuation:current"]
    output = PassBBatchOutput(
        contract=PASS_B_CONTRACT,
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        decisions=(PassBDecision.model_validate(payload),),
    )

    result = validate_pass_b_batch(
        output,
        expected_identity=_identity(PASS_B_CONTRACT),
        subjects=("RENAMED",),
        catalogs={"RENAMED": catalog},
        pass_a_by_ticker={"RENAMED": _pass_a().model_dump(mode="json")},
    )

    assert "RENAMED:review_supported_only_by_valuation" in result["errors"]


def test_new_buyer_wait_is_consistent_above_fundamental_range() -> None:
    decision = _pass_b()
    option = select_matrix_option(_matrix(), _pass_a())
    entry = materialize_policy_entry_range(
        ticker="RENAMED",
        new_buyer="WAIT",
        policy_option=option,
        entry_catalog=_catalog()["entry_catalog"],
        tactical_choice="tactical:one",
        re_evaluate_conditions=decision.re_evaluate_conditions,
    )

    result = validate_new_buyer_consistency(
        decision=decision,
        policy_option=option,
        entry_range=entry,
        catalog=_catalog(),
    )

    assert result["status"] == "PASS"


def test_new_buyer_attractive_above_range_fails() -> None:
    payload = _pass_b(new_buyer="ATTRACTIVE", tactical_choice="NOT_APPLICABLE").model_dump(
        mode="json"
    )
    payload["new_buyer_reason_class"] = "ATTRACTIVE_WITHIN_RANGE"
    decision = PassBDecision.model_validate(payload)
    option = select_matrix_option(_matrix(), _pass_a())
    entry = materialize_policy_entry_range(
        ticker="RENAMED",
        new_buyer="ATTRACTIVE",
        policy_option=option,
        entry_catalog=_catalog()["entry_catalog"],
        tactical_choice="NOT_APPLICABLE",
        re_evaluate_conditions=(),
    )

    result = validate_new_buyer_consistency(
        decision=decision,
        policy_option=option,
        entry_range=entry,
        catalog=_catalog(),
    )

    assert "attractive_without_permitted_fundamental_position" in result["errors"]


def test_generic_controls_are_identity_independent() -> None:
    controls = generic_control_matrix()

    assert controls["status"] == "PASS"
    assert controls["renamed_identity_same_policy"] is True
    assert controls["ticker_specific_rule_count"] == 0
