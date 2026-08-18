from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable


SEMANTIC_SCOPE_CONTRACT = "semantic-scope-and-decision-hierarchy-v1"
SEMANTIC_CLAIM_REFERENCE_FIELD = "semantic_claim_refs"
DECISION_MATERIAL_DELTA_CONTRACT = "decision-material-delta-v1"
VALUATION_CONTEXT_CONTRACT = "valuation-context-wording-v1"
VALUATION_CONTEXT_REFERENCE_FIELD = "valuation_context_ref"
VALUATION_CONTEXT_CLASSES = {
    "CURRENT_ONLY",
    "CURRENT_PLUS_HISTORY",
    "CURRENT_PLUS_PEER",
    "CURRENT_PLUS_HISTORY_PLUS_PEER",
    "LIMITED_VALUATION",
}
VALUATION_CONTEXT_STATUSES = {"available", "unsafe", "unavailable"}
VALUATION_SCOPES = {
    "company",
    "listed_security",
    "segment",
    "sum_of_parts_component",
    "unknown",
}
CLAIM_SCOPES = VALUATION_SCOPES | {"market", "industry", "portfolio"}

_SEGMENT_VALUATION = re.compile(
    r"(?:(?:사업|부문|세그먼트)(?:의|별)|\bsegment(?:-level)?\b)"
    r".{0,28}(?:f?PER|f?PBR|이익\s*기준|장부가\s*기준)",
    re.IGNORECASE,
)
_OBSERVER_ROLE = re.compile(r"^(?:신규\s*관찰자|관찰자)(?:는|은)?\s*")
_HOLDER_ROLE = re.compile(r"^(?:기존\s*)?보유자(?:는|은)?\s*")
_OBSERVER_DECISION = re.compile(
    r"진입|추격|손익비|저항|지지\s*(?:접근|재시험)|확인선|매수\s*조건|가격\s*매력"
)
_HOLDER_DECISION = re.compile(
    r"논리|무효화|실적|이익|수익성|마진|margin|현금흐름|FCF|CAPEX|재고|"
    r"경고|지지\s*유지|실행|자본|부채|희석|계약|billing"
)
_DENIED_ECHO_PATTERNS = {
    "revenue": re.compile(r"외형\s*(?:성장|증가|둔화|감소)|매출.{0,10}(?:성장|증가|둔화|감소|개선|악화)"),
    "operating_income": re.compile(
        r"영업이익.{0,10}(?:성장|증가|둔화|감소|개선|악화)|이익\s*(?:성장|증가|둔화|감소)"
    ),
    "margin": re.compile(r"수익성.{0,10}(?:개선|악화|상승|하락)|이익률.{0,10}(?:개선|악화|상승|하락)"),
    "earnings": re.compile(r"전사\s*실적|실적.{0,10}(?:개선|증가|둔화|악화|강화|약화)"),
    "pe": re.compile(r"낮은\s*이익\s*배수|높은\s*이익\s*배수|피크\s*이익", re.IGNORECASE),
}
_EXCLUSIVE_CURRENT_ONLY = re.compile(
    r"현재\s*(?:회사\s*전체\s*)?(?:절대\s*)?배수(?:만|에만)|"
    r"현재\s*(?:회사\s*전체\s*)?배수에\s*한정"
)


@dataclass(frozen=True)
class DecisionCandidate:
    key: str
    tier: int
    changed: bool
    materiality: str
    reason: str
    fact_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "tier": self.tier,
            "changed": self.changed,
            "materiality": self.materiality,
            "reason": self.reason,
            "fact_ids": list(self.fact_ids),
        }


@dataclass(frozen=True)
class DecisionMaterialSelection:
    contract: str
    candidates: tuple[DecisionCandidate, ...]
    selected_primary: str
    selected_secondary: str | None
    decision_context: str
    override: str | None
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "selected_primary": self.selected_primary,
            "selected_secondary": self.selected_secondary,
            "decision_context": self.decision_context,
            "override": self.override,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ValuationContextSelection:
    contract: str
    valuation_context_class: str
    current_status: str
    historical_status: str
    peer_status: str
    forward_status: str
    current_used: bool
    history_used: bool
    peer_used: bool
    forward_used: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "valuation_context_class": self.valuation_context_class,
            "current_status": self.current_status,
            "historical_status": self.historical_status,
            "peer_status": self.peer_status,
            "forward_status": self.forward_status,
            "current_used": self.current_used,
            "history_used": self.history_used,
            "peer_used": self.peer_used,
            "forward_used": self.forward_used,
            "reason": self.reason,
        }


