from __future__ import annotations

import copy
import re
from collections.abc import Mapping


NUMERIC_PRIMARY_OWNER_CONTRACT = "numeric-primary-owner-v1"
CURRENT_PRICE_RR_SEMANTIC = "current_price_risk_reward_ratio"
CURRENT_PRICE_RR_PRIMARY_TEXT_REF = "price_positioning.text"
STALE_RR_TRANSITION_FACT_ID = "monitoring:risk_reward_transition"
WORKING_CAPITAL_RELATION_TYPE = "working_capital_inventory_relation"
SIGNED_INVENTORY_GAP_FIELD = "fields.gap_percentage_points_signed"
MARKET_ONLY_FRAMEWORK_MISOWNERS = {"hyperscaler_capex_transmission"}

_VALUATION_FACT_BY_FIELD = {
    "fields.trailing_pe": ("pe", "valuation:trailing_earnings"),
    "fields.forward_pe": ("forward_pe", "valuation:consensus_forward_earnings"),
    "fields.price_to_book": ("pbr", "valuation:current_pbr"),
    "fields.forward_price_to_book": (
        "forward_pbr",
        "valuation:modeled_forward_book",
    ),
    "fields.historical_pe_statistics.current_percentile": (
        "pe",
        "valuation:historical_pe",
    ),
    "fields.historical_pb_statistics.current_percentile": (
        "pbr",
        "valuation:historical_pb",
    ),
}

_PATH_PART = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[([0-9]+)\])?$")

_CANONICAL_SINGLE_NUMERIC_WRAPPERS = (
    re.compile(
        r"(?P<placeholder>\{\{numeric:[A-Za-z][A-Za-z0-9_-]{0,63}\}\})"
        r"\s*수준의 현재 가격을 기준으로 봅니다\."
    ),
    re.compile(
        r"(?P<placeholder>\{\{numeric:[A-Za-z][A-Za-z0-9_-]{0,63}\}\})"
        r"\s*수준의 거래량 참여입니다\."
    ),
)

_UNSUPPORTED_PEAK_MULTIPLE_DIRECTION = re.compile(r"피크\s*이익(?:의)?\s*(?:낮은|높은)\s*배수")

_REPEATED_SECONDARY_PROSE = {
    "price_positioning.text": {
        "이 현재가 비대칭은 신규 관찰자의 추격 판단에 우호적이지 않습니다.": (
            "new_observer_view_primary_ownership"
        ),
    },
    "valuation_analysis.text": {
        "이는 현재 이익 배수의 절대 수준을 보여 줍니다.": (
            "canonical_valuation_fact_is_primary"
        ),
        "이는 공급된 향후 이익 기준 배수의 절대 수준을 보여 줍니다.": (
            "canonical_valuation_fact_is_primary"
        ),
        "이는 현재 장부가 기준 배수의 절대 수준을 보여 줍니다.": (
            "canonical_valuation_fact_is_primary"
        ),
    },
    "core_judgment.text": {
        "오늘 자료는 사업 논리를 바꾸지 않았습니다.": (
            "entity_specific_core_judgment_is_primary"
        ),
        "오늘 자료만으로 사업 논리는 변하지 않았습니다.": (
            "entity_specific_core_judgment_is_primary"
        ),
    },
}


def _registry_semantics(packet: Mapping[str, object]) -> dict[str, dict[tuple[str, str], str]]:
    result: dict[str, dict[tuple[str, str], str]] = {}
    stocks = packet.get("stocks")
    if not isinstance(stocks, list):
        return result
    for stock in stocks:
        if not isinstance(stock, Mapping):
            continue
        ticker = str(stock.get("ticker") or "")
        rows: dict[tuple[str, str], str] = {}
        registry = stock.get("numeric_registry")
        if isinstance(registry, list):
            for item in registry:
                if not isinstance(item, Mapping):
                    continue
                rows[
                    (
                        str(item.get("fact_id") or ""),
                        str(item.get("field_path") or ""),
                    )
                ] = str(item.get("semantic_type") or "")
        result[ticker] = rows
    return result


