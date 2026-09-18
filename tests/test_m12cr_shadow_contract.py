from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m12cp_valuation_policy_contract import Archetype, ValuationRegimeTier
from scripts.m12cr_shadow_contract import (
    PASS_A_MODEL_FIELDS,
    PASS_B_MODEL_FIELDS,
    field_ownership_inventory,
    future_pass_a_batch_schema,
    future_pass_b_batch_schema,
    materialize_directional_balance,
    materialize_future_pass_a,
    normalize_future_pass_b,
    parity_matrix,
    project_data_quality_base_state,
    schema_completeness_and_parity_scan,
    semantic_rule_inventory,
    source_rule_ids,
    validate_future_pass_a_shape,
    validate_future_pass_b_shape,
    validate_materialized_pass_b,
    validate_materialized_directional_balance,
    validate_new_buyer_consistency,
    validate_security_basis_gate,
)


def _context(*, quality_refs: bool = True) -> dict[str, object]:
    financial_quality_ref = "canonical:financial_quality:2026-06-30"
    evidence = [
        {
            "ref_id": "core:thesis",
            "category": "thesis",
            "label": "핵심 사업 근거",
            "statement": {"state": "verified"},
        },
        {
            "ref_id": financial_quality_ref,
            "category": "earnings",
            "label": "financial_quality",
            "statement": {
                "decision_version": "financial-quality-taint-v2",
                "reason_codes": [],
                "source_period": "2026-06-30",
                "source_type": "full_statement",
                "state": "caution_usable" if quality_refs else "verified_usable",
            },
        },
        {
            "ref_id": "quality:negative",
            "category": "quality",
            "label": "material disclosure failure",
            "statement": {"state": "verified"},
        },
        {
            "ref_id": "quality:positive",
            "category": "quality",
            "label": "data quality restored",
            "statement": {"state": "verified"},
        },
    ]
    return {
        "ticker": "RENAMED",
        "accepted_fundamental_claims": [],
        "eligible_non_price_evidence": evidence,
        "eligible_claim_refs": ["claim:bull", "claim:bear"],
        "premium_eligible_claim_refs": ["claim:bull"],
        "data_quality_catalog": {
            "evidence_refs": [financial_quality_ref] if quality_refs else [],
            "material_disclosure_failure_refs": ["quality:negative"],
            "positive_quality_refs": ["quality:positive"],
        },
    }


def _claim(claim_ref: str, polarity: str) -> dict[str, object]:
    return {
        "claim_ref": claim_ref,
        "ticker": "RENAMED",
        "claim": {
            "text": "검증된 일반화 사업 근거입니다.",
            "polarity": polarity,
            "logical_condition": None,
        },
        "parent_source_refs": ["core:thesis"],
    }


def _catalog(*, current_price: float = 90.0) -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "all_evidence_refs": [
            "core:thesis",
            "quality:provider",
            "canonical:valuation",
            "canonical:price",
            "timing:support",
        ],
        "core_evidence_refs": ["core:thesis", "quality:provider", "canonical:valuation"],
        "timing_evidence_refs": ["canonical:price", "timing:support"],
        "valuation_evidence_refs": ["canonical:valuation"],
        "material_disclosure_failure_refs": [],
        "positive_quality_refs": [],
        "claim_refs": ["claim:bull", "claim:bear"],
        "atomic_claims": [
            _claim("claim:bull", "BULLISH"),
            _claim("claim:bear", "BEARISH"),
        ],
        "entry_catalog": {
            "ticker": "RENAMED",
            "current_price": {
                "value": current_price,
                "as_of": "2026-09-17",
                "ref_id": "canonical:price",
            },
            "tactical_candidates": [
                {
                    "ticker": "RENAMED",
                    "candidate_id": "tactical:one",
                    "low": 80.0,
                    "high": 100.0,
                    "currency": "USD",
                    "evidence_refs": ["timing:support"],
                }
            ],
            "unresolved_policy": {"tactical_unresolved_reason": "tactical unavailable"},
        },
    }


def _pass_a_choice(
    *,
    archetype: str = "DURABLE_FRANCHISE",
    tier: str = "BASE",
    quality_effect: str = "NONE",
) -> dict[str, object]:
    quality = {
        "effect": "NONE",
        "reason_class": "NOT_APPLICABLE",
        "reason": None,
        "evidence_refs": [],
    }
    if quality_effect == "DIRECTIONAL_NEGATIVE":
        quality = {
            "effect": quality_effect,
            "reason_class": "MATERIAL_DISCLOSURE_FAILURE",
            "reason": "중대한 공시 실패가 확인됐습니다.",
            "evidence_refs": ["quality:negative"],
        }
    elif quality_effect == "DIRECTIONAL_POSITIVE":
        quality = {
            "effect": quality_effect,
            "reason_class": "EVIDENCED_QUALITY_IMPROVEMENT",
            "reason": "데이터 품질 복구가 확인됐습니다.",
            "evidence_refs": ["quality:positive"],
        }
    return {
        "archetype": archetype,
        "archetype_confidence": "HIGH",
        "archetype_supporting_claim_refs": ["claim:bull"],
        "archetype_rationale": "가격과 무관한 사업 근거로 분류했습니다.",
        "valuation_regime_tier": tier,
        "tier_supporting_claim_refs": [] if tier == "UNRESOLVED" else ["claim:bull"],
        "tier_rationale": "비가격 근거로 정책 tier를 선택했습니다.",
        "directional_data_quality_judgment": quality,
        "classification_summary": "동결 근거만 사용한 일반화 분류입니다.",
    }


