from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


ConfluenceRenderClass = Literal[
    "IDENTICAL_DISPLAY_RANGE",
    "MATERIAL_RANGE_EXTENSION",
    "DISTINCT_RANGE",
]

UserVisibleSRClass = Literal[
    "NEAR",
    "STRUCTURAL",
    "LONG_HORIZON",
    "OMIT",
]

PriceOwner = Literal[
    "CURRENT_PRICE_STRUCTURE",
    "STORED_MONITORING_PRICE_RULE",
]

LegacySemanticField = Literal[
    "PROTECTED_STRUCTURAL_FIELD",
    "BUSINESS_PROSE",
    "TECHNICAL_PROSE_CANDIDATE",
    "STORED_PRICE_RULE",
    "CURRENT_V3_PRICE_STRUCTURE",
    "VALUATION_PROSE",
    "OTHER",
]


@dataclass(frozen=True)
class ConfluenceRenderDecision:
    classification: ConfluenceRenderClass
    overlapping_zone_ids: tuple[str, ...]


@dataclass(frozen=True)
class PriceStructureRender:
    section: str
    numeric_bindings: tuple[dict[str, object], ...]
    confluence_decision: ConfluenceRenderDecision | None
    displayed_zone_ids: tuple[str, ...]


@dataclass(frozen=True)
class PriceStructureRenderValidation:
    status: Literal["PASS", "FAIL"]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class StoredPriceRuleRender:
    message: str
    section: str | None
    numeric_bindings: tuple[dict[str, object], ...]
    source_lines: tuple[str, ...]


@dataclass(frozen=True)
class LegacyTechnicalOccurrence:
    text: str
    classification: Literal[
        "CURRENT_V3",
        "STORED_PRICE_RULE",
        "VALID_NONREDUNDANT_LEGACY",
        "STALE_OR_REDUNDANT_LEGACY",
    ]
    action: Literal["KEEP", "SUPPRESS"]
    semantic_field: LegacySemanticField = "OTHER"
    matched_terms: tuple[str, ...] = ()
    match_spans: tuple[tuple[int, int], ...] = ()
    token_boundary_types: tuple[str, ...] = ()
    suppression_reason: str | None = None


@dataclass(frozen=True)
class LegacyTechnicalTokenMatch:
    matched_term: str
    match_span: tuple[int, int]
    token_boundary_type: str


@dataclass(frozen=True)
class LegacyTechnicalRender:
    message: str
    occurrences: tuple[LegacyTechnicalOccurrence, ...]


_LEGACY_TECHNICAL_TOKEN_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])(?P<acronym>OHLCV|RSI|MACD|ATR|EMA|SMA)(?![A-Za-z_])|"
    r"(?<![A-Za-z0-9_])(?P<english>Bollinger)(?![A-Za-z0-9_])|"
    r"(?P<korean>볼린저|월봉|주봉|일봉|상승 레짐|하락 레짐|지지선|저항선|"
    r"기술적|차트 구조)",
    re.IGNORECASE,
)
_DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_STORED_RULE_BLOCK = re.compile(
    r"\n보유자:\n(?P<body>.*?)(?=\n📐 Valuation)",
    re.DOTALL,
)
_PRICE_TOKEN = re.compile(
    r"\$[\d,]+(?:\.\d+)?|[\d,]+(?:\.\d+)?(?:원|만원)",
)

_SECTION_BODY_FIELDS: dict[str, LegacySemanticField] = {
    "🎯 핵심": "TECHNICAL_PROSE_CANDIDATE",
    "📈 사업·실적": "BUSINESS_PROSE",
    "👁 핵심 감시": "OTHER",
    "💰 가격": "OTHER",
    "📐 가격 구조": "CURRENT_V3_PRICE_STRUCTURE",
    "📐 현재 가격 구조": "CURRENT_V3_PRICE_STRUCTURE",
    "보유자:": "STORED_PRICE_RULE",
    "🧭 기존 등록 가격 규칙": "STORED_PRICE_RULE",
    "📐 Valuation": "VALUATION_PROSE",
    "⚠️ 데이터 주의": "OTHER",
    "📌 다음 확인": "OTHER",
}
_PROTECTED_LINE_PREFIXES = (
    "🏢 ",
    "투자 논리:",
    "구조적 위험:",
    "시장 기대:",
)


def _zone(selection: object) -> Mapping[str, object] | None:
    if not isinstance(selection, Mapping):
        return None
    value = selection.get("zone")
    return value if isinstance(value, Mapping) else None