def _stock_packets(packet: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    stocks = packet.get("stocks")
    if not isinstance(stocks, list):
        return {}
    return {
        str(stock.get("ticker") or ""): stock
        for stock in stocks
        if isinstance(stock, Mapping) and stock.get("ticker")
    }


def _fact_catalog(stock: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    facts = stock.get("fact_catalog")
    if not isinstance(facts, list):
        return {}
    return {
        str(item.get("fact_id") or ""): item
        for item in facts
        if isinstance(item, Mapping) and item.get("fact_id")
    }


def _append_unique(values: object, item: str) -> list[object]:
    output = list(values) if isinstance(values, list) else []
    if item not in output:
        output.append(item)
    return output


def _remove_value(values: object, item: str) -> list[object]:
    if not isinstance(values, list):
        return []
    return [value for value in values if str(value) != item]


def _section(review: dict[str, object], name: str) -> dict[str, object] | None:
    value = review.get(name)
    return value if isinstance(value, dict) else None


def _placeholder_sentence(text: str, ref_id: str) -> str | None:
    placeholder = f"{{{{numeric:{ref_id}}}}}"
    for match in re.finditer(r"[^.!?]+[.!?]?", text):
        sentence = match.group(0).strip()
        if sentence.count(placeholder) == 1 and sentence.count("{{numeric:") == 1:
            return sentence
    return None


def _sync_exact_text_spans(value: object, old: str, new: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "exact_text_span" and isinstance(item, str) and old in item:
                updated = item.replace(old, new)
                updated = re.sub(r"\s+([.!?])", r"\1", updated)
                value[key] = re.sub(r"\s{2,}", " ", updated).strip()
            else:
                _sync_exact_text_spans(item, old, new)
    elif isinstance(value, list):
        for item in value:
            _sync_exact_text_spans(item, old, new)


def _canonicalize_single_numeric_wrappers(
    review: dict[str, object],
    section_name: str,
    text: str,
) -> tuple[str, list[dict[str, object]]]:
    ticker = str(review.get("ticker") or "")
    handoffs: list[dict[str, object]] = []
    for pattern in _CANONICAL_SINGLE_NUMERIC_WRAPPERS:
        while match := pattern.search(text):
            old = match.group(0)
            placeholder = match.group("placeholder")
            new = f"{placeholder}입니다."
            text = f"{text[: match.start()]}{new}{text[match.end() :]}"
            _sync_exact_text_spans(review, old, new)
            handoffs.append(
                {
                    "ticker": ticker,
                    "section": section_name,
                    "numeric_ref_id": placeholder[10:-2],
                    "reason": "canonical_single_numeric_fact_ownership",
                }
            )
    return text, handoffs


def _canonicalize_standalone_numeric_sentences(
    review: dict[str, object],
) -> list[dict[str, object]]:
    handoffs: list[dict[str, object]] = []
    ticker = str(review.get("ticker") or "")
    for section_name in (
        "core_judgment",
        "business_earnings",
        "price_positioning",
        "supply_analysis",
        "valuation_analysis",
    ):
        section = _section(review, section_name)
        if section is None or not isinstance(section.get("text"), str):
            continue
        text, wrapper_handoffs = _canonicalize_single_numeric_wrappers(
            review,
            section_name,
            str(section["text"]),
        )
        handoffs.extend(wrapper_handoffs)
        if section_name == "valuation_analysis":
            for unsupported in _UNSUPPORTED_PEAK_MULTIPLE_DIRECTION.findall(text):
                text = text.replace(unsupported, "피크 이익 배수")
                _sync_exact_text_spans(review, unsupported, "피크 이익 배수")
                handoffs.append(
                    {
                        "ticker": ticker,
                        "section": section_name,
                        "reason": "unsupported_peak_multiple_direction_removed",
                    }
                )
        for ref_id in re.findall(r"\{\{numeric:([A-Za-z][A-Za-z0-9_-]{0,63})\}\}", text):
            placeholder = f"{{{{numeric:{ref_id}}}}}"
            sentence = _placeholder_sentence(text, ref_id)
            if sentence != f"{placeholder}.":
                continue
            replacement = f"{placeholder}입니다."
            text = text.replace(sentence, replacement, 1)
            _sync_exact_text_spans(review, sentence, replacement)
            handoffs.append(
                {
                    "ticker": ticker,
                    "section": section_name,
                    "numeric_ref_id": ref_id,
                    "reason": "canonical_numeric_sentence_completion",
                }
            )
        section["text"] = text
    return handoffs


def _remove_repeated_secondary_prose(
    reviews: list[object],
) -> list[dict[str, object]]:
    occurrences: dict[tuple[str, str], list[dict[str, object]]] = {}
    for review in reviews:
        if not isinstance(review, dict):
            continue
        for text_ref, phrases in _REPEATED_SECONDARY_PROSE.items():
            section_name, _ = text_ref.split(".", 1)
            section = _section(review, section_name)
            text = str(section.get("text") or "") if section is not None else ""
            for phrase in phrases:
                if phrase in text:
                    occurrences.setdefault((text_ref, phrase), []).append(review)

    suppressions: list[dict[str, object]] = []
    for (text_ref, phrase), owners in occurrences.items():
        if len(owners) < 3:
            continue
        section_name, _ = text_ref.split(".", 1)
        for review in owners:
            section = _section(review, section_name)
            if section is None:
                continue
            old_text = str(section.get("text") or "")
            updated = re.sub(r"\s{2,}", " ", old_text.replace(phrase, "")).strip()
            if not updated:
                continue
            section["text"] = updated
            _sync_exact_text_spans(review, phrase, "")
            suppressions.append(
                {
                    "ticker": str(review.get("ticker") or ""),
                    "text_ref": text_ref,
                    "suppressed_span": phrase,
                    "reason": _REPEATED_SECONDARY_PROSE[text_ref][phrase],
                }
            )
    return suppressions


def _remove_stale_rr_transition(
    review: dict[str, object],
    stock: Mapping[str, object],
) -> dict[str, object] | None:
    catalog = _fact_catalog(stock)
    if STALE_RR_TRANSITION_FACT_ID in catalog:
        return None
    referenced = any(
        isinstance(item, Mapping)
        and str(item.get("fact_id") or "") == STALE_RR_TRANSITION_FACT_ID
        for item in review.get("numeric_fact_refs", [])
        if isinstance(review.get("numeric_fact_refs"), list)
    )
    if referenced:
        return None
    removed = False
    if STALE_RR_TRANSITION_FACT_ID in review.get("facts_used", []):
        review["facts_used"] = _remove_value(
            review.get("facts_used"), STALE_RR_TRANSITION_FACT_ID
        )
        removed = True
    for name in (
        "core_judgment",
        "business_earnings",
        "price_positioning",
        "supply_analysis",
        "valuation_analysis",
    ):
        section = _section(review, name)
        if section is None or STALE_RR_TRANSITION_FACT_ID not in section.get(
            "fact_ids", []
        ):
            continue
        section["fact_ids"] = _remove_value(
            section.get("fact_ids"), STALE_RR_TRANSITION_FACT_ID
        )
        removed = True
    if not removed:
        return None
    return {
        "ticker": str(review.get("ticker") or ""),
        "fact_id": STALE_RR_TRANSITION_FACT_ID,
        "reason": "unavailable_rr_transition_declaration_without_claim",
    }


def _inject_inventory_owner(
    review: dict[str, object],
    stock: Mapping[str, object],
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    context = stock.get("working_capital_user_visible")
    if not isinstance(context, Mapping) or context.get("user_visible_enabled") is not True:
        return None, None
    relation_id = str(context.get("relation_id") or "")
    fact = _fact_catalog(stock).get(relation_id)
    business = _section(review, "business_earnings")
    if (
        not relation_id
        or fact is None
        or fact.get("fact_type") != WORKING_CAPITAL_RELATION_TYPE
        or fact.get("interpretation_eligible") is False
        or business is None
    ):
        return None, {
            "ticker": str(review.get("ticker") or ""),
            "reason": "inventory_relation_context_incomplete",
        }
    refs = review.get("numeric_fact_refs")
    refs = refs if isinstance(refs, list) else []
    if any(
        isinstance(item, Mapping) and str(item.get("fact_id") or "") == relation_id
        for item in refs
    ):
        return None, None
    business_text = str(business.get("text") or "")
    if "재고" in business_text or "inventory" in business_text.lower():
        return None, {
            "ticker": str(review.get("ticker") or ""),
            "reason": "inventory_prose_present_without_unambiguous_numeric_owner",
        }
    family = str(context.get("relation_family") or "")
    direction = str(context.get("direction") or "")
    comparator = {
        "inventory_vs_cogs": "매출원가",
        "inventory_vs_revenue": "매출",
    }.get(family)
    relation_word = {"LOWER": "밑돌았습니다", "GREATER": "웃돌았습니다"}.get(
        direction
    )
    if comparator is None or relation_word is None:
        return None, {
            "ticker": str(review.get("ticker") or ""),
            "reason": "inventory_relation_family_or_direction_unsupported",
        }
    ref_id = "owned_inventory_relation"
    sentence = (
        f"재고 증가율은 {comparator} 증가율을 "
        f"{{{{numeric:{ref_id}}}}} {relation_word}."
    )
    business["text"] = f"{sentence} {business_text}".strip()
    business["fact_ids"] = _append_unique(business.get("fact_ids"), relation_id)
    review["facts_used"] = _append_unique(review.get("facts_used"), relation_id)
    review["numeric_fact_refs"] = [
        *refs,
        {
            "ref_id": ref_id,
            "fact_id": relation_id,
            "field_path": SIGNED_INVENTORY_GAP_FIELD,
            "text_ref": "business_earnings.text",
        },
    ]
    return {
        "ticker": str(review.get("ticker") or ""),
        "relation_id": relation_id,
        "owner": "business_earnings",
        "relation_family": family,
        "reason": "selected_inventory_relation_owner_handoff",
    }, None


def _eligible_fact(
    stock: Mapping[str, object], fact_id: str
) -> Mapping[str, object] | None:
    fact = _fact_catalog(stock).get(fact_id)
    if fact is None or fact.get("interpretation_eligible") is False:
        return None
    return fact


def _inject_valuation_owners(
    review: dict[str, object],
    stock: Mapping[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    valuation = _section(review, "valuation_analysis")
    if valuation is None:
        return [], []
    refs = review.get("numeric_fact_refs")
    refs = refs if isinstance(refs, list) else []
    typed = review.get("valuation_interpretation_refs")
    typed = list(typed) if isinstance(typed, list) else []
    handoffs: list[dict[str, object]] = []
    catalog = _fact_catalog(stock)
    for item in typed:
        if not isinstance(item, dict):
            continue
        fact = catalog.get(str(item.get("fact_id") or ""))
        if (
            item.get("interpretation_type") != "quality_unknown"
            or item.get("basis_status") != "insufficient_metadata"
            or fact is None
            or str(fact.get("valuation_scope") or "unknown") != "unknown"
            or item.get("economic_scope") == "unknown"
        ):
            continue
        item["economic_scope"] = "unknown"
        handoffs.append(
            {
                "ticker": str(review.get("ticker") or ""),
                "ref_id": str(item.get("ref_id") or ""),
                "fact_id": str(item.get("fact_id") or ""),
                "owner": "valuation_analysis",
                "reason": "quality_unknown_scope_normalized_to_canonical_unknown",
            }
        )
    already_owned = {
        str(ref_id)
        for item in typed
        if isinstance(item, Mapping)
        for ref_id in item.get("comparison_numeric_ref_ids", [])
        if isinstance(item.get("comparison_numeric_ref_ids"), list)
    }
    text = str(valuation.get("text") or "")
    unresolved: list[dict[str, object]] = []
    mapped_ref_ids: set[str] = set()
    valuation_ref_ids: set[str] = set()
    for item in refs:
        if not isinstance(item, Mapping) or item.get("text_ref") != "valuation_analysis.text":
            continue
        ref_id = str(item.get("ref_id") or "")
        valuation_ref_ids.add(ref_id)
        if ref_id in already_owned:
            mapped_ref_ids.add(ref_id)
            continue
        mapping = _VALUATION_FACT_BY_FIELD.get(str(item.get("field_path") or ""))
        if mapping is None:
            unresolved.append(
                {
                    "ticker": str(review.get("ticker") or ""),
                    "ref_id": ref_id,
                    "reason": "valuation_numeric_field_has_no_typed_owner_mapping",
                }
            )
            continue
        metric, narrow_fact_id = mapping
        if _eligible_fact(stock, narrow_fact_id) is None:
            unresolved.append(
                {
                    "ticker": str(review.get("ticker") or ""),
                    "ref_id": ref_id,
                    "fact_id": narrow_fact_id,
                    "reason": "valuation_typed_owner_not_eligible",
                }
            )
            continue
        sentence = _placeholder_sentence(text, ref_id)
        if sentence is None:
            unresolved.append(
                {
                    "ticker": str(review.get("ticker") or ""),
                    "ref_id": ref_id,
                    "reason": "valuation_numeric_span_ambiguous",
                }
            )
            continue
        typed.append(
            {
                "ref_id": f"owned_{ref_id}",
                "interpretation_type": "absolute",
                "metric": metric,
                "fact_id": narrow_fact_id,
                "text_ref": "valuation_analysis.text",
                "exact_text_span": sentence,
                "comparison_numeric_ref_ids": [ref_id],
                "direction": "neutral",
            }
        )
        review["facts_used"] = _append_unique(
            review.get("facts_used"), narrow_fact_id
        )
        valuation["fact_ids"] = _append_unique(
            valuation.get("fact_ids"), narrow_fact_id
        )
        mapped_ref_ids.add(ref_id)
        handoffs.append(
            {
                "ticker": str(review.get("ticker") or ""),
                "numeric_ref_id": ref_id,
                "fact_id": narrow_fact_id,
                "owner": "valuation_analysis",
                "reason": "typed_valuation_numeric_owner_handoff",
            }
        )
    if "낮은 피크 이익 배수" in text:
        text = text.replace("낮은 피크 이익 배수", "피크 이익 배수")
        valuation["text"] = text
        handoffs.append(
            {
                "ticker": str(review.get("ticker") or ""),
                "reason": "unsupported_peak_multiple_direction_neutralized",
            }
        )
    unknown_pattern = re.compile(
        r"현재 (?P<us>미국 )?(?P<listing>상장|거래) 증권의 (?:"
        r"주식·통화 denominator가 검증되지 않아 "
        r"per-share valuation 해석을 보류합니다|"
        r"검증 가능한 배수 근거가 없어 .{1,96} 가치평가가 필요합니다)\."
    )
    match = unknown_pattern.fullmatch(text)
    if match is not None and _eligible_fact(stock, "security_basis:current") is not None:
        country = "미국 " if match.group("us") else ""
        text = (
            f"현재 {country}{match.group('listing')} 증권의 주식·통화 기준이 "
            "검증되지 않아 "
            "실적 기반 가치평가 해석을 보류합니다."
        )
        valuation["text"] = text
        typed.append(
            {
                "ref_id": "owned_security_basis_unknown",
                "interpretation_type": "quality_unknown",
                "metric": "earnings",
                "fact_id": "security_basis:current",
                "text_ref": "valuation_analysis.text",
                "exact_text_span": text,
                "comparison_numeric_ref_ids": [],
                "basis_status": "insufficient_metadata",
                "source_type": "canonical_quality_gate",
                "direction": "unknown",
                "economic_scope": "listed_security",
            }
        )
        review["facts_used"] = _append_unique(
            review.get("facts_used"), "security_basis:current"
        )
        valuation["fact_ids"] = _append_unique(
            valuation.get("fact_ids"), "security_basis:current"
        )
        handoffs.append(
            {
                "ticker": str(review.get("ticker") or ""),
                "fact_id": "security_basis:current",
                "owner": "valuation_analysis",
                "reason": "typed_valuation_quality_unknown_handoff",
            }
        )
    aggregate = _fact_catalog(stock).get("valuation:current")
    if (
        aggregate is not None
        and aggregate.get("interpretation_eligible") is False
        and valuation_ref_ids
        and valuation_ref_ids.issubset(mapped_ref_ids)
    ):
        valuation["fact_ids"] = _remove_value(
            valuation.get("fact_ids"), "valuation:current"
        )
        handoffs.append(
            {
                "ticker": str(review.get("ticker") or ""),
                "fact_id": "valuation:current",
                "reason": "mixed_aggregate_interpretation_replaced_by_typed_facts",
            }
        )
    if typed:
        review["valuation_interpretation_refs"] = typed
    return handoffs, unresolved


def _remove_market_authored_numeric_labels(
    packet: Mapping[str, object],
    output: dict[str, object],
) -> list[dict[str, object]]:
    market_context = packet.get("market_context")
    market_review = output.get("market_review")
    if not isinstance(market_context, Mapping) or not isinstance(market_review, dict):
        return []
    registry = {
        (str(item.get("fact_id") or ""), str(item.get("field_path") or "")): item
        for item in market_context.get("numeric_registry", [])
        if isinstance(item, Mapping)
    }
    refs = market_review.get("numeric_fact_refs")
    if not isinstance(refs, list):
        return []
    suppressions: list[dict[str, object]] = []
    for ref in refs:
        if not isinstance(ref, Mapping):
            continue
        source = registry.get(
            (str(ref.get("fact_id") or ""), str(ref.get("field_path") or ""))
        )
        if source is None or source.get("semantic_type") != "market_advance_ratio":
            continue
        ref_id = str(ref.get("ref_id") or "")
        text_ref = str(ref.get("text_ref") or "")
        node = _text_node(market_review, text_ref)
        if node is None:
            continue
        parent, key = node
        text = parent.get(key)
        placeholder = f"{{{{numeric:{ref_id}}}}}"
        if not isinstance(text, str) or text.count(placeholder) != 1:
            continue
        placeholder_start = text.index(placeholder)
        prefix = text[:placeholder_start]
        labels = source.get("approved_labels")
        candidates = sorted(
            (str(label) for label in labels if str(label).strip()),
            key=len,
            reverse=True,
        ) if isinstance(labels, list) else []
        for label in candidates:
            match = re.search(
                rf"{re.escape(label)}(?:은|는|이|가|을|를)?\s*$",
                prefix,
            )
            if match is None:
                continue
            parent[key] = (
                prefix[: match.start()].rstrip()
                + " "
                + text[placeholder_start:]
            ).strip()
            suppressions.append(
                {
                    "scope": "market_review",
                    "ref_id": ref_id,
                    "text_ref": text_ref,
                    "suppressed_label": label,
                    "reason": "canonical_market_numeric_label_ownership",
                }
            )
            break
    return suppressions


def _apply_market_plan_ownership(
    packet: Mapping[str, object], output: dict[str, object]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    market_context = packet.get("market_context")
    market_review = output.get("market_review")
    if not isinstance(market_context, Mapping) or not isinstance(market_review, dict):
        return [], []
    plan = market_context.get("us_market_digest_plan")
    if not isinstance(plan, Mapping) or plan.get("contract") != "us-market-digest-plan-v1":
        return [], []
    section = market_review.get("market_context")
    if not isinstance(section, dict):
        return [], [{"reason": "market_context_owner_missing"}]
    facts_used = market_review.get("facts_used")
    facts_used = list(facts_used) if isinstance(facts_used, list) else []
    text = str(section.get("text") or "")
    handoffs: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    items = plan.get("items")
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, Mapping) or item.get("required_consumption") is not True:
            continue
        claim = str(item.get("claim_text") or "").strip()
        evidence = item.get("evidence_refs")
        evidence = [str(value) for value in evidence] if isinstance(evidence, list) else []
        if not claim or not evidence:
            unresolved.append(
                {
                    "slot": str(item.get("slot") or ""),
                    "reason": "required_market_plan_item_incomplete",
                }
            )
            continue
        if claim not in text:
            text = f"{text} {claim}".strip()
        for fact_id in evidence:
            facts_used = _append_unique(facts_used, fact_id)
            section["fact_ids"] = _append_unique(section.get("fact_ids"), fact_id)
        handoffs.append(
            {
                "slot": str(item.get("slot") or ""),
                "evidence_refs": evidence,
                "owner": "market_context",
                "reason": "canonical_market_plan_owner_handoff",
            }
        )
    section["text"] = text
    market_review["facts_used"] = facts_used
    frameworks = market_review.get("frameworks_used")
    if isinstance(frameworks, list):
        removed = sorted(
            MARKET_ONLY_FRAMEWORK_MISOWNERS.intersection(str(item) for item in frameworks)
        )
        if removed:
            market_review["frameworks_used"] = [
                item for item in frameworks if str(item) not in removed
            ]
            handoffs.extend(
                {
                    "framework": item,
                    "reason": "stock_framework_removed_from_market_owner",
                }
                for item in removed
            )
    return handoffs, unresolved


def _text_node(review: dict[str, object], text_ref: str) -> tuple[dict[str, object], str] | None:
    value: object = review
    parts = text_ref.split(".")
    for raw_part in parts[:-1]:
        match = _PATH_PART.fullmatch(raw_part)
        if match is None or not isinstance(value, dict):
            return None
        value = value.get(match.group(1))
        if match.group(2) is not None:
            if not isinstance(value, list):
                return None
            index = int(match.group(2))
            if index >= len(value):
                return None
            value = value[index]
    terminal = _PATH_PART.fullmatch(parts[-1])
    if terminal is None or terminal.group(2) is not None or not isinstance(value, dict):
        return None
    return value, terminal.group(1)


def _remove_standalone_placeholder_sentence(text: str, ref_id: str) -> str | None:
    placeholder = re.escape(f"{{{{numeric:{ref_id}}}}}")
    pattern = re.compile(
        rf"(?:(?<=^)|(?<=[.!?])\s){placeholder}"
        rf"(?:입니다|이었습니다|였습니다)?[.!?]?(?=\s|$)"
    )
    match = pattern.search(text)
    if match is None:
        list_tail = re.compile(
            rf";\s*{placeholder}(?P<copula>입니다|이었습니다|였습니다)(?P<end>[.!?])"
        )
        tail_match = list_tail.search(text)
        if tail_match is None:
            return None
        return (
            text[: tail_match.start()]
            + tail_match.group("copula")
            + tail_match.group("end")
            + text[tail_match.end() :]
        )
    updated = (text[: match.start()] + text[match.end() :]).strip()
    return re.sub(r"[ \t]{2,}", " ", updated)


def apply_candidate_ownership_contracts(
    packet: Mapping[str, object],
    output_value: object,
) -> tuple[object, dict[str, object]]:
    """Repair unambiguous structured-owner handoffs before strict validation."""
    if not isinstance(output_value, Mapping):
        return output_value, {
            "contract": NUMERIC_PRIMARY_OWNER_CONTRACT,
            "status": "not_applicable",
            "suppressions": [],
            "unresolved": [],
        }
    output = copy.deepcopy(dict(output_value))
    reviews = output.get("stock_reviews")
    if not isinstance(reviews, list):
        return output, {
            "contract": NUMERIC_PRIMARY_OWNER_CONTRACT,
            "status": "not_applicable",
            "suppressions": [],
            "unresolved": [],
        }
    semantics = _registry_semantics(packet)
    stock_packets = _stock_packets(packet)
    suppressions: list[dict[str, object]] = []
    handoffs: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    market_handoffs, market_unresolved = _apply_market_plan_ownership(packet, output)
    suppressions.extend(_remove_market_authored_numeric_labels(packet, output))
    handoffs.extend(market_handoffs)
    unresolved.extend(market_unresolved)
    for review in reviews:
        if not isinstance(review, dict):
            continue
        ticker = str(review.get("ticker") or "")
        stock = stock_packets.get(ticker, {})
        handoffs.extend(_canonicalize_standalone_numeric_sentences(review))
        stale_rr = _remove_stale_rr_transition(review, stock)
        if stale_rr is not None:
            suppressions.append(stale_rr)
        inventory_handoff, inventory_unresolved = _inject_inventory_owner(
            review, stock
        )
        if inventory_handoff is not None:
            handoffs.append(inventory_handoff)
        if inventory_unresolved is not None:
            unresolved.append(inventory_unresolved)
        valuation_handoffs, valuation_unresolved = _inject_valuation_owners(
            review, stock
        )
        handoffs.extend(valuation_handoffs)
        unresolved.extend(valuation_unresolved)
        refs = review.get("numeric_fact_refs")
        if not isinstance(refs, list):
            continue
        rr_refs = [
            item
            for item in refs
            if isinstance(item, dict)
            and semantics.get(ticker, {}).get(
                (
                    str(item.get("fact_id") or ""),
                    str(item.get("field_path") or ""),
                )
            )
            == CURRENT_PRICE_RR_SEMANTIC
        ]
        primary = [
            item
            for item in rr_refs
            if item.get("text_ref") == CURRENT_PRICE_RR_PRIMARY_TEXT_REF
        ]
        if len(primary) != 1:
            if rr_refs:
                unresolved.append(
                    {
                        "ticker": ticker,
                        "reason": "current_rr_primary_owner_missing_or_ambiguous",
                        "occurrence_count": len(rr_refs),
                        "primary_occurrence_count": len(primary),
                    }
                )
            continue
        removed_ids: set[str] = set()
        for item in rr_refs:
            text_ref = str(item.get("text_ref") or "")
            if text_ref == CURRENT_PRICE_RR_PRIMARY_TEXT_REF:
                continue
            ref_id = str(item.get("ref_id") or "")
            node = _text_node(review, text_ref)
            if node is None:
                unresolved.append(
                    {
                        "ticker": ticker,
                        "ref_id": ref_id,
                        "text_ref": text_ref,
                        "reason": "current_rr_secondary_text_ref_unresolved",
                    }
                )
                continue
            parent, key = node
            text = parent.get(key)
            updated = (
                _remove_standalone_placeholder_sentence(text, ref_id)
                if isinstance(text, str)
                else None
            )
            if updated is None:
                unresolved.append(
                    {
                        "ticker": ticker,
                        "ref_id": ref_id,
                        "text_ref": text_ref,
                        "reason": "current_rr_secondary_not_safely_removable",
                    }
                )
                continue
            parent[key] = updated
            removed_ids.add(ref_id)
            suppressions.append(
                {
                    "ticker": ticker,
                    "ref_id": ref_id,
                    "text_ref": text_ref,
                    "primary_text_ref": CURRENT_PRICE_RR_PRIMARY_TEXT_REF,
                    "reason": "current_rr_secondary_exact_occurrence",
                }
            )
        if removed_ids:
            review["numeric_fact_refs"] = [
                item
                for item in refs
                if not isinstance(item, dict)
                or str(item.get("ref_id") or "") not in removed_ids
            ]
    suppressions.extend(_remove_repeated_secondary_prose(reviews))
    return output, {
        "contract": NUMERIC_PRIMARY_OWNER_CONTRACT,
        "status": "passed" if not unresolved else "unresolved",
        "suppressions": suppressions,
        "handoffs": handoffs,
        "unresolved": unresolved,
    }