def _pass_a_output(**kwargs: str) -> dict[str, object]:
    return {"classifications": {"RENAMED": _pass_a_choice(**kwargs)}}


def _pass_b_choice(
    *,
    overall: str = "BUY",
    new_buyer: str = "ATTRACTIVE",
    holder: str = "HOLDABLE",
) -> dict[str, object]:
    holder_decision: dict[str, object] = {
        "holder": "HOLDABLE",
        "reason_class": "NOT_APPLICABLE",
        "reason": "장기 논리를 훼손하는 근거가 없습니다.",
        "evidence_refs": [],
    }
    if holder == "REVIEW":
        holder_decision = {
            "holder": "REVIEW",
            "reason_class": "THESIS_UNCERTAINTY",
            "reason": "사업 불확실성을 재검토해야 합니다.",
            "evidence_refs": ["core:thesis"],
        }
    elif holder == "REDUCE":
        holder_decision = {
            "holder": "REDUCE",
            "reason_class": "THESIS_IMPAIRMENT",
            "reason": "핵심 논리 훼손 근거가 확인됐습니다.",
            "evidence_refs": ["core:thesis"],
        }
    new_buyer_decision: dict[str, object] = {
        "new_buyer": "ATTRACTIVE",
        "reason_class": "ATTRACTIVE_WITHIN_RANGE",
        "reason": "현재 가격이 기본 범위 안에 있습니다.",
        "evidence_refs": ["canonical:price"],
        "tactical_choice": "NOT_APPLICABLE",
        "re_evaluate_conditions": [],
    }
    if new_buyer == "WAIT":
        new_buyer_decision = {
            "new_buyer": "WAIT",
            "reason_class": "FUNDAMENTAL_RANGE_POSITION",
            "reason": "현재 가격이 기본 범위 위에 있습니다.",
            "evidence_refs": ["canonical:price"],
            "tactical_choice": "tactical:one",
            "re_evaluate_conditions": ["가격이 기본 범위로 진입하는지 확인"],
        }
    elif new_buyer == "AVOID":
        new_buyer_decision = {
            "new_buyer": "AVOID",
            "reason_class": "EXECUTION_OR_THESIS_RISK",
            "reason": "핵심 실행 위험이 확인됐습니다.",
            "evidence_refs": ["core:thesis"],
            "tactical_choice": "NOT_APPLICABLE",
            "re_evaluate_conditions": [],
        }
    return {
        "overall_direction": overall,
        "directional_buy_score": 6.0,
        "decision_confidence": "MEDIUM",
        "decisive_supporting_claim_refs": ["claim:bull"],
        "decisive_contradicting_claim_refs": ["claim:bear"],
        "thesis_state": "INTACT" if holder != "REDUCE" else "IMPAIRED",
        "holder_decision": holder_decision,
        "new_buyer_decision": new_buyer_decision,
        "policy_summary": "세 축을 분리해 판단했습니다.",
    }


def _pass_b_output(**kwargs: str) -> dict[str, object]:
    return {"decisions": {"RENAMED": _pass_b_choice(**kwargs)}}


def _resolved_option() -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "archetype": "DURABLE_FRANCHISE",
        "valuation_regime_tier": "BASE",
        "status": "RESOLVED",
        "option_id": "policy:one",
        "low": 80.0,
        "high": 100.0,
        "currency": "USD",
        "method_family": "HISTORICAL_TRAILING_PE_QUANTILE",
        "selection_basis": "GENERIC",
        "evidence_refs": ["canonical:valuation"],
        "unresolved_reasons": [],
    }


def _unresolved_option() -> dict[str, object]:
    option = _resolved_option()
    option.update(
        {
            "status": "UNRESOLVED",
            "option_id": None,
            "low": None,
            "high": None,
            "currency": None,
            "method_family": None,
            "selection_basis": None,
            "evidence_refs": [],
            "unresolved_reasons": ["VALUATION_UNRESOLVED"],
        }
    )
    return option