def select_valuation_context(
    *,
    current_status: str,
    historical_status: str,
    peer_status: str,
    forward_status: str,
    current_used: bool,
    history_used: bool,
    peer_used: bool,
    forward_used: bool,
) -> ValuationContextSelection:
    statuses = (current_status, historical_status, peer_status, forward_status)
    if any(status not in VALUATION_CONTEXT_STATUSES for status in statuses):
        raise ValueError("unsupported valuation context availability status")
    for status, used, name in (
        (current_status, current_used, "current"),
        (historical_status, history_used, "history"),
        (peer_status, peer_used, "peer"),
        (forward_status, forward_used, "forward"),
    ):
        if used and status != "available":
            raise ValueError(f"{name} valuation context cannot be used when {status}")

    context_class = _valuation_context_class(
        current_used=current_used,
        history_used=history_used,
        peer_used=peer_used,
    )
    return ValuationContextSelection(
        contract=VALUATION_CONTEXT_CONTRACT,
        valuation_context_class=context_class,
        current_status=current_status,
        historical_status=historical_status,
        peer_status=peer_status,
        forward_status=forward_status,
        current_used=current_used,
        history_used=history_used,
        peer_used=peer_used,
        forward_used=forward_used,
        reason=_valuation_context_reason(
            context_class,
            historical_status=historical_status,
            peer_status=peer_status,
        ),
    )


def build_valuation_context_selection(
    stock: dict[str, object],
    historical: dict[str, object],
    *,
    current_used: bool,
    history_used: bool,
    peer_used: bool = False,
    forward_used: bool = False,
) -> ValuationContextSelection:
    candidates = historical.get("candidates")
    historical_items = (
        [item for item in candidates if isinstance(item, dict)]
        if isinstance(candidates, list)
        else []
    )
    historical_status = (
        "available"
        if any(item.get("safe") is True for item in historical_items)
        else "unsafe"
        if any(item.get("percentile") is not None for item in historical_items)
        else "unavailable"
    )
    return select_valuation_context(
        current_status="available" if current_used else "unavailable",
        historical_status=historical_status,
        peer_status=_peer_context_status(stock),
        forward_status=_forward_context_status(stock),
        current_used=current_used,
        history_used=history_used,
        peer_used=peer_used,
        forward_used=forward_used,
    )


def assign_listed_security_valuation_scope(
    facts: Iterable[dict[str, object]],
) -> None:
    for fact in facts:
        fact_type = str(fact.get("fact_type") or "")
        fact_id = str(fact.get("fact_id") or "")
        if not (fact_type.startswith("valuation") or fact_id.startswith("valuation:")):
            continue
        scope = str(fact.get("valuation_scope") or "")
        if scope not in VALUATION_SCOPES:
            fact["valuation_scope"] = "listed_security"


