from __future__ import annotations

import re
from enum import StrEnum
from typing import Iterable, Mapping

from pydantic import BaseModel, ConfigDict


CONTRACT_VERSION = "bounded-production-validation-policy-v1"
BOUNDED_REWRITE_CONTRACT = "production-bounded-rewrite-invariance-v1"


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ValidationClass(StrEnum):
    HARD_DETERMINISTIC = "HARD_DETERMINISTIC"
    SEMANTIC_HARD = "SEMANTIC_HARD"
    SOFT_QUALITY = "SOFT_QUALITY"


class RepetitionClass(StrEnum):
    BENIGN_TEMPLATE_REPEAT = "BENIGN_TEMPLATE_REPEAT"
    REQUIRED_SAFETY_REPEAT = "REQUIRED_SAFETY_REPEAT"
    RENDERER_OWNED_REPEAT = "RENDERER_OWNED_REPEAT"
    MODEL_OWNED_SUBSTANTIVE_REPEAT = "MODEL_OWNED_SUBSTANTIVE_REPEAT"
    MATERIAL_SPAM_REPEAT = "MATERIAL_SPAM_REPEAT"


class RewriteDisposition(StrEnum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED_KEEP_ORIGINAL = "FAILED_KEEP_ORIGINAL"
    REJECTED_INVARIANCE = "REJECTED_INVARIANCE"


class BoundedRewriteResult(FrozenModel):
    contract: str = BOUNDED_REWRITE_CONTRACT
    disposition: RewriteDisposition
    invariant_errors: tuple[str, ...] = ()
    class_ab_rerun_required: bool
    original_remains_eligible: bool
    attempt_count: int


_SOFT_BINDING_CODES = (
    "numeric_fact_ref_raw_postposition",
    "numeric_fact_ref_redundant_authored_label",
    "numeric_fact_ref_postposition_resolution_failed",
    "numeric_fact_ref_postposition_mismatch",
)


def classify_repeated_span(
    span: str,
    *,
    stock_count: int,
    evidence_signature_count: int = 1,
    required_safety: bool = False,
    renderer_owned: bool = False,
    typed_template: bool = False,
) -> RepetitionClass:
    if required_safety:
        return RepetitionClass.REQUIRED_SAFETY_REPEAT
    if renderer_owned:
        return RepetitionClass.RENDERER_OWNED_REPEAT
    compact = re.sub(r"\s+", " ", span).strip()
    if typed_template or len(compact.split()) <= 8:
        return RepetitionClass.BENIGN_TEMPLATE_REPEAT
    if stock_count >= 3 and evidence_signature_count >= 2 and len(compact) >= 48:
        return RepetitionClass.MATERIAL_SPAM_REPEAT
    return RepetitionClass.MODEL_OWNED_SUBSTANTIVE_REPEAT


def _count(mapping: Mapping[str, object], key: str) -> int:
    try:
        return int(mapping.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def evaluate_production_quality(
    quality: Mapping[str, object],
    *,
    binding_errors: Iterable[str] = (),
    validation_errors: Iterable[str] = (),
) -> dict[str, object]:
    hard: list[str] = []
    semantic: list[str] = []
    soft: list[str] = []
    repetition_rows: list[dict[str, object]] = []

    for error in binding_errors:
        target = soft if any(code in error for code in _SOFT_BINDING_CODES) else hard
        target.append(str(error))
    hard.extend(str(error) for error in validation_errors)

    numeric = quality.get("numeric_label_quality")
    numeric = numeric if isinstance(numeric, Mapping) else {}
    for key in (
        "source_label_mismatch_count",
        "instrument_label_mismatch_count",
        "period_label_mismatch_count",
        "zone_role_mismatch_count",
    ):
        if _count(numeric, key):
            hard.append(f"numeric_label_quality:{key}")
    for key in (
        "redundant_authored_label_count",
        "repeated_bound_label_count",
        "postposition_mismatch_count",
    ):
        if _count(numeric, key):
            soft.append(f"numeric_label_quality:{key}")

    hard_count_fields = (
        "identity_prose_mismatch_count",
        "financial_period_error_count",
        "valuation_evidence_error_count",
        "rendered_identity_prose_mismatch_count",
    )
    semantic_count_fields = (
        "unsupported_comparative_claim_count",
        "supply_grounding_error_count",
    )
    for key in hard_count_fields:
        if _count(quality, key):
            hard.append(key)
    for key in semantic_count_fields:
        if _count(quality, key):
            semantic.append(key)

    completeness = quality.get("message_set_completeness")
    if isinstance(completeness, Mapping) and completeness.get("passed") is not True:
        hard.append("message_set_completeness")
    observer_holder = quality.get("observer_holder")
    if isinstance(observer_holder, list) and any(
        isinstance(item, Mapping) and item.get("distinct") is not True
        for item in observer_holder
    ):
        semantic.append("observer_holder_semantic_collision")

    supply = quality.get("supply_routing")
    supply = supply if isinstance(supply, Mapping) else {}
    for key in (
        "us_kr_style_horizon_count",
        "generic_us_supply_count",
    ):
        if _count(supply, key):
            semantic.append(f"supply_routing:{key}")
    if _count(supply, "generic_us_investor_flow_unknown_count") >= int(
        quality.get("duplicate_threshold") or 3
    ):
        semantic.append("supply_routing:generic_us_investor_flow_unknown_count")

    coverage = quality.get("kr_supply_numeric_coverage")
    if isinstance(coverage, list) and any(
        isinstance(item, Mapping) and item.get("numeric_horizon_coverage_passed") is not True
        for item in coverage
    ):
        semantic.append("kr_supply_numeric_coverage")

    business_owner = quality.get("numeric_ownership")
    if isinstance(business_owner, Mapping) and business_owner.get("hard_checks_passed") is not True:
        semantic.append("business_numeric_semantic_owner")
    primary_owner = quality.get("numeric_primary_ownership")
    if isinstance(primary_owner, Mapping) and primary_owner.get("hard_checks_passed") is not True:
        hard.append("numeric_primary_ownership")

    repeated = quality.get("repeated_sentences")
    if isinstance(repeated, list):
        for item in repeated:
            if not isinstance(item, Mapping):
                continue
            classification = classify_repeated_span(
                str(item.get("sentence") or ""),
                stock_count=_count(item, "stock_count"),
                evidence_signature_count=_count(item, "evidence_signature_count") or 1,
                required_safety=str(item.get("classification") or "").startswith("required_"),
            )
            row = {**dict(item), "production_classification": classification}
            repetition_rows.append(row)
            if classification == RepetitionClass.MATERIAL_SPAM_REPEAT:
                semantic.append("material_spam_repeat")
            elif classification not in {
                RepetitionClass.REQUIRED_SAFETY_REPEAT,
                RepetitionClass.RENDERER_OWNED_REPEAT,
            }:
                soft.append(f"repetition:{classification}")

    templates = quality.get("template_skeleton_repeats")
    if isinstance(templates, list):
        for item in templates:
            if not isinstance(item, Mapping):
                continue
            repetition_rows.append(
                {
                    **dict(item),
                    "production_classification": RepetitionClass.BENIGN_TEMPLATE_REPEAT,
                }
            )
            soft.append("repetition:BENIGN_TEMPLATE_REPEAT")

    for key in (
        "generic_numeric_summary_repeat_count",
        "generic_methodology_repeat_count",
        "generic_next_check_count",
        "generic_unknown_count",
        "template_skeleton_repeat_count",
        "substantive_repeated_sentence_count",
    ):
        if _count(quality, key):
            soft.append(f"quality:{key}")
    for key in (
        "rendered_heading_quality",
        "final_rendered_language",
        "watch_next_check_overlap",
        "numeric_fact_repetition",
    ):
        report = quality.get(key)
        if isinstance(report, Mapping) and report.get("hard_checks_passed") is not True:
            soft.append(key)

    hard = list(dict.fromkeys(hard))
    semantic = list(dict.fromkeys(semantic))
    soft = list(dict.fromkeys(soft))
    return {
        "contract": CONTRACT_VERSION,
        "hard_deterministic": hard,
        "semantic_hard": semantic,
        "soft_quality": soft,
        "hard_deterministic_count": len(hard),
        "semantic_hard_count": len(semantic),
        "soft_quality_count": len(soft),
        "repetition_assessments": repetition_rows,
        "material_spam_safety": "PASS" if "material_spam_repeat" not in semantic else "BLOCKED",
        "delivery_eligible": not hard and not semantic,
        "ai_semantic_reviewer_production_hard_veto": False,
    }


def evaluate_bounded_rewrite(
    before: Mapping[str, object],
    after: Mapping[str, object] | None,
    *,
    attempted: bool,
    attempt_count: int | None = None,
) -> BoundedRewriteResult:
    attempts = int(attempted) if attempt_count is None else attempt_count
    if attempts > 1:
        return BoundedRewriteResult(
            disposition=RewriteDisposition.REJECTED_INVARIANCE,
            invariant_errors=("rewrite_attempt_limit",),
            class_ab_rerun_required=False,
            original_remains_eligible=True,
            attempt_count=1,
        )
    if not attempted:
        return BoundedRewriteResult(
            disposition=RewriteDisposition.NOT_ATTEMPTED,
            class_ab_rerun_required=False,
            original_remains_eligible=True,
            attempt_count=0,
        )
    if after is None:
        return BoundedRewriteResult(
            disposition=RewriteDisposition.FAILED_KEEP_ORIGINAL,
            class_ab_rerun_required=False,
            original_remains_eligible=True,
            attempt_count=1,
        )
    preserved_fields = (
        "decision_fields",
        "claim_types",
        "condition_expression_refs",
        "evidence_refs",
        "numeric_refs",
        "price_refs",
        "new_buyer_stance",
        "holder_stance",
        "severity",
    )
    errors = tuple(field for field in preserved_fields if before.get(field) != after.get(field))
    return BoundedRewriteResult(
        disposition=(
            RewriteDisposition.REJECTED_INVARIANCE if errors else RewriteDisposition.SUCCEEDED
        ),
        invariant_errors=errors,
        class_ab_rerun_required=not errors,
        original_remains_eligible=True,
        attempt_count=1,
    )