@pytest.mark.parametrize(
    ("field", "error"),
    (
        ("archetype_supporting_claim_refs", "PA_ARCHETYPE_REF_DUPLICATE"),
        ("tier_supporting_claim_refs", "PA_TIER_REF_DUPLICATE"),
    ),
)
def test_pass_a_local_validator_rejects_duplicate_model_refs(
    field: str,
    error: str,
) -> None:
    output = _pass_a_output()
    output["classifications"]["RENAMED"][field] = ["claim:bull", "claim:bull"]

    result = validate_future_pass_a_shape(
        output,
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )

    assert result["status"] == "FAIL"
    assert error in result["per_ticker"]["RENAMED"]


def test_pass_a_local_validator_rejects_duplicate_quality_refs() -> None:
    output = _pass_a_output(quality_effect="DIRECTIONAL_NEGATIVE")
    output["classifications"]["RENAMED"]["directional_data_quality_judgment"]["evidence_refs"] = [
        "quality:negative",
        "quality:negative",
    ]

    result = validate_future_pass_a_shape(
        output,
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )

    assert result["status"] == "FAIL"
    assert "PA_QUALITY_EVIDENCE_REF_DUPLICATE" in result["per_ticker"]["RENAMED"]


@pytest.mark.parametrize(
    ("target", "error"),
    (
        ("support", "PB_SUPPORT_REF_DUPLICATE"),
        ("contradiction", "PB_CONTRADICTION_REF_DUPLICATE"),
        ("holder", "PB_HOLDER_EVIDENCE_REF_DUPLICATE"),
        ("new_buyer", "PB_NEW_BUYER_EVIDENCE_REF_DUPLICATE"),
        ("conditions", "PB_REEVALUATE_CONDITION_DUPLICATE"),
    ),
)
def test_pass_b_local_validator_rejects_duplicate_model_arrays(
    target: str,
    error: str,
) -> None:
    output = _pass_b_output(new_buyer="WAIT", holder="REVIEW")
    row = output["decisions"]["RENAMED"]
    if target == "support":
        row["decisive_supporting_claim_refs"] = ["claim:bull", "claim:bull"]
    elif target == "contradiction":
        row["decisive_contradicting_claim_refs"] = ["claim:bear", "claim:bear"]
    elif target == "holder":
        row["holder_decision"]["evidence_refs"] = ["core:thesis", "core:thesis"]
    elif target == "new_buyer":
        row["new_buyer_decision"]["evidence_refs"] = [
            "canonical:price",
            "canonical:price",
        ]
    else:
        row["new_buyer_decision"]["re_evaluate_conditions"] = [
            "가격 확인",
            "가격 확인",
        ]

    result = validate_future_pass_b_shape(
        deepcopy(output),
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )

    assert result["status"] == "FAIL"
    assert error in result["per_ticker"]["RENAMED"]


def test_future_schemas_are_strict_subject_keyed_and_complete() -> None:
    pass_a = future_pass_a_batch_schema(
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )
    pass_b = future_pass_b_batch_schema(
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )

    assert (
        schema_completeness_and_parity_scan(
            pass_a,
            stage="pass-a",
            subjects=("RENAMED",),
        )["status"]
        == "PASS"
    )
    assert (
        schema_completeness_and_parity_scan(
            pass_b,
            stage="pass-b",
            subjects=("RENAMED",),
        )["status"]
        == "PASS"
    )


@pytest.mark.parametrize("archetype", [item.value for item in Archetype])
def test_pass_a_all_archetypes_are_accepted(archetype: str) -> None:
    result = validate_future_pass_a_shape(
        _pass_a_output(archetype=archetype),
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )
    assert result["status"] == "PASS"


@pytest.mark.parametrize("tier", [item.value for item in ValuationRegimeTier])
def test_pass_a_all_regime_tiers_are_accepted(tier: str) -> None:
    result = validate_future_pass_a_shape(
        _pass_a_output(tier=tier),
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )
    assert result["status"] == "PASS"


@pytest.mark.parametrize(
    "effect",
    ["NONE", "DIRECTIONAL_NEGATIVE", "DIRECTIONAL_POSITIVE"],
)
def test_pass_a_all_model_quality_branches_are_accepted(effect: str) -> None:
    result = validate_future_pass_a_shape(
        _pass_a_output(quality_effect=effect),
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )
    assert result["status"] == "PASS"


@pytest.mark.parametrize("confidence", ["LOW", "MEDIUM", "HIGH"])
def test_pass_a_all_confidence_values_are_accepted(confidence: str) -> None:
    output = _pass_a_output()
    output["classifications"]["RENAMED"]["archetype_confidence"] = confidence
    result = validate_future_pass_a_shape(
        output,
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )
    assert result["status"] == "PASS"


def test_m12cq_none_with_nonempty_refs_is_rejected_offline() -> None:
    output = _pass_a_output()
    judgment = output["classifications"]["RENAMED"]["directional_data_quality_judgment"]
    judgment["evidence_refs"] = ["quality:provider"]

    result = validate_future_pass_a_shape(
        output,
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )

    assert "RENAMED:PA_QUALITY_NONE_SHAPE" in result["errors"]


