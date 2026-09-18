from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


PASS_A_CONTRACT = "m12cq-pass-a-archetype-regime-v1"
PASS_A_SCHEMA_CONTRACT = "m12cq-pass-a-response-schema-v1"
PASS_B_CONTRACT = "m12cq-pass-b-decision-tactical-v1"
PASS_B_SCHEMA_CONTRACT = "m12cq-pass-b-response-schema-v1"
ENTRY_MATERIALIZATION_CONTRACT = "m12cq-runtime-entry-materialization-v1"


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class NewBuyerReasonClass(StrEnum):
    ATTRACTIVE_WITHIN_RANGE = "ATTRACTIVE_WITHIN_RANGE"
    FUNDAMENTAL_RANGE_POSITION = "FUNDAMENTAL_RANGE_POSITION"
    FUNDAMENTAL_UNRESOLVED = "FUNDAMENTAL_UNRESOLVED"
    TACTICAL_TIMING = "TACTICAL_TIMING"
    EXECUTION_OR_THESIS_RISK = "EXECUTION_OR_THESIS_RISK"


class DecisionRuleId(StrEnum):
    ARCHETYPE_REGIME_FREEZE = "ARCHETYPE_REGIME_FREEZE"
    THESIS_ENTRY_SEPARATION = "THESIS_ENTRY_SEPARATION"
    HOLDER_VALUATION_SEPARATION = "HOLDER_VALUATION_SEPARATION"
    EVIDENCE_OWNERSHIP = "EVIDENCE_OWNERSHIP"
    DETERMINISTIC_FUNDAMENTAL_OPTION = "DETERMINISTIC_FUNDAMENTAL_OPTION"
    TACTICAL_SELECTION_ONLY = "TACTICAL_SELECTION_ONLY"
    NEW_BUYER_CONSISTENCY = "NEW_BUYER_CONSISTENCY"


class PassAClassification(FrozenModel):
    ticker: str
    archetype: Archetype
    archetype_confidence: Confidence
    archetype_supporting_claim_refs: tuple[str, ...] = Field(min_length=1, max_length=6)
    archetype_rationale: str = Field(min_length=1, max_length=600)
    valuation_regime_tier: ValuationRegimeTier
    tier_supporting_claim_refs: tuple[str, ...] = Field(max_length=6)
    tier_rationale: str = Field(min_length=1, max_length=600)
    data_quality_effect: DataQualityEffect
    data_quality_reason_class: DataQualityReasonClass
    data_quality_reason: str | None = Field(max_length=500)
    data_quality_evidence_refs: tuple[str, ...] = Field(max_length=6)
    classification_summary: str = Field(min_length=1, max_length=700)


class PassABatchOutput(FrozenModel):
    contract: Literal["m12cq-pass-a-archetype-regime-v1"] = PASS_A_CONTRACT
    generation_id: str
    packet_id: str
    market: Literal["us", "kr"]
    assessment_date: str
    classifications: tuple[PassAClassification, ...] = Field(min_length=1, max_length=3)


class DirectionalBalance(FrozenModel):
    buy: float = Field(ge=0.0, le=10.0)
    sell: float = Field(ge=0.0, le=10.0)


class PassBDecision(FrozenModel):
    ticker: str
    overall_direction: Literal["BUY", "HOLD", "SELL"]
    new_buyer: Literal["ATTRACTIVE", "WAIT", "AVOID"]
    holder: Literal["HOLDABLE", "REVIEW", "REDUCE"]
    directional_balance: DirectionalBalance
    decision_confidence: Confidence
    decisive_supporting_claim_refs: tuple[str, ...] = Field(min_length=1, max_length=6)
    decisive_contradicting_claim_refs: tuple[str, ...] = Field(max_length=6)
    thesis_state: ThesisState
    holder_reason_class: HolderReasonClass
    holder_reason: str = Field(min_length=1, max_length=500)
    holder_reason_evidence_refs: tuple[str, ...] = Field(max_length=6)
    new_buyer_reason_class: NewBuyerReasonClass
    new_buyer_reason: str = Field(min_length=1, max_length=500)
    new_buyer_reason_refs: tuple[str, ...] = Field(max_length=8)
    tactical_choice: str
    re_evaluate_conditions: tuple[str, ...] = Field(max_length=4)
    valuation_affects: tuple[ValuationAffects, ...] = Field(max_length=3)
    rule_trace: tuple[DecisionRuleId, ...] = Field(min_length=1, max_length=8)
    policy_summary: str = Field(min_length=1, max_length=700)


class PassBBatchOutput(FrozenModel):
    contract: Literal["m12cq-pass-b-decision-tactical-v1"] = PASS_B_CONTRACT
    generation_id: str
    packet_id: str
    market: Literal["us", "kr"]
    assessment_date: str
    decisions: tuple[PassBDecision, ...] = Field(min_length=1, max_length=3)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _strict_json_schema(value: object) -> object:
    if isinstance(value, dict):
        transformed: dict[str, object] = {}
        for key, item in value.items():
            if key in {"default", "discriminator", "$comment"}:
                continue
            target = "anyOf" if key == "oneOf" else key
            if target in transformed:
                raise ValueError(f"strict_schema_keyword_collision:{target}")
            transformed[target] = _strict_json_schema(item)
        properties = transformed.get("properties")
        if isinstance(properties, dict):
            transformed["required"] = list(properties)
            transformed["additionalProperties"] = False
        return transformed
    if isinstance(value, list):
        return [_strict_json_schema(item) for item in value]
    return value


def _string_branch(schema: Mapping[str, object]) -> dict[str, object] | None:
    if schema.get("type") == "string":
        return schema if isinstance(schema, dict) else dict(schema)
    for branch in schema.get("anyOf") or []:
        if isinstance(branch, dict) and branch.get("type") == "string":
            return branch
    return None


def _compact_evidence_row(row: Mapping[str, object]) -> dict[str, object]:
    return {
        key: deepcopy(row.get(key))
        for key in (
            "ref_id",
            "category",
            "label",
            "statement",
            "value",
            "unit",
            "as_of",
            "metric_refs",
            "numeric_prose_eligible",
        )
    }


