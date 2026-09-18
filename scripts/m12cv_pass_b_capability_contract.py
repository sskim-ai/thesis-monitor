from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation

from scripts.m12cn_policy_contract import Confidence, HolderReasonClass, ThesisState
from scripts.m12cp_valuation_policy_contract import Archetype
from scripts.m12cq_two_pass_contract import (
    eligible_material_risk_claim_refs,
    eligible_material_risk_evidence_refs,
)
from scripts.m12cr_shadow_contract import validate_future_pass_b_shape


CAPABILITY_CONTRACT = "m12cv-pass-b-capability-catalog-v1"
CAPABILITY_SCHEMA = "m12cv-pass-b-capability-response-schema-v1"
CAPABILITY_VALIDATION = "m12cv-pass-b-capability-selection-validation-v1"

NEW_BUYER_REASONS = (
    "ATTRACTIVE_WITHIN_RANGE",
    "FUNDAMENTAL_RANGE_POSITION",
    "FUNDAMENTAL_UNRESOLVED",
    "TACTICAL_TIMING",
    "EXECUTION_OR_THESIS_RISK",
)

REDUCE_REASON_CLASSES = (
    HolderReasonClass.EXECUTION_DETERIORATION.value,
    HolderReasonClass.BALANCE_SHEET_RISK.value,
    HolderReasonClass.THESIS_IMPAIRMENT.value,
    HolderReasonClass.DOWNSIDE_ASYMMETRY.value,
)

REVIEW_REASON_CLASSES = tuple(
    item.value for item in HolderReasonClass if item is not HolderReasonClass.NOT_APPLICABLE
)


def _ordered_unique(values: Sequence[object]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))


def _decimal(value: object) -> Decimal | None:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _strict_object(properties: Mapping[str, object]) -> dict[str, object]:
    return {
        "type": "object",
        "properties": deepcopy(dict(properties)),
        "required": list(properties),
        "additionalProperties": False,
    }


def _string(*, maximum: int) -> dict[str, object]:
    return {"type": "string", "minLength": 1, "maxLength": maximum}


def _const(value: str) -> dict[str, object]:
    return {"type": "string", "const": value}


def _enum(values: Sequence[str]) -> dict[str, object]:
    return {"type": "string", "enum": list(values)}


def _string_array(
    *,
    values: Sequence[str] | None = None,
    minimum: int = 0,
    maximum: int,
) -> dict[str, object]:
    items: dict[str, object] = {"type": "string"}
    if values is not None:
        items["enum"] = _ordered_unique(values)
    return {
        "type": "array",
        "items": items,
        "minItems": minimum,
        "maxItems": maximum,
        "uniqueItems": True,
    }


def material_business_claim_refs(catalog: Mapping[str, object]) -> list[str]:
    excluded = set(catalog.get("valuation_evidence_refs") or ()) | set(
        catalog.get("timing_evidence_refs") or ()
    )
    refs: list[str] = []
    for row in catalog.get("atomic_claims") or ():
        if not isinstance(row, Mapping):
            continue
        claim_ref = str(row.get("claim_ref") or "")
        parent_refs = {str(ref) for ref in row.get("parent_source_refs") or ()}
        if claim_ref and any(ref not in excluded for ref in parent_refs):
            refs.append(claim_ref)
    return _ordered_unique(refs)


def material_risk_claim_refs(catalog: Mapping[str, object]) -> list[str]:
    return sorted(eligible_material_risk_claim_refs(catalog))


def material_risk_evidence_refs(catalog: Mapping[str, object]) -> list[str]:
    return sorted(eligible_material_risk_evidence_refs(catalog))


def _source_refs(
    *,
    catalog: Mapping[str, object],
    context: Mapping[str, object],
    policy_option: Mapping[str, object],
) -> dict[str, list[str]]:
    all_refs = set(catalog.get("all_evidence_refs") or ()) | set(catalog.get("claim_refs") or ())
    current = context.get("current_price")
    current_ref = str(current.get("ref_id") or "") if isinstance(current, Mapping) else ""
    security = context.get("security_valuation_basis_state")
    security_refs = list(security.get("source_refs") or ()) if isinstance(security, Mapping) else []
    fundamental_refs = list(policy_option.get("evidence_refs") or ())
    valuation_refs = list(catalog.get("valuation_evidence_refs") or ())
    unresolved = _ordered_unique([*fundamental_refs, *valuation_refs, *security_refs, current_ref])
    unresolved = [ref for ref in unresolved if ref in all_refs]
    fundamental = _ordered_unique([*fundamental_refs, *valuation_refs, current_ref])
    fundamental = [ref for ref in fundamental if ref in all_refs]
    if not unresolved:
        unresolved = _ordered_unique(catalog.get("core_evidence_refs") or ())[:8]
    if not fundamental:
        fundamental = _ordered_unique(catalog.get("core_evidence_refs") or ())[:8]
    return {"fundamental": fundamental, "unresolved": unresolved}