def test_runtime_projects_normal_quality_state_and_model_cannot_recopy_it() -> None:
    base = project_data_quality_base_state(_context())
    rows, result = materialize_future_pass_a(
        _pass_a_output(),
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )

    assert base["effect"] == "CONFIDENCE_ONLY"
    assert rows[0]["data_quality_effect"] == "CONFIDENCE_ONLY"
    assert rows[0]["data_quality_evidence_refs"] == ["canonical:financial_quality:2026-06-30"]
    assert result["status"] == "PASS"


def test_runtime_projects_none_when_no_normal_quality_limitation_exists() -> None:
    base = project_data_quality_base_state(_context(quality_refs=False))
    assert base["effect"] == "NONE"
    assert base["evidence_refs"] == []


def test_premium_without_structural_ref_is_rejected_before_inference() -> None:
    context = _context()
    context["premium_eligible_claim_refs"] = []
    result = validate_future_pass_a_shape(
        _pass_a_output(tier="PREMIUM"),
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": context},
    )
    assert "RENAMED:PA_RESOLVED_TIER_REF_OWNERSHIP" in result["errors"]


@pytest.mark.parametrize("overall", ["BUY", "HOLD", "SELL"])
@pytest.mark.parametrize("new_buyer", ["ATTRACTIVE", "WAIT", "AVOID"])
@pytest.mark.parametrize("holder", ["HOLDABLE", "REVIEW", "REDUCE"])
def test_pass_b_all_axis_enums_have_structural_branches(
    overall: str,
    new_buyer: str,
    holder: str,
) -> None:
    result = validate_future_pass_b_shape(
        _pass_b_output(overall=overall, new_buyer=new_buyer, holder=holder),
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )
    assert result["status"] == "PASS"


@pytest.mark.parametrize("confidence", ["LOW", "MEDIUM", "HIGH"])
def test_pass_b_all_confidence_values_are_accepted(confidence: str) -> None:
    output = _pass_b_output()
    output["decisions"]["RENAMED"]["decision_confidence"] = confidence
    result = validate_future_pass_b_shape(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )
    assert result["status"] == "PASS"


@pytest.mark.parametrize(
    ("score", "expected"),
    (
        (0, {"buy": 0.0, "sell": 10.0}),
        (0.62, {"buy": 0.62, "sell": 9.38}),
        (3.5, {"buy": 3.5, "sell": 6.5}),
        (5, {"buy": 5.0, "sell": 5.0}),
        (6.2, {"buy": 6.2, "sell": 3.8}),
        (10, {"buy": 10.0, "sell": 0.0}),
    ),
)
def test_directional_buy_score_materializes_decimal_safe_complement(
    score: float,
    expected: dict[str, float],
) -> None:
    balance = materialize_directional_balance(score)

    assert balance == expected
    assert validate_materialized_directional_balance(balance)["status"] == "PASS"


@pytest.mark.parametrize("score", (-0.01, 10.01, float("nan"), float("inf")))
def test_directional_buy_score_rejects_nonfinite_or_out_of_range(score: float) -> None:
    output = _pass_b_output()
    output["decisions"]["RENAMED"]["directional_buy_score"] = score

    result = validate_future_pass_b_shape(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )

    assert "PB_BALANCE_BOUNDS" in result["per_ticker"]["RENAMED"]


@pytest.mark.parametrize("score", (None, "0.62", True))
def test_directional_buy_score_rejects_nonnumeric_values(score: object) -> None:
    output = _pass_b_output()
    output["decisions"]["RENAMED"]["directional_buy_score"] = score

    result = validate_future_pass_b_shape(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )

    assert "PB_BALANCE_SHAPE" in result["per_ticker"]["RENAMED"]


def test_old_raw_balance_object_is_not_accepted_by_new_contract() -> None:
    output = _pass_b_output()
    row = output["decisions"]["RENAMED"]
    row.pop("directional_buy_score")
    row["directional_balance"] = {"buy": 0.62, "sell": 0.38}

    result = validate_future_pass_b_shape(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )

    assert "PB_ROW_EXACT_FIELDS" in result["per_ticker"]["RENAMED"]


def test_model_cannot_author_separate_sell_score() -> None:
    output = _pass_b_output()
    output["decisions"]["RENAMED"]["directional_sell_score"] = 4.0

    result = validate_future_pass_b_shape(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )

    assert "PB_ROW_EXACT_FIELDS" in result["per_ticker"]["RENAMED"]


def test_final_directional_balance_preserves_sum_invariant() -> None:
    result = validate_materialized_directional_balance({"buy": 6.2, "sell": 3.7})

    assert result["status"] == "FAIL"
    assert result["errors"] == ["PB_BALANCE_SUM"]


