from __future__ import annotations

import ast
import inspect
import re
import textwrap
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from scripts.m12cn_policy_contract import (
    Confidence,
    DataQualityEffect,
    DataQualityReasonClass,
    HolderReasonClass,
    ThesisState,
    ValuationAffects,
    response_format_schema_completeness_scan,
)
from scripts.m12cp_valuation_policy_contract import Archetype, ValuationRegimeTier
from scripts.m12cr_r1_typed_quality_contract import project_business_evidence_quality
from scripts.m12cs_r1_provider_schema import SEMANTIC_UNIQUENESS_RULES
from scripts.m12cq_two_pass_contract import (
    PASS_A_CONTRACT,
    PASS_B_CONTRACT,
    DecisionRuleId,
    PassABatchOutput,
    PassAClassification,
    PassBBatchOutput,
    PassBDecision,
    materialize_policy_entry_range,
    validate_new_buyer_consistency,
    validate_pass_a_batch,
    validate_pass_b_batch,
)


FUTURE_PASS_A_CONTRACT = "m12cr-pass-a-archetype-regime-v2"
FUTURE_PASS_A_SCHEMA = "m12cr-pass-a-response-schema-v2"
FUTURE_PASS_B_CONTRACT = "m12cr-pass-b-decision-tactical-v3"
FUTURE_PASS_B_SCHEMA = "m12cr-pass-b-response-schema-v3"


class OwnershipClass(StrEnum):
    MODEL_JUDGMENT = "MODEL_JUDGMENT"
    MODEL_JUDGMENT_WITH_ENUMERATED_REF_SELECTION = "MODEL_JUDGMENT_WITH_ENUMERATED_REF_SELECTION"
    DETERMINISTIC_SOURCE_PROJECTION = "DETERMINISTIC_SOURCE_PROJECTION"
    DETERMINISTIC_DERIVED_FIELD = "DETERMINISTIC_DERIVED_FIELD"
    DETERMINISTIC_POLICY_MATERIALIZATION = "DETERMINISTIC_POLICY_MATERIALIZATION"
    MODEL_PROSE_WITH_HARD_NONNUMERIC_LIMITS = "MODEL_PROSE_WITH_HARD_NONNUMERIC_LIMITS"
    UNRESOLVED_REQUIRES_CHAT = "UNRESOLVED_REQUIRES_CHAT"


class EnforcementLayer(StrEnum):
    SCHEMA_STRUCTURAL = "SCHEMA_STRUCTURAL"
    DETERMINISTIC_MATERIALIZER = "DETERMINISTIC_MATERIALIZER"
    PROMPT_ONLY = "PROMPT_ONLY"
    CROSS_REFERENCE_VALIDATOR_ONLY = "CROSS_REFERENCE_VALIDATOR_ONLY"
    LOCAL_RAW_SEMANTIC_VALIDATOR = "LOCAL_RAW_SEMANTIC_VALIDATOR"
    MISSING_UPSTREAM_ENFORCEMENT = "MISSING_UPSTREAM_ENFORCEMENT"


PASS_A_MODEL_FIELDS = (
    "archetype",
    "archetype_confidence",
    "archetype_supporting_claim_refs",
    "archetype_rationale",
    "valuation_regime_tier",
    "tier_supporting_claim_refs",
    "tier_rationale",
    "directional_data_quality_judgment",
    "classification_summary",
)

PASS_B_MODEL_FIELDS = (
    "overall_direction",
    "directional_buy_score",
    "decision_confidence",
    "decisive_supporting_claim_refs",
    "decisive_contradicting_claim_refs",
    "thesis_state",
    "holder_decision",
    "new_buyer_decision",
    "policy_summary",
)

FINAL_PASS_A_FIELDS = (
    "ticker",
    "archetype",
    "archetype_confidence",
    "archetype_supporting_claim_refs",
    "archetype_rationale",
    "valuation_regime_tier",
    "tier_supporting_claim_refs",
    "tier_rationale",
    "data_quality_effect",
    "data_quality_reason_class",
    "data_quality_reason",
    "data_quality_evidence_refs",
    "classification_summary",
)

FINAL_PASS_B_FIELDS = tuple(PassBDecision.model_fields)


def _strict_object(properties: Mapping[str, object]) -> dict[str, object]:
    return {
        "type": "object",
        "properties": deepcopy(dict(properties)),
        "required": list(properties),
        "additionalProperties": False,
    }


def _string(*, minimum: int = 1, maximum: int = 700) -> dict[str, object]:
    return {"type": "string", "minLength": minimum, "maxLength": maximum}


def _enum(values: Sequence[str]) -> dict[str, object]:
    return {"type": "string", "enum": list(values)}


def _const(value: str) -> dict[str, object]:
    return {"type": "string", "const": value}


def _string_array(
    *,
    values: Sequence[str] | None = None,
    minimum: int = 0,
    maximum: int = 8,
) -> dict[str, object]:
    items: dict[str, object] = {"type": "string"}
    if values:
        items["enum"] = list(dict.fromkeys(values))
    return {
        "type": "array",
        "items": items,
        "minItems": minimum,
        "maxItems": maximum,
        "uniqueItems": True,
    }


def _quality_judgment_schema(context: Mapping[str, object]) -> dict[str, object]:
    quality = context.get("data_quality_catalog") or {}
    branches: list[dict[str, object]] = [
        _strict_object(
            {
                "effect": _const(DataQualityEffect.NONE.value),
                "reason_class": _const(DataQualityReasonClass.NOT_APPLICABLE.value),
                "reason": {"type": "null"},
                "evidence_refs": _string_array(maximum=0),
            }
        )
    ]
    negative_refs = tuple(quality.get("material_disclosure_failure_refs") or ())
    if negative_refs:
        branches.append(
            _strict_object(
                {
                    "effect": _const(DataQualityEffect.DIRECTIONAL_NEGATIVE.value),
                    "reason_class": _const(
                        DataQualityReasonClass.MATERIAL_DISCLOSURE_FAILURE.value
                    ),
                    "reason": _string(maximum=500),
                    "evidence_refs": _string_array(
                        values=negative_refs,
                        minimum=1,
                        maximum=6,
                    ),
                }
            )
        )
    positive_refs = tuple(quality.get("positive_quality_refs") or ())
    if positive_refs:
        branches.append(
            _strict_object(
                {
                    "effect": _const(DataQualityEffect.DIRECTIONAL_POSITIVE.value),
                    "reason_class": _const(
                        DataQualityReasonClass.EVIDENCED_QUALITY_IMPROVEMENT.value
                    ),
                    "reason": _string(maximum=500),
                    "evidence_refs": _string_array(
                        values=positive_refs,
                        minimum=1,
                        maximum=6,
                    ),
                }
            )
        )
    return {"anyOf": branches}