def _tactical_capability(
    *,
    context: Mapping[str, object],
    policy_option: Mapping[str, object],
) -> dict[str, object]:
    current = context.get("current_price")
    current_value = _decimal(current.get("value")) if isinstance(current, Mapping) else None
    current_currency = str(current.get("currency") or "") if isinstance(current, Mapping) else ""
    option_resolved = policy_option.get("status") == "RESOLVED"
    option_currency = str(policy_option.get("currency") or "") if option_resolved else ""
    valid: list[dict[str, object]] = []
    excluded: list[dict[str, str]] = []
    for candidate in context.get("tactical_candidates") or ():
        if not isinstance(candidate, Mapping):
            continue
        candidate_id = str(candidate.get("candidate_id") or "")
        low = _decimal(candidate.get("low"))
        high = _decimal(candidate.get("high"))
        currency = str(candidate.get("currency") or "")
        reason: str | None = None
        if not candidate_id or low is None or high is None or low > high:
            reason = "malformed_tactical_candidate"
        elif current_currency and currency != current_currency:
            reason = "tactical_current_currency_mismatch"
        elif option_resolved and option_currency and currency != option_currency:
            reason = "fundamental_tactical_currency_mismatch"
        if reason is not None:
            excluded.append({"candidate_id": candidate_id, "reason": reason})
            continue
        valid.append(
            {
                "candidate_id": candidate_id,
                "low": float(low),
                "high": float(high),
                "currency": currency,
                "evidence_refs": _ordered_unique(candidate.get("evidence_refs") or ()),
                "current_above_high": current_value is not None and current_value > high,
            }
        )
    return {
        "valid_candidates": valid,
        "valid_candidate_ids": [str(row["candidate_id"]) for row in valid],
        "wait_candidate_ids": [
            str(row["candidate_id"]) for row in valid if row["current_above_high"]
        ],
        "wait_evidence_refs": _ordered_unique(
            [ref for row in valid if row["current_above_high"] for ref in row["evidence_refs"]]
            + ([str(current.get("ref_id"))] if isinstance(current, Mapping) else [])
        ),
        "excluded_candidates": excluded,
    }