def select_decision_material_delta(
    stock: dict[str, object],
    *,
    financial_available: bool,
) -> DecisionMaterialSelection:
    assessment = _mapping(stock.get("deterministic_assessment"))
    monitoring = _mapping(stock.get("monitoring_state"))
    delta = _mapping(monitoring.get("delta"))
    candidates: list[DecisionCandidate] = []

    severity = str(assessment.get("daily_change_severity") or "none")
    thesis_change = str(assessment.get("business_thesis_change") or "no_material_change")
    earnings_impact = str(assessment.get("earnings_estimate_impact") or "unchanged")
    if severity not in {"", "none"} or thesis_change not in {
        "",
        "no_material_change",
        "unchanged",
    } or earnings_impact not in {"", "unchanged", "no_material_change"}:
        candidates.append(
            DecisionCandidate(
                key="earnings_or_thesis",
                tier=1,
                changed=True,
                materiality="material",
                reason="deterministic_assessment_records_business_or_earnings_change",
            )
        )
    elif financial_available:
        candidates.append(
            DecisionCandidate(
                key="earnings_context",
                tier=1,
                changed=False,
                materiality="decision_context",
                reason="verified_financial_relation_is_current_context_not_historical_date_delta",
            )
        )

    chart_transition = str(delta.get("chart_state_change") or "")
    confirmation_transition = str(delta.get("confirmation_transition") or "")
    if _transition_changed(chart_transition) or _transition_changed(
        confirmation_transition
    ):
        candidates.append(
            DecisionCandidate(
                key="price_structure",
                tier=2,
                changed=True,
                materiality="material",
                reason="verified_chart_or_confirmation_lifecycle_transition",
            )
        )

    valuation_change = str(delta.get("valuation_change") or "")
    if valuation_change not in {
        "",
        "unchanged",
        "unchanged_or_unavailable",
        "unavailable",
        "unknown",
    }:
        candidates.append(
            DecisionCandidate(
                key="valuation",
                tier=2,
                changed=True,
                materiality="material",
                reason="verified_valuation_state_transition",
            )
        )

    rr_change = str(delta.get("rr_change") or "")
    if rr_change not in {"", "unchanged", "unavailable", "unknown"}:
        candidates.append(
            DecisionCandidate(
                key="risk_reward",
                tier=3,
                changed=True,
                materiality="supporting",
                reason="verified_current_price_rr_change",
            )
        )

    supply_transition = str(delta.get("supply_transition") or "")
    if supply_transition not in {"", "aligned", "unavailable", "unknown"}:
        major = any(
            token in supply_transition.casefold()
            for token in ("major", "extreme", "reversal", "invalidation")
        )
        candidates.append(
            DecisionCandidate(
                key="supply",
                tier=2 if major else 3,
                changed=True,
                materiality="material_override" if major else "supporting",
                reason=(
                    "verified_major_supply_transition"
                    if major
                    else "verified_mild_actor_horizon_divergence"
                ),
            )
        )

    changed = [candidate for candidate in candidates if candidate.changed]
    changed.sort(key=lambda candidate: (candidate.tier, candidate.key))
    override: str | None = None
    if changed and changed[0].materiality == "material_override":
        override = changed[0].reason

    if changed and changed[0].tier <= 2:
        primary = changed[0].key
        secondary = changed[1].key if len(changed) > 1 else None
        reason = f"lowest_verified_materiality_tier:{changed[0].tier}"
    elif not financial_available and changed:
        primary = changed[0].key
        secondary = changed[1].key if len(changed) > 1 else None
        reason = "best_available_verified_delta_without_safe_earnings_context"
    else:
        primary = "none"
        secondary = changed[0].key if changed else None
        reason = (
            "supporting_delta_does_not_override_verified_earnings_context"
            if financial_available and changed
            else "no_verified_material_delta"
        )

    if financial_available:
        decision_context = "earnings_and_valuation"
    elif _has_safe_historical_book_context(stock):
        decision_context = "valuation_price_and_execution"
    else:
        decision_context = "price_and_execution"
    return DecisionMaterialSelection(
        contract=DECISION_MATERIAL_DELTA_CONTRACT,
        candidates=tuple(candidates),
        selected_primary=primary,
        selected_secondary=secondary,
        decision_context=decision_context,
        override=override,
        reason=reason,
    )