def test_m12cn_wait_with_not_applicable_tactical_is_rejected_offline() -> None:
    output = _pass_b_output(new_buyer="WAIT")
    output["decisions"]["RENAMED"]["new_buyer_decision"]["tactical_choice"] = "NOT_APPLICABLE"

    result = validate_future_pass_b_shape(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog(current_price=120.0)},
    )

    assert "RENAMED:PB_WAIT_BRANCH_SHAPE" in result["errors"]


def test_m12cn_r2_model_authored_fundamental_metadata_is_impossible() -> None:
    output = _pass_b_output()
    output["decisions"]["RENAMED"]["fundamental_entry_band"] = {
        "status": "UNRESOLVED",
        "low": 1,
    }

    result = validate_future_pass_b_shape(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )

    assert "RENAMED:PB_ROW_EXACT_FIELDS" in result["errors"]


def test_resolved_attractive_pipeline_materializes_without_model_owned_metadata() -> None:
    pass_a_rows, pass_a_result = materialize_future_pass_a(
        _pass_a_output(),
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )
    pass_b_rows, pass_b_result = normalize_future_pass_b(
        _pass_b_output(),
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )
    validation = validate_materialized_pass_b(
        pass_b_rows,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
        pass_a_by_ticker={"RENAMED": pass_a_rows[0]},
        policy_options={"RENAMED": _resolved_option()},
    )

    assert pass_a_result["status"] == "PASS"
    assert pass_b_result["status"] == "PASS"
    assert validation["status"] == "PASS"
    assert pass_b_rows[0]["rule_trace"]
    assert pass_b_rows[0]["valuation_affects"] == ["NEW_BUYER"]


def test_unresolved_wait_pipeline_preserves_runtime_ownership() -> None:
    pass_a_rows, _ = materialize_future_pass_a(
        _pass_a_output(tier="UNRESOLVED"),
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )
    output = _pass_b_output(new_buyer="WAIT")
    decision = output["decisions"]["RENAMED"]["new_buyer_decision"]
    decision["reason_class"] = "FUNDAMENTAL_UNRESOLVED"
    pass_b_rows, _ = normalize_future_pass_b(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )
    validation = validate_materialized_pass_b(
        pass_b_rows,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
        pass_a_by_ticker={"RENAMED": pass_a_rows[0]},
        policy_options={"RENAMED": _unresolved_option()},
    )

    assert validation["status"] == "PASS"
    assert validation["entry_rows"][0]["entry_range"]["entry_range_status"] == (
        "ENTRY_RANGE_UNRESOLVED"
    )


def test_holder_review_supported_only_by_valuation_fails_cross_reference_gate() -> None:
    output = _pass_b_output(holder="REVIEW")
    output["decisions"]["RENAMED"]["holder_decision"]["evidence_refs"] = ["canonical:valuation"]
    rows, shape = normalize_future_pass_b(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )
    validation = validate_materialized_pass_b(
        rows,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
        pass_a_by_ticker={"RENAMED": _pass_a_choice()},
        policy_options={"RENAMED": _resolved_option()},
    )

    assert shape["status"] == "PASS"
    assert any("review_supported_only_by_valuation" in item for item in validation["errors"])


def test_rule_inventory_covers_every_new_validator_code() -> None:
    inventory = semantic_rule_inventory()
    inventoried = {row["rule"] for row in inventory["rules"]}
    assert source_rule_ids() <= inventoried
    assert inventory["missing_upstream_enforcement_count"] == 0


def test_parity_and_ownership_close_without_unresolved_fields() -> None:
    ownership = field_ownership_inventory()
    parity = parity_matrix()

    assert ownership["unresolved_requires_chat_count"] == 0
    assert ownership["after"]["pass_a_model_field_count"] == len(PASS_A_MODEL_FIELDS)
    assert ownership["after"]["pass_b_model_field_count"] == len(PASS_B_MODEL_FIELDS)
    assert (
        ownership["after"]["pass_a_model_field_count"]
        < ownership["before"]["pass_a_model_field_count"]
    )
    assert (
        ownership["after"]["pass_b_model_field_count"]
        < ownership["before"]["pass_b_model_field_count"]
    )
    assert parity["missing_upstream_enforcement_count"] == 0