def build_pass_b_capability_catalog(
    *,
    context: Mapping[str, object],
    catalog: Mapping[str, object],
    pass_a: Mapping[str, object],
    policy_option: Mapping[str, object],
) -> dict[str, object]:
    ticker = str(context.get("ticker") or "")
    if not ticker or ticker != str(catalog.get("ticker") or ""):
        raise ValueError("capability_subject_catalog_mismatch")
    if ticker != str(pass_a.get("ticker") or ""):
        raise ValueError("capability_subject_pass_a_mismatch")
    if ticker != str(policy_option.get("ticker") or ""):
        raise ValueError("capability_subject_policy_option_mismatch")

    current = context.get("current_price")
    current_value = _decimal(current.get("value")) if isinstance(current, Mapping) else None
    option_resolved = (
        policy_option.get("status") == "RESOLVED"
        and _decimal(policy_option.get("low")) is not None
        and _decimal(policy_option.get("high")) is not None
        and bool(policy_option.get("currency"))
    )
    high = _decimal(policy_option.get("high")) if option_resolved else None
    security = context.get("security_valuation_basis_state")
    security_safe = bool(
        isinstance(security, Mapping)
        and security.get("state") == "RESOLVED"
        and security.get("new_buyer_price_resolution_use_allowed") is True
    )
    material_claims = material_business_claim_refs(catalog)
    risk_claims = material_risk_claim_refs(catalog)
    risk_evidence = material_risk_evidence_refs(catalog)
    tactical = _tactical_capability(context=context, policy_option=policy_option)
    source_refs = _source_refs(
        catalog=catalog,
        context=context,
        policy_option=policy_option,
    )

    new_buyer_branches: list[dict[str, object]] = []
    excluded_new_buyer: list[dict[str, str]] = []
    if option_resolved and security_safe and current_value is not None and high is not None:
        if current_value <= high:
            new_buyer_branches.append(
                {
                    "stance": "ATTRACTIVE",
                    "reason_class": "ATTRACTIVE_WITHIN_RANGE",
                    "allowed_evidence_refs": source_refs["fundamental"],
                    "allowed_tactical_choices": ["NOT_APPLICABLE"],
                    "prerequisite": "resolved_safe_fundamental_position",
                }
            )
        else:
            new_buyer_branches.append(
                {
                    "stance": "WAIT",
                    "reason_class": "FUNDAMENTAL_RANGE_POSITION",
                    "allowed_evidence_refs": source_refs["fundamental"],
                    "allowed_tactical_choices": [
                        *tactical["valid_candidate_ids"],
                        "UNRESOLVED",
                    ],
                    "prerequisite": "current_price_above_resolved_fundamental_high",
                }
            )
    else:
        if option_resolved and not security_safe:
            excluded_new_buyer.append(
                {
                    "branch": "ATTRACTIVE/ATTRACTIVE_WITHIN_RANGE",
                    "reason": "security_valuation_basis_unresolved",
                }
            )
        elif not option_resolved:
            excluded_new_buyer.append(
                {
                    "branch": "ATTRACTIVE/ATTRACTIVE_WITHIN_RANGE",
                    "reason": "fundamental_option_unresolved",
                }
            )
        else:
            excluded_new_buyer.append(
                {
                    "branch": "ATTRACTIVE/ATTRACTIVE_WITHIN_RANGE",
                    "reason": "current_price_unavailable",
                }
            )
    if not option_resolved:
        new_buyer_branches.append(
            {
                "stance": "WAIT",
                "reason_class": "FUNDAMENTAL_UNRESOLVED",
                "allowed_evidence_refs": source_refs["unresolved"],
                "allowed_tactical_choices": [
                    *tactical["valid_candidate_ids"],
                    "UNRESOLVED",
                ],
                "prerequisite": "fundamental_option_unresolved",
            }
        )
        excluded_new_buyer.append(
            {
                "branch": "WAIT/FUNDAMENTAL_RANGE_POSITION",
                "reason": "fundamental_option_unresolved",
            }
        )
    elif current_value is None or high is None or current_value <= high:
        excluded_new_buyer.append(
            {
                "branch": "WAIT/FUNDAMENTAL_RANGE_POSITION",
                "reason": "current_price_not_above_fundamental_high",
            }
        )
    if tactical["wait_candidate_ids"]:
        new_buyer_branches.append(
            {
                "stance": "WAIT",
                "reason_class": "TACTICAL_TIMING",
                "allowed_evidence_refs": tactical["wait_evidence_refs"],
                "allowed_tactical_choices": tactical["wait_candidate_ids"],
                "prerequisite": "current_price_above_eligible_tactical_high",
            }
        )
    else:
        excluded_new_buyer.append(
            {
                "branch": "WAIT/TACTICAL_TIMING",
                "reason": "eligible_tactical_wait_surface_absent",
            }
        )
    risk_refs = _ordered_unique([*risk_claims, *risk_evidence])
    if risk_refs:
        new_buyer_branches.extend(
            [
                {
                    "stance": "WAIT",
                    "reason_class": "EXECUTION_OR_THESIS_RISK",
                    "allowed_evidence_refs": risk_refs,
                    "allowed_tactical_choices": [
                        *tactical["valid_candidate_ids"],
                        "UNRESOLVED",
                    ],
                    "prerequisite": "material_bearish_business_evidence_available",
                },
                {
                    "stance": "AVOID",
                    "reason_class": "EXECUTION_OR_THESIS_RISK",
                    "allowed_evidence_refs": risk_refs,
                    "allowed_tactical_choices": ["NOT_APPLICABLE"],
                    "prerequisite": "material_bearish_business_evidence_available",
                },
            ]
        )
    else:
        excluded_new_buyer.extend(
            [
                {
                    "branch": "WAIT/EXECUTION_OR_THESIS_RISK",
                    "reason": "material_bearish_business_evidence_absent",
                },
                {
                    "branch": "AVOID/EXECUTION_OR_THESIS_RISK",
                    "reason": "material_bearish_business_evidence_absent",
                },
            ]
        )

    holder_branches: list[dict[str, object]] = [
        {
            "stance": "HOLDABLE",
            "reason_classes": [HolderReasonClass.NOT_APPLICABLE.value],
            "allowed_evidence_refs": [],
            "prerequisite": "always_admissible_baseline",
        }
    ]
    excluded_holder: list[dict[str, str]] = []
    if risk_evidence:
        holder_branches.extend(
            [
                {
                    "stance": "REVIEW",
                    "reason_classes": list(REVIEW_REASON_CLASSES),
                    "allowed_evidence_refs": risk_evidence,
                    "prerequisite": "material_nonvaluation_risk_evidence_available",
                },
                {
                    "stance": "REDUCE",
                    "reason_classes": list(REDUCE_REASON_CLASSES),
                    "allowed_evidence_refs": risk_evidence,
                    "prerequisite": "material_nonvaluation_risk_evidence_available",
                },
            ]
        )
    else:
        excluded_holder.extend(
            [
                {
                    "branch": "REVIEW",
                    "reason": "material_nonvaluation_risk_evidence_absent",
                },
                {
                    "branch": "REDUCE",
                    "reason": "material_nonvaluation_risk_evidence_absent",
                },
            ]
        )

    archetype = str(pass_a.get("archetype") or "")
    protected = archetype in {
        Archetype.DURABLE_FRANCHISE.value,
        Archetype.STRUCTURAL_CYCLICAL_LEADER.value,
    }
    overall_values = ["BUY", "HOLD", "SELL"]
    excluded_overall: list[dict[str, str]] = []
    if protected and not material_claims:
        overall_values = ["BUY"]
        excluded_overall = [
            {
                "branch": direction,
                "reason": "material_business_downgrade_evidence_absent",
            }
            for direction in ("HOLD", "SELL")
        ]

    if not new_buyer_branches:
        raise ValueError("empty_new_buyer_capability_surface")
    return {
        "contract": CAPABILITY_CONTRACT,
        "contract_version": 1,
        "risk_wait_authorization_rule": ("risk_wait_requires_eligible_material_risk_evidence-v2"),
        "ticker": ticker,
        "deterministic_prerequisites": {
            "archetype": archetype,
            "fundamental_status": policy_option.get("status"),
            "fundamental_unresolved_reasons": list(policy_option.get("unresolved_reasons") or ()),
            "current_price": float(current_value) if current_value is not None else None,
            "fundamental_high": float(high) if high is not None else None,
            "security_valuation_basis_state": (
                security.get("state") if isinstance(security, Mapping) else None
            ),
            "security_price_resolution_allowed": security_safe,
        },
        "evidence_classes": {
            "material_business_claim_refs": material_claims,
            "material_risk_claim_refs": risk_claims,
            "material_risk_evidence_refs": risk_evidence,
            "fundamental_position_refs": source_refs["fundamental"],
            "fundamental_unresolved_refs": source_refs["unresolved"],
        },
        "tactical": tactical,
        "overall": {
            "allowed_values": overall_values,
            "excluded_branches": excluded_overall,
        },
        "holder": {
            "branches": holder_branches,
            "excluded_branches": excluded_holder,
        },
        "new_buyer": {
            "branches": new_buyer_branches,
            "excluded_branches": excluded_new_buyer,
        },
        "historical_judgment_inputs_used": [],
        "status": "PASS",
    }


