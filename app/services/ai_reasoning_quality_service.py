from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Iterable

from app.schemas.ai_review import AIDailyReviewOutput, AIStockReview
from app.services.numeric_provenance_service import (
    canonical_numeric_label_mismatch,
    numeric_conjunction_error,
    redundant_numeric_label_before,
)


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")
_SPACE = re.compile(r"\s+")
_BULLET_PREFIX = re.compile(r"^[•*-]\s*")
_PATH_PART = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[([0-9]+)\])?$")
_US_KR_SUPPLY_HORIZON = re.compile(
    r"(?:\b(?:1|5|20)\s*일(?:간)?\b.{0,24}(?:투자주체|외국인|기관|수급|순매수|순매도)"
    r"|당일.{0,8}단기.{0,8}중기.{0,16}(?:투자주체|수급|순매수|순매도))",
    re.IGNORECASE,
)
_US_INVESTOR_FLOW_UNKNOWN = re.compile(
    r"(?=.*(?:투자주체|외국인|기관))(?=.*(?:수급|순매수|순매도))"
    r"(?=.*(?:없|미확인|unknown)).+",
    re.IGNORECASE,
)
_DEPOSITARY_PROSE = re.compile(r"\b(?:ADR|ADS)\b|예탁증권", re.IGNORECASE)
_COMMON_STOCK_PROSE = re.compile(r"common\s+(?:stock|share)|보통주", re.IGNORECASE)

# These are safety boundaries, not stock analysis. They remain visible in the audit but do not
# count as cross-stock investment boilerplate.
_COMMON_SAFETY_SENTENCES = {
    "수급 공백은 펀더멘털 상태를 바꾸지 않습니다.",
    "차트 무효화는 기업가치 무효화가 아닙니다.",
}


def normalize_decision_text(value: str) -> str:
    normalized = _BULLET_PREFIX.sub("", value.strip())
    return _SPACE.sub(" ", normalized).casefold()


def _sentences(value: str) -> list[str]:
    return [
        normalized
        for part in _SENTENCE_BOUNDARY.split(value)
        if (normalized := normalize_decision_text(part))
    ]


def _review_sentences(review: AIStockReview) -> list[str]:
    values = [
        review.core_judgment.text,
        review.business_earnings.text,
        review.price_positioning.text,
        review.supply_analysis.text,
        review.valuation_analysis.text,
        *review.priority_watch,
        *review.next_checks,
        *review.unknowns,
    ]
    return [sentence for value in values for sentence in _sentences(value)]


def _template_skeleton(review: AIStockReview, sentence: str) -> str:
    skeleton = normalize_decision_text(sentence)
    for claim in review.numeric_claims:
        skeleton = skeleton.replace(normalize_decision_text(claim.usage), "<numeric>")
    return skeleton.replace(review.ticker.casefold(), "<ticker>")


def _structural_template_exception(sentence: str, skeleton: str) -> str | None:
    if skeleton == "<numeric>입니다.":
        return "single_canonical_numeric_statement"
    if (
        "동적 지지구간 하단" in sentence
        and "동적 지지구간 상단" in sentence
    ) or (
        "동적 저항구간 하단" in sentence
        and "동적 저항구간 상단" in sentence
    ):
        return "canonical_zone_endpoint_contract"
    if "현재의 주 지지선이 아니라 등록 당시 전환 기준" in sentence:
        return "registered_rule_not_dynamic_support_safety"
    if all(
        marker in sentence
        for marker in ("당일 외국인", "기관", "최근 흐름", "중기 누적")
    ):
        return "kr_six_horizon_numeric_supply_contract"
    return None


def _claim_section_counts(review: AIStockReview) -> dict[str, int]:
    prefixes = {
        "core": "core_judgment.",
        "earnings": "business_earnings.",
        "price": "price_positioning.",
        "supply": "supply_analysis.",
        "valuation": "valuation_analysis.",
    }
    return {
        section: sum(
            claim.text_ref.startswith(prefix) for claim in review.numeric_claims
        )
        for section, prefix in prefixes.items()
    }


def _text_at_ref(review: dict[str, object], text_ref: str) -> str | None:
    node: object = review
    for raw_part in text_ref.split("."):
        match = _PATH_PART.fullmatch(raw_part)
        if match is None or not isinstance(node, dict):
            return None
        key, list_index = match.groups()
        node = node.get(key)
        if list_index is not None:
            if not isinstance(node, list) or int(list_index) >= len(node):
                return None
            node = node[int(list_index)]
    return node if isinstance(node, str) else None