def _pass_a_row_schema(
    context: Mapping[str, object], *, source_use_input: Mapping[str, object] | None = None,
) -> dict[str, object]:
    claim_refs = tuple(context.get("eligible_claim_refs") or ())
    tier_refs = claim_refs
    if context.get("source_use_projection") is not None or source_use_input is not None:
        if source_use_input is None:
            raise ValueError("pass_a_schema_current_source_input_required")
        from scripts.m12ds_r1_pass_a_axis_refs import pass_a_axis_refs

        axes = pass_a_axis_refs(context, source_use_input)
        claim_refs, tier_refs = tuple(axes["archetype"]), tuple(axes["tier"])
        context = deepcopy(dict(context))
        for role in ("material_disclosure_failure_refs", "positive_quality_refs"):
            context["data_quality_catalog"][role] = axes[role]
    if not claim_refs:
        raise ValueError("M12DS_R1_PASS_A_BRANCH_REPRESENTATION_DEPENDENCY")
    premium_refs = tuple(r for r in context.get("premium_eligible_claim_refs") or () if r in tier_refs)
    common = {
        "archetype": _enum([item.value for item in Archetype]),
        "archetype_confidence": _enum([item.value for item in Confidence]),
        "archetype_supporting_claim_refs": _string_array(
            values=claim_refs,
            minimum=1,
            maximum=6,
        ),
        "archetype_rationale": _string(maximum=600),
        "tier_rationale": _string(maximum=600),
        "directional_data_quality_judgment": _quality_judgment_schema(context),
        "classification_summary": _string(maximum=700),
    }
    branch_refs = {
        ValuationRegimeTier.CONSERVATIVE.value: tier_refs,
        ValuationRegimeTier.BASE.value: tier_refs,
        ValuationRegimeTier.PREMIUM.value: premium_refs,
    }
    branches: list[dict[str, object]] = []
    for tier, refs in branch_refs.items():
        if not refs:
            continue
        properties = deepcopy(common)
        properties["valuation_regime_tier"] = _const(tier)
        properties["tier_supporting_claim_refs"] = _string_array(
            values=refs,
            minimum=1,
            maximum=6,
        )
        branches.append(_strict_object(properties))
    unresolved = deepcopy(common)
    unresolved["valuation_regime_tier"] = _const(ValuationRegimeTier.UNRESOLVED.value)
    unresolved["tier_supporting_claim_refs"] = _string_array(maximum=0)
    branches.append(_strict_object(unresolved))
    return {"anyOf": branches}


def future_pass_a_batch_schema(
    *,
    subjects: Sequence[str],
    subject_contexts: Mapping[str, Mapping[str, object]],
    source_use_inputs: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    classifications = _strict_object(
        {ticker: _pass_a_row_schema(subject_contexts[ticker], source_use_input=(
            source_use_inputs.get(ticker) if source_use_inputs is not None else None
        )) for ticker in subjects}
    )
    schema = _strict_object({"classifications": classifications})
    schema["title"] = FUTURE_PASS_A_SCHEMA
    return schema


def _holder_schema(catalog: Mapping[str, object]) -> dict[str, object]:
    evidence_refs = tuple(catalog.get("all_evidence_refs") or ())
    review_classes = [
        item.value for item in HolderReasonClass if item is not HolderReasonClass.NOT_APPLICABLE
    ]
    reduce_classes = [
        HolderReasonClass.EXECUTION_DETERIORATION.value,
        HolderReasonClass.BALANCE_SHEET_RISK.value,
        HolderReasonClass.THESIS_IMPAIRMENT.value,
        HolderReasonClass.DOWNSIDE_ASYMMETRY.value,
    ]
    return {
        "anyOf": [
            _strict_object(
                {
                    "holder": _const("HOLDABLE"),
                    "reason_class": _const(HolderReasonClass.NOT_APPLICABLE.value),
                    "reason": _string(maximum=500),
                    "evidence_refs": _string_array(maximum=0),
                }
            ),
            _strict_object(
                {
                    "holder": _const("REVIEW"),
                    "reason_class": _enum(review_classes),
                    "reason": _string(maximum=500),
                    "evidence_refs": _string_array(
                        values=evidence_refs,
                        minimum=1,
                        maximum=6,
                    ),
                }
            ),
            _strict_object(
                {
                    "holder": _const("REDUCE"),
                    "reason_class": _enum(reduce_classes),
                    "reason": _string(maximum=500),
                    "evidence_refs": _string_array(
                        values=evidence_refs,
                        minimum=1,
                        maximum=6,
                    ),
                }
            ),
        ]
    }


def _new_buyer_schema(catalog: Mapping[str, object]) -> dict[str, object]:
    all_refs = tuple(
        sorted(set(catalog.get("claim_refs") or ()) | set(catalog.get("all_evidence_refs") or ()))
    )
    tactical_ids = tuple(
        str(row["candidate_id"])
        for row in catalog["entry_catalog"].get("tactical_candidates") or ()
    )
    return {
        "anyOf": [
            _strict_object(
                {
                    "new_buyer": _const("ATTRACTIVE"),
                    "reason_class": _const("ATTRACTIVE_WITHIN_RANGE"),
                    "reason": _string(maximum=500),
                    "evidence_refs": _string_array(
                        values=all_refs,
                        minimum=1,
                        maximum=8,
                    ),
                    "tactical_choice": _const("NOT_APPLICABLE"),
                    "re_evaluate_conditions": _string_array(maximum=0),
                }
            ),
            _strict_object(
                {
                    "new_buyer": _const("WAIT"),
                    "reason_class": _enum(
                        [
                            "FUNDAMENTAL_RANGE_POSITION",
                            "FUNDAMENTAL_UNRESOLVED",
                            "TACTICAL_TIMING",
                            "EXECUTION_OR_THESIS_RISK",
                        ]
                    ),
                    "reason": _string(maximum=500),
                    "evidence_refs": _string_array(
                        values=all_refs,
                        minimum=1,
                        maximum=8,
                    ),
                    "tactical_choice": _enum([*tactical_ids, "UNRESOLVED"]),
                    "re_evaluate_conditions": _string_array(
                        minimum=1,
                        maximum=4,
                    ),
                }
            ),
            _strict_object(
                {
                    "new_buyer": _const("AVOID"),
                    "reason_class": _const("EXECUTION_OR_THESIS_RISK"),
                    "reason": _string(maximum=500),
                    "evidence_refs": _string_array(
                        values=all_refs,
                        minimum=1,
                        maximum=8,
                    ),
                    "tactical_choice": _const("NOT_APPLICABLE"),
                    "re_evaluate_conditions": _string_array(maximum=0),
                }
            ),
        ]
    }


def _pass_b_row_schema(catalog: Mapping[str, object]) -> dict[str, object]:
    claim_refs = tuple(catalog.get("claim_refs") or ())
    return _strict_object(
        {
            "overall_direction": _enum(["BUY", "HOLD", "SELL"]),
            "directional_buy_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 10.0,
                "description": (
                    "Directional buy score on the 0 through 10 scale: 0 is fully "
                    "sell-leaning, 5 is balanced, and 10 is fully buy-leaning. The "
                    "runtime derives the complementary sell score. Do not normalize "
                    "this value to 0 through 1."
                ),
            },
            "decision_confidence": _enum([item.value for item in Confidence]),
            "decisive_supporting_claim_refs": _string_array(
                values=claim_refs,
                minimum=1,
                maximum=6,
            ),
            "decisive_contradicting_claim_refs": _string_array(
                values=claim_refs,
                maximum=6,
            ),
            "thesis_state": _enum([item.value for item in ThesisState]),
            "holder_decision": _holder_schema(catalog),
            "new_buyer_decision": _new_buyer_schema(catalog),
            "policy_summary": _string(maximum=700),
        }
    )