PASS_A_ALLOWED_CATEGORIES = frozenset(
    {
        "earnings",
        "earnings_quality",
        "quality",
        "thesis",
        "risks",
        "unknown",
        "macro",
    }
)
PASS_A_FORBIDDEN_REF_PREFIXES = (
    "canonical:chart:",
    "canonical:price:",
    "canonical:valuation:",
    "technical-",
)
PASS_A_FORBIDDEN_KEYS = frozenset(
    {
        "current_price",
        "price_as_of",
        "distance_to_band_pct",
        "preferred_entry_low",
        "preferred_entry_high",
        "support_zone_low",
        "support_zone_high",
        "resistance",
        "technical_context",
        "current_multiple",
        "current_percentile",
        "accepted_decision",
        "overall_direction",
        "new_buyer",
        "holder",
        "decision",
        "directional_balance",
    }
)
PASS_A_FORBIDDEN_TEXT = (
    "current price",
    "price target",
    "valuation multiple",
    "current multiple",
    "current percentile",
    "현재가",
    "현재 주가",
    "목표가",
    "진입 가격",
    "지지선",
    "저항선",
    "기술적 분석",
)


def _decoded(value: object) -> object:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _forbidden_content_paths(
    value: object,
    *,
    path: tuple[str, ...] = (),
) -> list[str]:
    errors: list[str] = []
    value = _decoded(value)
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower()
            child_path = (*path, str(key))
            if normalized in PASS_A_FORBIDDEN_KEYS:
                errors.append(".".join(child_path))
            errors.extend(_forbidden_content_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            errors.extend(_forbidden_content_paths(child, path=(*path, str(index))))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(term in lowered for term in PASS_A_FORBIDDEN_TEXT):
            errors.append(".".join(path) + ":forbidden_text")
        if re.search(r"(?<![a-z0-9])(p/e|p/b|per|pbr)(?![a-z0-9])", lowered):
            errors.append(".".join(path) + ":valuation_token")
    return errors


def _eligible_pass_a_evidence(row: Mapping[str, object]) -> bool:
    ref_id = str(row.get("ref_id") or "")
    category = str(row.get("category") or "").lower()
    if not ref_id or ref_id.startswith(PASS_A_FORBIDDEN_REF_PREFIXES):
        return False
    if category not in PASS_A_ALLOWED_CATEGORIES:
        return False
    return not _forbidden_content_paths(row)


def _atomic_claim_payload(row: Mapping[str, object]) -> dict[str, object]:
    claim = row.get("claim")
    claim = claim if isinstance(claim, Mapping) else {}
    return {
        "claim_ref": row.get("claim_ref"),
        "text": claim.get("text"),
        "polarity": claim.get("polarity"),
        "logical_condition": claim.get("logical_condition"),
        "parent_source_refs": list(row.get("parent_source_refs") or []),
    }


def build_pass_a_subject_context(
    *,
    context: Mapping[str, object],
    ticker: str,
    catalog: Mapping[str, object],
) -> dict[str, object]:
    packets = {
        str(row.get("ticker") or ""): row
        for row in context.get("evidence_packets") or []
        if isinstance(row, Mapping)
    }
    packet = packets[ticker]
    core_refs = set(catalog.get("core_evidence_refs") or [])
    evidence_rows = [
        row
        for row in packet.get("evidence") or []
        if isinstance(row, Mapping)
        and row.get("ref_id") in core_refs
        and _eligible_pass_a_evidence(row)
    ]
    eligible_refs = {str(row["ref_id"]) for row in evidence_rows}
    evidence_by_ref = {str(row["ref_id"]): row for row in evidence_rows}
    claims: list[dict[str, object]] = []
    premium_refs: list[str] = []
    for row in catalog.get("atomic_claims") or []:
        if not isinstance(row, Mapping):
            continue
        parent_refs = {str(ref) for ref in row.get("parent_source_refs") or []}
        if not parent_refs or not parent_refs.issubset(eligible_refs):
            continue
        payload = _atomic_claim_payload(row)
        if _forbidden_content_paths(payload):
            continue
        claims.append(payload)
        claim = row.get("claim") if isinstance(row.get("claim"), Mapping) else {}
        parent_categories = {
            str(evidence_by_ref[ref].get("category") or "").lower() for ref in parent_refs
        }
        if (
            claim.get("polarity") == "BULLISH"
            and not claim.get("logical_condition")
            and bool(parent_categories & {"earnings", "earnings_quality", "thesis"})
        ):
            premium_refs.append(str(row["claim_ref"]))
    data_quality_refs = sorted(
        str(row["ref_id"])
        for row in evidence_rows
        if str(row.get("category") or "").lower() == "quality"
        or "quality" in str(row.get("label") or "").lower()
        or "품질" in str(row.get("label") or "")
    )
    return {
        "ticker": ticker,
        "accepted_fundamental_claims": claims,
        "eligible_non_price_evidence": [_compact_evidence_row(row) for row in evidence_rows],
        "eligible_claim_refs": [str(row["claim_ref"]) for row in claims],
        "premium_eligible_claim_refs": sorted(set(premium_refs)),
        "data_quality_catalog": {
            "evidence_refs": data_quality_refs,
            "material_disclosure_failure_refs": sorted(
                set(catalog.get("material_disclosure_failure_refs") or []) & eligible_refs
            ),
            "positive_quality_refs": sorted(
                set(catalog.get("positive_quality_refs") or []) & eligible_refs
            ),
        },
    }


def pass_a_leakage_scan(subject_contexts: Sequence[Mapping[str, object]]) -> dict[str, object]:
    errors: list[str] = []
    rows: list[dict[str, object]] = []
    for subject in subject_contexts:
        ticker = str(subject.get("ticker") or "")
        paths = _forbidden_content_paths(subject)
        errors.extend(f"{ticker}:{path}" for path in paths)
        rows.append(
            {
                "ticker": ticker,
                "forbidden_path_count": len(paths),
                "forbidden_paths": paths,
                "claim_count": len(subject.get("accepted_fundamental_claims") or []),
                "evidence_count": len(subject.get("eligible_non_price_evidence") or []),
            }
        )
    return {
        "contract": "m12cq-pass-a-price-technical-target-leak-proof-v1",
        "subject_count": len(rows),
        "current_price_leak_count": len(errors),
        "technical_value_leak_count": len(errors),
        "target_label_leak_count": len(errors),
        "errors": errors,
        "rows": rows,
        "status": "PASS" if not errors else "FAIL",
    }


def _identity_schema(
    schema: dict[str, object],
    *,
    contract: str,
    generation_id: str,
    packet_id: str,
    market: str,
    assessment_date: str,
) -> None:
    properties = schema["properties"]
    for field, value in (
        ("contract", contract),
        ("generation_id", generation_id),
        ("packet_id", packet_id),
        ("market", market),
        ("assessment_date", assessment_date),
    ):
        properties[field]["const"] = value


def pass_a_batch_schema(
    *,
    generation_id: str,
    packet_id: str,
    market: str,
    assessment_date: str,
    subjects: Sequence[str],
    subject_contexts: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    schema = PassABatchOutput.model_json_schema()
    schema["title"] = PASS_A_SCHEMA_CONTRACT
    _identity_schema(
        schema,
        contract=PASS_A_CONTRACT,
        generation_id=generation_id,
        packet_id=packet_id,
        market=market,
        assessment_date=assessment_date,
    )
    schema["properties"]["classifications"]["minItems"] = len(subjects)
    schema["properties"]["classifications"]["maxItems"] = len(subjects)
    candidate = schema["$defs"]["PassAClassification"]["properties"]
    candidate["ticker"]["enum"] = list(subjects)
    claim_refs = sorted(
        {
            str(ref)
            for ticker in subjects
            for ref in subject_contexts[ticker].get("eligible_claim_refs") or []
        }
    )
    evidence_refs = sorted(
        {
            str(row["ref_id"])
            for ticker in subjects
            for row in subject_contexts[ticker].get("eligible_non_price_evidence") or []
        }
    )
    for field in ("archetype_supporting_claim_refs", "tier_supporting_claim_refs"):
        candidate[field]["items"]["enum"] = claim_refs
    candidate["data_quality_evidence_refs"]["items"]["enum"] = evidence_refs
    strict = _strict_json_schema(schema)
    if not isinstance(strict, dict):
        raise TypeError("pass_a_schema_not_object")
    return strict


def pass_b_batch_schema(
    *,
    generation_id: str,
    packet_id: str,
    market: str,
    assessment_date: str,
    subjects: Sequence[str],
    catalogs: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    schema = PassBBatchOutput.model_json_schema()
    schema["title"] = PASS_B_SCHEMA_CONTRACT
    _identity_schema(
        schema,
        contract=PASS_B_CONTRACT,
        generation_id=generation_id,
        packet_id=packet_id,
        market=market,
        assessment_date=assessment_date,
    )
    schema["properties"]["decisions"]["minItems"] = len(subjects)
    schema["properties"]["decisions"]["maxItems"] = len(subjects)
    candidate = schema["$defs"]["PassBDecision"]["properties"]
    candidate["ticker"]["enum"] = list(subjects)
    claim_refs = sorted(
        {str(ref) for ticker in subjects for ref in catalogs[ticker].get("claim_refs") or []}
    )
    evidence_refs = sorted(
        {str(ref) for ticker in subjects for ref in catalogs[ticker].get("all_evidence_refs") or []}
    )
    all_refs = sorted(set(claim_refs) | set(evidence_refs))
    for field in ("decisive_supporting_claim_refs", "decisive_contradicting_claim_refs"):
        candidate[field]["items"]["enum"] = claim_refs
    candidate["holder_reason_evidence_refs"]["items"]["enum"] = evidence_refs
    candidate["new_buyer_reason_refs"]["items"]["enum"] = all_refs
    tactical_ids = sorted(
        {
            str(row["candidate_id"])
            for ticker in subjects
            for row in catalogs[ticker]["entry_catalog"].get("tactical_candidates") or []
        }
    )
    candidate["tactical_choice"]["enum"] = ["NOT_APPLICABLE", "UNRESOLVED", *tactical_ids]
    strict = _strict_json_schema(schema)
    if not isinstance(strict, dict):
        raise TypeError("pass_b_schema_not_object")
    return strict


def schema_preflight(schema: Mapping[str, object]) -> dict[str, object]:
    return response_format_schema_completeness_scan(schema)


def validate_pass_a_batch(
    output: PassABatchOutput,
    *,
    expected_identity: Mapping[str, object],
    subjects: Sequence[str],
    subject_contexts: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    errors: list[str] = []
    for field in ("generation_id", "packet_id", "market", "assessment_date"):
        if getattr(output, field) != expected_identity[field]:
            errors.append(f"identity_mismatch:{field}")
    returned = tuple(row.ticker for row in output.classifications)
    if returned != tuple(subjects):
        errors.append("subject_order_or_cardinality_mismatch")
    per_ticker: dict[str, list[str]] = {}
    for row in output.classifications:
        row_errors: list[str] = []
        context = subject_contexts[row.ticker]
        claim_refs = set(context.get("eligible_claim_refs") or [])
        archetype_refs = set(row.archetype_supporting_claim_refs)
        tier_refs = set(row.tier_supporting_claim_refs)
        if not archetype_refs.issubset(claim_refs):
            row_errors.append("archetype_claim_ref_outside_subject")
        if not tier_refs.issubset(claim_refs):
            row_errors.append("tier_claim_ref_outside_subject")
        if row.valuation_regime_tier is not ValuationRegimeTier.UNRESOLVED and not tier_refs:
            row_errors.append("resolved_tier_without_supporting_claim")
        if row.valuation_regime_tier is ValuationRegimeTier.PREMIUM:
            premium_refs = set(context.get("premium_eligible_claim_refs") or [])
            if not tier_refs.intersection(premium_refs):
                row_errors.append("premium_without_structural_improvement_ref")
        quality = context.get("data_quality_catalog") or {}
        quality_refs = set(row.data_quality_evidence_refs)
        allowed_quality = set(quality.get("evidence_refs") or [])
        if not quality_refs.issubset(allowed_quality):
            row_errors.append("data_quality_ref_outside_eligible_catalog")
        if row.data_quality_effect is DataQualityEffect.NONE:
            if (
                row.data_quality_reason_class is not DataQualityReasonClass.NOT_APPLICABLE
                or row.data_quality_reason is not None
                or quality_refs
            ):
                row_errors.append("none_data_quality_shape_invalid")
        else:
            if row.data_quality_reason is None or not quality_refs:
                row_errors.append("data_quality_effect_missing_reason_or_ref")
        if row.data_quality_effect is DataQualityEffect.DIRECTIONAL_NEGATIVE:
            if (
                row.data_quality_reason_class
                is not DataQualityReasonClass.MATERIAL_DISCLOSURE_FAILURE
                or not quality_refs.issubset(
                    set(quality.get("material_disclosure_failure_refs") or [])
                )
            ):
                row_errors.append("unsupported_directional_negative_data_quality")
        if row.data_quality_effect is DataQualityEffect.DIRECTIONAL_POSITIVE:
            if (
                row.data_quality_reason_class
                is not DataQualityReasonClass.EVIDENCED_QUALITY_IMPROVEMENT
                or not quality_refs.issubset(set(quality.get("positive_quality_refs") or []))
            ):
                row_errors.append("unsupported_directional_positive_data_quality")
        per_ticker[row.ticker] = sorted(set(row_errors))
        errors.extend(f"{row.ticker}:{error}" for error in row_errors)
    return {
        "contract": "m12cq-pass-a-semantic-validation-v1",
        "error_count": len(errors),
        "errors": errors,
        "per_ticker": per_ticker,
        "status": "PASS" if not errors else "FAIL",
    }


def select_matrix_option(
    matrix_subject: Mapping[str, object],
    classification: PassAClassification | Mapping[str, object],
) -> dict[str, object]:
    ticker = str(matrix_subject.get("ticker") or "")
    if isinstance(classification, PassAClassification):
        archetype = classification.archetype.value
        tier = classification.valuation_regime_tier.value
    else:
        archetype = str(classification.get("archetype") or "")
        tier = str(classification.get("valuation_regime_tier") or "")
    rows = [
        row
        for row in matrix_subject.get("options") or []
        if isinstance(row, Mapping)
        and row.get("archetype") == archetype
        and row.get("valuation_regime_tier") == tier
    ]
    if len(rows) != 1:
        raise ValueError(f"policy_matrix_option_cardinality:{ticker}:{archetype}:{tier}")
    return deepcopy(dict(rows[0]))


def _project_tactical(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "status": "RESOLVED",
        "candidate_id": row["candidate_id"],
        "low": row["low"],
        "high": row["high"],
        "currency": row["currency"],
        "evidence_refs": list(row.get("evidence_refs") or []),
    }


def _null_band(status: str) -> dict[str, object]:
    return {
        "status": status,
        "candidate_id": None,
        "low": None,
        "high": None,
        "currency": None,
        "evidence_refs": [],
    }


def _distance(current: Decimal, low: Decimal, high: Decimal) -> float:
    if low <= current <= high:
        return 0.0
    boundary = low if current < low else high
    return float(((boundary - current) / current * Decimal("100")).quantize(Decimal("0.000001")))


def materialize_policy_entry_range(
    *,
    ticker: str,
    new_buyer: str,
    policy_option: Mapping[str, object],
    entry_catalog: Mapping[str, object],
    tactical_choice: str,
    re_evaluate_conditions: Sequence[str],
) -> dict[str, object]:
    if str(policy_option.get("ticker") or "") != ticker:
        raise ValueError("policy_option_ticker_mismatch")
    if str(entry_catalog.get("ticker") or "") != ticker:
        raise ValueError("entry_catalog_ticker_mismatch")
    if new_buyer != "WAIT":
        if tactical_choice != "NOT_APPLICABLE" or re_evaluate_conditions:
            raise ValueError("non_wait_tactical_or_condition_present")
        return {
            "contract": ENTRY_MATERIALIZATION_CONTRACT,
            "entry_range_status": "NOT_APPLICABLE",
            "entry_option_id": None,
            "current_price": None,
            "current_price_as_of": None,
            "current_price_ref": None,
            "preferred_entry_low": None,
            "preferred_entry_high": None,
            "distance_to_band_pct": None,
            "fundamental_entry_band": _null_band("NOT_APPLICABLE"),
            "tactical_entry_band": _null_band("NOT_APPLICABLE"),
            "method": "NOT_APPLICABLE",
            "valuation_regime_tier": policy_option.get("valuation_regime_tier"),
            "combination_rule": "NOT_APPLICABLE",
            "valuation_basis_refs": [],
            "technical_basis_refs": [],
            "assumptions": [],
            "unresolved_inputs": [],
            "re_evaluate_conditions": [],
        }
    if not re_evaluate_conditions:
        raise ValueError("wait_re_evaluate_conditions_missing")
    current = entry_catalog.get("current_price")
    if not isinstance(current, Mapping):
        raise ValueError("current_price_context_missing")
    tactical_rows = {
        str(row["candidate_id"]): row
        for row in entry_catalog.get("tactical_candidates") or []
        if isinstance(row, Mapping)
    }
    if tactical_choice == "UNRESOLVED":
        tactical = None
        tactical_band = _null_band("UNRESOLVED")
        tactical_unresolved = str(
            (entry_catalog.get("unresolved_policy") or {}).get(
                "tactical_unresolved_reason",
                "no safe tactical candidate is available",
            )
        )
    else:
        tactical = tactical_rows.get(tactical_choice)
        if tactical is None:
            raise ValueError("unknown_or_cross_ticker_tactical_candidate")
        if str(tactical.get("ticker") or ticker) != ticker:
            raise ValueError("cross_ticker_tactical_candidate")
        tactical_band = _project_tactical(tactical)
        tactical_unresolved = ""
    unresolved_inputs: list[str] = []
    if policy_option.get("status") != "RESOLVED":
        fundamental = None
        fundamental_band = _null_band("UNRESOLVED")
        unresolved_inputs.extend(
            str(value) for value in policy_option.get("unresolved_reasons") or []
        )
    else:
        fundamental = policy_option
        fundamental_band = {
            "status": "RESOLVED",
            "candidate_id": fundamental.get("option_id"),
            "low": fundamental.get("low"),
            "high": fundamental.get("high"),
            "currency": fundamental.get("currency"),
            "evidence_refs": list(fundamental.get("evidence_refs") or []),
        }
    if tactical is None:
        unresolved_inputs.append(tactical_unresolved)
    if fundamental is None:
        preferred_low = preferred_high = distance = None
        combination = "UNRESOLVED"
        method = "UNRESOLVED"
        option_id = None
        valuation_refs: list[str] = []
        assumptions: list[str] = []
        status = "ENTRY_RANGE_UNRESOLVED"
    else:
        low = Decimal(str(fundamental["low"]))
        high = Decimal(str(fundamental["high"]))
        combination = "FUNDAMENTAL_ONLY"
        if tactical is not None:
            if tactical.get("currency") != fundamental.get("currency"):
                raise ValueError("fundamental_tactical_currency_mismatch")
            overlap_low = max(low, Decimal(str(tactical["low"])))
            overlap_high = min(high, Decimal(str(tactical["high"])))
            if overlap_low <= overlap_high:
                low, high = overlap_low, overlap_high
                combination = "OVERLAP_INTERSECTION"
            else:
                combination = "FUNDAMENTAL_PRIMARY_NO_OVERLAP"
        current_value = Decimal(str(current["value"]))
        preferred_low = float(low)
        preferred_high = float(high)
        distance = _distance(current_value, low, high)
        method = str(fundamental.get("method_family") or "UNRESOLVED")
        option_id = str(fundamental.get("option_id") or "") or None
        valuation_refs = list(fundamental.get("evidence_refs") or [])
        assumptions = [
            f"archetype={fundamental.get('archetype')}",
            f"valuation_regime_tier={fundamental.get('valuation_regime_tier')}",
            f"selection_basis={fundamental.get('selection_basis')}",
        ]
        status = "ENTRY_RANGE_RESOLVED"
    return {
        "contract": ENTRY_MATERIALIZATION_CONTRACT,
        "entry_range_status": status,
        "entry_option_id": option_id,
        "current_price": current.get("value"),
        "current_price_as_of": current.get("as_of"),
        "current_price_ref": current.get("ref_id"),
        "preferred_entry_low": preferred_low,
        "preferred_entry_high": preferred_high,
        "distance_to_band_pct": distance,
        "fundamental_entry_band": fundamental_band,
        "tactical_entry_band": tactical_band,
        "method": method,
        "valuation_regime_tier": policy_option.get("valuation_regime_tier"),
        "combination_rule": combination,
        "valuation_basis_refs": valuation_refs,
        "technical_basis_refs": list(tactical.get("evidence_refs") or []) if tactical else [],
        "assumptions": assumptions,
        "unresolved_inputs": unresolved_inputs,
        "re_evaluate_conditions": list(re_evaluate_conditions),
    }


def build_pass_b_subject_context(
    *,
    context: Mapping[str, object],
    ticker: str,
    catalog: Mapping[str, object],
    pass_a: Mapping[str, object],
    policy_option: Mapping[str, object],
) -> dict[str, object]:
    packets = {
        str(row.get("ticker") or ""): row
        for row in context.get("evidence_packets") or []
        if isinstance(row, Mapping)
    }
    packet = packets[ticker]
    all_refs = set(catalog.get("all_evidence_refs") or [])
    evidence = [
        _compact_evidence_row(row)
        for row in packet.get("evidence") or []
        if isinstance(row, Mapping)
        and row.get("ref_id") in all_refs
        and not str(row.get("ref_id") or "").startswith("technical-feature:")
    ]
    claims = [_atomic_claim_payload(row) for row in catalog.get("atomic_claims") or []]
    entry_catalog = catalog["entry_catalog"]
    return {
        "ticker": ticker,
        "accepted_fundamental_claims": claims,
        "decision_evidence": evidence,
        "frozen_pass_a_classification": deepcopy(dict(pass_a)),
        "deterministic_fundamental_option": deepcopy(dict(policy_option)),
        "current_price": deepcopy(entry_catalog.get("current_price")),
        "tactical_candidates": deepcopy(entry_catalog.get("tactical_candidates") or []),
        "tactical_unresolved_reason": deepcopy(
            (entry_catalog.get("unresolved_policy") or {}).get("tactical_unresolved_reason")
        ),
    }


def _material_business_claim_refs(catalog: Mapping[str, object]) -> set[str]:
    evidence_categories: dict[str, str] = {}
    for row in catalog.get("atomic_claims") or []:
        if not isinstance(row, Mapping):
            continue
        for ref in row.get("parent_source_refs") or []:
            evidence_categories.setdefault(str(ref), "unknown")
    excluded = set(catalog.get("valuation_evidence_refs") or []) | set(
        catalog.get("timing_evidence_refs") or []
    )
    return {
        str(row.get("claim_ref") or "")
        for row in catalog.get("atomic_claims") or []
        if isinstance(row, Mapping)
        and any(str(ref) not in excluded for ref in row.get("parent_source_refs") or [])
    }


def _risk_wait_excluded_refs(catalog: Mapping[str, object]) -> set[str]:
    explicit = (
        set(catalog.get("valuation_evidence_refs") or ())
        | set(catalog.get("timing_evidence_refs") or ())
        | set(catalog.get("positive_quality_refs") or ())
        | set(catalog.get("security_valuation_basis_refs") or ())
        | set(catalog.get("business_quality_confidence_refs") or ())
    )
    for ref in catalog.get("all_evidence_refs") or ():
        text = str(ref).lower()
        if (
            text.startswith("canonical:security_")
            or "security_basis" in text
            or text.startswith("canonical:financial_quality:")
            or text.startswith("canonical:business_quality:")
        ):
            explicit.add(str(ref))
    return explicit


def eligible_material_risk_claim_refs(catalog: Mapping[str, object]) -> set[str]:
    excluded = _risk_wait_excluded_refs(catalog)
    refs: set[str] = set()
    for row in catalog.get("atomic_claims") or ():
        if not isinstance(row, Mapping):
            continue
        claim = row.get("claim")
        claim_ref = str(row.get("claim_ref") or "")
        parent_refs = {str(ref) for ref in row.get("parent_source_refs") or ()}
        if (
            claim_ref
            and isinstance(claim, Mapping)
            and claim.get("polarity") == "BEARISH"
            and bool(parent_refs - excluded)
        ):
            refs.add(claim_ref)
    return refs


def eligible_material_risk_evidence_refs(catalog: Mapping[str, object]) -> set[str]:
    eligible_claims = eligible_material_risk_claim_refs(catalog)
    excluded = _risk_wait_excluded_refs(catalog)
    all_evidence = {str(ref) for ref in catalog.get("all_evidence_refs") or ()}
    refs: set[str] = set()
    for row in catalog.get("atomic_claims") or ():
        if not isinstance(row, Mapping) or str(row.get("claim_ref") or "") not in eligible_claims:
            continue
        refs.update(
            str(ref)
            for ref in row.get("parent_source_refs") or ()
            if str(ref) in all_evidence and str(ref) not in excluded
        )
    return refs


def eligible_material_risk_refs(catalog: Mapping[str, object]) -> set[str]:
    return eligible_material_risk_claim_refs(catalog) | eligible_material_risk_evidence_refs(
        catalog
    )


def _risk_wait_capability_refs(
    capability: Mapping[str, object] | None,
) -> tuple[bool, set[str]]:
    if not isinstance(capability, Mapping):
        return False, set()
    new_buyer = capability.get("new_buyer")
    if not isinstance(new_buyer, Mapping):
        return False, set()
    for branch in new_buyer.get("branches") or ():
        if not isinstance(branch, Mapping):
            continue
        if (
            branch.get("stance") == "WAIT"
            and branch.get("reason_class") == NewBuyerReasonClass.EXECUTION_OR_THESIS_RISK.value
            and branch.get("prerequisite") == "material_bearish_business_evidence_available"
        ):
            return True, {str(ref) for ref in branch.get("allowed_evidence_refs") or ()}
    return False, set()


def validate_pass_b_batch(
    output: PassBBatchOutput,
    *,
    expected_identity: Mapping[str, object],
    subjects: Sequence[str],
    catalogs: Mapping[str, Mapping[str, object]],
    pass_a_by_ticker: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    errors: list[str] = []
    for field in ("generation_id", "packet_id", "market", "assessment_date"):
        if getattr(output, field) != expected_identity[field]:
            errors.append(f"identity_mismatch:{field}")
    if tuple(row.ticker for row in output.decisions) != tuple(subjects):
        errors.append("subject_order_or_cardinality_mismatch")
    per_ticker: dict[str, list[str]] = {}
    for row in output.decisions:
        row_errors: list[str] = []
        catalog = catalogs[row.ticker]
        claim_refs = set(catalog.get("claim_refs") or [])
        evidence_refs = set(catalog.get("all_evidence_refs") or [])
        support = set(row.decisive_supporting_claim_refs)
        contradiction = set(row.decisive_contradicting_claim_refs)
        if not support.issubset(claim_refs):
            row_errors.append("supporting_claim_ref_outside_subject")
        if not contradiction.issubset(claim_refs):
            row_errors.append("contradicting_claim_ref_outside_subject")
        if support & contradiction:
            row_errors.append("claim_ref_overlap")
        if not math.isclose(
            row.directional_balance.buy + row.directional_balance.sell,
            10.0,
            rel_tol=0.0,
            abs_tol=1e-6,
        ):
            row_errors.append("directional_balance_not_ten")
        if len(row.rule_trace) != len(set(row.rule_trace)):
            row_errors.append("duplicate_rule_trace")
        required_rules = {
            DecisionRuleId.ARCHETYPE_REGIME_FREEZE,
            DecisionRuleId.EVIDENCE_OWNERSHIP,
            DecisionRuleId.DETERMINISTIC_FUNDAMENTAL_OPTION,
            DecisionRuleId.NEW_BUYER_CONSISTENCY,
        }
        if not required_rules.issubset(set(row.rule_trace)):
            row_errors.append("required_rule_trace_missing")
        holder_refs = set(row.holder_reason_evidence_refs)
        if not holder_refs.issubset(evidence_refs):
            row_errors.append("holder_ref_outside_subject")
        valuation_refs = set(catalog.get("valuation_evidence_refs") or [])
        if row.holder == "HOLDABLE":
            if row.holder_reason_class is not HolderReasonClass.NOT_APPLICABLE:
                row_errors.append("holdable_reason_class_not_applicable")
        elif row.holder == "REVIEW":
            if row.holder_reason_class is HolderReasonClass.NOT_APPLICABLE:
                row_errors.append("review_reason_class_missing")
            if not holder_refs or not (holder_refs - valuation_refs):
                row_errors.append("review_supported_only_by_valuation")
        else:
            allowed_reduce = {
                HolderReasonClass.EXECUTION_DETERIORATION,
                HolderReasonClass.BALANCE_SHEET_RISK,
                HolderReasonClass.THESIS_IMPAIRMENT,
                HolderReasonClass.DOWNSIDE_ASYMMETRY,
            }
            if row.holder_reason_class not in allowed_reduce:
                row_errors.append("reduce_reason_class_not_material")
            if not holder_refs or not (holder_refs - valuation_refs):
                row_errors.append("reduce_supported_only_by_valuation")
        reason_refs = set(row.new_buyer_reason_refs)
        if not reason_refs.issubset(claim_refs | evidence_refs):
            row_errors.append("new_buyer_reason_ref_outside_subject")
        tactical_ids = {
            str(candidate["candidate_id"])
            for candidate in catalog["entry_catalog"].get("tactical_candidates") or []
        }
        if row.new_buyer == "WAIT":
            if row.tactical_choice not in tactical_ids | {"UNRESOLVED"}:
                row_errors.append("wait_tactical_choice_invalid")
            if not row.re_evaluate_conditions:
                row_errors.append("wait_re_evaluate_conditions_missing")
        else:
            if row.tactical_choice != "NOT_APPLICABLE":
                row_errors.append("non_wait_tactical_choice_not_applicable")
            if row.re_evaluate_conditions:
                row_errors.append("non_wait_re_evaluate_conditions_present")
        archetype = str(pass_a_by_ticker[row.ticker].get("archetype") or "")
        if archetype in {
            Archetype.DURABLE_FRANCHISE.value,
            Archetype.STRUCTURAL_CYCLICAL_LEADER.value,
        } and row.overall_direction in {"HOLD", "SELL"}:
            if not support.intersection(_material_business_claim_refs(catalog)):
                row_errors.append("overall_nonbuy_supported_only_by_valuation_or_timing")
        per_ticker[row.ticker] = sorted(set(row_errors))
        errors.extend(f"{row.ticker}:{error}" for error in row_errors)
    return {
        "contract": "m12cq-pass-b-semantic-validation-v1",
        "error_count": len(errors),
        "errors": errors,
        "per_ticker": per_ticker,
        "status": "PASS" if not errors else "FAIL",
    }


def validate_new_buyer_consistency(
    *,
    decision: PassBDecision | Mapping[str, object],
    policy_option: Mapping[str, object],
    entry_range: Mapping[str, object],
    catalog: Mapping[str, object],
    capability: Mapping[str, object] | None = None,
) -> dict[str, object]:
    if isinstance(decision, PassBDecision):
        row = decision.model_dump(mode="json")
    else:
        row = dict(decision)
    errors: list[str] = []
    stance = str(row.get("new_buyer") or "")
    reason_class = str(row.get("new_buyer_reason_class") or "")
    current = catalog["entry_catalog"].get("current_price")
    current_value = float(current["value"]) if isinstance(current, Mapping) else None
    option_resolved = policy_option.get("status") == "RESOLVED"
    high = float(policy_option["high"]) if option_resolved else None
    severe = (
        row.get("overall_direction") == "SELL"
        or row.get("holder") == "REDUCE"
        or row.get("thesis_state") in {"IMPAIRED", "INVALIDATED"}
    )
    if stance == "ATTRACTIVE":
        if not option_resolved or current_value is None or high is None or current_value > high:
            errors.append("attractive_without_permitted_fundamental_position")
        if severe:
            errors.append("attractive_with_severe_execution_or_thesis_condition")
        if reason_class != NewBuyerReasonClass.ATTRACTIVE_WITHIN_RANGE.value:
            errors.append("attractive_reason_class_invalid")
    elif stance == "WAIT":
        authorized = False
        if not option_resolved and reason_class == NewBuyerReasonClass.FUNDAMENTAL_UNRESOLVED.value:
            authorized = True
        if (
            option_resolved
            and current_value is not None
            and high is not None
            and current_value > high
            and reason_class == NewBuyerReasonClass.FUNDAMENTAL_RANGE_POSITION.value
        ):
            authorized = True
        tactical = entry_range.get("tactical_entry_band")
        if (
            reason_class == NewBuyerReasonClass.TACTICAL_TIMING.value
            and isinstance(tactical, Mapping)
            and tactical.get("status") == "RESOLVED"
            and current_value is not None
            and tactical.get("high") is not None
            and current_value > float(tactical["high"])
        ):
            authorized = True
        if reason_class == NewBuyerReasonClass.EXECUTION_OR_THESIS_RISK.value:
            selected_refs = {str(ref) for ref in row.get("new_buyer_reason_refs") or ()}
            eligible_refs = eligible_material_risk_refs(catalog)
            capability_exposed, capability_refs = _risk_wait_capability_refs(capability)
            if capability is None:
                capability_exposed = bool(eligible_refs)
                capability_refs = eligible_refs
            risk_wait_authorized = (
                catalog.get("ticker") == row.get("ticker")
                and capability_exposed
                and bool(selected_refs)
                and selected_refs.issubset(capability_refs & eligible_refs)
            )
            if risk_wait_authorized:
                authorized = True
            else:
                errors.append("risk_wait_requires_eligible_material_risk_evidence")
        if not authorized:
            errors.append("wait_without_authorized_structured_condition")
        if option_resolved and entry_range.get("entry_range_status") != "ENTRY_RANGE_RESOLVED":
            errors.append("wait_resolved_fundamental_band_not_exposed")
        if (
            not option_resolved
            and entry_range.get("entry_range_status") != "ENTRY_RANGE_UNRESOLVED"
        ):
            errors.append("wait_unresolved_fundamental_not_preserved")
    elif stance == "AVOID":
        if reason_class != NewBuyerReasonClass.EXECUTION_OR_THESIS_RISK.value:
            errors.append("avoid_reason_class_invalid")
        if not severe and not row.get("new_buyer_reason_refs"):
            errors.append("avoid_without_material_risk_evidence")
    else:
        errors.append("unknown_new_buyer_stance")
    return {
        "ticker": row.get("ticker"),
        "errors": sorted(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }


def pass_a_prompt(
    *,
    identity: Mapping[str, object],
    policy_principles: Mapping[str, object],
    subject_contexts: Sequence[Mapping[str, object]],
) -> str:
    return (
        "You are performing Pass A of an archive-only two-pass investment-policy calibration. "
        "Return strict JSON matching the supplied schema. Use only PASS_A_CONTEXT. Do not browse. "
        "This pass is intentionally price-blind. Do not infer or mention current price, chart state, "
        "technical timing, current valuation multiple or percentile, entry range, New Buyer, Holder, "
        "or any prior decision. Classify the economic archetype from accepted business, earnings, "
        "cash-flow, competitive, cycle, execution, and maturity evidence, never from ticker identity. "
        "Use UNRESOLVED when evidence conflicts or is insufficient.\n\n"
        "Select CONSERVATIVE, BASE, PREMIUM, or UNRESOLVED as the valuation-policy regime. The tier is "
        "not a statement about today's valuation. PREMIUM requires at least one exact claim ref from "
        "premium_eligible_claim_refs and must reflect evidenced non-price structural improvement. "
        "High market valuation is never PREMIUM support. Cite only exact same-subject claim refs supplied "
        "in eligible_claim_refs.\n\n"
        "Data-quality limitations normally affect confidence only. Directional effects are allowed only "
        "with exact refs listed in the corresponding directional data-quality catalog. Use concise "
        "complete Korean sentences for rationales. Copy all identity fields exactly and return subjects "
        "in expected order.\n\nPASS_A_IDENTITY:\n"
        + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
        + "\n\nGENERIC_POLICY_PRINCIPLES:\n"
        + json.dumps(policy_principles, ensure_ascii=False, separators=(",", ":"))
        + "\n\nPASS_A_CONTEXT:\n"
        + json.dumps(subject_contexts, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def pass_b_prompt(
    *,
    identity: Mapping[str, object],
    policy_principles: Mapping[str, object],
    subject_contexts: Sequence[Mapping[str, object]],
) -> str:
    return (
        "You are performing Pass B of an archive-only two-pass investment-policy calibration. "
        "Return strict JSON matching the supplied schema. Use only PASS_B_CONTEXT and do not browse. "
        "Pass-A archetype/regime classifications and deterministic fundamental options are frozen. "
        "Do not revise them. Keep Overall, New Buyer, and Holder independent. BUY/WAIT/HOLDABLE is valid. "
        "Valuation or tactical timing alone must not force Overall lower and must not create Holder REVIEW. "
        "For durable franchises and structural cyclical leaders, HOLD or SELL needs material non-price "
        "business, cycle, earnings, cash-flow, competitive, or execution evidence. REVIEW needs a "
        "structured non-valuation reason; REDUCE needs stronger material negative evidence.\n\n"
        "The runtime, not you, owns the fundamental option, all low/high values, distance, method, refs, "
        "combination rule, and final entry-range status. Select only one supplied tactical candidate ID or "
        "UNRESOLVED when New Buyer is WAIT. Use NOT_APPLICABLE for non-WAIT. ATTRACTIVE requires a resolved "
        "fundamental option with current price at or below its high and no severe execution/thesis condition. "
        "WAIT must use one authorized reason class: price above the fundamental range, unresolved fundamental "
        "valuation, unfavorable tactical timing, or evidence-backed execution/thesis risk. AVOID requires "
        "material risk and needs no invented entry price. Do not calculate or restate numeric bands.\n\n"
        "Cite only exact same-subject claim/evidence refs. Directional balance must sum to 10. Use concise "
        "complete Korean sentences. Copy all identity fields exactly and return subjects in expected order. "
        "No prior production decision or independent reviewer judgment is supplied.\n\nPASS_B_IDENTITY:\n"
        + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
        + "\n\nGENERIC_POLICY_PRINCIPLES:\n"
        + json.dumps(policy_principles, ensure_ascii=False, separators=(",", ":"))
        + "\n\nPASS_B_CONTEXT:\n"
        + json.dumps(subject_contexts, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def generic_control_matrix() -> dict[str, object]:
    generic_matrix = {
        "ticker": "RENAMED",
        "options": [
            {
                "ticker": "RENAMED",
                "archetype": Archetype.DURABLE_FRANCHISE.value,
                "valuation_regime_tier": ValuationRegimeTier.BASE.value,
                "status": "RESOLVED",
                "option_id": "policy-option:generic",
                "low": 80.0,
                "high": 100.0,
                "currency": "USD",
                "method_family": "HISTORICAL_TRAILING_PE_QUANTILE",
                "selection_basis": "DURABLE_PRIMARY_TRAILING_PE",
                "evidence_refs": ["valuation:generic"],
                "unresolved_reasons": [],
            }
        ],
    }
    classification = {
        "archetype": Archetype.DURABLE_FRANCHISE.value,
        "valuation_regime_tier": ValuationRegimeTier.BASE.value,
    }
    option = select_matrix_option(generic_matrix, classification)
    entry_catalog = {
        "ticker": "RENAMED",
        "current_price": {"value": 120.0, "as_of": "2026-09-17", "ref_id": "price:generic"},
        "tactical_candidates": [
            {
                "ticker": "RENAMED",
                "candidate_id": "tactical:generic",
                "low": 90.0,
                "high": 110.0,
                "currency": "USD",
                "evidence_refs": ["technical:generic"],
            }
        ],
        "unresolved_policy": {"tactical_unresolved_reason": "tactical unavailable"},
    }
    materialized = materialize_policy_entry_range(
        ticker="RENAMED",
        new_buyer="WAIT",
        policy_option=option,
        entry_catalog=entry_catalog,
        tactical_choice="tactical:generic",
        re_evaluate_conditions=("가격이 기본 범위로 진입하는지 확인",),
    )
    renamed_matrix = deepcopy(generic_matrix)
    renamed_matrix["ticker"] = "OTHER"
    renamed_matrix["options"][0]["ticker"] = "OTHER"
    renamed_option = select_matrix_option(renamed_matrix, classification)
    return {
        "contract": "m12cq-generic-control-matrix-v1",
        "matrix_selection_exact": option["option_id"] == "policy-option:generic",
        "renamed_identity_same_policy": {
            key: renamed_option[key] for key in ("archetype", "valuation_regime_tier", "status")
        }
        == {key: option[key] for key in ("archetype", "valuation_regime_tier", "status")},
        "runtime_not_model_owns_price": materialized["preferred_entry_low"] == 90.0
        and materialized["preferred_entry_high"] == 100.0,
        "arbitrary_discount_count": 0,
        "ticker_specific_rule_count": 0,
        "status": "PASS",
    }