def _numeric_label_quality_report(
    output: AIDailyReviewOutput,
    packet: dict[str, object] | None,
    binding_errors: Iterable[str],
) -> dict[str, object]:
    details: list[dict[str, str]] = []
    redundant = sum(
        "numeric_fact_ref_redundant_authored_label" in item
        for item in binding_errors
    )
    repeated = 0
    source_mismatch = 0
    instrument_mismatch = 0
    zone_role_mismatch = sum("zone_role_mismatch" in item for item in binding_errors)
    postposition_mismatch = sum(
        "postposition_mismatch" in item for item in binding_errors
    )
    if packet is not None:
        market_context = packet.get("market_context")
        market_registry = (
            market_context.get("numeric_registry", [])
            if isinstance(market_context, dict)
            else []
        )
        stock_packets = {
            str(item.get("ticker") or ""): item
            for item in packet.get("stocks", [])
            if isinstance(item, dict)
        }
        reviews: list[tuple[str, dict[str, object], object]] = [
            ("market_review", output.market_review.model_dump(), market_registry)
        ]
        reviews.extend(
            (
                review.ticker,
                review.model_dump(),
                stock_packets.get(review.ticker, {}).get("numeric_registry", []),
            )
            for review in output.stock_reviews
        )
        for scope, review, registry_value in reviews:
            registry = {
                (str(item.get("fact_id")), str(item.get("field_path"))): item
                for item in registry_value
                if isinstance(item, dict)
            } if isinstance(registry_value, list) else {}
            for claim in review.get("numeric_claims", []):
                if not isinstance(claim, dict):
                    continue
                source = registry.get(
                    (str(claim.get("fact_id")), str(claim.get("field_path")))
                )
                if source is None:
                    continue
                usage = str(claim.get("usage") or "")
                text_ref = str(claim.get("text_ref") or "")
                semantic_type = str(claim.get("semantic_type") or "")
                mismatch = canonical_numeric_label_mismatch(source, usage)
                if mismatch == "source":
                    source_mismatch += 1
                elif mismatch == "instrument":
                    instrument_mismatch += 1
                elif mismatch == "role":
                    zone_role_mismatch += 1
                if mismatch is not None:
                    details.append(
                        {
                            "scope": scope,
                            "text_ref": text_ref,
                            "semantic_type": semantic_type,
                            "issue": f"{mismatch}_label_mismatch",
                        }
                    )
                text = _text_at_ref(review, text_ref)
                start = text.find(usage) if text is not None else -1
                if text is not None and start >= 0 and redundant_numeric_label_before(
                    text,
                    start,
                    source,
                ):
                    redundant += 1
                    repeated += 1
                    details.append(
                        {
                            "scope": scope,
                            "text_ref": text_ref,
                            "semantic_type": semantic_type,
                            "issue": "repeated_bound_label",
                        }
                    )
                if text is not None and numeric_conjunction_error(
                    text,
                    usage,
                    str(source.get("canonical_display_value") or ""),
                ):
                    postposition_mismatch += 1
                    details.append(
                        {
                            "scope": scope,
                            "text_ref": text_ref,
                            "semantic_type": semantic_type,
                            "issue": "postposition_mismatch",
                        }
                    )
    hard_checks_passed = not any(
        (
            redundant,
            repeated,
            source_mismatch,
            instrument_mismatch,
            zone_role_mismatch,
            postposition_mismatch,
        )
    )
    return {
        "redundant_authored_label_count": redundant,
        "repeated_bound_label_count": repeated,
        "source_label_mismatch_count": source_mismatch,
        "instrument_label_mismatch_count": instrument_mismatch,
        "zone_role_mismatch_count": zone_role_mismatch,
        "postposition_mismatch_count": postposition_mismatch,
        "details": details,
        "hard_checks_passed": hard_checks_passed,
    }
