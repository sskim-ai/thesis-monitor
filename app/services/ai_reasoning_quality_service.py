from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
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
_US_GENERIC_SUPPLY = re.compile(
    r"(?:수급(?:\s*(?:부재|공백|우호|약화|강화|개선|악화))?"
    r"|매수\s*주체|공동\s*(?:매수|매도)|외국인|기관|개인|순매수|순매도)",
    re.IGNORECASE,
)
_VARIABLE_NUMBER = re.compile(
    r"(?<![A-Za-z0-9_])[-+]?\d[\d,]*(?:\.\d+)?(?:%|bp|배|원|억원|조원|주)?"
)
_VARIABLE_DATE = re.compile(r"\b20\d{2}(?:[-./년]\d{1,2})?(?:[-./월]\d{1,2})?일?\b")
_DEPOSITARY_PROSE = re.compile(r"\b(?:ADR|ADS)\b|예탁증권", re.IGNORECASE)
_COMMON_STOCK_PROSE = re.compile(r"common\s+(?:stock|share)|보통주", re.IGNORECASE)
_RENDERED_DUPLICATE_LABEL = re.compile(
    r"현재가\s+현재가\s*기준|차트\s*손익비\s+차트\s*손익비",
    re.IGNORECASE,
)
_RENDERED_PRICE_PARTICLE = re.compile(
    r"(?:현재가|차트\s*무효화\s*가격)\s+"
    r"(?:(?:US\$|NT\$|\$)\s*\d[\d,]*(?:\.\d+)?"
    r"|(?:₩)?\s*\d[\d,]*(?:\.\d+)?(?:원)?)"
    r"(?:은|는|이|가|을|를|와|과)(?=$|[\s,.!?;:)])",
    re.IGNORECASE,
)
_RENDERED_INTERNAL_LEXICON = re.compile(
    r"(?:엔진이\s*(?:계산한|선택한|가장\s*가까운\s*적격\s*저항을\s*쓴)|"
    r"\bbinder\b|\bvalidator\b|numeric\s*registry|canonical\s*semantic|"
    r"\bplaceholder\b)",
    re.IGNORECASE,
)
_KOREAN_PARTICLE = re.compile(
    r"(?P<term>[가-힣]+|[A-Za-z][A-Za-z0-9]*)"
    r"(?P<particle>을|를)"
    r"(?=$|[\s,.;:!?)}\]])"
)
_MALFORMED_ACTOR_FLOW = re.compile(
    r"(?:외국인|기관).{0,24}순(?:매수|매도)\s+"
    r"[-+]?\d[\d,]*(?:\.\d+)?주(?:은|는|이|가|을|를)"
    r"(?=$|\s*[,.;!?])"
)
_INCOMPLETE_PARTICLE_PREDICATE = re.compile(r"(?:은|는|이|가|을|를|와|과)\s*[.!?](?:\s|$)")
_EVENT_ORIENTED_CHECK = re.compile(
    r"(?:다음|향후|차기|공식\s*(?:실적|공시|자료|발표)|"
    r"실적\s*(?:발표|공시)|공시에서|발표에서)"
)
_CHECK_WORDS = re.compile(
    r"(?:확인(?:합니다|되는지|할지|해야\s*합니다)?|점검(?:합니다)?|"
    r"검증(?:합니다|되는지)?|봅니다|판단합니다)"
)
_GENERIC_NUMERIC_SUMMARY = re.compile(
    r"^(?:현재\s*)?(?:확인된|판단의)?\s*(?:핵심|중요|주요)\s*"
    r"(?:숫자|수치|지표)(?:는|은)\b",
    re.IGNORECASE,
)

_SECTION_OWNERS = {
    "core_judgment": "decision_summary",
    "business_earnings": "business_earnings",
    "price_positioning": "price_context",
    "supply_analysis": "positioning",
    "valuation_analysis": "valuation",
    "priority_watch": "industry_driver",
    "next_checks": "next_check",
    "unknowns": "unknown",
}
_RR_SEMANTICS = {"previous_risk_reward_ratio", "current_risk_reward_ratio"}
_CURRENT_PRICE_RR_SEMANTIC = "current_price_risk_reward_ratio"
_PBR_HISTORY_SEMANTICS = {"price_to_book", "historical_pb_percentile"}
_CANONICAL_KR_SUPPLY_PAIRS = {
    frozenset({"foreign_net_buy_qty", "institution_net_buy_qty"}): "1d",
    frozenset({"foreign_net_buy_qty_5d", "institution_net_buy_qty_5d"}): "5d",
    frozenset({"foreign_net_buy_qty_20d", "institution_net_buy_qty_20d"}): "20d",
}
_VALUATION_ONLY_BUSINESS_SEMANTICS = {
    "bvps",
    "forward_pe",
    "historical_pb_percentile",
    "historical_pe_percentile",
    "price_to_book",
    "trailing_pe",
}