def historical_valuation_selection(
    stock: dict[str, object],
    *,
    denied_earnings: bool,
) -> dict[str, object]:
    current_fact = _fact(stock, "valuation:current")
    current_fields = _mapping(current_fact.get("fields"))
    comparability = str(current_fields.get("historical_comparability") or "unknown")
    candidates: list[dict[str, object]] = []
    for metric, fact_id, statistics_key in (
        ("pe", "valuation:historical_pe", "historical_pe_statistics"),
        ("pbr", "valuation:historical_pb", "historical_pb_statistics"),
    ):
        fact = _fact(stock, fact_id)
        statistics = _mapping(_mapping(fact.get("fields")).get(statistics_key))
        percentile = _number(statistics.get("current_percentile"))
        observation_count = statistics.get("deduplicated_observation_count")
        quality = str(statistics.get("history_quality") or "unknown")
        coverage = _number(statistics.get("history_coverage_ratio"))
        history_end = _parsed_date(statistics.get("history_end_date"))
        fact_as_of = _parsed_date(fact.get("as_of_date"))
        stale = bool(
            history_end is None
            or fact_as_of is None
            or (fact_as_of - history_end).days > 14
        )
        safe = bool(
            fact
            and fact.get("interpretation_eligible") is not False
            and comparability == "normal"
            and quality == "high"
            and isinstance(observation_count, int)
            and observation_count >= 30
            and coverage is not None
            and coverage >= 0.8
            and percentile is not None
            and not (metric == "pe" and denied_earnings)
            and not stale
        )
        triggered = bool(safe and (percentile <= 25.0 or percentile >= 75.0))
        reason = (
            "selected_decision_band_candidate"
            if triggered
            else "denied_earnings_family"
            if metric == "pe" and denied_earnings
            else "historical_comparability_failed"
            if comparability != "normal"
            else "historical_context_stale"
            if stale
            else "history_quality_or_sample_failed"
            if not safe
            else "percentile_not_in_decision_band"
        )
        candidates.append(
            {
                "metric": metric,
                "fact_id": fact_id,
                "field_path": f"fields.{statistics_key}.current_percentile",
                "percentile": percentile,
                "sample_count": observation_count,
                "history_start_date": statistics.get("history_start_date"),
                "history_end_date": statistics.get("history_end_date"),
                "stale": stale,
                "history_quality": quality,
                "coverage_ratio": coverage,
                "comparability": comparability,
                "safe": safe,
                "decision_relevant": triggered,
                "selected": False,
                "reason": reason,
            }
        )
    eligible = [item for item in candidates if item["decision_relevant"]]
    selected = max(
        eligible,
        key=lambda item: abs(float(item["percentile"]) - 50.0),
        default=None,
    )
    if selected is not None:
        selected["selected"] = True
        for item in eligible:
            if item is not selected:
                item["reason"] = "suppressed_by_stronger_safe_historical_context"
    return {
        "available": bool([item for item in candidates if item["percentile"] is not None]),
        "selected": dict(selected) if selected is not None else None,
        "candidates": candidates,
        "safe_context_lost": False,
        "replacement_context": None,
    }


def financial_cross_field_coherence_report(
    recovery: dict[str, object],
) -> dict[str, object]:
    fields = _mapping(recovery.get("fields"))
    revenue = _mapping(fields.get("revenue"))
    operating = _mapping(fields.get("operating_income"))
    margin = _mapping(fields.get("operating_margin"))
    revenue_value = _number(revenue.get("value"))
    operating_value = _number(operating.get("value"))
    rendered_margin = _number(margin.get("value"))
    calculated_margin = (
        operating_value / revenue_value * 100.0
        if operating_value is not None and revenue_value not in {None, 0.0}
        else None
    )
    margin_match = _close(calculated_margin, rendered_margin)
    yoy_checks: dict[str, object] = {}
    for field_name in ("revenue", "operating_income"):
        field = _mapping(fields.get(field_name))
        yoy = _mapping(field.get("yoy"))
        current_lineage = _mapping(yoy.get("current_lineage"))
        comparison_lineage = _mapping(yoy.get("comparison_lineage"))
        current = _number(current_lineage.get("amount"))
        comparison = _number(comparison_lineage.get("amount"))
        derived = (
            (current / comparison - 1.0) * 100.0
            if current is not None and comparison not in {None, 0.0}
            else None
        )
        lineage_match = _comparable_financial_lineage(
            current_lineage, comparison_lineage
        )
        value_match = _close(derived, _number(yoy.get("value")))
        yoy_checks[field_name] = {
            "status": yoy.get("status"),
            "current_amount": current,
            "comparison_amount": comparison,
            "derived_yoy_pct": derived,
            "rendered_yoy_pct": yoy.get("value"),
            "lineage_comparable": lineage_match,
            "formula_match": value_match,
            "current_lineage": _coherence_lineage(current_lineage),
            "comparison_lineage": _coherence_lineage(comparison_lineage),
        }
    complete = all(
        _mapping(fields.get(name))
        for name in ("revenue", "operating_income", "operating_margin")
    )
    direct_verified = complete and all(
        _mapping(fields.get(name)).get("status") == "verified_usable"
        for name in ("revenue", "operating_income", "operating_margin")
    )
    coherent = bool(
        direct_verified
        and margin_match
        and all(
            item["status"] == "verified_usable"
            and item["lineage_comparable"]
            and item["formula_match"]
            for item in yoy_checks.values()
        )
    )
    classification = (
        "VALID_AND_COHERENT"
        if coherent
        else "NOT_APPLICABLE_INCOMPLETE"
        if not complete
        else "LINEAGE_CONFLICT"
    )
    return {
        "classification": classification,
        "economic_plausibility_inferred": False,
        "revenue": {
            "value": revenue_value,
            "lineage": _coherence_lineage(_mapping(revenue.get("lineage"))),
        },
        "operating_income": {
            "value": operating_value,
            "lineage": _coherence_lineage(_mapping(operating.get("lineage"))),
        },
        "operating_margin": {
            "rendered_pct": rendered_margin,
            "calculated_pct": calculated_margin,
            "formula_match": margin_match,
        },
        "yoy": yoy_checks,
    }


