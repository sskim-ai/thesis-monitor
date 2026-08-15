from __future__ import annotations

import re
from collections import Counter, defaultdict

from app.schemas.ai_review import AIDailyReviewOutput, AIStockReview


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")
_SPACE = re.compile(r"\s+")
_BULLET_PREFIX = re.compile(r"^[•*-]\s*")

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


def relational_reasoning_quality_report(
    output: AIDailyReviewOutput,
    *,
    duplicate_threshold: int = 3,
) -> dict[str, object]:
    sentence_tickers: dict[str, set[str]] = defaultdict(set)
    for review in output.stock_reviews:
        for sentence in set(_review_sentences(review)):
            sentence_tickers[sentence].add(review.ticker)

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
    return {
        "contract": "relational-reasoning-quality-v1",
        "duplicate_threshold": duplicate_threshold,
        "stock_count": len(output.stock_reviews),
        "repeated_sentences": repeated,
        "substantive_repeated_sentence_count": len(substantive_repeats),
        "max_substantive_repeat": max(
            (int(item["stock_count"]) for item in substantive_repeats),
            default=0,
        ),
        "observer_holder": observer_holder,
        "observer_holder_distinct_count": sum(
            bool(item["distinct"]) for item in observer_holder
        ),
        "section_numeric_grounding": section_grounding,
        "stock_specific_next_check_count": sum(
            count for count in next_check_counts.values() if count < duplicate_threshold
        ),
        "generic_next_check_count": sum(
            count for count in next_check_counts.values() if count >= duplicate_threshold
        ),
        "stock_specific_unknown_count": sum(
            count for count in unknown_counts.values() if count < duplicate_threshold
        ),
        "generic_unknown_count": sum(
            count for count in unknown_counts.values() if count >= duplicate_threshold
        ),
        "hard_checks_passed": all(bool(item["distinct"]) for item in observer_holder),
    }