def _holder_schema(capability: Mapping[str, object]) -> dict[str, object]:
    branches: list[dict[str, object]] = []
    for branch in capability["holder"]["branches"]:
        stance = str(branch["stance"])
        refs = list(branch["allowed_evidence_refs"])
        if stance == "HOLDABLE":
            branches.append(
                _strict_object(
                    {
                        "holder": _const(stance),
                        "reason_class": _const(HolderReasonClass.NOT_APPLICABLE.value),
                        "reason": _string(maximum=500),
                        "evidence_refs": _string_array(maximum=0),
                    }
                )
            )
            continue
        branches.append(
            _strict_object(
                {
                    "holder": _const(stance),
                    "reason_class": _enum(branch["reason_classes"]),
                    "reason": _string(maximum=500),
                    "evidence_refs": _string_array(
                        values=refs,
                        minimum=1,
                        maximum=min(6, len(refs)),
                    ),
                }
            )
        )
    return {"anyOf": branches}


def _new_buyer_schema(capability: Mapping[str, object]) -> dict[str, object]:
    branches: list[dict[str, object]] = []
    for branch in capability["new_buyer"]["branches"]:
        stance = str(branch["stance"])
        reason = str(branch["reason_class"])
        refs = list(branch["allowed_evidence_refs"])
        tactical = list(branch["allowed_tactical_choices"])
        common = {
            "new_buyer": _const(stance),
            "reason_class": _const(reason),
            "reason": _string(maximum=500),
            "evidence_refs": _string_array(
                values=refs,
                minimum=1,
                maximum=min(8, len(refs)),
            ),
        }
        if stance == "WAIT":
            common.update(
                {
                    "tactical_choice": _enum(tactical),
                    "re_evaluate_conditions": _string_array(minimum=1, maximum=4),
                }
            )
        else:
            common.update(
                {
                    "tactical_choice": _const("NOT_APPLICABLE"),
                    "re_evaluate_conditions": _string_array(maximum=0),
                }
            )
        branches.append(_strict_object(common))
    return {"anyOf": branches}