def classify_user_visible_sr(zone: Mapping[str, object]) -> UserVisibleSRClass:
    tier = str(zone.get("proximity_tier") or "")
    relevance = str(zone.get("active_relevance") or "")
    if tier == "NEAR" and relevance == "ACTIVE_NEAR":
        return "NEAR"
    if tier == "RELEVANT" and relevance == "ACTIVE_STRUCTURAL":
        return "STRUCTURAL"
    if (
        tier == "LONG_HORIZON"
        and relevance == "LONG_HORIZON_HISTORICAL"
    ):
        return "LONG_HORIZON"
    return "OMIT"


def _decimal(zone: Mapping[str, object], key: str) -> Decimal:
    return Decimal(str(zone[key]))


def _overlap(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return not (
        _decimal(left, "raw_high") < _decimal(right, "raw_low")
        or _decimal(right, "raw_high") < _decimal(left, "raw_low")
    )


def _contains(container: Mapping[str, object], value: Mapping[str, object]) -> bool:
    return (
        _decimal(container, "raw_low") <= _decimal(value, "raw_low")
        and _decimal(container, "raw_high") >= _decimal(value, "raw_high")
    )


def classify_confluence_render_equivalence(
    confluence: Mapping[str, object],
    displayed_structural_zones: Sequence[Mapping[str, object]],
) -> ConfluenceRenderDecision:
    overlapping = tuple(
        zone for zone in displayed_structural_zones if _overlap(confluence, zone)
    )
    overlapping_ids = tuple(str(zone.get("zone_id") or "") for zone in overlapping)
    if not overlapping:
        return ConfluenceRenderDecision("DISTINCT_RANGE", ())
    if any(
        str(confluence.get("display") or "") == str(zone.get("display") or "")
        or _contains(zone, confluence)
        for zone in overlapping
    ):
        return ConfluenceRenderDecision(
            "IDENTICAL_DISPLAY_RANGE",
            overlapping_ids,
        )
    return ConfluenceRenderDecision("MATERIAL_RANGE_EXTENSION", overlapping_ids)


def _binding(
    zone: Mapping[str, object],
    *,
    semantic_type: str,
    owner: PriceOwner = "CURRENT_PRICE_STRUCTURE",
) -> dict[str, object]:
    return {
        "owner": owner,
        "semantic_type": semantic_type,
        "fact_ref": zone["zone_id"],
        "raw_low": zone["raw_low"],
        "raw_high": zone["raw_high"],
        "display": zone["display"],
        "currency": zone["currency"],
        "source_refs": zone["source_refs"],
        "source_timeframe": zone.get("source_timeframe"),
        "source_timeframes": zone.get("source_timeframes", ()),
        "distance_pct": zone.get("distance_pct"),
        "proximity_tier": zone.get("proximity_tier"),
        "active_relevance": zone.get("active_relevance"),
    }


def _price_display(value: object, currency: str) -> str:
    amount = Decimal(str(value))
    if currency == "KRW":
        return f"{amount:,.0f}원"
    return f"${amount:,.2f}"


_VISIBLE_SR_LABELS = {
    "NEAR_SUPPORT": "가까운 지지",
    "NEAR_RESISTANCE": "가까운 저항",
    "MAJOR_SUPPORT": "주요 구조 지지",
    "MAJOR_RESISTANCE": "주요 구조 저항",
    "LONG_HORIZON_SUPPORT": "장기 구조 지지",
    "LONG_HORIZON_RESISTANCE": "장기 구조 저항",
}


def _semantic_type(user_class: UserVisibleSRClass, role: str) -> str:
    if role not in {"SUPPORT", "RESISTANCE"}:
        raise ValueError("user-visible SR zone must have a support or resistance role")
    side = role
    return {
        "NEAR": f"NEAR_{side}",
        "STRUCTURAL": f"MAJOR_{side}",
        "LONG_HORIZON": f"LONG_HORIZON_{side}",
    }[user_class]


def _append_sr_zone(
    *,
    lines: list[str],
    bindings: list[dict[str, object]],
    displayed: list[Mapping[str, object]],
    zone: Mapping[str, object],
    user_class: UserVisibleSRClass,
) -> None:
    if user_class == "OMIT":
        return
    if any(zone.get("zone_id") == item.get("zone_id") for item in displayed):
        return
    semantic_type = _semantic_type(user_class, str(zone.get("current_role") or ""))
    if any(binding.get("semantic_type") == semantic_type for binding in bindings):
        return
    label = _VISIBLE_SR_LABELS[semantic_type]
    lines.append(f"• {label}: {zone['display']}")
    displayed.append(zone)
    bindings.append(_binding(zone, semantic_type=semantic_type))


def validate_price_structure_render(
    render: PriceStructureRender,
) -> PriceStructureRenderValidation:
    errors: list[str] = []
    sr_bindings = [
        binding
        for binding in render.numeric_bindings
        if binding.get("semantic_type") in _VISIBLE_SR_LABELS
    ]
    for semantic_type, label in _VISIBLE_SR_LABELS.items():
        prefix = f"• {label}: "
        rendered_values = [
            line.removeprefix(prefix)
            for line in render.section.splitlines()
            if line.startswith(prefix)
        ]
        bindings = [
            binding
            for binding in sr_bindings
            if binding.get("semantic_type") == semantic_type
        ]
        bound_values = [str(binding.get("display") or "") for binding in bindings]
        if sorted(rendered_values) != sorted(bound_values):
            errors.append(f"render_binding_mismatch:{semantic_type}")
        if len(bindings) > 1:
            errors.append(f"duplicate_user_visible_semantic:{semantic_type}")
        for binding in bindings:
            fact_ref = str(binding.get("fact_ref") or "missing_fact_ref")
            tier = str(binding.get("proximity_tier") or "")
            relevance = str(binding.get("active_relevance") or "")
            if semantic_type.startswith("NEAR_") and (
                tier != "NEAR" or relevance != "ACTIVE_NEAR"
            ):
                errors.append(f"near_label_ineligible_proximity:{fact_ref}")
            elif semantic_type.startswith("MAJOR_") and (
                tier not in {"NEAR", "RELEVANT"}
                or relevance not in {"ACTIVE_NEAR", "ACTIVE_STRUCTURAL"}
            ):
                errors.append(f"major_label_ineligible_proximity:{fact_ref}")
            elif semantic_type.startswith("LONG_HORIZON_") and (
                tier != "LONG_HORIZON"
                or relevance != "LONG_HORIZON_HISTORICAL"
            ):
                errors.append(f"long_horizon_label_ineligible_proximity:{fact_ref}")

    semantic_by_fact: dict[str, set[str]] = {}
    for binding in sr_bindings:
        fact_ref = str(binding.get("fact_ref") or "")
        semantic_by_fact.setdefault(fact_ref, set()).add(
            str(binding.get("semantic_type") or "")
        )
    errors.extend(
        f"sr_semantic_duplication:{fact_ref}"
        for fact_ref, semantics in semantic_by_fact.items()
        if fact_ref and len(semantics) > 1
    )
    unique_errors = tuple(dict.fromkeys(errors))
    return PriceStructureRenderValidation(
        status="FAIL" if unique_errors else "PASS",
        errors=unique_errors,
    )


def render_current_price_structure(
    summary: Mapping[str, object],
    *,
    ticker: str,
    as_of: str,
    current_price: object,
    currency: str,
    include_current_price: bool,
) -> PriceStructureRender:
    nearest_support = summary.get("nearest_support")
    nearest_resistance = summary.get("nearest_resistance")
    major_support = summary.get("major_structural_support")
    major_resistance = summary.get("major_structural_resistance")
    support_zone = _zone(nearest_support)
    resistance_zone = _zone(nearest_resistance)
    major_support_zone = _zone(major_support)
    major_resistance_zone = _zone(major_resistance)

    lines = ["📐 현재 가격 구조"]
    bindings: list[dict[str, object]] = []
    displayed: list[Mapping[str, object]] = []
    if include_current_price:
        lines.append(f"• 기준 종가: {_price_display(current_price, currency)}")
        bindings.append(
            {
                "owner": "CURRENT_PRICE_STRUCTURE",
                "semantic_type": "CURRENT_PRICE",
                "fact_ref": f"current-price:{ticker}:{as_of}",
                "value": str(current_price),
                "currency": currency,
            }
        )

    deferred: list[tuple[Mapping[str, object], UserVisibleSRClass]] = []
    for zone in (support_zone, resistance_zone):
        if zone is None:
            continue
        user_class = classify_user_visible_sr(zone)
        if user_class == "NEAR":
            _append_sr_zone(
                lines=lines,
                bindings=bindings,
                displayed=displayed,
                zone=zone,
                user_class=user_class,
            )
        elif user_class != "OMIT":
            deferred.append((zone, user_class))

    for zone in (major_support_zone, major_resistance_zone):
        if zone is None:
            continue
        user_class = classify_user_visible_sr(zone)
        if user_class in {"NEAR", "STRUCTURAL"}:
            user_class = "STRUCTURAL"
        if user_class != "OMIT":
            deferred.append((zone, user_class))

    for user_class in ("STRUCTURAL", "LONG_HORIZON"):
        for zone, zone_class in deferred:
            if zone_class != user_class:
                continue
            if any(
                zone.get("display") == item.get("display")
                or _overlap(zone, item)
                for item in displayed
            ):
                continue
            _append_sr_zone(
                lines=lines,
                bindings=bindings,
                displayed=displayed,
                zone=zone,
                user_class=user_class,
            )

    confluence = summary.get("fib_sr_confluence")
    confluence_state = str(summary.get("fib_sr_confluence_state") or "")
    confluence_decision: ConfluenceRenderDecision | None = None
    if isinstance(confluence, Mapping) and confluence_state in {
        "DIRECT_SR_CONFLUENCE",
        "NEAR_SR_CONFLUENCE",
    }:
        confluence_decision = classify_confluence_render_equivalence(
            confluence,
            displayed,
        )
        if confluence_decision.classification == "IDENTICAL_DISPLAY_RANGE":
            lines.append(
                "• Fib/SR 겹침: 같은 구조 구간의 보조 확인 근거입니다."
            )
        else:
            lines.append(
                f"• Fib/SR 겹침: {confluence['display']} · 보조 확인 근거"
            )
            bindings.append(_binding(confluence, semantic_type="FIB_SR_CONFLUENCE"))
            displayed.append(confluence)

    return PriceStructureRender(
        section="\n".join(lines),
        numeric_bindings=tuple(bindings),
        confluence_decision=confluence_decision,
        displayed_zone_ids=tuple(str(zone.get("zone_id") or "") for zone in displayed),
    )


def replace_current_price_structure(message: str, section: str) -> str:
    pattern = re.compile(
        r"\n📐 (?:현재 )?가격 구조\n.*?"
        r"(?=\n(?:보유자:|🧭 기존 등록 가격 규칙|📐 Valuation|📌 다음 확인))",
        re.DOTALL,
    )
    if not pattern.search(message):
        raise ValueError("current price-structure section is missing")
    return pattern.sub("\n" + section + "\n", message, count=1)


def _stored_field(line: str) -> str:
    if "무효화" in line:
        return "invalidation_price"
    if "지지" in line:
        return "support_zone"
    if "경고" in line:
        return "warning_price"
    if "확인선" in line:
        return "confirmation_price"
    return "other_price_rule"


def _stored_line(line: str) -> str | None:
    if line == "가격 규칙 이력:":
        return None
    if line.startswith("• 차트 무효화 가격:"):
        return line.replace("• 차트 무효화 가격:", "• 기존 무효화 가격:", 1)
    if line.startswith("• 동적 지지 유지 여부:"):
        return line.replace("• 동적 지지 유지 여부:", "• 기존 등록 지지 규칙:", 1)
    if line.startswith("• 등록 확인선 "):
        return line.replace("• 등록 확인선 ", "• 기존 확인선 ", 1)
    match = re.match(r"• 기존 (\$[\d,.]+) 확인선(.*)", line)
    if match:
        return f"• 기존 확인선 {match.group(1)}{match.group(2)}"
    return line


def relabel_stored_price_rules(message: str, *, ticker: str) -> StoredPriceRuleRender:
    match = _STORED_RULE_BLOCK.search(message)
    if not match:
        return StoredPriceRuleRender(message, None, (), ())
    source_lines = tuple(
        line for line in match.group("body").strip().splitlines() if line.strip()
    )
    rendered_lines = [
        rendered
        for line in source_lines
        if (rendered := _stored_line(line)) is not None
    ]
    section = "\n".join(("🧭 기존 등록 가격 규칙", *rendered_lines))
    bindings: list[dict[str, object]] = []
    for line in rendered_lines:
        for token in _PRICE_TOKEN.findall(line):
            bindings.append(
                {
                    "owner": "STORED_MONITORING_PRICE_RULE",
                    "semantic_type": _stored_field(line),
                    "fact_ref": "chart:stored_price_rules",
                    "field_ref": _stored_field(line),
                    "ticker": ticker,
                    "display": token,
                    "source": "investment_thesis",
                }
            )
    repaired = message[: match.start()] + "\n" + section + "\n" + message[match.end() :]
    return StoredPriceRuleRender(
        message=repaired,
        section=section,
        numeric_bindings=tuple(bindings),
        source_lines=source_lines,
    )


def detect_legacy_technical_tokens(
    text: str,
) -> tuple[LegacyTechnicalTokenMatch, ...]:
    matches: list[LegacyTechnicalTokenMatch] = []
    for match in _LEGACY_TECHNICAL_TOKEN_PATTERN.finditer(text):
        if match.lastgroup == "acronym":
            boundary = "ASCII_TOKEN_OR_KOREAN_SUFFIX_BOUNDARY"
        elif match.lastgroup == "english":
            boundary = "ENGLISH_WORD_OR_KOREAN_SUFFIX_BOUNDARY"
        else:
            boundary = "KOREAN_TECHNICAL_TERM"
        matches.append(
            LegacyTechnicalTokenMatch(
                matched_term=match.group(0),
                match_span=match.span(),
                token_boundary_type=boundary,
            )
        )
    return tuple(matches)


def _line_semantic_field(
    line: str,
    current: LegacySemanticField,
) -> tuple[LegacySemanticField, LegacySemanticField]:
    body_field = _SECTION_BODY_FIELDS.get(line)
    if body_field is not None:
        return "PROTECTED_STRUCTURAL_FIELD", body_field
    if line.startswith(_PROTECTED_LINE_PREFIXES):
        return "PROTECTED_STRUCTURAL_FIELD", current
    if line.startswith(("🎯 ", "📈 ", "👁 ", "💰 ", "📐 ", "⚠️ ", "📌 ", "🧭 ")):
        return "PROTECTED_STRUCTURAL_FIELD", "OTHER"
    return current, current


def _technical_occurrence(
    text: str,
    classification: Literal[
        "CURRENT_V3",
        "STORED_PRICE_RULE",
        "VALID_NONREDUNDANT_LEGACY",
        "STALE_OR_REDUNDANT_LEGACY",
    ],
    action: Literal["KEEP", "SUPPRESS"],
    semantic_field: LegacySemanticField,
    matches: Sequence[LegacyTechnicalTokenMatch],
    suppression_reason: str | None,
) -> LegacyTechnicalOccurrence:
    return LegacyTechnicalOccurrence(
        text=text,
        classification=classification,
        action=action,
        semantic_field=semantic_field,
        matched_terms=tuple(match.matched_term for match in matches),
        match_spans=tuple(match.match_span for match in matches),
        token_boundary_types=tuple(match.token_boundary_type for match in matches),
        suppression_reason=suppression_reason,
    )


def suppress_legacy_technical_prose(
    message: str,
    *,
    current_session: str,
    active_v3: bool,
    canonical_indicator_sessions: Sequence[str] = (),
) -> LegacyTechnicalRender:
    section_field: LegacySemanticField = "OTHER"
    output: list[str] = []
    occurrences: list[LegacyTechnicalOccurrence] = []
    valid_sessions = set(canonical_indicator_sessions)
    for line in message.splitlines():
        semantic_field, section_field = _line_semantic_field(line, section_field)
        line_matches = detect_legacy_technical_tokens(line)
        if semantic_field == "CURRENT_V3_PRICE_STRUCTURE" and line_matches:
            occurrences.append(
                _technical_occurrence(
                    line,
                    "CURRENT_V3",
                    "KEEP",
                    semantic_field,
                    line_matches,
                    "owned_by_current_v3_price_structure",
                )
            )
            output.append(line)
            continue
        if semantic_field == "STORED_PRICE_RULE" and line_matches:
            occurrences.append(
                _technical_occurrence(
                    line,
                    "STORED_PRICE_RULE",
                    "KEEP",
                    semantic_field,
                    line_matches,
                    "owned_by_stored_price_rule",
                )
            )
            output.append(line)
            continue
        if (
            not active_v3
            or semantic_field != "TECHNICAL_PROSE_CANDIDATE"
            or not line_matches
        ):
            output.append(line)
            continue

        kept_sentences: list[str] = []
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            sentence_matches = detect_legacy_technical_tokens(sentence)
            if not sentence_matches:
                kept_sentences.append(sentence)
                continue
            dates = set(_DATE_PATTERN.findall(sentence))
            is_current = current_session in dates and current_session in valid_sessions
            classification = (
                "VALID_NONREDUNDANT_LEGACY"
                if is_current
                else "STALE_OR_REDUNDANT_LEGACY"
            )
            action = "KEEP" if is_current else "SUPPRESS"
            occurrences.append(
                _technical_occurrence(
                    sentence,
                    classification,
                    action,
                    semantic_field,
                    sentence_matches,
                    (
                        "current_canonical_nonredundant_legacy_technical_sentence"
                        if is_current
                        else "stale_or_redundant_legacy_technical_sentence"
                    ),
                )
            )
            if is_current:
                kept_sentences.append(sentence)
        if kept_sentences:
            output.append(" ".join(kept_sentences))

    repaired = "\n".join(output)
    repaired = re.sub(r"\n{3,}", "\n\n", repaired).strip()
    return LegacyTechnicalRender(repaired, tuple(occurrences))