# Preferred Korean usage for canonical finance and industry abbreviations. Unknown Latin
# words are not guessed because their spoken Korean ending is not deterministic.
_LATIN_FINAL_CONSONANT = {
    "asp": False,
    "capex": False,
    "fcf": False,
    "hbm": True,
    "ocf": False,
    "pbr": True,
    "per": True,
    "roe": False,
    "rr": True,
    "runway": False,
}
_PARTICLE_BY_FINAL = {
    "은/는": ("은", "는"),
    "이/가": ("이", "가"),
    "을/를": ("을", "를"),
    "와/과": ("과", "와"),
}

# These are safety boundaries, not stock analysis. They remain visible in the audit but do not
# count as cross-stock investment boilerplate.
_COMMON_SAFETY_SENTENCES = {
    "수급 공백은 펀더멘털 상태를 바꾸지 않습니다.",
    "차트 무효화는 기업가치 무효화가 아닙니다.",
}

_GENERIC_METHODOLOGY_FAMILIES = {
    "registered_rule_methodology": re.compile(
        r"(?:자동\s*지지.{0,12}승격|과거\s*가격\s*규칙.{0,24}동적\s*지지)",
        re.IGNORECASE,
    ),
    "supply_separation_methodology": re.compile(
        r"(?:사업\s*논리|펀더멘털).{0,20}분리.{0,12}(?:해석|판단|봅니다?)",
        re.IGNORECASE,
    ),
    "cash_conversion_checklist": re.compile(
        r"^(?:영업현금흐름.{0,12}설비투자.{0,12}잉여현금흐름.{0,20}"
        r"이익의\s*현금전환.{0,12}(?:확인|판단)|"
        r"\bocf\b.{0,12}\bcapex\b.{0,12}\bfcf\b.{0,20}(?:확인|판단))",
        re.IGNORECASE,
    ),
    "price_not_company_value_methodology": re.compile(
        r"가격\s*구조.{0,24}기업가치\s*변화.{0,12}(?:아니|아닙)",
        re.IGNORECASE,
    ),
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
    return [sentence for _, sentence in _review_sentence_rows(review)]


def _review_sentence_rows(review: AIStockReview) -> list[tuple[str, str]]:
    values = {
        "core_judgment.text": review.core_judgment.text,
        "business_earnings.text": review.business_earnings.text,
        "price_positioning.text": review.price_positioning.text,
        "price_positioning.new_observer_view": (review.price_positioning.new_observer_view),
        "price_positioning.holder_view": review.price_positioning.holder_view,
        "supply_analysis.text": review.supply_analysis.text,
        "valuation_analysis.text": review.valuation_analysis.text,
        **{f"priority_watch[{index}]": value for index, value in enumerate(review.priority_watch)},
        **{f"next_checks[{index}]": value for index, value in enumerate(review.next_checks)},
        **{f"unknowns[{index}]": value for index, value in enumerate(review.unknowns)},
    }
    return [
        (text_ref, sentence) for text_ref, value in values.items() for sentence in _sentences(value)
    ]


def _claims_for_sentence(
    review: AIStockReview,
    text_ref: str,
    sentence: str,
) -> list[object]:
    return [
        claim
        for claim in review.numeric_claims
        if claim.text_ref == text_ref and normalize_decision_text(claim.usage) in sentence
    ]


def _semantic_relation(semantic_types: set[str]) -> str:
    if _RR_SEMANTICS.issubset(semantic_types):
        return "previous_to_current"
    if _PBR_HISTORY_SEMANTICS.issubset(semantic_types):
        return "current_to_historical_percentile"
    if {"revenue", "operating_margin"}.issubset(semantic_types):
        return "revenue_to_operating_margin"
    if len(semantic_types) == 1:
        return "single_metric"
    if semantic_types:
        return "metric_set"
    return "no_numeric_relation"


def _typed_template_identity(
    review: AIStockReview,
    text_ref: str,
    sentence: str,
    skeleton: str,
) -> tuple[tuple[object, ...], dict[str, object]]:
    claims = _claims_for_sentence(review, text_ref, sentence)
    semantic_types = {str(claim.semantic_type) for claim in claims}
    section = text_ref.split(".", 1)[0].split("[", 1)[0]
    owner = _SECTION_OWNERS.get(section, "unknown")
    if _RR_SEMANTICS.intersection(semantic_types):
        owner = "price_context"
    relation = _semantic_relation(semantic_types)
    identity = (
        section,
        owner,
        tuple(sorted(semantic_types)),
        relation,
        skeleton,
    )
    return identity, {
        "section": section,
        "owner": owner,
        "semantic_types": sorted(semantic_types),
        "relation": relation,
        "skeleton": skeleton,
    }


def _business_numeric_ownership_report(
    output: AIDailyReviewOutput,
) -> dict[str, object]:
    violations: list[dict[str, str]] = []
    for review in output.stock_reviews:
        for claim in review.numeric_claims:
            if not claim.text_ref.startswith("business_earnings."):
                continue
            valuation_owned = claim.semantic_type in _VALUATION_ONLY_BUSINESS_SEMANTICS
            valuation_denominator_eps = (
                claim.semantic_type == "ttm_eps" and claim.fact_id.startswith("valuation:")
            )
            if valuation_owned or valuation_denominator_eps:
                violations.append(
                    {
                        "ticker": review.ticker,
                        "text_ref": claim.text_ref,
                        "fact_id": claim.fact_id,
                        "field_path": claim.field_path,
                        "semantic_type": claim.semantic_type,
                        "reason": (
                            "valuation_denominator_used_as_business_filler"
                            if valuation_denominator_eps
                            else "valuation_owned_metric_used_as_business_filler"
                        ),
                    }
                )
    return {
        "contract": "numeric-summary-ownership-v1",
        "business_earnings_violation_count": len(violations),
        "business_earnings_violations": violations,
        "hard_checks_passed": not violations,
    }


def _template_skeleton(
    review: AIStockReview,
    sentence: str,
    company_name: str = "",
) -> str:
    skeleton = normalize_decision_text(sentence)
    for claim in review.numeric_claims:
        skeleton = skeleton.replace(normalize_decision_text(claim.usage), "<numeric>")
    skeleton = skeleton.replace(review.ticker.casefold(), "<ticker>")
    if company_name.strip():
        skeleton = skeleton.replace(company_name.strip().casefold(), "<company>")
    skeleton = _VARIABLE_DATE.sub("<date>", skeleton)
    skeleton = _VARIABLE_NUMBER.sub("<numeric>", skeleton)
    return _SPACE.sub(" ", skeleton).strip()


def _structural_template_exception(sentence: str, skeleton: str) -> str | None:
    if skeleton == "<numeric>입니다.":
        return "single_canonical_numeric_statement"
    if skeleton in {
        "<numeric> 이익 기준의 절대 배수입니다.",
        "<numeric>는 이익 기준의 절대 배수입니다.",
        "<numeric> 장부가 기준의 절대 배수입니다.",
        "<numeric>는 장부가 기준의 절대 배수입니다.",
        "<numeric> 시장 예상 이익의 절대 배수입니다.",
        "<numeric>는 시장 예상 이익의 절대 배수입니다.",
        "<numeric> 현재 이익 기준의 절대 배수입니다.",
        "<numeric> 현재 장부가 기준의 절대 배수입니다.",
        "<numeric> 현재 시장 예상 이익의 절대 배수입니다.",
    }:
        return "typed_neutral_absolute_valuation_statement"
    if sentence.startswith("현재가 ") and skeleton == "<numeric> 수준입니다.":
        return "canonical_current_price_statement"
    if ("동적 지지구간 하단" in sentence and "동적 지지구간 상단" in sentence) or (
        "동적 저항구간 하단" in sentence and "동적 저항구간 상단" in sentence
    ):
        return "canonical_zone_endpoint_contract"
    if "현재의 주 지지선이 아니라 등록 당시 전환 기준" in sentence:
        return "registered_rule_not_dynamic_support_safety"
    if all(marker in sentence for marker in ("당일 외국인", "기관", "최근 흐름", "중기 누적")):
        return "kr_six_horizon_numeric_supply_contract"
    if "외국인" in sentence and "기관" in sentence and skeleton == "<numeric>, <numeric>.":
        return "kr_actor_horizon_numeric_pair"
    if "차트 무효화 가격" in sentence and "사업 논리 무효화가 아니다" in sentence:
        return "chart_vs_thesis_invalidation_safety"
    if "가장 가까운 적격 저항" in sentence and "차트 손익비" in sentence:
        return "canonical_nearest_resistance_rr_contract"
    if skeleton == "현재가 손익비는 필요한 동적 구조가 완성되지 않아 제공되지 않습니다.":
        return "canonical_current_price_rr_unavailable_state"
    return None


def _common_stock_identity_asserted(message: str) -> bool:
    for sentence in re.split(r"(?<=[.!?])\s+|\n", message):
        if _COMMON_STOCK_PROSE.search(sentence) is None:
            continue
        underlying_ratio_context = bool(
            _DEPOSITARY_PROSE.search(sentence)
            and re.search(
                r"(?:=|당|기초|underlying|구조)",
                sentence,
                flags=re.IGNORECASE,
            )
        )
        if not underlying_ratio_context:
            return True
    return False


def _typed_structural_template_exception(
    metadata: dict[str, object],
) -> str | None:
    semantic_types = frozenset(str(value) for value in metadata["semantic_types"])
    if (
        metadata["section"] == "supply_analysis"
        and metadata["owner"] == "positioning"
        and metadata["relation"] == "metric_set"
        and semantic_types in _CANONICAL_KR_SUPPLY_PAIRS
    ):
        return "canonical_supply_flow_tuple_v1"
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
        section: sum(claim.text_ref.startswith(prefix) for claim in review.numeric_claims)
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
    redundant = sum("numeric_fact_ref_redundant_authored_label" in item for item in binding_errors)
    repeated = 0
    source_mismatch = 0
    instrument_mismatch = 0
    period_mismatch = 0
    zone_role_mismatch = sum("zone_role_mismatch" in item for item in binding_errors)
    postposition_mismatch = sum("postposition_mismatch" in item for item in binding_errors)
    if packet is not None:
        market_context = packet.get("market_context")
        market_registry = (
            market_context.get("numeric_registry", []) if isinstance(market_context, dict) else []
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
            registry = (
                {
                    (str(item.get("fact_id")), str(item.get("field_path"))): item
                    for item in registry_value
                    if isinstance(item, dict)
                }
                if isinstance(registry_value, list)
                else {}
            )
            for claim in review.get("numeric_claims", []):
                if not isinstance(claim, dict):
                    continue
                source = registry.get((str(claim.get("fact_id")), str(claim.get("field_path"))))
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
                elif mismatch == "period":
                    period_mismatch += 1
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
                if (
                    text is not None
                    and start >= 0
                    and redundant_numeric_label_before(
                        text,
                        start,
                        source,
                    )
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
            period_mismatch,
            zone_role_mismatch,
            postposition_mismatch,
        )
    )
    return {
        "redundant_authored_label_count": redundant,
        "repeated_bound_label_count": repeated,
        "source_label_mismatch_count": source_mismatch,
        "instrument_label_mismatch_count": instrument_mismatch,
        "period_label_mismatch_count": period_mismatch,
        "zone_role_mismatch_count": zone_role_mismatch,
        "postposition_mismatch_count": postposition_mismatch,
        "details": details,
        "hard_checks_passed": hard_checks_passed,
    }


def _term_has_final_consonant(term: str) -> bool | None:
    if not term:
        return None
    last = term[-1]
    if "가" <= last <= "힣":
        return (ord(last) - ord("가")) % 28 != 0
    return _LATIN_FINAL_CONSONANT.get(term.casefold())


def _expected_particle(term: str, particle: str) -> str | None:
    has_final = _term_has_final_consonant(term)
    if has_final is None:
        return None
    for family, choices in _PARTICLE_BY_FINAL.items():
        if particle in choices:
            return choices[0] if has_final else choices[1]
    return None


def _watch_next_overlap_report(output: AIDailyReviewOutput) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for review in output.stock_reviews:
        for watch_index, watch in enumerate(review.priority_watch):
            watch_normalized = normalize_decision_text(watch)
            watch_event_oriented = bool(_EVENT_ORIENTED_CHECK.search(watch))
            watch_core = normalize_decision_text(
                _CHECK_WORDS.sub("", _EVENT_ORIENTED_CHECK.sub("", watch))
            ).strip(" .,;:")
            for next_index, next_check in enumerate(review.next_checks):
                next_normalized = normalize_decision_text(next_check)
                next_event_oriented = bool(_EVENT_ORIENTED_CHECK.search(next_check))
                next_core = normalize_decision_text(
                    _CHECK_WORDS.sub("", _EVENT_ORIENTED_CHECK.sub("", next_check))
                ).strip(" .,;:")
                exact = watch_normalized == next_normalized
                semantic_same = bool(
                    watch_core
                    and next_core
                    and (
                        watch_core == next_core
                        or watch_core in next_core
                        or next_core in watch_core
                    )
                )
                role_violation = watch_event_oriented
                meaningless_overlap = (
                    exact or role_violation or (semantic_same and not next_event_oriented)
                )
                if meaningless_overlap or semantic_same:
                    rows.append(
                        {
                            "ticker": review.ticker,
                            "watch_index": watch_index,
                            "next_check_index": next_index,
                            "watch": watch,
                            "next_check": next_check,
                            "exact": exact,
                            "semantic_same": semantic_same,
                            "watch_event_oriented": watch_event_oriented,
                            "next_check_event_oriented": next_event_oriented,
                            "meaningless_overlap": meaningless_overlap,
                        }
                    )
    failures = [item for item in rows if item["meaningless_overlap"] is True]
    return {
        "rows": rows,
        "exact_overlap_count": sum(bool(item["exact"]) for item in rows),
        "semantic_overlap_count": sum(bool(item["semantic_same"]) for item in rows),
        "watch_role_violation_count": sum(bool(item["watch_event_oriented"]) for item in rows),
        "meaningless_overlap_count": len(failures),
        "hard_checks_passed": not failures,
    }


def _numeric_fact_repetition_report(output: AIDailyReviewOutput) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for review in output.stock_reviews:
        claims: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for claim in review.numeric_claims:
            claims[(claim.fact_id, claim.field_path)].append(
                {
                    "text_ref": claim.text_ref,
                    "usage": claim.usage,
                    "semantic_type": claim.semantic_type,
                }
            )
        for (fact_id, field_path), occurrences in claims.items():
            if len(occurrences) < 3:
                continue
            rows.append(
                {
                    "ticker": review.ticker,
                    "fact_id": fact_id,
                    "field_path": field_path,
                    "occurrence_count": len(occurrences),
                    "occurrences": occurrences,
                }
            )
    return {
        "rows": rows,
        "same_fact_three_or_more_count": len(rows),
        "hard_checks_passed": not rows,
    }


def _numeric_primary_ownership_report(
    output: AIDailyReviewOutput,
) -> dict[str, object]:
    violations: list[dict[str, object]] = []
    for review in output.stock_reviews:
        claims = [
            claim
            for claim in review.numeric_claims
            if claim.semantic_type == _CURRENT_PRICE_RR_SEMANTIC
        ]
        invalid = [
            {
                "text_ref": claim.text_ref,
                "fact_id": claim.fact_id,
                "field_path": claim.field_path,
                "usage": claim.usage,
            }
            for claim in claims
            if claim.text_ref != "price_positioning.text"
        ]
        if invalid or len(claims) > 1:
            violations.append(
                {
                    "ticker": review.ticker,
                    "semantic_type": _CURRENT_PRICE_RR_SEMANTIC,
                    "primary_owner": "price_context",
                    "primary_text_ref": "price_positioning.text",
                    "occurrence_count": len(claims),
                    "invalid_occurrences": invalid,
                    "reason": (
                        "current_rr_outside_primary_owner"
                        if invalid
                        else "current_rr_exact_value_repeated"
                    ),
                }
            )
    return {
        "contract": "numeric-primary-owner-v1",
        "current_rr_primary_owner": "price_context",
        "current_rr_primary_text_ref": "price_positioning.text",
        "current_rr_violation_count": len(violations),
        "current_rr_violations": violations,
        "hard_checks_passed": not violations,
    }


def _final_rendered_language_report(messages: Iterable[str]) -> dict[str, object]:
    details: list[dict[str, object]] = []
    counts = {
        "duplicate_canonical_label_count": 0,
        "price_particle_error_count": 0,
        "internal_implementation_term_count": 0,
        "korean_particle_error_count": 0,
        "malformed_actor_flow_count": 0,
        "incomplete_predicate_count": 0,
    }
    for index, message in enumerate(messages, start=1):
        checks = (
            ("duplicate_canonical_label", _RENDERED_DUPLICATE_LABEL),
            ("price_particle_error", _RENDERED_PRICE_PARTICLE),
            ("internal_implementation_term", _RENDERED_INTERNAL_LEXICON),
        )
        for issue, pattern in checks:
            matches = [match.group(0) for match in pattern.finditer(message)]
            if not matches:
                continue
            counts[f"{issue}_count"] += len(matches)
            details.append({"message_index": index, "issue": issue, "matches": matches})
        particle_matches = []
        for match in _KOREAN_PARTICLE.finditer(message):
            term = match.group("term")
            particle = match.group("particle")
            expected = _expected_particle(term, particle)
            if expected is not None and expected != particle:
                particle_matches.append(
                    {
                        "text": match.group(0),
                        "term": term,
                        "actual": particle,
                        "expected": expected,
                    }
                )
        if particle_matches:
            counts["korean_particle_error_count"] += len(particle_matches)
            details.append(
                {
                    "message_index": index,
                    "issue": "korean_particle_error",
                    "matches": particle_matches,
                }
            )
        malformed_actor_flow = [match.group(0) for match in _MALFORMED_ACTOR_FLOW.finditer(message)]
        if malformed_actor_flow:
            counts["malformed_actor_flow_count"] += len(malformed_actor_flow)
            details.append(
                {
                    "message_index": index,
                    "issue": "malformed_actor_flow",
                    "matches": malformed_actor_flow,
                }
            )
        incomplete_predicates = [
            match.group(0) for match in _INCOMPLETE_PARTICLE_PREDICATE.finditer(message)
        ]
        if incomplete_predicates:
            counts["incomplete_predicate_count"] += len(incomplete_predicates)
            details.append(
                {
                    "message_index": index,
                    "issue": "incomplete_predicate",
                    "matches": incomplete_predicates,
                }
            )
    return {
        **counts,
        "details": details,
        "hard_checks_passed": not any(counts.values()),
    }


def relational_reasoning_quality_report(
    output: AIDailyReviewOutput,
    *,
    duplicate_threshold: int = 3,
    packet: dict[str, object] | None = None,
    binding_errors: Iterable[str] = (),
    validation_errors: Iterable[str] = (),
    rendered_messages: Iterable[str] = (),
    expected_stock_tickers: Iterable[str] | None = None,
) -> dict[str, object]:
    packet_stocks = {
        str(item.get("ticker") or ""): item
        for item in (packet or {}).get("stocks", [])
        if isinstance(item, dict)
    }
    sentence_tickers: dict[str, set[str]] = defaultdict(set)
    for review in output.stock_reviews:
        for sentence in set(_review_sentences(review)):
            sentence_tickers[sentence].add(review.ticker)
    template_tickers: dict[tuple[object, ...], set[str]] = defaultdict(set)
    template_metadata: dict[tuple[object, ...], dict[str, object]] = {}
    template_exception_reasons: dict[tuple[object, ...], dict[str, str]] = defaultdict(dict)
    sentence_exception_reasons: dict[str, dict[str, str]] = defaultdict(dict)
    generic_numeric_summary_matches: list[dict[str, object]] = []
    for review in output.stock_reviews:
        stock = packet_stocks.get(review.ticker, {})
        company_name = str(
            stock.get("company_name") or stock.get("name") or stock.get("company") or ""
        )
        for text_ref, sentence in set(_review_sentence_rows(review)):
            skeleton = _template_skeleton(review, sentence, company_name)
            typed_key, typed_metadata = _typed_template_identity(
                review,
                text_ref,
                sentence,
                skeleton,
            )
            template_tickers[typed_key].add(review.ticker)
            template_metadata[typed_key] = typed_metadata
            reason = _typed_structural_template_exception(
                typed_metadata
            ) or _structural_template_exception(sentence, skeleton)
            if reason is not None:
                template_exception_reasons[typed_key][review.ticker] = reason
                sentence_exception_reasons[sentence][review.ticker] = reason
            if text_ref == "business_earnings.text" and _GENERIC_NUMERIC_SUMMARY.search(sentence):
                generic_numeric_summary_matches.append(
                    {
                        "ticker": review.ticker,
                        "text_ref": text_ref,
                        "sentence": sentence,
                        "semantic_types": typed_metadata["semantic_types"],
                    }
                )

    common_safety = {normalize_decision_text(value) for value in _COMMON_SAFETY_SENTENCES}
    repeated = [
        {
            "sentence": sentence,
            "stock_count": len(tickers),
            "tickers": sorted(tickers),
            "classification": (
                "required_common_safety"
                if sentence in common_safety
                else "required_structural_safety"
                if set(sentence_exception_reasons.get(sentence, {})) == tickers
                else "substantive"
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
            "distinct": normalize_decision_text(review.price_positioning.new_observer_view)
            != normalize_decision_text(review.price_positioning.holder_view),
        }
        for review in output.stock_reviews
    ]
    section_grounding = {
        review.ticker: _claim_section_counts(review) for review in output.stock_reviews
    }
    substantive_repeats = [item for item in repeated if item["classification"] == "substantive"]
    template_repeats = [
        {
            **template_metadata[typed_key],
            "typed_skeleton": "|".join(
                [
                    str(template_metadata[typed_key]["section"]),
                    str(template_metadata[typed_key]["owner"]),
                    str(template_metadata[typed_key]["relation"]),
                    str(template_metadata[typed_key]["skeleton"]),
                ]
            ),
            "stock_count": len(tickers),
            "tickers": sorted(tickers),
        }
        for typed_key, tickers in template_tickers.items()
        if len(tickers) >= duplicate_threshold
        and str(template_metadata[typed_key]["skeleton"]) not in common_safety
        and set(template_exception_reasons.get(typed_key, {})) != tickers
    ]
    template_repeats.sort(key=lambda item: (-int(item["stock_count"]), str(item["skeleton"])))
    methodology_rows: list[dict[str, object]] = []
    for family, pattern in _GENERIC_METHODOLOGY_FAMILIES.items():
        matches = [
            {
                "ticker": review.ticker,
                "sentences": sorted(
                    {sentence for sentence in _review_sentences(review) if pattern.search(sentence)}
                ),
            }
            for review in output.stock_reviews
            if any(pattern.search(sentence) for sentence in _review_sentences(review))
        ]
        if matches:
            methodology_rows.append(
                {
                    "family": family,
                    "stock_count": len(matches),
                    "matches": matches,
                    "repeated": len(matches) >= duplicate_threshold,
                }
            )
    repeated_methodology = [item for item in methodology_rows if item["repeated"] is True]
    template_exceptions = [
        {
            **template_metadata[typed_key],
            "stock_count": len(tickers),
            "tickers": sorted(tickers),
            "reason": next(iter(template_exception_reasons[typed_key].values())),
        }
        for typed_key, tickers in template_tickers.items()
        if len(tickers) >= duplicate_threshold
        and set(template_exception_reasons.get(typed_key, {})) == tickers
    ]
    template_exceptions.sort(key=lambda item: (-int(item["stock_count"]), str(item["skeleton"])))
    generic_numeric_summary_families = []
    if generic_numeric_summary_matches:
        tickers = sorted({str(item["ticker"]) for item in generic_numeric_summary_matches})
        generic_numeric_summary_families.append(
            {
                "family": "business_earnings_generic_numeric_summary",
                "stock_count": len(tickers),
                "tickers": tickers,
                "matches": generic_numeric_summary_matches,
                "repeated": len(tickers) >= duplicate_threshold,
            }
        )
    repeated_numeric_summary_families = [
        item for item in generic_numeric_summary_families if item["repeated"] is True
    ]
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
    generic_us_supply_rows = (
        [
            {
                "ticker": review.ticker,
                "text_ref": text_ref,
                "text": text,
            }
            for review in output.stock_reviews
            for text_ref, text in {
                "core_judgment.text": review.core_judgment.text,
                "business_earnings.text": review.business_earnings.text,
                "price_positioning.text": review.price_positioning.text,
                "price_positioning.new_observer_view": (review.price_positioning.new_observer_view),
                "price_positioning.holder_view": review.price_positioning.holder_view,
                "supply_analysis.text": review.supply_analysis.text,
                "valuation_analysis.text": review.valuation_analysis.text,
                **{
                    f"priority_watch[{index}]": text
                    for index, text in enumerate(review.priority_watch)
                },
                **{f"next_checks[{index}]": text for index, text in enumerate(review.next_checks)},
                **{f"unknowns[{index}]": text for index, text in enumerate(review.unknowns)},
            }.items()
            if _US_GENERIC_SUPPLY.search(text)
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
    supply_grounding_error_count = sum(
        "kr_supply_" in item or "us_investor_flow_not_in_packet" in item
        for item in validator_error_values
    )
    financial_period_error_count = sum(
        "financial_period_label_missing" in item for item in validator_error_values
    )
    valuation_evidence_error_count = sum(
        any(
            marker in item
            for marker in (
                "negative_book_interpretation",
                "historical_valuation_interpretation",
                "peer_valuation_interpretation",
                "valuation_coherence",
            )
        )
        for item in validator_error_values
    )
    expected_heading = "📊 거래량·포지셔닝" if output.market == "us" else "📊 수급"
    rendered_values = list(rendered_messages)
    final_rendered_language = _final_rendered_language_report(rendered_values)
    watch_next_overlap = _watch_next_overlap_report(output)
    numeric_fact_repetition = _numeric_fact_repetition_report(output)
    numeric_ownership = _business_numeric_ownership_report(output)
    numeric_primary_ownership = _numeric_primary_ownership_report(output)
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
            elif state == "verified_depositary" and _common_stock_identity_asserted(message):
                issue = "depositary_rendered_as_common_stock"
            elif state == "verified_non_depositary" and _DEPOSITARY_PROSE.search(message):
                issue = "non_depositary_rendered_as_depositary"
            if issue is not None:
                rendered_identity_mismatches.append(
                    {"ticker": review.ticker, "identity_state": state, "issue": issue}
                )
    expected_tickers = (
        set(expected_stock_tickers) if expected_stock_tickers is not None else set(packet_stocks)
    )
    output_tickers = {review.ticker for review in output.stock_reviews}
    completeness_passed = (
        packet is None
        or not rendered_values
        or (
            expected_tickers == output_tickers
            and len(rendered_values) == len(output.stock_reviews) + 1
        )
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
        and not repeated_numeric_summary_families
        and not repeated_methodology
        and not supply_repeats
        and not us_kr_horizon_rows
        and not generic_us_supply_rows
        and len(generic_us_investor_unknown_rows) < duplicate_threshold
        and generic_next_check_count == 0
        and generic_unknown_count == 0
        and all(bool(item["numeric_horizon_coverage_passed"]) for item in supply_numeric_coverage)
        and identity_prose_mismatch_count == 0
        and unsupported_comparative_count == 0
        and supply_grounding_error_count == 0
        and financial_period_error_count == 0
        and valuation_evidence_error_count == 0
        and completeness_passed
        and not heading_mismatches
        and not rendered_identity_mismatches
        and final_rendered_language["hard_checks_passed"] is True
        and watch_next_overlap["hard_checks_passed"] is True
        and numeric_fact_repetition["hard_checks_passed"] is True
        and numeric_ownership["hard_checks_passed"] is True
        and numeric_primary_ownership["hard_checks_passed"] is True
    )
    return {
        "contract": "relational-reasoning-quality-v2",
        "template_skeleton_contract": "typed-template-skeleton-v1",
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
        "generic_numeric_summary_families": generic_numeric_summary_families,
        "generic_numeric_summary_repeat_count": len(repeated_numeric_summary_families),
        "generic_methodology_families": methodology_rows,
        "generic_methodology_repeat_count": len(repeated_methodology),
        "observer_holder": observer_holder,
        "observer_holder_distinct_count": sum(bool(item["distinct"]) for item in observer_holder),
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
            "generic_us_investor_flow_unknown_count": len(generic_us_investor_unknown_rows),
            "generic_us_supply_count": len(generic_us_supply_rows),
            "us_kr_style_horizon_rows": us_kr_horizon_rows,
            "generic_us_investor_flow_unknown_rows": (generic_us_investor_unknown_rows),
            "generic_us_supply_rows": generic_us_supply_rows,
        },
        "numeric_label_quality": numeric_label_quality,
        "kr_supply_numeric_coverage": supply_numeric_coverage,
        "identity_prose_mismatch_count": identity_prose_mismatch_count,
        "unsupported_comparative_claim_count": unsupported_comparative_count,
        "supply_grounding_error_count": supply_grounding_error_count,
        "financial_period_error_count": financial_period_error_count,
        "valuation_evidence_error_count": valuation_evidence_error_count,
        "message_set_completeness": {
            "expected_stock_count": len(expected_tickers),
            "output_stock_count": len(output_tickers),
            "rendered_message_count": len(rendered_values),
            "passed": completeness_passed,
        },
        "rendered_heading_quality": {
            "expected_heading": expected_heading,
            "mismatch_count": len(heading_mismatches),
            "message_indexes": heading_mismatches,
        },
        "rendered_identity_prose_mismatches": rendered_identity_mismatches,
        "rendered_identity_prose_mismatch_count": len(rendered_identity_mismatches),
        "final_rendered_language": final_rendered_language,
        "watch_next_check_overlap": watch_next_overlap,
        "numeric_fact_repetition": numeric_fact_repetition,
        "numeric_ownership": numeric_ownership,
        "numeric_primary_ownership": numeric_primary_ownership,
        "hard_checks_passed": hard_checks_passed,
        "deterministic_quality_gate_passed": hard_checks_passed,
        "production_assist_evidence_eligible": False,
        "human_quality_approval_required": True,
    }


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def runtime_message_quality_receipt(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    rendered_messages: Iterable[dict[str, object]],
    *,
    binding_errors: Iterable[str] = (),
    validation_errors: Iterable[str] = (),
    expected_stock_tickers: Iterable[str] | None = None,
    checked_at: datetime | None = None,
) -> dict[str, object]:
    messages = [
        {
            "ticker": str(item.get("ticker") or ""),
            "text": str(item.get("text") or ""),
            "logical_identity": str(item.get("logical_identity") or ""),
        }
        for item in rendered_messages
    ]
    binding_error_values = list(binding_errors)
    validation_error_values = list(validation_errors)
    quality = relational_reasoning_quality_report(
        output,
        packet=packet,
        binding_errors=binding_error_values,
        validation_errors=validation_error_values,
        rendered_messages=[item["text"] for item in messages],
        expected_stock_tickers=expected_stock_tickers,
    )
    status = (
        "passed"
        if quality.get("hard_checks_passed") is True
        and len(messages) == len(output.stock_reviews) + 1
        and not binding_error_values
        and not validation_error_values
        else "failed"
    )
    errors = [*binding_error_values, *validation_error_values]
    if quality.get("hard_checks_passed") is not True:
        errors.append("runtime_message_quality_gate_failed")
    return {
        "contract": "runtime-message-quality-receipt-v2",
        "receipt_schema_version": "2",
        "gate_version": "runtime-message-quality-v1",
        "packet_id": str(packet.get("packet_id") or ""),
        "policy_version": str(packet.get("analysis_policy_version") or ""),
        "schema_version": str(packet.get("output_schema_version") or ""),
        "packet_sha256": _canonical_sha256(packet),
        "validated_output_sha256": _canonical_sha256(output.model_dump(mode="json")),
        "rendered_payload_set_sha256": _canonical_sha256(messages),
        "message_count": len(messages),
        "expected_stock_tickers": (
            sorted(set(expected_stock_tickers)) if expected_stock_tickers is not None else None
        ),
        "check_results": quality,
        "errors": errors,
        "status": status,
        "checked_at": (checked_at or datetime.now(UTC)).isoformat(),
    }


def verify_runtime_message_quality_receipt(
    receipt: dict[str, object],
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    rendered_messages: Iterable[dict[str, object]],
    *,
    expected_stock_tickers: Iterable[str] | None = None,
) -> bool:
    messages = [
        {
            "ticker": str(item.get("ticker") or ""),
            "text": str(item.get("text") or ""),
            "logical_identity": str(item.get("logical_identity") or ""),
        }
        for item in rendered_messages
    ]
    quality = receipt.get("check_results")
    errors = receipt.get("errors")
    checked_at = receipt.get("checked_at")
    checked_at_valid = False
    if isinstance(checked_at, str) and checked_at:
        try:
            parsed_checked_at = datetime.fromisoformat(checked_at)
        except ValueError:
            pass
        else:
            checked_at_valid = parsed_checked_at.tzinfo is not None
    return bool(
        receipt.get("contract") == "runtime-message-quality-receipt-v2"
        and receipt.get("receipt_schema_version") == "2"
        and receipt.get("gate_version") == "runtime-message-quality-v1"
        and receipt.get("status") == "passed"
        and receipt.get("packet_id") == packet.get("packet_id")
        and receipt.get("policy_version") == packet.get("analysis_policy_version")
        and receipt.get("schema_version") == str(packet.get("output_schema_version") or "")
        and receipt.get("packet_sha256") == _canonical_sha256(packet)
        and receipt.get("validated_output_sha256")
        == _canonical_sha256(output.model_dump(mode="json"))
        and receipt.get("rendered_payload_set_sha256") == _canonical_sha256(messages)
        and int(receipt.get("message_count") or 0) == len(messages)
        and receipt.get("expected_stock_tickers")
        == (sorted(set(expected_stock_tickers)) if expected_stock_tickers is not None else None)
        and isinstance(quality, dict)
        and quality.get("contract") == "relational-reasoning-quality-v2"
        and quality.get("hard_checks_passed") is True
        and quality.get("deterministic_quality_gate_passed") is True
        and isinstance(errors, list)
        and not errors
        and checked_at_valid
    )