def semantic_claim_reference_errors(
    review: dict[str, object],
    stock: dict[str, object],
    *,
    prefix: str,
) -> tuple[list[str], list[dict[str, object]]]:
    refs_value = review.pop(SEMANTIC_CLAIM_REFERENCE_FIELD, [])
    if stock.get("semantic_scope_contract") != SEMANTIC_SCOPE_CONTRACT:
        return [f"{prefix}:semantic_scope_contract_unsupported"], []
    if not isinstance(refs_value, list):
        return [f"{prefix}:semantic_claim_refs_not_list"], []
    facts = {
        str(item.get("fact_id") or ""): item
        for item in stock.get("fact_catalog", [])
        if isinstance(item, dict) and item.get("fact_id")
    }
    facts_used = {
        str(item) for item in review.get("facts_used", [])
    } if isinstance(review.get("facts_used"), list) else set()
    denied_families = {
        str(item) for item in stock.get("denied_semantic_families", [])
    }
    errors: list[str] = []
    accepted: list[dict[str, object]] = []
    coverage: dict[str, list[tuple[int, int, set[str], str]]] = {}
    seen: set[str] = set()
    for index, item in enumerate(refs_value):
        if not isinstance(item, dict):
            errors.append(f"{prefix}:semantic_claim_ref_not_object:{index}")
            continue
        ref_id = str(item.get("ref_id") or "")
        text_ref = str(item.get("text_ref") or "")
        exact_span = _normalize(str(item.get("exact_text_span") or ""))
        claim_type = str(item.get("claim_type") or "")
        economic_scope = str(item.get("economic_scope") or "")
        supporting = {
            str(value) for value in item.get("supporting_fact_ids", [])
        } if isinstance(item.get("supporting_fact_ids"), list) else set()
        families = {
            str(value) for value in item.get("semantic_families", [])
        } if isinstance(item.get("semantic_families"), list) else set()
        if not ref_id or ref_id in seen:
            errors.append(f"{prefix}:semantic_claim_ref_invalid_id:{ref_id or index}")
            continue
        seen.add(ref_id)
        target = _text_value(review, text_ref)
        normalized_target = _normalize(target)
        if not exact_span or normalized_target.count(exact_span) != 1:
            errors.append(f"{prefix}:semantic_claim_span_not_unique:{ref_id}")
            continue
        if economic_scope not in CLAIM_SCOPES:
            errors.append(f"{prefix}:semantic_claim_scope_invalid:{ref_id}")
            continue
        if not supporting or not supporting.issubset(facts_used) or not supporting.issubset(facts):
            errors.append(f"{prefix}:semantic_claim_fact_not_grounded:{ref_id}")
            continue
        section_facts = _section_fact_ids(review, text_ref)
        if section_facts and not supporting.issubset(section_facts):
            errors.append(f"{prefix}:semantic_claim_fact_outside_section:{ref_id}")
            continue
        denied_support = {fact_id for fact_id in supporting if _fact_is_denied(facts[fact_id])}
        denial_explanation = claim_type == "denial_explanation"
        if denied_support and not denial_explanation:
            errors.append(f"{prefix}:semantic_claim_denied_fact_support:{ref_id}")
            continue
        if families.intersection(denied_families) and not denial_explanation:
            errors.append(f"{prefix}:semantic_claim_denied_family:{ref_id}")
            continue
        if denial_explanation and not denied_support:
            errors.append(f"{prefix}:semantic_claim_denial_without_denied_fact:{ref_id}")
            continue
        start = normalized_target.index(exact_span)
        end = start + len(exact_span)
        coverage.setdefault(text_ref, []).append((start, end, families, claim_type))
        accepted.append(
            {
                "ref_id": ref_id,
                "text_ref": text_ref,
                "exact_text_span": exact_span,
                "normalized_span_sha256": hashlib.sha256(
                    exact_span.encode("utf-8")
                ).hexdigest(),
                "claim_type": claim_type,
                "economic_scope": economic_scope,
                "supporting_fact_ids": sorted(supporting),
                "semantic_families": sorted(families),
            }
        )

    for text_ref, text in _review_texts(review):
        normalized = _normalize(text)
        for family in denied_families:
            pattern = _DENIED_ECHO_PATTERNS.get(family)
            if pattern is None:
                continue
            for match in pattern.finditer(normalized):
                if not any(
                    start <= match.start() and match.end() <= end and family in families
                    for start, end, families, claim_type in coverage.get(text_ref, [])
                    if claim_type != "denial_explanation"
                ):
                    errors.append(
                        f"{prefix}:denied_fact_qualitative_echo:{text_ref}:{family}"
                    )
    return list(dict.fromkeys(errors)), accepted