def _row_schema(
    *,
    catalog: Mapping[str, object],
    capability: Mapping[str, object],
) -> dict[str, object]:
    claim_refs = list(catalog.get("claim_refs") or ())
    return _strict_object(
        {
            "overall_direction": _enum(capability["overall"]["allowed_values"]),
            "directional_buy_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 10.0,
                "description": (
                    "One directional buy score from 0 through 10. Runtime derives sell as "
                    "the exact complement to 10."
                ),
            },
            "decision_confidence": _enum([item.value for item in Confidence]),
            "decisive_supporting_claim_refs": _string_array(
                values=claim_refs,
                minimum=1,
                maximum=min(6, len(claim_refs)),
            ),
            "decisive_contradicting_claim_refs": _string_array(
                values=claim_refs,
                maximum=min(6, len(claim_refs)),
            ),
            "thesis_state": _enum([item.value for item in ThesisState]),
            "holder_decision": _holder_schema(capability),
            "new_buyer_decision": _new_buyer_schema(capability),
            "policy_summary": _string(maximum=700),
        }
    )


def capability_pass_b_batch_schema(
    *,
    subjects: Sequence[str],
    catalogs: Mapping[str, Mapping[str, object]],
    capabilities: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    decisions = _strict_object(
        {
            ticker: _row_schema(
                catalog=catalogs[ticker],
                capability=capabilities[ticker],
            )
            for ticker in subjects
        }
    )
    schema = _strict_object({"decisions": decisions})
    schema["title"] = CAPABILITY_SCHEMA
    return schema


def _branch(
    capability: Mapping[str, object],
    *,
    axis: str,
    stance: str,
    reason_class: str | None = None,
) -> Mapping[str, object] | None:
    for branch in capability[axis]["branches"]:
        if branch["stance"] != stance:
            continue
        if reason_class is None or (
            branch.get("reason_class") == reason_class
            or reason_class in branch.get("reason_classes", ())
        ):
            return branch
    return None


def validate_capability_selection(
    output: Mapping[str, object],
    *,
    subjects: Sequence[str],
    catalogs: Mapping[str, Mapping[str, object]],
    capabilities: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    shape = validate_future_pass_b_shape(output, subjects=subjects, catalogs=catalogs)
    errors = list(shape["errors"])
    per_ticker: dict[str, list[str]] = {ticker: [] for ticker in subjects}
    rows = output.get("decisions")
    if isinstance(rows, Mapping):
        for ticker in subjects:
            row = rows.get(ticker)
            if not isinstance(row, Mapping):
                continue
            capability = capabilities[ticker]
            row_errors: list[str] = []
            if row.get("overall_direction") not in capability["overall"]["allowed_values"]:
                row_errors.append("PB_CAP_OVERALL_BRANCH_FORBIDDEN")
            holder = row.get("holder_decision")
            if isinstance(holder, Mapping):
                branch = _branch(
                    capability,
                    axis="holder",
                    stance=str(holder.get("holder") or ""),
                    reason_class=str(holder.get("reason_class") or ""),
                )
                if branch is None:
                    row_errors.append("PB_CAP_HOLDER_BRANCH_FORBIDDEN")
                elif not set(holder.get("evidence_refs") or ()).issubset(
                    set(branch["allowed_evidence_refs"])
                ):
                    row_errors.append("PB_CAP_HOLDER_REF_FORBIDDEN")
            new_buyer = row.get("new_buyer_decision")
            if isinstance(new_buyer, Mapping):
                branch = _branch(
                    capability,
                    axis="new_buyer",
                    stance=str(new_buyer.get("new_buyer") or ""),
                    reason_class=str(new_buyer.get("reason_class") or ""),
                )
                if branch is None:
                    row_errors.append("PB_CAP_NEW_BUYER_BRANCH_FORBIDDEN")
                else:
                    if not set(new_buyer.get("evidence_refs") or ()).issubset(
                        set(branch["allowed_evidence_refs"])
                    ):
                        row_errors.append("PB_CAP_NEW_BUYER_REF_FORBIDDEN")
                    if new_buyer.get("tactical_choice") not in set(
                        branch["allowed_tactical_choices"]
                    ):
                        row_errors.append("PB_CAP_TACTICAL_CHOICE_FORBIDDEN")
            per_ticker[ticker] = sorted(set(row_errors))
            errors.extend(f"{ticker}:{error}" for error in row_errors)
    return {
        "contract": CAPABILITY_VALIDATION,
        "base_shape": shape,
        "per_ticker": per_ticker,
        "errors": sorted(set(errors)),
        "error_count": len(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }


def pass_b_capability_validator_parity_matrix() -> dict[str, object]:
    rows = [
        {
            "rule": "attractive_without_permitted_fundamental_position",
            "classification": "CAPABILITY_SCHEMA_ENFORCED",
            "boundary": "resolved option, safe security basis, and current price position",
        },
        {
            "rule": "wait_fundamental_range_requires_resolved_option",
            "classification": "CAPABILITY_SCHEMA_ENFORCED",
            "boundary": "deterministic option and current price position",
        },
        {
            "rule": "wait_fundamental_unresolved_requires_unresolved_option",
            "classification": "CAPABILITY_SCHEMA_ENFORCED",
            "boundary": "deterministic option status",
        },
        {
            "rule": "wait_tactical_requires_eligible_above-band_candidate",
            "classification": "CAPABILITY_SCHEMA_ENFORCED",
            "boundary": "candidate structure, currency, and current price",
        },
        {
            "rule": "wait_or_avoid_risk_requires_material_bearish_evidence",
            "classification": "CAPABILITY_SCHEMA_ENFORCED",
            "boundary": "typed bearish material business evidence",
        },
        {
            "rule": "holder_review_reduce_requires_material_nonvaluation_risk_evidence",
            "classification": "CAPABILITY_SCHEMA_ENFORCED",
            "boundary": "typed claim parent evidence",
        },
        {
            "rule": "durable_or_structural_nonbuy_requires_material_business_evidence",
            "classification": "CAPABILITY_SCHEMA_ENFORCED",
            "boundary": "branch removed only when eligible evidence set is empty",
        },
        {
            "rule": "selected_refs_match_selected_reason_meaning",
            "classification": "MODEL_DEPENDENT_CROSS_REFERENCE",
            "boundary": "model-selected refs remain defense-in-depth validated",
        },
        {
            "rule": "risk_wait_requires_eligible_material_risk_evidence",
            "classification": "MODEL_DEPENDENT_CROSS_REFERENCE",
            "boundary": (
                "selected refs must belong to the subject-local eligible material-risk "
                "branch; Holder and thesis labels are independent"
            ),
        },
        {
            "rule": "entry_range_projection",
            "classification": "DETERMINISTIC_MATERIALIZER",
            "boundary": "runtime-owned price, method, distance, and refs",
        },
    ]
    unresolved = [row for row in rows if row["classification"] == "UNRESOLVED_REQUIRES_CHAT"]
    return {
        "contract": "m12cv-pass-b-capability-validator-parity-matrix-v1",
        "rows": rows,
        "rule_count": len(rows),
        "deterministic_branch_rules_left_as_model_cross_reference": 0,
        "unresolved_requires_chat_count": len(unresolved),
        "status": "PASS" if not unresolved else "FAIL",
    }


def capability_prompt_template() -> str:
    return (
        "Pass B returns strict JSON matching the supplied subject-keyed schema. Do not output "
        "identity or ticker fields. Pass-A classifications, deterministic policy options, and each "
        "subject's PASS_B_CAPABILITY_CATALOG are frozen. Choose only branches and exact refs offered "
        "by that subject's schema; absence means the frozen deterministic policy makes the branch "
        "structurally impossible. Do not repair, reinterpret, or invent a missing branch. Judge "
        "Overall, New Buyer, Holder, one directional_buy_score from 0 through 10, confidence, exact "
        "evidence selections, and bounded Korean prose. Runtime derives sell as 10 minus buy and owns "
        "all entry prices, bands, methods, distances, source metadata, and final materialization. "
        "Security-basis or valuation limitations alone cannot lower Overall or Holder. Valuation or "
        "timing alone cannot create Holder REVIEW or REDUCE. Use one schema branch exactly."
    )