def relational_reasoning_quality_report(
    output: AIDailyReviewOutput,
    *,
    duplicate_threshold: int = 3,
    packet: dict[str, object] | None = None,
    binding_errors: Iterable[str] = (),
    validation_errors: Iterable[str] = (),
    rendered_messages: Iterable[str] = (),
) -> dict[str, object]:
    sentence_tickers: dict[str, set[str]] = defaultdict(set)
    for review in output.stock_reviews:
        for sentence in set(_review_sentences(review)):
            sentence_tickers[sentence].add(review.ticker)
    template_tickers: dict[str, set[str]] = defaultdict(set)
    template_exception_reasons: dict[str, dict[str, str]] = defaultdict(dict)
    for review in output.stock_reviews:
        for sentence in set(_review_sentences(review)):
            skeleton = _template_skeleton(review, sentence)
            template_tickers[skeleton].add(review.ticker)
            reason = _structural_template_exception(sentence, skeleton)
            if reason is not None:
                template_exception_reasons[skeleton][review.ticker] = reason

    common_safety = {normalize_decision_text(value) for value in _COMMON_SAFETY_SENTENCES}
    repeated = [
        {
            "sentence": sentence,
            "stock_count": len(tickers),
            "tickers": sorted(tickers),
            "classification": (
                "required_common_safety" if sentence in common_safety else "substantive"
            ),
        }
        for sentence, tickers in sentence_tickers.items()
        if len(tickers) >= duplicate_threshold
    ]
    repeated.sort(key=lambda item: (-int(item["stock_count"]), str(item["sentence"])))

    next_check_counts = Counter(
        normalize_decision_text(item)
        for review in output.stock_reviews
        for item in review.next_checks
        if normalize_decision_text(item)
    )
    unknown_counts = Counter(
        normalize_decision_text(item)
        for review in output.stock_reviews
        for item in review.unknowns
        if normalize_decision_text(item)
    )
    observer_holder = [
        {
            "ticker": review.ticker,
            "distinct": normalize_decision_text(
                review.price_positioning.new_observer_view
            )
            != normalize_decision_text(review.price_positioning.holder_view),
        }
        for review in output.stock_reviews
    ]
    section_grounding = {
        review.ticker: _claim_section_counts(review) for review in output.stock_reviews
    }
    substantive_repeats = [
        item for item in repeated if item["classification"] == "substantive"
    ]
    template_repeats = [
        {
            "skeleton": skeleton,
            "stock_count": len(tickers),
            "tickers": sorted(tickers),
        }
        for skeleton, tickers in template_tickers.items()
        if len(tickers) >= 5
        and skeleton not in common_safety
        and set(template_exception_reasons.get(skeleton, {})) != tickers
    ]
    template_repeats.sort(
        key=lambda item: (-int(item["stock_count"]), str(item["skeleton"]))
    )
    template_exceptions = [
        {
            "skeleton": skeleton,
            "stock_count": len(tickers),
            "tickers": sorted(tickers),
            "reason": next(iter(template_exception_reasons[skeleton].values())),
        }
        for skeleton, tickers in template_tickers.items()
        if len(tickers) >= 5
        and set(template_exception_reasons.get(skeleton, {})) == tickers
    ]
    template_exceptions.sort(
        key=lambda item: (-int(item["stock_count"]), str(item["skeleton"]))
    )
    supply_repeats = [
        item
        for item in substantive_repeats
        if any(
            item["sentence"] in _sentences(review.supply_analysis.text)
            for review in output.stock_reviews
        )
    ]
    us_kr_horizon_rows = (
        [
            {
                "ticker": review.ticker,
                "text": review.supply_analysis.text,
            }
            for review in output.stock_reviews
            if _US_KR_SUPPLY_HORIZON.search(review.supply_analysis.text)
        ]
        if output.market == "us"
        else []
    )
    generic_us_investor_unknown_rows = (
        [
            {
                "ticker": review.ticker,
                "text": review.supply_analysis.text,
            }
            for review in output.stock_reviews
            if _US_INVESTOR_FLOW_UNKNOWN.search(review.supply_analysis.text)
        ]
        if output.market == "us"
        else []
    )
    numeric_label_quality = _numeric_label_quality_report(
        output,
        packet,
        binding_errors,
    )
    supply_numeric_coverage: list[dict[str, object]] = []
    if output.market == "kr" and packet is not None:
        packet_stocks = {
            str(item.get("ticker") or ""): item
            for item in packet.get("stocks", [])
            if isinstance(item, dict)
        }
        supply_semantics = {
            "foreign_net_buy_qty",
            "foreign_net_buy_qty_5d",
            "foreign_net_buy_qty_20d",
            "institution_net_buy_qty",
            "institution_net_buy_qty_5d",
            "institution_net_buy_qty_20d",
        }
        for review in output.stock_reviews:
            stock = packet_stocks.get(review.ticker, {})
            eligible = {
                str(item.get("semantic_type") or "")
                for item in stock.get("numeric_registry", [])
                if isinstance(item, dict)
                and item.get("prose_allowed") is True
                and str(item.get("semantic_type") or "") in supply_semantics
            }
            claimed = {
                claim.semantic_type
                for claim in review.numeric_claims
                if claim.text_ref.startswith("supply_analysis.")
                and claim.semantic_type in supply_semantics
            }
            supply_numeric_coverage.append(
                {
                    "ticker": review.ticker,
                    "eligible_semantics": sorted(eligible),
                    "claimed_semantics": sorted(claimed),
                    "missing_semantics": sorted(eligible - claimed),
                    "numeric_horizon_coverage_passed": not (eligible - claimed),
                }
            )
    validator_error_values = list(validation_errors)
    identity_prose_mismatch_count = sum(
        any(
            marker in item
            for marker in (
                "security_identity_described",
                "security_type_asserted",
                "described_as_depositary",
                "described_as_common_stock",
                "depositary_ratio_described",
            )
        )
        for item in validator_error_values
    )
    unsupported_comparative_count = sum(
        "risk_reward_comparison" in item for item in validator_error_values
    )
    expected_heading = "📊 거래량·포지셔닝" if output.market == "us" else "📊 수급"
    rendered_values = list(rendered_messages)
    heading_mismatches = [
        index
        for index, message in enumerate(rendered_values, start=1)
        if index > 1 and expected_heading not in message
    ]
    rendered_identity_mismatches: list[dict[str, str]] = []
    if packet is not None and rendered_values:
        packet_stocks = {
            str(item.get("ticker") or ""): item
            for item in packet.get("stocks", [])
            if isinstance(item, dict)
        }
        for review, message in zip(
            output.stock_reviews,
            rendered_values[1:],
            strict=False,
        ):
            stock = packet_stocks.get(review.ticker, {})
            valuation = stock.get("valuation", {})
            state = (
                str(valuation.get("security_identity_state") or "unknown")
                if isinstance(valuation, dict)
                else "unknown"
            )
            issue = None
            if state in {"unknown", "conflict"} and (
                _DEPOSITARY_PROSE.search(message) or _COMMON_STOCK_PROSE.search(message)
            ):
                issue = "unverified_security_type_in_rendered_payload"
            elif state == "verified_depositary" and _COMMON_STOCK_PROSE.search(message):
                issue = "depositary_rendered_as_common_stock"
            elif state == "verified_non_depositary" and _DEPOSITARY_PROSE.search(message):
                issue = "non_depositary_rendered_as_depositary"
            if issue is not None:
                rendered_identity_mismatches.append(
                    {"ticker": review.ticker, "identity_state": state, "issue": issue}
                )
    generic_next_check_count = sum(
        count for count in next_check_counts.values() if count >= duplicate_threshold
    )
    generic_unknown_count = sum(
        count for count in unknown_counts.values() if count >= duplicate_threshold
    )
    hard_checks_passed = (
        all(bool(item["distinct"]) for item in observer_holder)
        and bool(numeric_label_quality["hard_checks_passed"])
        and not substantive_repeats
        and not template_repeats
        and not supply_repeats
        and not us_kr_horizon_rows
        and len(generic_us_investor_unknown_rows) < duplicate_threshold
        and generic_next_check_count == 0
        and generic_unknown_count == 0
        and all(
            bool(item["numeric_horizon_coverage_passed"])
            for item in supply_numeric_coverage
        )
        and identity_prose_mismatch_count == 0
        and unsupported_comparative_count == 0
        and not heading_mismatches
        and not rendered_identity_mismatches
    )
    return {
        "contract": "relational-reasoning-quality-v2",
        "duplicate_threshold": duplicate_threshold,
        "stock_count": len(output.stock_reviews),
        "repeated_sentences": repeated,
        "substantive_repeated_sentence_count": len(substantive_repeats),
        "max_substantive_repeat": max(
            (int(item["stock_count"]) for item in substantive_repeats),
            default=0,
        ),
        "template_skeleton_repeats": template_repeats,
        "template_skeleton_repeat_count": len(template_repeats),
        "template_skeleton_exceptions": template_exceptions,
        "observer_holder": observer_holder,
        "observer_holder_distinct_count": sum(
            bool(item["distinct"]) for item in observer_holder
        ),
        "section_numeric_grounding": section_grounding,
        "stock_specific_next_check_count": sum(
            count for count in next_check_counts.values() if count < duplicate_threshold
        ),
        "generic_next_check_count": generic_next_check_count,
        "stock_specific_unknown_count": sum(
            count for count in unknown_counts.values() if count < duplicate_threshold
        ),
        "generic_unknown_count": generic_unknown_count,
        "supply_routing": {
            "substantive_repeated_supply_sentence_count": len(supply_repeats),
            "us_kr_style_horizon_count": len(us_kr_horizon_rows),
            "generic_us_investor_flow_unknown_count": len(
                generic_us_investor_unknown_rows
            ),
            "us_kr_style_horizon_rows": us_kr_horizon_rows,
            "generic_us_investor_flow_unknown_rows": (
                generic_us_investor_unknown_rows
            ),
        },
        "numeric_label_quality": numeric_label_quality,
        "kr_supply_numeric_coverage": supply_numeric_coverage,
        "identity_prose_mismatch_count": identity_prose_mismatch_count,
        "unsupported_comparative_claim_count": unsupported_comparative_count,
        "rendered_heading_quality": {
            "expected_heading": expected_heading,
            "mismatch_count": len(heading_mismatches),
            "message_indexes": heading_mismatches,
        },
        "rendered_identity_prose_mismatches": rendered_identity_mismatches,
        "rendered_identity_prose_mismatch_count": len(
            rendered_identity_mismatches
        ),
        "hard_checks_passed": hard_checks_passed,
        "deterministic_quality_gate_passed": hard_checks_passed,
        "production_assist_evidence_eligible": False,
        "human_quality_approval_required": True,
    }