def valuation_context_reference_errors(
    review: dict[str, object],
    stock: dict[str, object],
    bindings: list[dict[str, object]],
    *,
    prefix: str,
) -> tuple[list[str], dict[str, object] | None]:
    value = review.pop(VALUATION_CONTEXT_REFERENCE_FIELD, None)
    if value is None:
        return [], None
    if not isinstance(value, dict):
        return [f"{prefix}:valuation_context_ref_not_object"], None

    context_class = str(value.get("valuation_context_class") or "")
    text_ref = str(value.get("text_ref") or "")
    exact_span = _normalize(str(value.get("exact_text_span") or ""))
    current_used = value.get("current_used") is True
    history_used = value.get("history_used") is True
    peer_used = value.get("peer_used") is True
    forward_used = value.get("forward_used") is True
    statuses = {
        name: str(value.get(f"{name}_status") or "")
        for name in ("current", "historical", "peer", "forward")
    }
    errors: list[str] = []
    if value.get("contract") != VALUATION_CONTEXT_CONTRACT:
        errors.append(f"{prefix}:valuation_context_contract_unsupported")
    if context_class not in VALUATION_CONTEXT_CLASSES:
        errors.append(f"{prefix}:valuation_context_class_invalid")
    if any(status not in VALUATION_CONTEXT_STATUSES for status in statuses.values()):
        errors.append(f"{prefix}:valuation_context_status_invalid")

    expected = _valuation_context_class(
        current_used=current_used,
        history_used=history_used,
        peer_used=peer_used,
    )
    if context_class != expected:
        errors.append(f"{prefix}:valuation_context_class_state_mismatch")
    for name, used in (
        ("current", current_used),
        ("historical", history_used),
        ("peer", peer_used),
        ("forward", forward_used),
    ):
        if used and statuses[name] != "available":
            errors.append(f"{prefix}:valuation_context_used_unsafe:{name}")

    target = _normalize(_text_value(review, text_ref))
    if not exact_span or target.count(exact_span) != 1:
        errors.append(f"{prefix}:valuation_context_span_not_unique")

    semantics = {
        str(item.get("semantic_type") or "")
        for item in bindings
        if str(item.get("text_ref") or "") == text_ref
    }
    actual_current = bool({"trailing_pe", "price_to_book"}.intersection(semantics))
    actual_history = bool(
        {"historical_pe_percentile", "historical_pb_percentile"}.intersection(
            semantics
        )
    )
    actual_peer = bool(
        {
            "peer_pe_multiple",
            "peer_pb_multiple",
            "peer_pe_relative_pct",
            "peer_pb_relative_pct",
            "peer_pe_relative_multiple",
            "peer_pb_relative_multiple",
            "peer_pe_cross_section_percentile",
            "peer_pb_cross_section_percentile",
        }.intersection(semantics)
    )
    actual_forward = bool(
        {"forward_pe", "forward_price_to_book"}.intersection(semantics)
    )
    for name, declared, actual in (
        ("current", current_used, actual_current),
        ("history", history_used, actual_history),
        ("peer", peer_used, actual_peer),
        ("forward", forward_used, actual_forward),
    ):
        if declared != actual:
            errors.append(f"{prefix}:valuation_context_usage_mismatch:{name}")

    if actual_history and _EXCLUSIVE_CURRENT_ONLY.search(target):
        errors.append(f"{prefix}:valuation_context_current_only_history_contradiction")
    if history_used and "자체 역사" not in exact_span:
        errors.append(f"{prefix}:valuation_context_history_wording_missing")
    if peer_used and "동종기업" not in exact_span:
        errors.append(f"{prefix}:valuation_context_peer_wording_missing")

    accepted = {
        "contract": VALUATION_CONTEXT_CONTRACT,
        "valuation_context_class": context_class,
        "text_ref": text_ref,
        "exact_text_span": exact_span,
        "normalized_span_sha256": hashlib.sha256(
            exact_span.encode("utf-8")
        ).hexdigest(),
        **{f"{name}_status": status for name, status in statuses.items()},
        "current_used": current_used,
        "history_used": history_used,
        "peer_used": peer_used,
        "forward_used": forward_used,
    }
    return list(dict.fromkeys(errors)), accepted