def _pass_a_negative_cases() -> list[tuple[str, dict[str, object]]]:
    cases: list[tuple[str, dict[str, object]]] = []

    def add(rule: str, mutate: object) -> None:
        value = _pass_a_output()
        if callable(mutate):
            mutate(value)
        cases.append((rule, value))

    add("PA_ROOT_EXACT_FIELDS", lambda value: value.update({"extra": True}))
    add(
        "PA_SUBJECT_KEY_SCOPE",
        lambda value: value["classifications"].update(
            {"OTHER": value["classifications"].pop("RENAMED")}
        ),
    )
    add(
        "PA_ROW_EXACT_FIELDS",
        lambda value: value["classifications"]["RENAMED"].update({"extra": True}),
    )
    add(
        "PA_ARCHETYPE_ENUM",
        lambda value: value["classifications"]["RENAMED"].update({"archetype": "NOPE"}),
    )
    add(
        "PA_CONFIDENCE_ENUM",
        lambda value: value["classifications"]["RENAMED"].update({"archetype_confidence": "NOPE"}),
    )
    add(
        "PA_ARCHETYPE_REF_OWNERSHIP",
        lambda value: value["classifications"]["RENAMED"].update(
            {"archetype_supporting_claim_refs": ["claim:other"]}
        ),
    )
    add(
        "PA_ARCHETYPE_RATIONALE_BOUNDS",
        lambda value: value["classifications"]["RENAMED"].update({"archetype_rationale": ""}),
    )
    add(
        "PA_TIER_ENUM",
        lambda value: value["classifications"]["RENAMED"].update({"valuation_regime_tier": "NOPE"}),
    )
    add(
        "PA_UNRESOLVED_TIER_EMPTY_REFS",
        lambda value: value["classifications"]["RENAMED"].update(
            {"valuation_regime_tier": "UNRESOLVED"}
        ),
    )
    add(
        "PA_RESOLVED_TIER_REF_OWNERSHIP",
        lambda value: value["classifications"]["RENAMED"].update(
            {"tier_supporting_claim_refs": []}
        ),
    )
    add(
        "PA_TIER_RATIONALE_BOUNDS",
        lambda value: value["classifications"]["RENAMED"].update({"tier_rationale": ""}),
    )
    add(
        "PA_QUALITY_BRANCH_SHAPE",
        lambda value: value["classifications"]["RENAMED"].update(
            {"directional_data_quality_judgment": None}
        ),
    )
    add(
        "PA_QUALITY_NONE_SHAPE",
        lambda value: value["classifications"]["RENAMED"][
            "directional_data_quality_judgment"
        ].update({"evidence_refs": ["quality:provider"]}),
    )
    add(
        "PA_QUALITY_NEGATIVE_SHAPE",
        lambda value: value["classifications"]["RENAMED"].update(
            {
                "directional_data_quality_judgment": {
                    "effect": "DIRECTIONAL_NEGATIVE",
                    "reason_class": "PROVIDER_LIMITATION",
                    "reason": "wrong class",
                    "evidence_refs": ["quality:negative"],
                }
            }
        ),
    )
    add(
        "PA_QUALITY_POSITIVE_SHAPE",
        lambda value: value["classifications"]["RENAMED"].update(
            {
                "directional_data_quality_judgment": {
                    "effect": "DIRECTIONAL_POSITIVE",
                    "reason_class": "PROVIDER_LIMITATION",
                    "reason": "wrong class",
                    "evidence_refs": ["quality:positive"],
                }
            }
        ),
    )
    add(
        "PA_QUALITY_EFFECT_ENUM",
        lambda value: value["classifications"]["RENAMED"][
            "directional_data_quality_judgment"
        ].update({"effect": "NOPE"}),
    )
    add(
        "PA_SUMMARY_BOUNDS",
        lambda value: value["classifications"]["RENAMED"].update({"classification_summary": ""}),
    )
    return cases


@pytest.mark.parametrize(("rule", "output"), _pass_a_negative_cases())
def test_pass_a_every_structural_rule_has_negative_fixture(
    rule: str,
    output: dict[str, object],
) -> None:
    result = validate_future_pass_a_shape(
        output,
        subjects=("RENAMED",),
        subject_contexts={"RENAMED": _context()},
    )
    assert any(rule in error for error in result["errors"])


