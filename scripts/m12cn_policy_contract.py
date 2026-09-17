from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CONTRACT = "m12cn-investment-policy-shadow-v1"


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CompanyArchetype(StrEnum):
    DURABLE_FRANCHISE = "DURABLE_FRANCHISE"
    STRUCTURAL_CYCLICAL_LEADER = "STRUCTURAL_CYCLICAL_LEADER"
    PROFITABLE_PREMIUM_GROWTH = "PROFITABLE_PREMIUM_GROWTH"
    EXECUTION_DEPENDENT_GROWTH = "EXECUTION_DEPENDENT_GROWTH"
    MATURE_VALUE_DEFENSIVE = "MATURE_VALUE_DEFENSIVE"
    UNRESOLVED = "UNRESOLVED"


class Confidence(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ThesisState(StrEnum):
    STRENGTHENING = "STRENGTHENING"
    INTACT = "INTACT"
    MIXED = "MIXED"
    IMPAIRED = "IMPAIRED"
    INVALIDATED = "INVALIDATED"
    UNRESOLVED = "UNRESOLVED"


class DataQualityEffect(StrEnum):
    CONFIDENCE_ONLY = "CONFIDENCE_ONLY"
    DIRECTIONAL_NEGATIVE = "DIRECTIONAL_NEGATIVE"
    DIRECTIONAL_POSITIVE = "DIRECTIONAL_POSITIVE"
    NONE = "NONE"


class DataQualityReasonClass(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PROVIDER_LIMITATION = "PROVIDER_LIMITATION"
    STALE_OR_UNSUPPORTED = "STALE_OR_UNSUPPORTED"
    MATERIAL_DISCLOSURE_FAILURE = "MATERIAL_DISCLOSURE_FAILURE"
    EVIDENCED_QUALITY_IMPROVEMENT = "EVIDENCED_QUALITY_IMPROVEMENT"


class HolderReasonClass(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    THESIS_UNCERTAINTY = "THESIS_UNCERTAINTY"
    EVIDENCE_CONTRADICTION = "EVIDENCE_CONTRADICTION"
    EXECUTION_DETERIORATION = "EXECUTION_DETERIORATION"
    BALANCE_SHEET_RISK = "BALANCE_SHEET_RISK"
    OWNERSHIP_RELEVANT_UNRESOLVED_RISK = "OWNERSHIP_RELEVANT_UNRESOLVED_RISK"
    THESIS_IMPAIRMENT = "THESIS_IMPAIRMENT"
    DOWNSIDE_ASYMMETRY = "DOWNSIDE_ASYMMETRY"


class EntryRangeStatus(StrEnum):
    ENTRY_RANGE_RESOLVED = "ENTRY_RANGE_RESOLVED"
    ENTRY_RANGE_UNRESOLVED = "ENTRY_RANGE_UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EntryBandStatus(StrEnum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EntryMethod(StrEnum):
    FORWARD_EARNINGS_MULTIPLE = "FORWARD_EARNINGS_MULTIPLE"
    NORMALIZED_CYCLE_EARNINGS = "NORMALIZED_CYCLE_EARNINGS"
    FCF_YIELD_OR_MULTIPLE = "FCF_YIELD_OR_MULTIPLE"
    EV_EBITDA = "EV_EBITDA"
    EV_SALES_SCENARIO = "EV_SALES_SCENARIO"
    EV_GROSS_PROFIT_SCENARIO = "EV_GROSS_PROFIT_SCENARIO"
    SOTP_EXISTING_EVIDENCE = "SOTP_EXISTING_EVIDENCE"
    BOOK_VALUE_MULTIPLE = "BOOK_VALUE_MULTIPLE"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CombinationRule(StrEnum):
    OVERLAP_INTERSECTION = "OVERLAP_INTERSECTION"
    FUNDAMENTAL_PRIMARY_NO_OVERLAP = "FUNDAMENTAL_PRIMARY_NO_OVERLAP"
    FUNDAMENTAL_ONLY = "FUNDAMENTAL_ONLY"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ValuationAffects(StrEnum):
    OVERALL = "OVERALL"
    NEW_BUYER = "NEW_BUYER"
    HOLDER = "HOLDER"


class RuleId(StrEnum):
    THESIS_ENTRY_SEPARATION = "THESIS_ENTRY_SEPARATION"
    HOLDER_VALUATION_SEPARATION = "HOLDER_VALUATION_SEPARATION"
    DATA_QUALITY_CONFIDENCE_DEFAULT = "DATA_QUALITY_CONFIDENCE_DEFAULT"
    MATERIAL_DISCLOSURE_EXCEPTION = "MATERIAL_DISCLOSURE_EXCEPTION"
    ARCHETYPE_WEIGHTING = "ARCHETYPE_WEIGHTING"
    EVIDENCE_OWNERSHIP = "EVIDENCE_OWNERSHIP"
    WAIT_ENTRY_RANGE = "WAIT_ENTRY_RANGE"
    NO_ARBITRARY_DISCOUNT = "NO_ARBITRARY_DISCOUNT"
    FUNDAMENTAL_TACTICAL_COMBINATION = "FUNDAMENTAL_TACTICAL_COMBINATION"


class EntryBand(FrozenModel):
    status: EntryBandStatus
    candidate_id: str | None
    low: float | None
    high: float | None
    currency: str | None
    evidence_refs: tuple[str, ...] = Field(max_length=8)


class EntryRange(FrozenModel):
    entry_range_status: EntryRangeStatus
    entry_option_id: str | None
    current_price: float | None
    current_price_as_of: str | None
    current_price_ref: str | None
    preferred_entry_low: float | None
    preferred_entry_high: float | None
    distance_to_band_pct: float | None
    fundamental_entry_band: EntryBand
    tactical_entry_band: EntryBand
    method: EntryMethod
    combination_rule: CombinationRule
    valuation_basis_refs: tuple[str, ...] = Field(max_length=8)
    technical_basis_refs: tuple[str, ...] = Field(max_length=8)
    assumptions: tuple[str, ...] = Field(max_length=8)
    unresolved_inputs: tuple[str, ...] = Field(max_length=8)
    re_evaluate_conditions: tuple[str, ...] = Field(max_length=8)


class ShadowCandidate(FrozenModel):
    ticker: str
    company_archetype: CompanyArchetype
    archetype_confidence: Confidence
    archetype_evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=8)
    archetype_rationale: str = Field(min_length=1, max_length=600)
    overall_direction: Literal["BUY", "HOLD", "SELL"]
    new_buyer: Literal["ATTRACTIVE", "WAIT", "AVOID"]
    holder: Literal["HOLDABLE", "REVIEW", "REDUCE"]
    decision_confidence: Confidence
    decisive_supporting_claim_refs: tuple[str, ...] = Field(min_length=1, max_length=6)
    decisive_contradicting_claim_refs: tuple[str, ...] = Field(max_length=6)
    thesis_state: ThesisState
    data_quality_effect: DataQualityEffect
    data_quality_reason_class: DataQualityReasonClass
    data_quality_reason: str | None = Field(max_length=500)
    data_quality_evidence_refs: tuple[str, ...] = Field(max_length=6)
    holder_reason_class: HolderReasonClass
    holder_reason: str = Field(min_length=1, max_length=500)
    holder_reason_evidence_refs: tuple[str, ...] = Field(max_length=6)
    entry_range: EntryRange
    valuation_affects: tuple[ValuationAffects, ...] = Field(max_length=3)
    rule_trace: tuple[RuleId, ...] = Field(min_length=1, max_length=10)
    policy_summary: str = Field(min_length=1, max_length=700)


class ShadowBatchOutput(FrozenModel):
    contract: Literal["m12cn-investment-policy-shadow-v1"] = CONTRACT
    generation_id: str
    packet_id: str
    market: Literal["us", "kr"]
    assessment_date: str
    candidates: tuple[ShadowCandidate, ...] = Field(min_length=1, max_length=3)


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


def _statement(row: Mapping[str, object]) -> dict[str, object]:
    statement = row.get("statement")
    if isinstance(statement, Mapping):
        return dict(statement)
    if isinstance(statement, str):
        try:
            parsed = json.loads(statement)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _finite_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _entry_id(prefix: str, payload: Mapping[str, object]) -> str:
    return f"{prefix}:{canonical_sha256(payload)[:20]}"


def _signed_distance_to_band(current: float, low: float, high: float) -> float:
    if low <= current <= high:
        return 0.0
    boundary = low if current < low else high
    return round(((boundary - current) / current) * 100.0, 6)


def _resolved_band(candidate: Mapping[str, object]) -> dict[str, object]:
    return {
        "status": EntryBandStatus.RESOLVED.value,
        "candidate_id": candidate["candidate_id"],
        "low": candidate["low"],
        "high": candidate["high"],
        "currency": candidate["currency"],
        "evidence_refs": list(candidate["evidence_refs"]),
    }


def build_entry_catalog(
    packet: Mapping[str, object],
    ownership: Mapping[str, object],
) -> dict[str, object]:
    evidence = [row for row in packet.get("evidence") or [] if isinstance(row, Mapping)]
    by_ref = {str(row.get("ref_id") or ""): row for row in evidence}
    timing_refs = {str(ref) for ref in ownership.get("timing_ref_ids") or []}
    valuation_refs = {
        str(ref)
        for ref in (
            (ownership.get("expectation_valuation") or {}).get("valuation_refs")
            if isinstance(ownership.get("expectation_valuation"), Mapping)
            else []
        )
    }

    current_price: dict[str, object] | None = None
    for row in evidence:
        if row.get("label") != "price" or str(row.get("ref_id") or "") not in timing_refs:
            continue
        statement = _statement(row)
        value = _finite_number(statement.get("current_price"))
        currency = statement.get("currency")
        as_of = statement.get("price_as_of") or row.get("as_of")
        if value is not None and value > 0 and isinstance(currency, str) and currency:
            current_price = {
                "value": value,
                "currency": currency,
                "as_of": str(as_of) if as_of is not None else None,
                "ref_id": str(row.get("ref_id")),
                "basis": statement.get("price_basis"),
                "confirmation": statement.get("price_state_confirmation"),
            }
            break

    fundamental_candidates: list[dict[str, object]] = []
    valuation_row = by_ref.get("canonical:valuation:current")
    quality_row = by_ref.get("canonical:valuation:book_quality")
    if valuation_row is not None and quality_row is not None:
        valuation = _statement(valuation_row)
        quality = _statement(quality_row)
        history = valuation.get("historical_pb_statistics")
        if isinstance(history, Mapping):
            bvps = _finite_number(valuation.get("bvps"))
            low_multiple = _finite_number(history.get("percentile_25"))
            high_multiple = _finite_number(history.get("percentile_50"))
            quality_pass = (
                quality.get("status") == "passed"
                and quality.get("price_to_book_basis_status") == "directly_comparable"
                and history.get("history_quality") == "high"
                and valuation.get("historical_comparability") == "normal"
            )
            currency = valuation.get("currency")
            if (
                quality_pass
                and bvps is not None
                and bvps > 0
                and low_multiple is not None
                and low_multiple > 0
                and high_multiple is not None
                and high_multiple >= low_multiple
                and isinstance(currency, str)
                and currency
            ):
                candidate: dict[str, object] = {
                    "method": EntryMethod.BOOK_VALUE_MULTIPLE.value,
                    "low": round(bvps * low_multiple, 6),
                    "high": round(bvps * high_multiple, 6),
                    "currency": currency,
                    "evidence_refs": [
                        "canonical:valuation:current",
                        "canonical:valuation:book_quality",
                    ],
                    "assumptions": [
                        "positive directly comparable BVPS",
                        "high-quality historical P/B distribution",
                        "25th-to-50th historical P/B percentile band",
                    ],
                    "allowed_archetypes": [
                        CompanyArchetype.STRUCTURAL_CYCLICAL_LEADER.value,
                        CompanyArchetype.MATURE_VALUE_DEFENSIVE.value,
                    ],
                    "calculation": {
                        "bvps": bvps,
                        "multiple_low": low_multiple,
                        "multiple_high": high_multiple,
                    },
                }
                candidate["candidate_id"] = _entry_id("fundamental", candidate)
                fundamental_candidates.append(candidate)

    tactical_candidates: list[dict[str, object]] = []
    for row in evidence:
        ref_id = str(row.get("ref_id") or "")
        if ref_id not in timing_refs:
            continue
        statement = _statement(row)
        label = str(row.get("label") or "")
        role = str(statement.get("role") or "")
        low: float | None = None
        high: float | None = None
        currency = statement.get("currency")
        if label == "chart_price_structure_v3_zone" and "support" in role:
            if statement.get("eligibility") not in {"ELIGIBLE", "ELIGIBLE_SR_ONLY"}:
                continue
            low = _finite_number(statement.get("raw_low"))
            high = _finite_number(statement.get("raw_high"))
        elif label == "chart_support_zone":
            low = _finite_number(statement.get("zone_low"))
            high = _finite_number(statement.get("zone_high"))
            role = role or "support_zone"
        elif label == "chart_price_rules":
            low = _finite_number(statement.get("support_zone_low"))
            high = _finite_number(statement.get("support_zone_high"))
            role = role or "stored_support_zone"
        if (
            low is None
            or high is None
            or low <= 0
            or high < low
            or not isinstance(currency, str)
            or not currency
        ):
            continue
        candidate = {
            "low": low,
            "high": high,
            "currency": currency,
            "evidence_refs": [ref_id],
            "role": role,
            "source_label": label,
            "family_consensus_safe": statement.get("family_consensus_safe"),
        }
        candidate["candidate_id"] = _entry_id("tactical", candidate)
        tactical_candidates.append(candidate)

    unique_tactical: dict[str, dict[str, object]] = {}
    for candidate in tactical_candidates:
        unique_tactical[str(candidate["candidate_id"])] = candidate
    tactical_candidates = sorted(
        unique_tactical.values(),
        key=lambda row: (float(row["low"]), float(row["high"]), str(row["candidate_id"])),
    )

    resolved_options: list[dict[str, object]] = []
    if current_price is not None:
        current_value = float(current_price["value"])
        current_currency = str(current_price["currency"])
        for fundamental in fundamental_candidates:
            if fundamental["currency"] != current_currency:
                continue
            combinations: list[dict[str, object] | None] = [None, *tactical_candidates]
            for tactical in combinations:
                fundamental_low = float(fundamental["low"])
                fundamental_high = float(fundamental["high"])
                if tactical is None:
                    preferred_low = fundamental_low
                    preferred_high = fundamental_high
                    combination = CombinationRule.FUNDAMENTAL_ONLY.value
                elif tactical["currency"] != current_currency:
                    continue
                else:
                    tactical_low = float(tactical["low"])
                    tactical_high = float(tactical["high"])
                    preferred_low = max(fundamental_low, tactical_low)
                    preferred_high = min(fundamental_high, tactical_high)
                    if preferred_low <= preferred_high:
                        combination = CombinationRule.OVERLAP_INTERSECTION.value
                    else:
                        preferred_low = fundamental_low
                        preferred_high = fundamental_high
                        combination = CombinationRule.FUNDAMENTAL_PRIMARY_NO_OVERLAP.value
                option: dict[str, object] = {
                    "method": fundamental["method"],
                    "combination_rule": combination,
                    "fundamental_candidate_id": fundamental["candidate_id"],
                    "tactical_candidate_id": (
                        tactical["candidate_id"] if tactical is not None else None
                    ),
                    "preferred_entry_low": round(preferred_low, 6),
                    "preferred_entry_high": round(preferred_high, 6),
                    "distance_to_band_pct": _signed_distance_to_band(
                        current_value,
                        preferred_low,
                        preferred_high,
                    ),
                    "currency": current_currency,
                    "valuation_basis_refs": list(fundamental["evidence_refs"]),
                    "technical_basis_refs": (
                        list(tactical["evidence_refs"]) if tactical is not None else []
                    ),
                    "assumptions": list(fundamental["assumptions"]),
                    "allowed_archetypes": list(fundamental["allowed_archetypes"]),
                    "fundamental_entry_band": _resolved_band(fundamental),
                    "tactical_entry_band": (
                        _resolved_band(tactical)
                        if tactical is not None
                        else {
                            "status": EntryBandStatus.NOT_APPLICABLE.value,
                            "candidate_id": None,
                            "low": None,
                            "high": None,
                            "currency": None,
                            "evidence_refs": [],
                        }
                    ),
                }
                option["entry_option_id"] = _entry_id("option", option)
                resolved_options.append(option)

    return {
        "contract": "m12cn-entry-range-catalog-v1",
        "ticker": packet.get("ticker"),
        "current_price": current_price,
        "valuation_refs": sorted(valuation_refs),
        "fundamental_candidates": fundamental_candidates,
        "tactical_candidates": tactical_candidates,
        "resolved_options": resolved_options,
        "unresolved_policy": {
            "technical_only_is_not_fundamental_entry": True,
            "preferred_numeric_fields_must_be_null": True,
        },
    }


def build_subject_catalog(
    *,
    context: Mapping[str, object],
    ticker: str,
    atomic_claims: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    packets = {
        str(row.get("ticker") or ""): row
        for row in context.get("evidence_packets") or []
        if isinstance(row, Mapping)
    }
    ownership_rows = {
        str(row.get("ticker") or ""): row
        for row in context.get("evidence_ownership") or []
        if isinstance(row, Mapping)
    }
    packet = packets[ticker]
    ownership = ownership_rows[ticker]
    evidence = [row for row in packet.get("evidence") or [] if isinstance(row, Mapping)]
    all_refs = {str(row.get("ref_id") or "") for row in evidence}
    core_refs = {
        str(ref)
        for ref in ownership.get("core_ref_ids") or []
        if str(ref) in all_refs and not str(ref).startswith("technical-feature:")
    }
    timing_refs = {
        str(ref)
        for ref in ownership.get("timing_ref_ids") or []
        if str(ref) in all_refs and not str(ref).startswith("technical-feature:")
    }
    expectation = ownership.get("expectation_valuation")
    valuation_refs = {
        str(ref)
        for ref in (
            expectation.get("valuation_refs")
            if isinstance(expectation, Mapping)
            else []
        )
    }
    material_terms = (
        "material disclosure failure",
        "material non-disclosure",
        "중대한 공시 실패",
        "중대한 미공시",
    )
    positive_terms = (
        "data quality restored",
        "quality improvement independently verified",
        "데이터 품질 복구가 검증",
    )
    material_refs: set[str] = set()
    positive_quality_refs: set[str] = set()
    for row in evidence:
        text = " ".join(
            (
                str(row.get("label") or ""),
                str(row.get("statement") or ""),
            )
        ).lower()
        ref_id = str(row.get("ref_id") or "")
        if any(term in text for term in material_terms):
            material_refs.add(ref_id)
        if any(term in text for term in positive_terms):
            positive_quality_refs.add(ref_id)
    claim_rows = [row for row in atomic_claims if str(row.get("ticker") or "") == ticker]
    claim_refs = {str(row.get("claim_ref") or "") for row in claim_rows}
    return {
        "ticker": ticker,
        "all_evidence_refs": sorted(core_refs | timing_refs),
        "core_evidence_refs": sorted(core_refs),
        "timing_evidence_refs": sorted(timing_refs),
        "valuation_evidence_refs": sorted(valuation_refs & all_refs),
        "material_disclosure_failure_refs": sorted(material_refs),
        "positive_quality_refs": sorted(positive_quality_refs),
        "claim_refs": sorted(claim_refs),
        "atomic_claims": claim_rows,
        "entry_catalog": build_entry_catalog(packet, ownership),
    }


def _compact_evidence(
    packet: Mapping[str, object],
    refs: Sequence[str],
) -> dict[str, object]:
    allowed = set(refs)
    rows = []
    for row in packet.get("evidence") or []:
        if not isinstance(row, Mapping) or row.get("ref_id") not in allowed:
            continue
        rows.append(
            {
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
        )
    return {
        "ticker": packet.get("ticker"),
        "company_name": packet.get("company_name"),
        "assessment_date": packet.get("assessment_date"),
        "technical_context_status": packet.get("technical_context_status"),
        "technical_context_quality": packet.get("technical_context_quality"),
        "data_quality_cautions": deepcopy(packet.get("data_quality_cautions") or []),
        "evidence": rows,
    }


def model_subject_payload(
    *,
    context: Mapping[str, object],
    frozen_core: Mapping[str, object],
    catalog: Mapping[str, object],
) -> dict[str, object]:
    ticker = str(frozen_core["ticker"])
    packets = {
        str(row.get("ticker") or ""): row
        for row in context.get("evidence_packets") or []
        if isinstance(row, Mapping)
    }
    ownership_rows = {
        str(row.get("ticker") or ""): row
        for row in context.get("evidence_ownership") or []
        if isinstance(row, Mapping)
    }
    packet = packets[ticker]
    ownership = ownership_rows[ticker]
    return {
        "ticker": ticker,
        "frozen_fundamental_core": deepcopy(dict(frozen_core)),
        "fundamental_evidence": _compact_evidence(
            packet,
            catalog["core_evidence_refs"],
        ),
        "price_timing_evidence": _compact_evidence(
            packet,
            catalog["timing_evidence_refs"],
        ),
        "expectation_valuation_interaction": deepcopy(
            ownership.get("expectation_valuation")
        ),
        "maturity_atomic_claim_catalog": deepcopy(catalog["atomic_claims"]),
        "entry_range_catalog": deepcopy(catalog["entry_catalog"]),
        "directional_data_quality_catalog": {
            "material_disclosure_failure_refs": deepcopy(
                catalog["material_disclosure_failure_refs"]
            ),
            "positive_quality_refs": deepcopy(catalog["positive_quality_refs"]),
        },
    }


def _string_branch(schema: dict[str, object]) -> dict[str, object] | None:
    if schema.get("type") == "string":
        return schema
    for branch in schema.get("anyOf") or []:
        if isinstance(branch, dict) and branch.get("type") == "string":
            return branch
    return None


def batch_output_schema(
    *,
    generation_id: str,
    packet_id: str,
    market: str,
    assessment_date: str,
    subjects: Sequence[str],
    catalogs: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    schema = ShadowBatchOutput.model_json_schema()
    properties = schema["properties"]
    for field, value in (
        ("contract", CONTRACT),
        ("generation_id", generation_id),
        ("packet_id", packet_id),
        ("market", market),
        ("assessment_date", assessment_date),
    ):
        properties[field]["const"] = value
    required = schema.setdefault("required", [])
    if "contract" not in required:
        required.insert(0, "contract")
    properties["candidates"]["minItems"] = len(subjects)
    properties["candidates"]["maxItems"] = len(subjects)

    definitions = schema["$defs"]
    candidate = definitions["ShadowCandidate"]["properties"]
    candidate["ticker"]["enum"] = list(subjects)
    all_evidence_refs = sorted(
        {
            str(ref)
            for ticker in subjects
            for ref in catalogs[ticker]["all_evidence_refs"]
        }
    )
    all_claim_refs = sorted(
        {
            str(ref)
            for ticker in subjects
            for ref in catalogs[ticker]["claim_refs"]
        }
    )
    for field in (
        "archetype_evidence_refs",
        "data_quality_evidence_refs",
        "holder_reason_evidence_refs",
    ):
        candidate[field]["items"]["enum"] = all_evidence_refs
    for field in (
        "decisive_supporting_claim_refs",
        "decisive_contradicting_claim_refs",
    ):
        candidate[field]["items"]["enum"] = all_claim_refs

    entry = definitions["EntryRange"]["properties"]
    current_ref = _string_branch(entry["current_price_ref"])
    if current_ref is not None:
        current_ref["enum"] = all_evidence_refs
    for field in ("valuation_basis_refs", "technical_basis_refs"):
        entry[field]["items"]["enum"] = all_evidence_refs
    option_ids = sorted(
        {
            str(option["entry_option_id"])
            for ticker in subjects
            for option in catalogs[ticker]["entry_catalog"]["resolved_options"]
        }
    )
    option_branch = _string_branch(entry["entry_option_id"])
    if option_branch is not None and option_ids:
        option_branch["enum"] = option_ids

    band = definitions["EntryBand"]["properties"]
    band["evidence_refs"]["items"]["enum"] = all_evidence_refs
    candidate_ids = sorted(
        {
            str(row["candidate_id"])
            for ticker in subjects
            for group in ("fundamental_candidates", "tactical_candidates")
            for row in catalogs[ticker]["entry_catalog"][group]
        }
    )
    candidate_branch = _string_branch(band["candidate_id"])
    if candidate_branch is not None and candidate_ids:
        candidate_branch["enum"] = candidate_ids
    return schema


def policy_prompt(
    *,
    identity: Mapping[str, object],
    policy_principles: Mapping[str, object],
    subject_payloads: Sequence[Mapping[str, object]],
) -> str:
    return (
        """You are performing an archive-only M12CN investment-policy calibration shadow. """
        """Return strict JSON matching the supplied schema. Do not browse and do not use any """
        """fact, label, judgment, or desired answer outside SHADOW_POLICY_CONTEXT.\n\n"""
        """Keep three axes independent. overall_direction is the long-term enterprise thesis; """
        """new_buyer is current entry attractiveness; holder is existing-holder posture. A strong """
        """thesis may be BUY while new_buyer is WAIT and holder is HOLDABLE. Expensive valuation """
        """alone must not force holder REVIEW. REVIEW requires a material thesis question, evidence """
        """contradiction, execution deterioration, balance-sheet concern, or ownership-relevant """
        """unresolved risk. REDUCE requires actual impairment, downside asymmetry, or risk evidence.\n\n"""
        """Classify company_archetype from economic evidence, never from ticker, company name, """
        """country, or a memorized sector map. Use UNRESOLVED when evidence is insufficient. Cite only """
        """exact same-ticker core evidence refs for archetype and holder reasoning. Use only exact """
        """same-ticker maturity claim refs for decisive supporting and contradicting claims. Never """
        """invent, alter, shorten, or repair a ref.\n\n"""
        """Data-quality limitations normally affect confidence only. DIRECTIONAL_NEGATIVE is allowed """
        """only for an exact ref listed in material_disclosure_failure_refs. DIRECTIONAL_POSITIVE is """
        """allowed only for an exact ref listed in positive_quality_refs. Missing provider data alone """
        """is never bearish evidence.\n\n"""
        """For every WAIT, emit exactly ENTRY_RANGE_RESOLVED or ENTRY_RANGE_UNRESOLVED. A resolved """
        """range must copy one supplied resolved option exactly, including option ID, current price, """
        """bands, method, combination rule, refs, assumptions, and signed distance. The signed distance """
        """is already runtime-computed: positive means price is below the band, negative means price """
        """must fall to the band, and zero means price is inside. The selected option's """
        """allowed_archetypes must contain the chosen company_archetype. Never calculate or adjust a """
        """price. If no suitable fundamental option exists, return ENTRY_RANGE_UNRESOLVED with all """
        """preferred numeric fields null and exact unresolved inputs. A tactical support alone cannot """
        """become a fundamental entry range. For non-WAIT outputs, use NOT_APPLICABLE and null numeric """
        """fields.\n\n"""
        """BOOK_VALUE_MULTIPLE is usable only where its supplied allowed_archetypes and positive, """
        """directly comparable book evidence apply. Do not assign an earnings multiple to a loss-making """
        """company. Do not create an arbitrary discount from current price. Do not infer target prices, """
        """order sizes, stops, or guaranteed fair value. Use concise complete Korean sentences for """
        """rationales and summaries.\n\n"""
        """Copy contract, generation_id, packet_id, market, and assessment_date exactly. Return one """
        """candidate for each ticker in exact expected_subjects order, with no extra ticker. No prior """
        """Stage-2 verdict or external reviewer judgment is supplied or """
        """permitted.\n\nSHADOW_IDENTITY:\n"""
        + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
        + "\n\nGENERIC_POLICY_PRINCIPLES:\n"
        + json.dumps(policy_principles, ensure_ascii=False, separators=(",", ":"))
        + "\n\nSHADOW_POLICY_CONTEXT:\n"
        + json.dumps(subject_payloads, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def _same_float(left: object, right: object) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-6)


def _band_matches(actual: EntryBand, expected: Mapping[str, object]) -> bool:
    return (
        actual.status.value == expected["status"]
        and actual.candidate_id == expected["candidate_id"]
        and _same_float(actual.low, expected["low"])
        and _same_float(actual.high, expected["high"])
        and actual.currency == expected["currency"]
        and tuple(actual.evidence_refs) == tuple(expected["evidence_refs"])
    )


def _band_has_no_numeric_identity(actual: EntryBand) -> bool:
    return all(
        value is None
        for value in (
            actual.candidate_id,
            actual.low,
            actual.high,
            actual.currency,
        )
    )


def validate_shadow_candidate(
    candidate: ShadowCandidate,
    catalog: Mapping[str, object],
) -> tuple[str, ...]:
    errors: list[str] = []
    core_refs = set(catalog["core_evidence_refs"])
    all_refs = set(catalog["all_evidence_refs"])
    valuation_refs = set(catalog["valuation_evidence_refs"])
    claim_refs = set(catalog["claim_refs"])
    support = set(candidate.decisive_supporting_claim_refs)
    contradiction = set(candidate.decisive_contradicting_claim_refs)
    if not set(candidate.archetype_evidence_refs).issubset(core_refs):
        errors.append("archetype_ref_outside_core_ownership")
    if not support.issubset(claim_refs):
        errors.append("supporting_claim_ref_outside_ticker")
    if not contradiction.issubset(claim_refs):
        errors.append("contradicting_claim_ref_outside_ticker")
    if support & contradiction:
        errors.append("claim_ref_overlap")
    if len(candidate.valuation_affects) != len(set(candidate.valuation_affects)):
        errors.append("duplicate_valuation_affects")
    if len(candidate.rule_trace) != len(set(candidate.rule_trace)):
        errors.append("duplicate_rule_trace")
    required_rules = {RuleId.ARCHETYPE_WEIGHTING, RuleId.EVIDENCE_OWNERSHIP}
    if not required_rules.issubset(set(candidate.rule_trace)):
        errors.append("required_generic_rule_trace_missing")

    data_refs = set(candidate.data_quality_evidence_refs)
    if not data_refs.issubset(all_refs):
        errors.append("data_quality_ref_outside_ticker")
    if candidate.data_quality_effect == DataQualityEffect.NONE:
        if (
            candidate.data_quality_reason_class != DataQualityReasonClass.NOT_APPLICABLE
            or candidate.data_quality_reason is not None
            or data_refs
        ):
            errors.append("none_data_quality_shape_invalid")
    else:
        if candidate.data_quality_reason is None or not data_refs:
            errors.append("data_quality_effect_missing_reason_or_refs")
    if candidate.data_quality_effect == DataQualityEffect.DIRECTIONAL_NEGATIVE:
        allowed = set(catalog["material_disclosure_failure_refs"])
        if (
            candidate.data_quality_reason_class
            != DataQualityReasonClass.MATERIAL_DISCLOSURE_FAILURE
            or not data_refs
            or not data_refs.issubset(allowed)
        ):
            errors.append("unsupported_directional_negative_data_quality")
    if candidate.data_quality_effect == DataQualityEffect.DIRECTIONAL_POSITIVE:
        allowed = set(catalog["positive_quality_refs"])
        if (
            candidate.data_quality_reason_class
            != DataQualityReasonClass.EVIDENCED_QUALITY_IMPROVEMENT
            or not data_refs
            or not data_refs.issubset(allowed)
        ):
            errors.append("unsupported_directional_positive_data_quality")

    holder_refs = set(candidate.holder_reason_evidence_refs)
    if not holder_refs.issubset(core_refs):
        errors.append("holder_ref_outside_core_ownership")
    if candidate.holder == "REVIEW":
        if candidate.holder_reason_class == HolderReasonClass.NOT_APPLICABLE:
            errors.append("review_reason_class_missing")
        if not holder_refs or not (holder_refs - valuation_refs):
            errors.append("review_supported_only_by_valuation")
    if candidate.holder == "REDUCE":
        allowed_reduce = {
            HolderReasonClass.EXECUTION_DETERIORATION,
            HolderReasonClass.BALANCE_SHEET_RISK,
            HolderReasonClass.THESIS_IMPAIRMENT,
            HolderReasonClass.DOWNSIDE_ASYMMETRY,
        }
        if candidate.holder_reason_class not in allowed_reduce:
            errors.append("reduce_reason_class_not_material")
        if not holder_refs or not (holder_refs - valuation_refs):
            errors.append("reduce_supported_only_by_valuation")

    entry = candidate.entry_range
    entry_catalog = catalog["entry_catalog"]
    current = entry_catalog["current_price"]
    if candidate.new_buyer == "WAIT":
        required_entry_rules = {
            RuleId.WAIT_ENTRY_RANGE,
            RuleId.NO_ARBITRARY_DISCOUNT,
        }
        if not required_entry_rules.issubset(set(candidate.rule_trace)):
            errors.append("wait_rule_trace_missing")
        if entry.entry_range_status not in {
            EntryRangeStatus.ENTRY_RANGE_RESOLVED,
            EntryRangeStatus.ENTRY_RANGE_UNRESOLVED,
        }:
            errors.append("wait_entry_status_invalid")
        if current is not None:
            if (
                not _same_float(entry.current_price, current["value"])
                or entry.current_price_as_of != current["as_of"]
                or entry.current_price_ref != current["ref_id"]
            ):
                errors.append("wait_current_price_not_exact")
        elif any(
            value is not None
            for value in (
                entry.current_price,
                entry.current_price_as_of,
                entry.current_price_ref,
            )
        ):
            errors.append("wait_current_price_invented")
        if not entry.re_evaluate_conditions:
            errors.append("wait_re_evaluate_conditions_missing")
    else:
        if entry.entry_range_status != EntryRangeStatus.NOT_APPLICABLE:
            errors.append("non_wait_entry_status_not_applicable")
        if any(
            value is not None
            for value in (
                entry.entry_option_id,
                entry.current_price,
                entry.current_price_as_of,
                entry.current_price_ref,
                entry.preferred_entry_low,
                entry.preferred_entry_high,
                entry.distance_to_band_pct,
            )
        ):
            errors.append("non_wait_numeric_or_identity_present")
        if (
            entry.method != EntryMethod.NOT_APPLICABLE
            or entry.combination_rule != CombinationRule.NOT_APPLICABLE
            or entry.fundamental_entry_band.status != EntryBandStatus.NOT_APPLICABLE
            or entry.tactical_entry_band.status != EntryBandStatus.NOT_APPLICABLE
        ):
            errors.append("non_wait_entry_shape_invalid")
        if (
            not _band_has_no_numeric_identity(entry.fundamental_entry_band)
            or not _band_has_no_numeric_identity(entry.tactical_entry_band)
        ):
            errors.append("non_wait_band_numeric_or_identity_present")

    if entry.entry_range_status == EntryRangeStatus.ENTRY_RANGE_RESOLVED:
        options = {
            str(row["entry_option_id"]): row
            for row in entry_catalog["resolved_options"]
        }
        option = options.get(str(entry.entry_option_id))
        if option is None:
            errors.append("resolved_entry_option_unknown")
        else:
            if candidate.company_archetype.value not in option["allowed_archetypes"]:
                errors.append("entry_method_incompatible_with_archetype")
            for actual, expected, name in (
                (entry.preferred_entry_low, option["preferred_entry_low"], "low"),
                (entry.preferred_entry_high, option["preferred_entry_high"], "high"),
                (entry.distance_to_band_pct, option["distance_to_band_pct"], "distance"),
            ):
                if not _same_float(actual, expected):
                    errors.append(f"resolved_entry_{name}_not_exact")
            if entry.method.value != option["method"]:
                errors.append("resolved_entry_method_not_exact")
            if entry.combination_rule.value != option["combination_rule"]:
                errors.append("resolved_combination_rule_not_exact")
            if tuple(entry.valuation_basis_refs) != tuple(option["valuation_basis_refs"]):
                errors.append("resolved_valuation_refs_not_exact")
            if tuple(entry.technical_basis_refs) != tuple(option["technical_basis_refs"]):
                errors.append("resolved_technical_refs_not_exact")
            if tuple(entry.assumptions) != tuple(option["assumptions"]):
                errors.append("resolved_assumptions_not_exact")
            if not _band_matches(entry.fundamental_entry_band, option["fundamental_entry_band"]):
                errors.append("resolved_fundamental_band_not_exact")
            if not _band_matches(entry.tactical_entry_band, option["tactical_entry_band"]):
                errors.append("resolved_tactical_band_not_exact")
        if entry.unresolved_inputs:
            errors.append("resolved_entry_has_unresolved_inputs")
    elif entry.entry_range_status == EntryRangeStatus.ENTRY_RANGE_UNRESOLVED:
        if any(
            value is not None
            for value in (
                entry.entry_option_id,
                entry.preferred_entry_low,
                entry.preferred_entry_high,
                entry.distance_to_band_pct,
            )
        ):
            errors.append("unresolved_entry_has_preferred_numbers")
        if entry.method != EntryMethod.UNRESOLVED:
            errors.append("unresolved_entry_method_invalid")
        if entry.combination_rule != CombinationRule.UNRESOLVED:
            errors.append("unresolved_entry_combination_invalid")
        if entry.fundamental_entry_band.status != EntryBandStatus.UNRESOLVED:
            errors.append("unresolved_fundamental_band_status_invalid")
        if not _band_has_no_numeric_identity(entry.fundamental_entry_band):
            errors.append("unresolved_fundamental_band_numeric_or_identity_present")
        if not entry.unresolved_inputs:
            errors.append("unresolved_inputs_missing")
        if entry.tactical_entry_band.status == EntryBandStatus.RESOLVED:
            tactical = {
                str(row["candidate_id"]): row
                for row in entry_catalog["tactical_candidates"]
            }.get(str(entry.tactical_entry_band.candidate_id))
            if tactical is None or not _band_matches(
                entry.tactical_entry_band,
                _resolved_band(tactical),
            ):
                errors.append("unresolved_tactical_band_not_exact")
        elif entry.tactical_entry_band.status != EntryBandStatus.UNRESOLVED:
            errors.append("unresolved_tactical_band_status_invalid")
        elif not _band_has_no_numeric_identity(entry.tactical_entry_band):
            errors.append("unresolved_tactical_band_numeric_or_identity_present")
    return tuple(sorted(set(errors)))


def validate_shadow_batch(
    output: ShadowBatchOutput,
    *,
    expected_identity: Mapping[str, object],
    subjects: Sequence[str],
    catalogs: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    errors: list[str] = []
    for field in ("generation_id", "packet_id", "market", "assessment_date"):
        if getattr(output, field) != expected_identity[field]:
            errors.append(f"identity_mismatch:{field}")
    returned = tuple(row.ticker for row in output.candidates)
    if returned != tuple(subjects):
        errors.append("subject_order_or_cardinality_mismatch")
    per_ticker: dict[str, list[str]] = {}
    for candidate in output.candidates:
        candidate_errors = list(validate_shadow_candidate(candidate, catalogs[candidate.ticker]))
        per_ticker[candidate.ticker] = candidate_errors
        errors.extend(f"{candidate.ticker}:{error}" for error in candidate_errors)
    return {
        "contract": "m12cn-shadow-batch-validation-v1",
        "market": output.market,
        "subjects": list(subjects),
        "error_count": len(errors),
        "errors": errors,
        "per_ticker": per_ticker,
        "status": "PASS" if not errors else "FAIL",
    }


@dataclass(frozen=True)
class GenericControlCase:
    identity: str
    archetype: CompanyArchetype
    strong_thesis: bool = False
    thesis_impaired: bool = False
    valuation_expensive: bool = False
    thesis_relevant_uncertainty: bool = False
    provider_limitation: bool = False
    material_disclosure_failure: bool = False
    severe_execution_risk: bool = False
    profitable: bool = False
    earnings_method_available: bool = False
    fundamental_entry_available: bool = False


def evaluate_generic_control(case: GenericControlCase) -> dict[str, object]:
    if case.thesis_impaired or case.severe_execution_risk:
        overall = "SELL"
        new_buyer = "AVOID"
        holder = "REDUCE"
        thesis_state = ThesisState.IMPAIRED.value
    elif case.strong_thesis:
        overall = "BUY"
        new_buyer = "WAIT" if case.valuation_expensive else "ATTRACTIVE"
        holder = "REVIEW" if case.thesis_relevant_uncertainty else "HOLDABLE"
        thesis_state = ThesisState.INTACT.value
    else:
        overall = "HOLD"
        new_buyer = "WAIT" if case.valuation_expensive else "ATTRACTIVE"
        holder = "REVIEW" if case.thesis_relevant_uncertainty else "HOLDABLE"
        thesis_state = ThesisState.MIXED.value

    if case.material_disclosure_failure:
        data_quality_effect = DataQualityEffect.DIRECTIONAL_NEGATIVE.value
    elif case.provider_limitation:
        data_quality_effect = DataQualityEffect.CONFIDENCE_ONLY.value
    else:
        data_quality_effect = DataQualityEffect.NONE.value

    if new_buyer == "WAIT":
        entry_status = (
            EntryRangeStatus.ENTRY_RANGE_RESOLVED.value
            if case.fundamental_entry_available
            else EntryRangeStatus.ENTRY_RANGE_UNRESOLVED.value
        )
    else:
        entry_status = EntryRangeStatus.NOT_APPLICABLE.value
    if new_buyer != "WAIT":
        method = EntryMethod.NOT_APPLICABLE.value
    elif case.profitable and case.earnings_method_available:
        method = EntryMethod.FORWARD_EARNINGS_MULTIPLE.value
    elif case.fundamental_entry_available:
        method = EntryMethod.BOOK_VALUE_MULTIPLE.value
    else:
        method = EntryMethod.UNRESOLVED.value
    return {
        "identity": case.identity,
        "overall_direction": overall,
        "new_buyer": new_buyer,
        "holder": holder,
        "thesis_state": thesis_state,
        "data_quality_effect": data_quality_effect,
        "entry_range_status": entry_status,
        "entry_method": method,
    }


def generic_policy_control_matrix() -> dict[str, object]:
    durable = GenericControlCase(
        identity="generic-durable-a",
        archetype=CompanyArchetype.DURABLE_FRANCHISE,
        strong_thesis=True,
        valuation_expensive=True,
    )
    renamed = replace(durable, identity="renamed-equivalent-b")
    cases = {
        "durable_expensive_separates_entry": durable,
        "holder_not_reviewed_for_valuation_only": durable,
        "provider_limit_is_confidence_only": GenericControlCase(
            identity="generic-provider-limit",
            archetype=CompanyArchetype.DURABLE_FRANCHISE,
            strong_thesis=True,
            provider_limitation=True,
        ),
        "material_disclosure_can_be_directional": GenericControlCase(
            identity="generic-material-disclosure",
            archetype=CompanyArchetype.MATURE_VALUE_DEFENSIVE,
            material_disclosure_failure=True,
        ),
        "execution_risk_can_impair_direction": GenericControlCase(
            identity="generic-execution-risk",
            archetype=CompanyArchetype.EXECUTION_DEPENDENT_GROWTH,
            strong_thesis=True,
            severe_execution_risk=True,
        ),
        "cyclical_leader_can_buy_wait": GenericControlCase(
            identity="generic-cyclical-leader",
            archetype=CompanyArchetype.STRUCTURAL_CYCLICAL_LEADER,
            strong_thesis=True,
            valuation_expensive=True,
        ),
        "wait_without_fundamental_is_unresolved": GenericControlCase(
            identity="generic-no-valuation-input",
            archetype=CompanyArchetype.PROFITABLE_PREMIUM_GROWTH,
            strong_thesis=True,
            valuation_expensive=True,
        ),
        "profitable_uses_earnings_method": GenericControlCase(
            identity="generic-profitable",
            archetype=CompanyArchetype.PROFITABLE_PREMIUM_GROWTH,
            strong_thesis=True,
            valuation_expensive=True,
            profitable=True,
            earnings_method_available=True,
            fundamental_entry_available=True,
        ),
        "loss_making_does_not_use_pe": GenericControlCase(
            identity="generic-loss-making",
            archetype=CompanyArchetype.EXECUTION_DEPENDENT_GROWTH,
            strong_thesis=True,
            valuation_expensive=True,
            profitable=False,
            earnings_method_available=False,
        ),
        "identity_renamed_equivalence_a": durable,
        "identity_renamed_equivalence_b": renamed,
    }
    expected: dict[str, dict[str, object]] = {
        "durable_expensive_separates_entry": {
            "overall_direction": "BUY",
            "new_buyer": "WAIT",
            "holder": "HOLDABLE",
        },
        "holder_not_reviewed_for_valuation_only": {"holder": "HOLDABLE"},
        "provider_limit_is_confidence_only": {
            "data_quality_effect": "CONFIDENCE_ONLY"
        },
        "material_disclosure_can_be_directional": {
            "data_quality_effect": "DIRECTIONAL_NEGATIVE"
        },
        "execution_risk_can_impair_direction": {
            "overall_direction": "SELL",
            "holder": "REDUCE",
        },
        "cyclical_leader_can_buy_wait": {
            "overall_direction": "BUY",
            "new_buyer": "WAIT",
        },
        "wait_without_fundamental_is_unresolved": {
            "entry_range_status": "ENTRY_RANGE_UNRESOLVED"
        },
        "profitable_uses_earnings_method": {
            "entry_method": "FORWARD_EARNINGS_MULTIPLE"
        },
        "loss_making_does_not_use_pe": {"entry_method": "UNRESOLVED"},
    }
    rows: list[dict[str, object]] = []
    for name, case in cases.items():
        result = evaluate_generic_control(case)
        expected_fields = expected.get(name, {})
        errors = [
            f"{field}:expected={value}:actual={result.get(field)}"
            for field, value in expected_fields.items()
            if result.get(field) != value
        ]
        rows.append(
            {
                "control": name,
                "input": asdict(case),
                "result": result,
                "errors": errors,
                "status": "PASS" if not errors else "FAIL",
            }
        )
    equivalent_a = rows[-2]["result"]
    equivalent_b = rows[-1]["result"]
    comparable_a = {key: value for key, value in equivalent_a.items() if key != "identity"}
    comparable_b = {key: value for key, value in equivalent_b.items() if key != "identity"}
    identity_status = "PASS" if comparable_a == comparable_b else "FAIL"
    rows[-2]["identity_equivalence_status"] = identity_status
    rows[-1]["identity_equivalence_status"] = identity_status
    status = "PASS" if all(row["status"] == "PASS" for row in rows) and identity_status == "PASS" else "FAIL"
    return {
        "contract": "m12cn-generic-policy-control-matrix-v1",
        "control_count": len(rows),
        "identity_renamed_equivalence": identity_status,
        "ticker_or_name_policy_mapping_count": 0,
        "rows": rows,
        "status": status,
    }