def typed_valuation_scope_error(
    item: dict[str, object],
    fact: dict[str, object],
    exact_span: str,
) -> str | None:
    economic_scope = str(item.get("economic_scope") or "")
    fact_scope = str(fact.get("valuation_scope") or "unknown")
    if economic_scope not in VALUATION_SCOPES:
        return "economic_scope_invalid"
    if fact_scope not in VALUATION_SCOPES:
        return "fact_scope_invalid"
    if economic_scope != fact_scope:
        return "economic_scope_mismatch"
    if _SEGMENT_VALUATION.search(exact_span) and fact_scope != "segment":
        return "company_multiple_presented_as_segment"
    return None


def observer_holder_semantic_error(observer: str, holder: str) -> str | None:
    observer_body = _normalize(_OBSERVER_ROLE.sub("", observer))
    holder_body = _normalize(_HOLDER_ROLE.sub("", holder))
    if not observer_body or not holder_body or observer_body == holder_body:
        return "observer_holder_label_only_duplication"
    if not _OBSERVER_DECISION.search(observer_body):
        return "observer_decision_variable_missing"
    if not _HOLDER_DECISION.search(holder_body):
        return "holder_decision_variable_missing"
    return None


def _review_texts(review: dict[str, object]) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    for section in (
        "core_judgment",
        "business_earnings",
        "price_positioning",
        "supply_analysis",
        "valuation_analysis",
    ):
        value = _mapping(review.get(section))
        for field in ("text", "new_observer_view", "holder_view"):
            if isinstance(value.get(field), str):
                output.append((f"{section}.{field}", str(value[field])))
    for field in ("priority_watch", "next_checks", "unknowns"):
        values = review.get(field)
        if isinstance(values, list):
            output.extend(
                (f"{field}[{index}]", str(value))
                for index, value in enumerate(values)
                if isinstance(value, str)
            )
    return output


def _text_value(review: dict[str, object], text_ref: str) -> str:
    for candidate, value in _review_texts(review):
        if candidate == text_ref:
            return value
    return ""


def _section_fact_ids(review: dict[str, object], text_ref: str) -> set[str]:
    section = text_ref.split(".", maxsplit=1)[0]
    value = review.get(section)
    if not isinstance(value, dict) or not isinstance(value.get("fact_ids"), list):
        return set()
    return {str(item) for item in value["fact_ids"]}


def _fact_is_denied(fact: dict[str, object]) -> bool:
    if fact.get("interpretation_eligible") is False:
        return True
    fields = _mapping(fact.get("fields"))
    if str(fields.get("state") or "") == "denied":
        return True
    quality = fact.get("field_quality")
    if isinstance(quality, dict) and quality:
        return all(
            isinstance(value, dict) and value.get("state") == "denied"
            for value in quality.values()
        )
    return False