def _pass_b_negative_cases() -> list[tuple[str, dict[str, object]]]:
    cases: list[tuple[str, dict[str, object]]] = []

    def add(rule: str, mutate: object) -> None:
        value = _pass_b_output()
        if callable(mutate):
            mutate(value)
        cases.append((rule, value))

    add("PB_ROOT_EXACT_FIELDS", lambda value: value.update({"extra": True}))
    add(
        "PB_SUBJECT_KEY_SCOPE",
        lambda value: value["decisions"].update({"OTHER": value["decisions"].pop("RENAMED")}),
    )
    add(
        "PB_ROW_EXACT_FIELDS",
        lambda value: value["decisions"]["RENAMED"].update({"extra": True}),
    )
    add(
        "PB_OVERALL_ENUM",
        lambda value: value["decisions"]["RENAMED"].update({"overall_direction": "NOPE"}),
    )
    add(
        "PB_BALANCE_SHAPE",
        lambda value: value["decisions"]["RENAMED"].update({"directional_buy_score": "6.0"}),
    )
    add(
        "PB_BALANCE_BOUNDS",
        lambda value: value["decisions"]["RENAMED"].update({"directional_buy_score": 11.0}),
    )
    add(
        "PB_CONFIDENCE_ENUM",
        lambda value: value["decisions"]["RENAMED"].update({"decision_confidence": "NOPE"}),
    )
    add(
        "PB_SUPPORT_REF_OWNERSHIP",
        lambda value: value["decisions"]["RENAMED"].update(
            {"decisive_supporting_claim_refs": ["claim:other"]}
        ),
    )
    add(
        "PB_CONTRADICTION_REF_OWNERSHIP",
        lambda value: value["decisions"]["RENAMED"].update(
            {"decisive_contradicting_claim_refs": ["claim:other"]}
        ),
    )
    add(
        "PB_CLAIM_REF_OVERLAP",
        lambda value: value["decisions"]["RENAMED"].update(
            {"decisive_contradicting_claim_refs": ["claim:bull"]}
        ),
    )
    add(
        "PB_THESIS_STATE_ENUM",
        lambda value: value["decisions"]["RENAMED"].update({"thesis_state": "NOPE"}),
    )
    add(
        "PB_HOLDER_BRANCH_SHAPE",
        lambda value: value["decisions"]["RENAMED"].update({"holder_decision": None}),
    )
    add(
        "PB_HOLDER_REASON_BOUNDS",
        lambda value: value["decisions"]["RENAMED"]["holder_decision"].update({"reason": ""}),
    )
    add(
        "PB_HOLDABLE_BRANCH_SHAPE",
        lambda value: value["decisions"]["RENAMED"]["holder_decision"].update(
            {"evidence_refs": ["core:thesis"]}
        ),
    )
    add(
        "PB_REVIEW_BRANCH_SHAPE",
        lambda value: value["decisions"]["RENAMED"].update(
            {
                "holder_decision": {
                    "holder": "REVIEW",
                    "reason_class": "NOT_APPLICABLE",
                    "reason": "검토합니다.",
                    "evidence_refs": ["core:thesis"],
                }
            }
        ),
    )
    add(
        "PB_REDUCE_BRANCH_SHAPE",
        lambda value: value["decisions"]["RENAMED"].update(
            {
                "holder_decision": {
                    "holder": "REDUCE",
                    "reason_class": "THESIS_UNCERTAINTY",
                    "reason": "축소합니다.",
                    "evidence_refs": ["core:thesis"],
                }
            }
        ),
    )
    add(
        "PB_HOLDER_ENUM",
        lambda value: value["decisions"]["RENAMED"]["holder_decision"].update({"holder": "NOPE"}),
    )
    add(
        "PB_NEW_BUYER_BRANCH_SHAPE",
        lambda value: value["decisions"]["RENAMED"].update({"new_buyer_decision": None}),
    )
    add(
        "PB_NEW_BUYER_REASON_OR_REF_SHAPE",
        lambda value: value["decisions"]["RENAMED"]["new_buyer_decision"].update(
            {"evidence_refs": []}
        ),
    )
    add(
        "PB_ATTRACTIVE_BRANCH_SHAPE",
        lambda value: value["decisions"]["RENAMED"]["new_buyer_decision"].update(
            {"tactical_choice": "tactical:one"}
        ),
    )
    add(
        "PB_WAIT_BRANCH_SHAPE",
        lambda value: value["decisions"]["RENAMED"].update(
            {
                "new_buyer_decision": {
                    **_pass_b_choice(new_buyer="WAIT")["new_buyer_decision"],
                    "tactical_choice": "NOT_APPLICABLE",
                }
            }
        ),
    )
    add(
        "PB_AVOID_BRANCH_SHAPE",
        lambda value: value["decisions"]["RENAMED"].update(
            {
                "new_buyer_decision": {
                    **_pass_b_choice(new_buyer="AVOID")["new_buyer_decision"],
                    "tactical_choice": "tactical:one",
                }
            }
        ),
    )
    add(
        "PB_NEW_BUYER_ENUM",
        lambda value: value["decisions"]["RENAMED"]["new_buyer_decision"].update(
            {"new_buyer": "NOPE"}
        ),
    )
    add(
        "PB_SUMMARY_BOUNDS",
        lambda value: value["decisions"]["RENAMED"].update({"policy_summary": ""}),
    )
    return cases


@pytest.mark.parametrize(("rule", "output"), _pass_b_negative_cases())
def test_pass_b_every_structural_rule_has_negative_fixture(
    rule: str,
    output: dict[str, object],
) -> None:
    result = validate_future_pass_b_shape(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )
    assert any(rule in error for error in result["errors"])


@pytest.mark.parametrize("holder", ["REVIEW", "REDUCE"])
def test_holder_negative_axes_reject_valuation_only_support(holder: str) -> None:
    output = _pass_b_output(holder=holder)
    output["decisions"]["RENAMED"]["holder_decision"]["evidence_refs"] = ["canonical:valuation"]
    rows, shape = normalize_future_pass_b(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )
    validation = validate_materialized_pass_b(
        rows,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
        pass_a_by_ticker={"RENAMED": _pass_a_choice()},
        policy_options={"RENAMED": _resolved_option()},
    )
    expected = (
        "review_supported_only_by_valuation"
        if holder == "REVIEW"
        else ("reduce_supported_only_by_valuation")
    )
    assert shape["status"] == "PASS"
    assert any(expected in item for item in validation["errors"])


