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

PriceOwner = Literal[
    "CURRENT_PRICE_STRUCTURE",
    "STORED_MONITORING_PRICE_RULE",
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


@dataclass(frozen=True)
class LegacyTechnicalRender:
    message: str
    occurrences: tuple[LegacyTechnicalOccurrence, ...]


_LEGACY_TECHNICAL_PATTERN = re.compile(
    r"OHLCV|RSI|MACD|Bollinger|볼린저|월봉|주봉|일봉|"
    r"상승 레짐|하락 레짐|지지선|저항선|기술적|차트 구조",
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


def _zone(selection: object) -> Mapping[str, object] | None:
    if not isinstance(selection, Mapping):
        return None
    value = selection.get("zone")
    return value if isinstance(value, Mapping) else None


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
    }


def _price_display(value: object, currency: str) -> str:
    amount = Decimal(str(value))
    if currency == "KRW":
        return f"{amount:,.0f}원"
    return f"${amount:,.2f}"


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

    for label, semantic_type, zone in (
        ("가까운 지지", "NEAREST_SUPPORT", support_zone),
        ("가까운 저항", "NEAREST_RESISTANCE", resistance_zone),
    ):
        if zone:
            lines.append(f"• {label}: {zone['display']}")
            displayed.append(zone)
            bindings.append(_binding(zone, semantic_type=semantic_type))
        else:
            lines.append(f"• {label}: 확인된 역사적 {label.split()[-1]} 없음")

    major_parts: list[str] = []
    for label, semantic_type, zone, nearest in (
        ("지지", "MAJOR_SUPPORT", major_support_zone, support_zone),
        ("저항", "MAJOR_RESISTANCE", major_resistance_zone, resistance_zone),
    ):
        if not zone or (nearest and zone.get("zone_id") == nearest.get("zone_id")):
            continue
        if nearest and _overlap(zone, nearest):
            continue
        if any(zone.get("display") == item.get("display") for item in displayed):
            continue
        major_parts.append(f"{label} {zone['display']}")
        displayed.append(zone)
        bindings.append(_binding(zone, semantic_type=semantic_type))
    if major_parts:
        lines.append("• 주요 구조: " + " · ".join(major_parts))

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


def _section_owner(line: str, current: str) -> str:
    if line == "📐 현재 가격 구조":
        return "CURRENT_V3"
    if line == "🧭 기존 등록 가격 규칙":
        return "STORED_PRICE_RULE"
    if line.startswith(("📐 Valuation", "📌 ", "🎯 ", "📈 ", "👁 ", "⚠️ ", "💰 ")):
        return "OTHER"
    return current


def suppress_legacy_technical_prose(
    message: str,
    *,
    current_session: str,
    active_v3: bool,
    canonical_indicator_sessions: Sequence[str] = (),
) -> LegacyTechnicalRender:
    owner = "OTHER"
    output: list[str] = []
    occurrences: list[LegacyTechnicalOccurrence] = []
    valid_sessions = set(canonical_indicator_sessions)
    for line in message.splitlines():
        owner = _section_owner(line, owner)
        if owner == "CURRENT_V3" and _LEGACY_TECHNICAL_PATTERN.search(line):
            occurrences.append(LegacyTechnicalOccurrence(line, "CURRENT_V3", "KEEP"))
            output.append(line)
            continue
        if owner == "STORED_PRICE_RULE" and _LEGACY_TECHNICAL_PATTERN.search(line):
            occurrences.append(
                LegacyTechnicalOccurrence(line, "STORED_PRICE_RULE", "KEEP")
            )
            output.append(line)
            continue
        if not active_v3 or not _LEGACY_TECHNICAL_PATTERN.search(line):
            output.append(line)
            continue

        kept_sentences: list[str] = []
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            if not _LEGACY_TECHNICAL_PATTERN.search(sentence):
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
            occurrences.append(LegacyTechnicalOccurrence(sentence, classification, action))
            if is_current:
                kept_sentences.append(sentence)
        if kept_sentences:
            output.append(" ".join(kept_sentences))

    repaired = "\n".join(output)
    repaired = re.sub(r"\n{3,}", "\n\n", repaired).strip()
    return LegacyTechnicalRender(repaired, tuple(occurrences))