def _fact(stock: dict[str, object], fact_id: str) -> dict[str, object]:
    return next(
        (
            item
            for item in stock.get("fact_catalog", [])
            if isinstance(item, dict) and item.get("fact_id") == fact_id
        ),
        {},
    )


def _has_safe_historical_book_context(stock: dict[str, object]) -> bool:
    fact = _fact(stock, "valuation:historical_pb")
    return bool(fact and fact.get("interpretation_eligible") is not False)


def _peer_context_status(stock: dict[str, object]) -> str:
    fact = _fact(stock, "valuation:peer")
    if not fact:
        return "unavailable"
    fields = _mapping(fact.get("fields"))
    usable = any(
        _number(fields.get(f"{prefix}_median")) is not None
        and isinstance(fields.get(f"{prefix}_sample_count"), int)
        and int(fields[f"{prefix}_sample_count"]) > 0
        for prefix in ("pe", "pb")
    )
    if usable and fact.get("interpretation_eligible") is not False:
        return "available"
    return "unsafe"


def _forward_context_status(stock: dict[str, object]) -> str:
    fact = _fact(stock, "valuation:multiple_relation")
    if not fact:
        return "unavailable"
    fields = _mapping(fact.get("fields"))
    if (
        fields.get("basis_comparable") is True
        and fields.get("forward_period_status") in {"exact", "provider_defined"}
        and fact.get("interpretation_eligible") is not False
    ):
        return "available"
    return "unsafe"


def _valuation_context_class(
    *,
    current_used: bool,
    history_used: bool,
    peer_used: bool,
) -> str:
    if not current_used:
        return "LIMITED_VALUATION"
    if history_used and peer_used:
        return "CURRENT_PLUS_HISTORY_PLUS_PEER"
    if history_used:
        return "CURRENT_PLUS_HISTORY"
    if peer_used:
        return "CURRENT_PLUS_PEER"
    return "CURRENT_ONLY"


def _valuation_context_reason(
    context_class: str,
    *,
    historical_status: str,
    peer_status: str,
) -> str:
    if context_class == "CURRENT_PLUS_HISTORY_PLUS_PEER":
        return "current_history_and_peer_selected"
    if context_class == "CURRENT_PLUS_HISTORY":
        return (
            "current_and_history_selected_peer_unavailable"
            if peer_status != "available"
            else "current_and_history_selected_peer_not_decision_relevant"
        )
    if context_class == "CURRENT_PLUS_PEER":
        return (
            "current_and_peer_selected_history_unsafe"
            if historical_status == "unsafe"
            else "current_and_peer_selected_history_not_decision_relevant"
        )
    if context_class == "CURRENT_ONLY":
        return (
            "current_only_history_unsafe_or_unavailable"
            if historical_status != "available"
            else "current_only_history_not_decision_relevant"
        )
    return "current_valuation_unavailable"


def _transition_changed(value: str) -> bool:
    if not value or value in {"unchanged", "unavailable", "unknown"}:
        return False
    left, separator, right = value.partition("_to_")
    return bool(not separator or left != right)


def _comparable_financial_lineage(
    current: dict[str, object], comparison: dict[str, object]
) -> bool:
    if not current or not comparison:
        return False
    return all(
        current.get(key) == comparison.get(key)
        for key in (
            "account_id",
            "amount_period_type",
            "currency",
            "fs_div",
            "statement_basis",
            "statement_type",
        )
    ) and _period_days(current) == _period_days(comparison)


def _period_days(lineage: dict[str, object]) -> int | None:
    try:
        start = date.fromisoformat(str(lineage["amount_period_start"]))
        end = date.fromisoformat(str(lineage["amount_period_end"]))
    except (KeyError, TypeError, ValueError):
        return None
    return (end - start).days + 1


def _coherence_lineage(lineage: dict[str, object]) -> dict[str, object]:
    return {
        key: lineage.get(key)
        for key in (
            "source_filing",
            "rcept_no",
            "fs_div",
            "statement_type",
            "account_id",
            "account_name",
            "amount_period_type",
            "amount_period_start",
            "amount_period_end",
            "currency",
            "source_row_identity",
        )
    }


def _close(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return False
    return abs(left - right) <= max(1e-8, abs(left) * 1e-9)


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _parsed_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}