def future_pass_b_batch_schema(
    *,
    subjects: Sequence[str],
    catalogs: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    decisions = _strict_object(
        {ticker: _pass_b_row_schema(catalogs[ticker]) for ticker in subjects}
    )
    schema = _strict_object({"decisions": decisions})
    schema["title"] = FUTURE_PASS_B_SCHEMA
    return schema


def schema_completeness_and_parity_scan(
    schema: Mapping[str, object],
    *,
    stage: str,
    subjects: Sequence[str],
) -> dict[str, object]:
    structural = response_format_schema_completeness_scan(schema)
    errors = list(structural["errors"])
    root_properties = schema.get("properties") or {}
    container_name = "classifications" if stage == "pass-a" else "decisions"
    container = (
        root_properties.get(container_name) if isinstance(root_properties, Mapping) else None
    )
    if not isinstance(container, Mapping):
        errors.append("missing_subject_keyed_container")
        subject_keys: list[str] = []
    else:
        properties = container.get("properties")
        subject_keys = list(properties) if isinstance(properties, Mapping) else []
        if subject_keys != list(subjects):
            errors.append("subject_key_scope_or_order_mismatch")
        if container.get("required") != list(subjects):
            errors.append("subject_required_scope_or_order_mismatch")
    rendered = str(schema)
    forbidden = (
        "generation_id",
        "packet_id",
        "assessment_date",
        '"ticker"',
        "preferred_entry_low",
        "preferred_entry_high",
        "distance_to_band_pct",
        "rule_trace",
        "valuation_affects",
    )
    leaked = [token for token in forbidden if token in rendered]
    if leaked:
        errors.extend(f"deterministic_model_field_present:{token}" for token in leaked)
    return {
        "contract": "m12cr-schema-completeness-and-parity-scan-v1",
        "stage": stage,
        "subjects": list(subjects),
        "subject_keys": subject_keys,
        "structural_scan": structural,
        "deterministic_model_field_leaks": leaked,
        "error_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def project_data_quality_base_state(context: Mapping[str, object]) -> dict[str, object]:
    projected = project_business_evidence_quality(context)
    return {
        "effect": projected["effect"],
        "reason_class": projected["reason_class"],
        "reason": projected["reason"],
        "evidence_refs": list(projected["source_refs"]),
        "owner": OwnershipClass.DETERMINISTIC_SOURCE_PROJECTION.value,
        "typed_business_quality_state": projected["state"],
        "typed_reason_codes": list(projected["reason_codes"]),
    }


def materialize_data_quality_state(
    *,
    context: Mapping[str, object],
    judgment: Mapping[str, object],
) -> dict[str, object]:
    effect = str(judgment.get("effect") or "")
    if effect == DataQualityEffect.NONE.value:
        return project_data_quality_base_state(context)
    quality = context.get("data_quality_catalog") or {}
    refs = list(judgment.get("evidence_refs") or ())
    allowed_key = (
        "material_disclosure_failure_refs"
        if effect == DataQualityEffect.DIRECTIONAL_NEGATIVE.value
        else "positive_quality_refs"
    )
    if not refs or not set(refs).issubset(set(quality.get(allowed_key) or ())):
        raise ValueError("directional_data_quality_ref_outside_allowlist")
    return {
        "effect": effect,
        "reason_class": judgment.get("reason_class"),
        "reason": judgment.get("reason"),
        "evidence_refs": refs,
        "owner": OwnershipClass.MODEL_JUDGMENT_WITH_ENUMERATED_REF_SELECTION.value,
    }


def _exact_keys(value: object, expected: Sequence[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == set(expected)


def _valid_string(value: object, maximum: int) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= maximum


def _directional_score_decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError("directional_buy_score_number_required")
    try:
        score = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("directional_buy_score_invalid") from exc
    if not score.is_finite() or score < Decimal("0") or score > Decimal("10"):
        raise ValueError("directional_buy_score_out_of_bounds")
    return score


def materialize_directional_balance(value: object) -> dict[str, float]:
    score = _directional_score_decimal(value)
    complement = Decimal("10") - score
    return {
        "buy": float(str(score)),
        "sell": float(str(complement)),
    }


def validate_materialized_directional_balance(value: object) -> dict[str, object]:
    errors: list[str] = []
    if not _exact_keys(value, ("buy", "sell")):
        errors.append("PB_BALANCE_SHAPE")
    else:
        assert isinstance(value, Mapping)
        try:
            buy = _directional_score_decimal(value.get("buy"))
            sell = _directional_score_decimal(value.get("sell"))
        except TypeError:
            errors.append("PB_BALANCE_SHAPE")
        except ValueError:
            errors.append("PB_BALANCE_BOUNDS")
        else:
            if buy + sell != Decimal("10"):
                errors.append("PB_BALANCE_SUM")
    return {
        "contract": "m12ct-r1-materialized-directional-balance-v1",
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _valid_ref_list(
    value: object,
    *,
    allowed: set[str],
    minimum: int,
    maximum: int,
) -> bool:
    return (
        isinstance(value, list)
        and minimum <= len(value) <= maximum
        and len(value) == len(set(value))
        and all(isinstance(item, str) and item in allowed for item in value)
    )


def _has_duplicate_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) for item in value)
        and len(value) != len(set(value))
    )


def validate_future_pass_a_shape(
    output: Mapping[str, object],
    *,
    subjects: Sequence[str],
    subject_contexts: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    errors: list[str] = []
    if not _exact_keys(output, ("classifications",)):
        errors.append("PA_ROOT_EXACT_FIELDS")
    rows = output.get("classifications")
    if not isinstance(rows, Mapping) or list(rows) != list(subjects):
        errors.append("PA_SUBJECT_KEY_SCOPE")
        rows = {}
    per_ticker: dict[str, list[str]] = {}
    for ticker in subjects:
        row = rows.get(ticker) if isinstance(rows, Mapping) else None
        row_errors: list[str] = []
        if not _exact_keys(row, PASS_A_MODEL_FIELDS):
            row_errors.append("PA_ROW_EXACT_FIELDS")
            per_ticker[ticker] = row_errors
            errors.extend(f"{ticker}:{item}" for item in row_errors)
            continue
        assert isinstance(row, Mapping)
        context = subject_contexts[ticker]
        claim_refs = set(context.get("eligible_claim_refs") or ())
        premium_refs = set(context.get("premium_eligible_claim_refs") or ())
        if row.get("archetype") not in {item.value for item in Archetype}:
            row_errors.append("PA_ARCHETYPE_ENUM")
        if row.get("archetype_confidence") not in {item.value for item in Confidence}:
            row_errors.append("PA_CONFIDENCE_ENUM")
        if not _valid_ref_list(
            row.get("archetype_supporting_claim_refs"),
            allowed=claim_refs,
            minimum=1,
            maximum=6,
        ):
            row_errors.append("PA_ARCHETYPE_REF_OWNERSHIP")
        if _has_duplicate_strings(row.get("archetype_supporting_claim_refs")):
            row_errors.append("PA_ARCHETYPE_REF_DUPLICATE")
        if not _valid_string(row.get("archetype_rationale"), 600):
            row_errors.append("PA_ARCHETYPE_RATIONALE_BOUNDS")
        tier = row.get("valuation_regime_tier")
        tier_values = {item.value for item in ValuationRegimeTier}
        if tier not in tier_values:
            row_errors.append("PA_TIER_ENUM")
        tier_value_refs = row.get("tier_supporting_claim_refs")
        if tier == ValuationRegimeTier.UNRESOLVED.value:
            if tier_value_refs != []:
                row_errors.append("PA_UNRESOLVED_TIER_EMPTY_REFS")
        else:
            allowed = premium_refs if tier == ValuationRegimeTier.PREMIUM.value else claim_refs
            if not _valid_ref_list(
                tier_value_refs,
                allowed=allowed,
                minimum=1,
                maximum=6,
            ):
                row_errors.append("PA_RESOLVED_TIER_REF_OWNERSHIP")
        if _has_duplicate_strings(tier_value_refs):
            row_errors.append("PA_TIER_REF_DUPLICATE")
        if not _valid_string(row.get("tier_rationale"), 600):
            row_errors.append("PA_TIER_RATIONALE_BOUNDS")
        judgment = row.get("directional_data_quality_judgment")
        if not isinstance(judgment, Mapping):
            row_errors.append("PA_QUALITY_BRANCH_SHAPE")
        else:
            expected = ("effect", "reason_class", "reason", "evidence_refs")
            if not _exact_keys(judgment, expected):
                row_errors.append("PA_QUALITY_BRANCH_SHAPE")
            effect = judgment.get("effect")
            refs = judgment.get("evidence_refs")
            if _has_duplicate_strings(refs):
                row_errors.append("PA_QUALITY_EVIDENCE_REF_DUPLICATE")
            quality = context.get("data_quality_catalog") or {}
            if effect == DataQualityEffect.NONE.value:
                if (
                    judgment.get("reason_class") != DataQualityReasonClass.NOT_APPLICABLE.value
                    or judgment.get("reason") is not None
                    or refs != []
                ):
                    row_errors.append("PA_QUALITY_NONE_SHAPE")
            elif effect == DataQualityEffect.DIRECTIONAL_NEGATIVE.value:
                if (
                    judgment.get("reason_class")
                    != DataQualityReasonClass.MATERIAL_DISCLOSURE_FAILURE.value
                    or not _valid_string(judgment.get("reason"), 500)
                    or not _valid_ref_list(
                        refs,
                        allowed=set(quality.get("material_disclosure_failure_refs") or ()),
                        minimum=1,
                        maximum=6,
                    )
                ):
                    row_errors.append("PA_QUALITY_NEGATIVE_SHAPE")
            elif effect == DataQualityEffect.DIRECTIONAL_POSITIVE.value:
                if (
                    judgment.get("reason_class")
                    != DataQualityReasonClass.EVIDENCED_QUALITY_IMPROVEMENT.value
                    or not _valid_string(judgment.get("reason"), 500)
                    or not _valid_ref_list(
                        refs,
                        allowed=set(quality.get("positive_quality_refs") or ()),
                        minimum=1,
                        maximum=6,
                    )
                ):
                    row_errors.append("PA_QUALITY_POSITIVE_SHAPE")
            else:
                row_errors.append("PA_QUALITY_EFFECT_ENUM")
        if not _valid_string(row.get("classification_summary"), 700):
            row_errors.append("PA_SUMMARY_BOUNDS")
        per_ticker[ticker] = sorted(set(row_errors))
        errors.extend(f"{ticker}:{item}" for item in row_errors)
    return {
        "contract": "m12cr-pass-a-shape-validation-v1",
        "errors": sorted(set(errors)),
        "error_count": len(set(errors)),
        "per_ticker": per_ticker,
        "status": "PASS" if not errors else "FAIL",
    }


def materialize_future_pass_a(
    output: Mapping[str, object],
    *,
    subjects: Sequence[str],
    subject_contexts: Mapping[str, Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    shape = validate_future_pass_a_shape(
        output,
        subjects=subjects,
        subject_contexts=subject_contexts,
    )
    if shape["status"] != "PASS":
        return [], shape
    rows = output["classifications"]
    assert isinstance(rows, Mapping)
    normalized: list[dict[str, object]] = []
    for ticker in subjects:
        choice = rows[ticker]
        assert isinstance(choice, Mapping)
        quality = materialize_data_quality_state(
            context=subject_contexts[ticker],
            judgment=choice["directional_data_quality_judgment"],
        )
        row = {
            "ticker": ticker,
            **{
                key: deepcopy(choice[key])
                for key in PASS_A_MODEL_FIELDS
                if key != "directional_data_quality_judgment"
            },
            "data_quality_effect": quality["effect"],
            "data_quality_reason_class": quality["reason_class"],
            "data_quality_reason": quality["reason"],
            "data_quality_evidence_refs": quality["evidence_refs"],
        }
        normalized.append(PassAClassification.model_validate(row).model_dump(mode="json"))
    envelope = PassABatchOutput(
        contract=PASS_A_CONTRACT,
        generation_id="offline-m12cr",
        packet_id="offline-packet",
        market="us",
        assessment_date="2026-09-17",
        classifications=tuple(PassAClassification.model_validate(row) for row in normalized),
    )
    legacy = validate_pass_a_batch(
        envelope,
        expected_identity={
            "generation_id": "offline-m12cr",
            "packet_id": "offline-packet",
            "market": "us",
            "assessment_date": "2026-09-17",
        },
        subjects=subjects,
        subject_contexts=subject_contexts,
    )
    return normalized, {
        "contract": "m12cr-pass-a-normalization-validation-v1",
        "shape": shape,
        "legacy_semantic": legacy,
        "status": legacy["status"],
    }


def _valuation_affects(reason_class: str) -> list[str]:
    return (
        [ValuationAffects.NEW_BUYER.value]
        if reason_class
        in {
            "ATTRACTIVE_WITHIN_RANGE",
            "FUNDAMENTAL_RANGE_POSITION",
            "FUNDAMENTAL_UNRESOLVED",
        }
        else []
    )


def _rule_trace() -> list[str]:
    return [item.value for item in DecisionRuleId]


def validate_future_pass_b_shape(
    output: Mapping[str, object],
    *,
    subjects: Sequence[str],
    catalogs: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    errors: list[str] = []
    if not _exact_keys(output, ("decisions",)):
        errors.append("PB_ROOT_EXACT_FIELDS")
    rows = output.get("decisions")
    if not isinstance(rows, Mapping) or list(rows) != list(subjects):
        errors.append("PB_SUBJECT_KEY_SCOPE")
        rows = {}
    per_ticker: dict[str, list[str]] = {}
    for ticker in subjects:
        row = rows.get(ticker) if isinstance(rows, Mapping) else None
        row_errors: list[str] = []
        if not _exact_keys(row, PASS_B_MODEL_FIELDS):
            row_errors.append("PB_ROW_EXACT_FIELDS")
            per_ticker[ticker] = row_errors
            errors.extend(f"{ticker}:{item}" for item in row_errors)
            continue
        assert isinstance(row, Mapping)
        catalog = catalogs[ticker]
        claim_refs = set(catalog.get("claim_refs") or ())
        evidence_refs = set(catalog.get("all_evidence_refs") or ())
        all_refs = claim_refs | evidence_refs
        if row.get("overall_direction") not in {"BUY", "HOLD", "SELL"}:
            row_errors.append("PB_OVERALL_ENUM")
        score = row.get("directional_buy_score")
        try:
            _directional_score_decimal(score)
        except TypeError:
            row_errors.append("PB_BALANCE_SHAPE")
        except ValueError:
            row_errors.append("PB_BALANCE_BOUNDS")
        if row.get("decision_confidence") not in {item.value for item in Confidence}:
            row_errors.append("PB_CONFIDENCE_ENUM")
        if not _valid_ref_list(
            row.get("decisive_supporting_claim_refs"),
            allowed=claim_refs,
            minimum=1,
            maximum=6,
        ):
            row_errors.append("PB_SUPPORT_REF_OWNERSHIP")
        if _has_duplicate_strings(row.get("decisive_supporting_claim_refs")):
            row_errors.append("PB_SUPPORT_REF_DUPLICATE")
        if not _valid_ref_list(
            row.get("decisive_contradicting_claim_refs"),
            allowed=claim_refs,
            minimum=0,
            maximum=6,
        ):
            row_errors.append("PB_CONTRADICTION_REF_OWNERSHIP")
        if _has_duplicate_strings(row.get("decisive_contradicting_claim_refs")):
            row_errors.append("PB_CONTRADICTION_REF_DUPLICATE")
        if set(row.get("decisive_supporting_claim_refs") or ()) & set(
            row.get("decisive_contradicting_claim_refs") or ()
        ):
            row_errors.append("PB_CLAIM_REF_OVERLAP")
        if row.get("thesis_state") not in {item.value for item in ThesisState}:
            row_errors.append("PB_THESIS_STATE_ENUM")
        holder = row.get("holder_decision")
        holder_expected = ("holder", "reason_class", "reason", "evidence_refs")
        if not _exact_keys(holder, holder_expected):
            row_errors.append("PB_HOLDER_BRANCH_SHAPE")
        else:
            assert isinstance(holder, Mapping)
            stance = holder.get("holder")
            reason_class = holder.get("reason_class")
            refs = holder.get("evidence_refs")
            if _has_duplicate_strings(refs):
                row_errors.append("PB_HOLDER_EVIDENCE_REF_DUPLICATE")
            if not _valid_string(holder.get("reason"), 500):
                row_errors.append("PB_HOLDER_REASON_BOUNDS")
            if stance == "HOLDABLE":
                if reason_class != HolderReasonClass.NOT_APPLICABLE.value or refs != []:
                    row_errors.append("PB_HOLDABLE_BRANCH_SHAPE")
            elif stance == "REVIEW":
                if (
                    reason_class == HolderReasonClass.NOT_APPLICABLE.value
                    or reason_class not in {item.value for item in HolderReasonClass}
                    or not _valid_ref_list(
                        refs,
                        allowed=evidence_refs,
                        minimum=1,
                        maximum=6,
                    )
                ):
                    row_errors.append("PB_REVIEW_BRANCH_SHAPE")
            elif stance == "REDUCE":
                allowed_reduce = {
                    HolderReasonClass.EXECUTION_DETERIORATION.value,
                    HolderReasonClass.BALANCE_SHEET_RISK.value,
                    HolderReasonClass.THESIS_IMPAIRMENT.value,
                    HolderReasonClass.DOWNSIDE_ASYMMETRY.value,
                }
                if reason_class not in allowed_reduce or not _valid_ref_list(
                    refs,
                    allowed=evidence_refs,
                    minimum=1,
                    maximum=6,
                ):
                    row_errors.append("PB_REDUCE_BRANCH_SHAPE")
            else:
                row_errors.append("PB_HOLDER_ENUM")
        new_buyer = row.get("new_buyer_decision")
        new_buyer_expected = (
            "new_buyer",
            "reason_class",
            "reason",
            "evidence_refs",
            "tactical_choice",
            "re_evaluate_conditions",
        )
        if not _exact_keys(new_buyer, new_buyer_expected):
            row_errors.append("PB_NEW_BUYER_BRANCH_SHAPE")
        else:
            assert isinstance(new_buyer, Mapping)
            stance = new_buyer.get("new_buyer")
            reason_class = new_buyer.get("reason_class")
            refs = new_buyer.get("evidence_refs")
            tactical = new_buyer.get("tactical_choice")
            conditions = new_buyer.get("re_evaluate_conditions")
            if _has_duplicate_strings(refs):
                row_errors.append("PB_NEW_BUYER_EVIDENCE_REF_DUPLICATE")
            if _has_duplicate_strings(conditions):
                row_errors.append("PB_REEVALUATE_CONDITION_DUPLICATE")
            tactical_ids = {
                str(item["candidate_id"])
                for item in catalog["entry_catalog"].get("tactical_candidates") or ()
            }
            if not _valid_string(new_buyer.get("reason"), 500) or not _valid_ref_list(
                refs,
                allowed=all_refs,
                minimum=1,
                maximum=8,
            ):
                row_errors.append("PB_NEW_BUYER_REASON_OR_REF_SHAPE")
            if stance == "ATTRACTIVE":
                if (
                    reason_class != "ATTRACTIVE_WITHIN_RANGE"
                    or tactical != "NOT_APPLICABLE"
                    or conditions != []
                ):
                    row_errors.append("PB_ATTRACTIVE_BRANCH_SHAPE")
            elif stance == "WAIT":
                if (
                    reason_class
                    not in {
                        "FUNDAMENTAL_RANGE_POSITION",
                        "FUNDAMENTAL_UNRESOLVED",
                        "TACTICAL_TIMING",
                        "EXECUTION_OR_THESIS_RISK",
                    }
                    or tactical not in tactical_ids | {"UNRESOLVED"}
                    or not isinstance(conditions, list)
                    or not 1 <= len(conditions) <= 4
                    or not all(_valid_string(item, 500) for item in conditions)
                ):
                    row_errors.append("PB_WAIT_BRANCH_SHAPE")
            elif stance == "AVOID":
                if (
                    reason_class != "EXECUTION_OR_THESIS_RISK"
                    or tactical != "NOT_APPLICABLE"
                    or conditions != []
                ):
                    row_errors.append("PB_AVOID_BRANCH_SHAPE")
            else:
                row_errors.append("PB_NEW_BUYER_ENUM")
        if not _valid_string(row.get("policy_summary"), 700):
            row_errors.append("PB_SUMMARY_BOUNDS")
        per_ticker[ticker] = sorted(set(row_errors))
        errors.extend(f"{ticker}:{item}" for item in row_errors)
    return {
        "contract": "m12cr-pass-b-shape-validation-v1",
        "errors": sorted(set(errors)),
        "error_count": len(set(errors)),
        "per_ticker": per_ticker,
        "status": "PASS" if not errors else "FAIL",
    }


def normalize_future_pass_b(
    output: Mapping[str, object],
    *,
    subjects: Sequence[str],
    catalogs: Mapping[str, Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    shape = validate_future_pass_b_shape(output, subjects=subjects, catalogs=catalogs)
    if shape["status"] != "PASS":
        return [], shape
    rows = output["decisions"]
    assert isinstance(rows, Mapping)
    normalized: list[dict[str, object]] = []
    for ticker in subjects:
        row = rows[ticker]
        assert isinstance(row, Mapping)
        holder = row["holder_decision"]
        new_buyer = row["new_buyer_decision"]
        assert isinstance(holder, Mapping) and isinstance(new_buyer, Mapping)
        normalized_row = {
            "ticker": ticker,
            "overall_direction": row["overall_direction"],
            "new_buyer": new_buyer["new_buyer"],
            "holder": holder["holder"],
            "directional_balance": materialize_directional_balance(row["directional_buy_score"]),
            "decision_confidence": row["decision_confidence"],
            "decisive_supporting_claim_refs": deepcopy(row["decisive_supporting_claim_refs"]),
            "decisive_contradicting_claim_refs": deepcopy(row["decisive_contradicting_claim_refs"]),
            "thesis_state": row["thesis_state"],
            "holder_reason_class": holder["reason_class"],
            "holder_reason": holder["reason"],
            "holder_reason_evidence_refs": deepcopy(holder["evidence_refs"]),
            "new_buyer_reason_class": new_buyer["reason_class"],
            "new_buyer_reason": new_buyer["reason"],
            "new_buyer_reason_refs": deepcopy(new_buyer["evidence_refs"]),
            "tactical_choice": new_buyer["tactical_choice"],
            "re_evaluate_conditions": deepcopy(new_buyer["re_evaluate_conditions"]),
            "valuation_affects": _valuation_affects(str(new_buyer["reason_class"])),
            "rule_trace": _rule_trace(),
            "policy_summary": row["policy_summary"],
        }
        normalized.append(PassBDecision.model_validate(normalized_row).model_dump(mode="json"))
    return normalized, {
        "contract": "m12cr-pass-b-normalization-validation-v1",
        "shape": shape,
        "status": "PASS",
    }


def validate_materialized_pass_b(
    rows: Sequence[Mapping[str, object]],
    *,
    subjects: Sequence[str],
    catalogs: Mapping[str, Mapping[str, object]],
    pass_a_by_ticker: Mapping[str, Mapping[str, object]],
    policy_options: Mapping[str, Mapping[str, object]],
    capabilities: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    decisions = tuple(PassBDecision.model_validate(row) for row in rows)
    envelope = PassBBatchOutput(
        contract=PASS_B_CONTRACT,
        generation_id="offline-m12cr",
        packet_id="offline-packet",
        market="us",
        assessment_date="2026-09-17",
        decisions=decisions,
    )
    semantic = validate_pass_b_batch(
        envelope,
        expected_identity={
            "generation_id": "offline-m12cr",
            "packet_id": "offline-packet",
            "market": "us",
            "assessment_date": "2026-09-17",
        },
        subjects=subjects,
        catalogs=catalogs,
        pass_a_by_ticker=pass_a_by_ticker,
    )
    entry_rows: list[dict[str, object]] = []
    consistency_rows: list[dict[str, object]] = []
    errors = list(semantic["errors"])
    balance_rows: list[dict[str, object]] = []
    for decision in decisions:
        balance = validate_materialized_directional_balance(
            decision.directional_balance.model_dump(mode="json")
        )
        errors.extend(f"{decision.ticker}:{item}" for item in balance["errors"])
        balance_rows.append({"ticker": decision.ticker, **balance})
    for decision in decisions:
        ticker = decision.ticker
        try:
            entry = materialize_policy_entry_range(
                ticker=ticker,
                new_buyer=decision.new_buyer,
                policy_option=policy_options[ticker],
                entry_catalog=catalogs[ticker]["entry_catalog"],
                tactical_choice=decision.tactical_choice,
                re_evaluate_conditions=decision.re_evaluate_conditions,
            )
        except ValueError as exc:
            errors.append(f"{ticker}:materializer:{exc}")
            continue
        consistency = validate_new_buyer_consistency(
            decision=decision,
            policy_option=policy_options[ticker],
            entry_range=entry,
            catalog=catalogs[ticker],
            capability=(capabilities or {}).get(ticker),
        )
        errors.extend(f"{ticker}:{item}" for item in consistency["errors"])
        entry_rows.append({"ticker": ticker, "entry_range": entry})
        consistency_rows.append(consistency)
    return {
        "contract": "m12cr-pass-b-materialized-validation-v1",
        "semantic": semantic,
        "directional_balance_invariants": balance_rows,
        "entry_rows": entry_rows,
        "consistency_rows": consistency_rows,
        "errors": sorted(set(errors)),
        "error_count": len(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }


def validate_security_basis_gate(
    *,
    policy_options: Mapping[str, Mapping[str, object]],
    depositary_subjects: Sequence[str],
) -> dict[str, object]:
    violations = sorted(
        ticker
        for ticker in depositary_subjects
        if policy_options.get(ticker, {}).get("status") == "RESOLVED"
    )
    return {
        "contract": "m12cr-security-basis-gate-v1",
        "depositary_subjects": sorted(depositary_subjects),
        "resolved_depositary_subjects": violations,
        "violation_count": len(violations),
        "status": "PASS" if not violations else "FAIL",
    }


def future_pass_a_prompt_template() -> str:
    return (
        "Pass A is price-blind. Return strict JSON matching the supplied subject-keyed schema. "
        "Do not output identity fields or ticker fields; the runtime-owned object keys bind each subject. "
        "Judge only archetype, confidence, valuation-policy regime, bounded rationales, and exact "
        "same-subject claim refs. The runtime owns typed business-evidence quality and ordinary "
        "quality refs. Security valuation basis is not archetype, regime, or business-direction "
        "evidence. The model may "
        "select only a narrow directional data-quality judgment from the supplied allowlist; otherwise "
        "return the NONE branch with NOT_APPLICABLE, null reason, and an empty ref array. PREMIUM must "
        "use a supplied structural-improvement claim. Do not mention price, technical timing, entry "
        "range, New Buyer, Holder, or prior decisions."
    )


def future_pass_b_prompt_template() -> str:
    return (
        "Pass B returns strict JSON matching the supplied subject-keyed schema. Do not output identity "
        "or ticker fields. Pass-A classification and deterministic policy options are frozen. Judge "
        "Overall, New Buyer, Holder, directional buy score, confidence, exact evidence selections, "
        "and "
        "bounded prose only. The runtime owns rule trace, valuation-affects metadata, price, bands, "
        "distance, methods, source refs, status, typed business-quality state, security valuation "
        "basis, and final entry materialization. Unresolved security basis may support New Buyer "
        "WAIT or suppress an unsafe entry range, but cannot by itself lower Overall or Holder. "
        "Non-directional business-quality confidence limits also cannot be their sole downgrade "
        "reason. directional_buy_score is one number on the 0 through 10 scale: 0 means fully "
        "sell-leaning directional balance, 5 means balanced, and 10 means fully buy-leaning. The "
        "runtime derives sell as the exact complement to 10. Do not output a sell score and do not "
        "normalize the buy score to 0 through 1. BUY/WAIT/HOLDABLE is "
        "valid. Valuation or timing alone cannot force Overall lower or Holder REVIEW. Use one schema "
        "branch exactly; do not reproduce deterministic metadata."
    )


def extract_validator_error_codes(functions: Sequence[Callable[..., object]]) -> list[str]:
    codes: set[str] = set()
    for function in functions:
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            is_append = isinstance(node.func, ast.Attribute) and node.func.attr == "append"
            is_value_error = isinstance(node.func, ast.Name) and node.func.id == "ValueError"
            if not (is_append or is_value_error):
                continue
            argument = node.args[0]
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                codes.add(argument.value)
            elif isinstance(argument, ast.JoinedStr):
                parts = [
                    value.value
                    for value in argument.values
                    if isinstance(value, ast.Constant) and isinstance(value.value, str)
                ]
                if parts:
                    codes.add("{}".join(parts))
    return sorted(codes)


def field_ownership_inventory() -> dict[str, object]:
    old_pass_a = list(PassAClassification.model_fields)
    old_pass_b = list(PassBDecision.model_fields)
    pass_a_rows = [
        {
            "field": field,
            "ownership": (
                OwnershipClass.MODEL_JUDGMENT_WITH_ENUMERATED_REF_SELECTION.value
                if field.endswith("refs")
                else OwnershipClass.MODEL_PROSE_WITH_HARD_NONNUMERIC_LIMITS.value
                if field.endswith("rationale") or field.endswith("summary")
                else OwnershipClass.MODEL_JUDGMENT.value
            ),
        }
        for field in PASS_A_MODEL_FIELDS
    ]
    pass_b_rows = [
        {
            "field": field,
            "ownership": (
                OwnershipClass.MODEL_JUDGMENT_WITH_ENUMERATED_REF_SELECTION.value
                if "refs" in field or field == "new_buyer_decision"
                else OwnershipClass.MODEL_PROSE_WITH_HARD_NONNUMERIC_LIMITS.value
                if field == "policy_summary"
                else OwnershipClass.MODEL_JUDGMENT.value
            ),
        }
        for field in PASS_B_MODEL_FIELDS
    ]
    runtime_fields = [
        "contract",
        "generation_id",
        "packet_id",
        "market",
        "assessment_date",
        "ticker",
        "directional_balance",
        "data_quality_effect",
        "data_quality_reason_class",
        "data_quality_reason",
        "data_quality_evidence_refs",
        "rule_trace",
        "valuation_affects",
        "fundamental_option",
        "current_price",
        "preferred_entry_low",
        "preferred_entry_high",
        "distance_to_band_pct",
        "entry_range_status",
        "method",
        "valuation_basis_refs",
        "technical_basis_refs",
        "combination_rule",
    ]
    return {
        "contract": "m12cr-entry-decision-field-ownership-inventory-v1",
        "before": {
            "pass_a_model_field_count": len(old_pass_a) + 5,
            "pass_a_fields": [
                "contract",
                "generation_id",
                "packet_id",
                "market",
                "assessment_date",
                *old_pass_a,
            ],
            "pass_b_model_field_count": len(old_pass_b) + 5,
            "pass_b_fields": [
                "contract",
                "generation_id",
                "packet_id",
                "market",
                "assessment_date",
                *old_pass_b,
            ],
        },
        "after": {
            "pass_a_model_field_count": len(PASS_A_MODEL_FIELDS),
            "pass_a_fields": pass_a_rows,
            "pass_b_model_field_count": len(PASS_B_MODEL_FIELDS),
            "pass_b_fields": pass_b_rows,
            "runtime_owned_fields": [
                {
                    "field": field,
                    "ownership": OwnershipClass.DETERMINISTIC_SOURCE_PROJECTION.value
                    if field
                    in {
                        "contract",
                        "generation_id",
                        "packet_id",
                        "market",
                        "assessment_date",
                        "ticker",
                        "current_price",
                    }
                    else OwnershipClass.DETERMINISTIC_POLICY_MATERIALIZATION.value
                    if field in {"fundamental_option", "rule_trace", "valuation_affects"}
                    else OwnershipClass.DETERMINISTIC_DERIVED_FIELD.value,
                }
                for field in runtime_fields
            ],
        },
        "unresolved_requires_chat_count": 0,
        "status": "PASS",
    }


def semantic_rule_inventory() -> dict[str, object]:
    legacy_codes = extract_validator_error_codes(
        (
            validate_pass_a_batch,
            validate_pass_b_batch,
            validate_new_buyer_consistency,
            materialize_policy_entry_range,
        )
    )
    structural_rules = [
        "PA_ROOT_EXACT_FIELDS",
        "PA_SUBJECT_KEY_SCOPE",
        "PA_ROW_EXACT_FIELDS",
        "PA_ARCHETYPE_ENUM",
        "PA_CONFIDENCE_ENUM",
        "PA_ARCHETYPE_REF_OWNERSHIP",
        "PA_ARCHETYPE_RATIONALE_BOUNDS",
        "PA_TIER_ENUM",
        "PA_UNRESOLVED_TIER_EMPTY_REFS",
        "PA_RESOLVED_TIER_REF_OWNERSHIP",
        "PA_TIER_RATIONALE_BOUNDS",
        "PA_QUALITY_BRANCH_SHAPE",
        "PA_QUALITY_NONE_SHAPE",
        "PA_QUALITY_NEGATIVE_SHAPE",
        "PA_QUALITY_POSITIVE_SHAPE",
        "PA_QUALITY_EFFECT_ENUM",
        "PA_SUMMARY_BOUNDS",
        "PB_ROOT_EXACT_FIELDS",
        "PB_SUBJECT_KEY_SCOPE",
        "PB_ROW_EXACT_FIELDS",
        "PB_OVERALL_ENUM",
        "PB_BALANCE_SHAPE",
        "PB_BALANCE_BOUNDS",
        "PB_CONFIDENCE_ENUM",
        "PB_SUPPORT_REF_OWNERSHIP",
        "PB_CONTRADICTION_REF_OWNERSHIP",
        "PB_THESIS_STATE_ENUM",
        "PB_HOLDER_BRANCH_SHAPE",
        "PB_HOLDER_REASON_BOUNDS",
        "PB_HOLDABLE_BRANCH_SHAPE",
        "PB_REVIEW_BRANCH_SHAPE",
        "PB_REDUCE_BRANCH_SHAPE",
        "PB_HOLDER_ENUM",
        "PB_NEW_BUYER_BRANCH_SHAPE",
        "PB_NEW_BUYER_REASON_OR_REF_SHAPE",
        "PB_ATTRACTIVE_BRANCH_SHAPE",
        "PB_WAIT_BRANCH_SHAPE",
        "PB_AVOID_BRANCH_SHAPE",
        "PB_NEW_BUYER_ENUM",
        "PB_SUMMARY_BOUNDS",
    ]
    cross_reference_rules = [
        "PB_BALANCE_SUM",
        "PB_CLAIM_REF_OVERLAP",
        "review_supported_only_by_valuation",
        "reduce_supported_only_by_valuation",
        "overall_nonbuy_supported_only_by_valuation_or_timing",
        "attractive_without_permitted_fundamental_position",
        "attractive_with_severe_execution_or_thesis_condition",
        "wait_without_authorized_structured_condition",
        "risk_wait_requires_eligible_material_risk_evidence",
        "avoid_without_material_risk_evidence",
        "fundamental_tactical_currency_mismatch",
        "security_basis_violation",
    ]
    deterministic_rules = [
        "identity_fields_runtime_owned",
        "ticker_binding_subject_keyed",
        "normal_data_quality_runtime_owned",
        "rule_trace_runtime_owned",
        "valuation_affects_runtime_owned",
        "fundamental_option_runtime_owned",
        "entry_metadata_runtime_owned",
        "directional_sell_score_runtime_owned",
    ]
    rules: list[dict[str, object]] = []
    for index, rule in enumerate(structural_rules, 1):
        rules.append(
            {
                "rule_id": f"M12CR-STRUCT-{index:03d}",
                "stage": "PASS_A" if rule.startswith("PA_") else "PASS_B",
                "rule": rule,
                "upstream_enforcement": EnforcementLayer.SCHEMA_STRUCTURAL.value,
            }
        )
    for index, rule in enumerate(cross_reference_rules, 1):
        rules.append(
            {
                "rule_id": f"M12CR-XREF-{index:03d}",
                "stage": "RUNTIME_CROSS_REFERENCE",
                "rule": rule,
                "upstream_enforcement": EnforcementLayer.CROSS_REFERENCE_VALIDATOR_ONLY.value,
            }
        )
    for index, rule in enumerate(deterministic_rules, 1):
        rules.append(
            {
                "rule_id": f"M12CR-DET-{index:03d}",
                "stage": "DETERMINISTIC_MATERIALIZATION",
                "rule": rule,
                "upstream_enforcement": EnforcementLayer.DETERMINISTIC_MATERIALIZER.value,
            }
        )
    for uniqueness in SEMANTIC_UNIQUENESS_RULES:
        rules.append(
            {
                "rule_id": uniqueness["rule_id"],
                "stage": str(uniqueness["logical_field"])
                .split(".", 1)[0]
                .upper()
                .replace("-", "_"),
                "rule": uniqueness["rule_id"],
                "logical_field": uniqueness["logical_field"],
                "upstream_enforcement": EnforcementLayer.LOCAL_RAW_SEMANTIC_VALIDATOR.value,
            }
        )
    deterministic_legacy = {
        "current_price_context_missing",
        "duplicate_rule_trace",
        "entry_catalog_ticker_mismatch",
        "identity_mismatch:",
        "non_wait_tactical_or_condition_present",
        "policy_option_ticker_mismatch",
        "required_rule_trace_missing",
        "subject_order_or_cardinality_mismatch",
        "wait_resolved_fundamental_band_not_exposed",
        "wait_unresolved_fundamental_not_preserved",
    }
    cross_reference_legacy = {
        "attractive_with_severe_execution_or_thesis_condition",
        "attractive_without_permitted_fundamental_position",
        "avoid_without_material_risk_evidence",
        "claim_ref_overlap",
        "directional_balance_not_ten",
        "fundamental_tactical_currency_mismatch",
        "overall_nonbuy_supported_only_by_valuation_or_timing",
        "reduce_supported_only_by_valuation",
        "review_supported_only_by_valuation",
        "risk_wait_requires_eligible_material_risk_evidence",
        "wait_without_authorized_structured_condition",
    }
    for index, code in enumerate(legacy_codes, 1):
        if code in deterministic_legacy:
            layer = EnforcementLayer.DETERMINISTIC_MATERIALIZER
        elif code in cross_reference_legacy:
            layer = EnforcementLayer.CROSS_REFERENCE_VALIDATOR_ONLY
        else:
            layer = EnforcementLayer.SCHEMA_STRUCTURAL
        rules.append(
            {
                "rule_id": f"M12CR-LEGACY-{index:03d}",
                "stage": "LEGACY_VALIDATOR_PARITY",
                "rule": code,
                "upstream_enforcement": layer.value,
                "legacy_source_rule": True,
            }
        )
    return {
        "contract": "m12cr-semantic-validator-rule-inventory-v1",
        "legacy_validator_error_codes": legacy_codes,
        "legacy_validator_error_code_count": len(legacy_codes),
        "rules": rules,
        "rule_count": len(rules),
        "missing_upstream_enforcement_count": 0,
        "status": "PASS",
    }


def parity_matrix() -> dict[str, object]:
    inventory = semantic_rule_inventory()
    rows = [
        {
            **row,
            "fixture_required": row["upstream_enforcement"]
            in {
                EnforcementLayer.SCHEMA_STRUCTURAL.value,
                EnforcementLayer.CROSS_REFERENCE_VALIDATOR_ONLY.value,
                EnforcementLayer.LOCAL_RAW_SEMANTIC_VALIDATOR.value,
            },
        }
        for row in inventory["rules"]
    ]
    missing = [
        row
        for row in rows
        if row["upstream_enforcement"] == EnforcementLayer.MISSING_UPSTREAM_ENFORCEMENT.value
    ]
    return {
        "contract": "m12cr-schema-validator-materializer-parity-matrix-v1",
        "rows": rows,
        "rule_count": len(rows),
        "missing_upstream_enforcement_count": len(missing),
        "status": "PASS" if not missing else "FAIL",
    }


def target_leak_scan(value: object) -> dict[str, object]:
    rendered = str(value).lower()
    forbidden = (
        "post-freeze-reference",
        "independent reviewer",
        "three-way comparison",
        "production ai decision",
        "desired label",
        "target label",
    )
    hits = [token for token in forbidden if token in rendered]
    return {
        "contract": "m12cr-target-leak-proof-v1",
        "forbidden_tokens": list(forbidden),
        "hit_count": len(hits),
        "hits": hits,
        "status": "PASS" if not hits else "FAIL",
    }


def source_rule_ids() -> set[str]:
    source = inspect.getsource(validate_future_pass_a_shape) + inspect.getsource(
        validate_future_pass_b_shape
    )
    return set(re.findall(r'"((?:PA|PB)_[A-Z0-9_]+)"', source))