def test_durable_nonbuy_rejects_valuation_only_support() -> None:
    catalog = _catalog()
    for claim in catalog["atomic_claims"]:
        claim["parent_source_refs"] = ["canonical:valuation"]
    output = _pass_b_output(overall="HOLD")
    rows, _ = normalize_future_pass_b(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": catalog},
    )
    validation = validate_materialized_pass_b(
        rows,
        subjects=("RENAMED",),
        catalogs={"RENAMED": catalog},
        pass_a_by_ticker={"RENAMED": _pass_a_choice()},
        policy_options={"RENAMED": _resolved_option()},
    )
    assert any(
        "overall_nonbuy_supported_only_by_valuation_or_timing" in item
        for item in validation["errors"]
    )


def test_attractive_above_range_and_severe_condition_are_rejected() -> None:
    output = _pass_b_output(holder="REDUCE")
    rows, _ = normalize_future_pass_b(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog(current_price=120.0)},
    )
    validation = validate_materialized_pass_b(
        rows,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog(current_price=120.0)},
        pass_a_by_ticker={"RENAMED": _pass_a_choice()},
        policy_options={"RENAMED": _resolved_option()},
    )
    assert any(
        "attractive_without_permitted_fundamental_position" in item for item in validation["errors"]
    )
    assert any(
        "attractive_with_severe_execution_or_thesis_condition" in item
        for item in validation["errors"]
    )


def test_wait_tactical_reason_requires_price_above_tactical_band() -> None:
    output = _pass_b_output(new_buyer="WAIT")
    decision = output["decisions"]["RENAMED"]["new_buyer_decision"]
    decision["reason_class"] = "TACTICAL_TIMING"
    rows, _ = normalize_future_pass_b(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog(current_price=90.0)},
    )
    validation = validate_materialized_pass_b(
        rows,
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog(current_price=90.0)},
        pass_a_by_ticker={"RENAMED": _pass_a_choice()},
        policy_options={"RENAMED": _resolved_option()},
    )
    assert any(
        "wait_without_authorized_structured_condition" in item for item in validation["errors"]
    )


def test_legacy_avoid_without_material_ref_remains_guarded() -> None:
    decision = _pass_b_choice(new_buyer="AVOID")
    normalized = {
        "ticker": "RENAMED",
        "overall_direction": "BUY",
        "new_buyer": "AVOID",
        "holder": "HOLDABLE",
        "directional_balance": {"buy": 6.0, "sell": 4.0},
        "decision_confidence": "MEDIUM",
        "decisive_supporting_claim_refs": ["claim:bull"],
        "decisive_contradicting_claim_refs": [],
        "thesis_state": "INTACT",
        "holder_reason_class": "NOT_APPLICABLE",
        "holder_reason": "유지합니다.",
        "holder_reason_evidence_refs": [],
        "new_buyer_reason_class": "EXECUTION_OR_THESIS_RISK",
        "new_buyer_reason": "회피합니다.",
        "new_buyer_reason_refs": [],
        "tactical_choice": "NOT_APPLICABLE",
        "re_evaluate_conditions": [],
        "valuation_affects": [],
        "rule_trace": [],
        "policy_summary": decision["policy_summary"],
    }
    result = validate_new_buyer_consistency(
        decision=normalized,
        policy_option=_resolved_option(),
        entry_range={"entry_range_status": "NOT_APPLICABLE"},
        catalog=_catalog(),
    )
    assert "avoid_without_material_risk_evidence" in result["errors"]


def test_materializer_currency_mismatch_is_fail_closed() -> None:
    catalog = _catalog(current_price=120.0)
    catalog["entry_catalog"]["tactical_candidates"][0]["currency"] = "KRW"
    output = _pass_b_output(new_buyer="WAIT")
    rows, _ = normalize_future_pass_b(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": catalog},
    )
    validation = validate_materialized_pass_b(
        rows,
        subjects=("RENAMED",),
        catalogs={"RENAMED": catalog},
        pass_a_by_ticker={"RENAMED": _pass_a_choice()},
        policy_options={"RENAMED": _resolved_option()},
    )
    assert any("fundamental_tactical_currency_mismatch" in item for item in validation["errors"])


def test_security_basis_gate_rejects_resolved_depositary_option() -> None:
    result = validate_security_basis_gate(
        policy_options={"RENAMED": _resolved_option()},
        depositary_subjects=("RENAMED",),
    )
    assert result["status"] == "FAIL"
    assert result["resolved_depositary_subjects"] == ["RENAMED"]
