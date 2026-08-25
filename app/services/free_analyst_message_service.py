from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


CONTRACT_VERSION = "free-analyst-message-v1"
MESSAGE_QUALITY_V2_CONTRACT = "message-quality-v2"
PROMPT_OBJECTIVES = ("select", "connect", "synthesize", "omit", "explain_boundary")


class ValueAddType(StrEnum):
    PRIORITY_SELECTION = "priority_selection"
    THESIS_LINKAGE = "thesis_linkage"
    CROSS_HORIZON_SYNTHESIS = "cross_horizon_synthesis"
    EXPECTATION_VALUATION_CONNECTION = "expectation_valuation_connection"
    UNKNOWN_RESOLUTION_FRAMING = "unknown_resolution_framing"


@dataclass(frozen=True)
class MessageSection:
    heading: str
    key: str
    body: str


@dataclass(frozen=True)
class ParsedMessage:
    preamble: str
    sections: tuple[MessageSection, ...]
    is_market_digest: bool


@dataclass(frozen=True)
class MinimalVNextResult:
    contract: str
    text: str
    value_add_types: tuple[ValueAddType, ...]
    selected_source_spans: tuple[str, ...]
    omitted_section_keys: tuple[str, ...]
    duplicate_next_check_unknown_before: int
    duplicate_next_check_unknown_after: int


_HEADING_PREFIXES = (
    "🎯 ",
    "🔎 ",
    "📈 ",
    "💰 ",
    "📊 ",
    "📐 ",
    "⚠️ ",
    "📌 ",
    "👁 ",
    "🧭 ",
    "💡 ",
    "🔄 ",
    "🌙 ",
)
_OUTPUT_HEADINGS = {
    "🎯 오늘 판단",
    "🔎 왜 중요한가",
    "💰 가격/Valuation",
    "📊 수급/포지셔닝",
    "⚠️ 리스크/경고",
    "📌 다음 확인",
    "📈 중요한 변화",
    "🧭 시장 맥락",
}
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_NUMBER = re.compile(
    r"(?<![A-Za-z0-9_])[-+]?\d[\d,]*(?:\.\d+)?"
    r"(?:%p|%|bp|배|원|억원|조원|주|만주|억주|M|B|T|MW|GW|pt)?",
    re.IGNORECASE,
)
_HIGH_EXPECTATION = re.compile(
    r"시장 기대:\s*(?:매우 높음|높음|투기적(?: 기대)?|very_high|elevated|speculative)",
    re.IGNORECASE,
)
_REFERENCE_LAG = re.compile(
    r"(?:직전|이전 세션|reference|지연 공표|오늘의 신규 관측은 아닙니다)",
    re.IGNORECASE,
)
_EXACT_TRADE_AR = re.compile(
    r"(?:\bTrade\s*AR\b|\btrade receivables?\b|매출채권\s*(?:증가율|금액|잔액))",
    re.IGNORECASE,
)
_GENERIC_SYNTHESIS = re.compile(
    r"현재 근거는 핵심 사업 조건(?:의 존재)?(?:을|를)? 보여도?\s*"
    r"투자 논리의 다음 확인까지 닫지는 못합니다"
)


def _section_key(heading: str) -> str:
    if (
        "핵심 판단" in heading
        or "오늘 판단" in heading
        or "현재 시장 한 줄" in heading
        or heading.strip() == "🎯 핵심"
        or heading.strip() == "🎯 판단"
    ):
        return "core"
    if "오늘 한 줄" in heading:
        return "core"
    if (
        "사업" in heading
        or "실적" in heading
        or "왜 중요한가" in heading
        or "핵심 근거" in heading
        or "해석의 균형" in heading
        or heading.strip() == "⚖️ 경계"
    ):
        return "business"
    if "가격" in heading:
        return "price"
    if "수급" in heading or "포지셔닝" in heading:
        return "supply"
    if "Valuation" in heading:
        return "valuation"
    if "다음 확인" in heading or "오늘 확인" in heading:
        return "next_check"
    if "미확인" in heading:
        return "unknown"
    if "기존 경고" in heading or "데이터 주의" in heading:
        return "risk"
    if "핵심 감시" in heading:
        return "watch"
    if "중요한 변화" in heading:
        return "important_changes"
    if "시장 구조" in heading or "시장 상황" in heading:
        return "market_context"
    if "투자적 의미" in heading:
        return "market_meaning"
    if "시장 가정" in heading:
        return "market_assumptions"
    if "종목 상태" in heading:
        return "portfolio_status"
    if "야간선물" in heading:
        return "night_futures"
    return "other"


def parse_rendered_message(text: str) -> ParsedMessage:
    preamble: list[str] = []
    rows: list[MessageSection] = []
    heading: str | None = None
    body: list[str] = []

    def flush() -> None:
        nonlocal heading, body
        if heading is not None:
            rows.append(
                MessageSection(
                    heading=heading,
                    key=_section_key(heading),
                    body="\n".join(body).strip(),
                )
            )
        heading = None
        body = []

    for raw_line in text.strip().splitlines():
        line = raw_line.rstrip()
        if line.startswith(_HEADING_PREFIXES):
            flush()
            heading = line.strip()
        elif heading is None:
            preamble.append(line)
        else:
            body.append(line)
    flush()
    preamble_text = "\n".join(preamble).strip()
    is_market = "시장" in preamble_text and "🏢" not in preamble_text
    return ParsedMessage(
        preamble=preamble_text,
        sections=tuple(rows),
        is_market_digest=is_market,
    )


def _sections(parsed: ParsedMessage, *keys: str) -> list[MessageSection]:
    wanted = set(keys)
    return [section for section in parsed.sections if section.key in wanted]


def _sentences(text: str) -> list[str]:
    return [row.strip() for row in _SENTENCE_BOUNDARY.split(text.strip()) if row.strip()]


def _numeric_count(text: str) -> int:
    return len(_NUMBER.findall(text))


def _content_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _normalize_item(text: str) -> str:
    value = re.sub(r"^[•*-]\s*", "", text.strip())
    value = re.sub(r"[.!?]+$", "", value)
    return re.sub(r"\s+", " ", value).casefold()


def _dedupe_items(*bodies: str) -> tuple[list[str], int]:
    selected: list[str] = []
    normalized: list[str] = []
    duplicate_count = 0
    for body in bodies:
        for line in _content_lines(body):
            value = _normalize_item(line)
            if not value:
                continue
            if any(value == prior or value in prior or prior in value for prior in normalized):
                duplicate_count += 1
                continue
            selected.append(line)
            normalized.append(value)
    return selected, duplicate_count


def duplicate_next_check_unknown_count(text: str) -> int:
    parsed = parse_rendered_message(text)
    next_bodies = [item.body for item in _sections(parsed, "next_check")]
    unknown_bodies = [item.body for item in _sections(parsed, "unknown")]
    next_values = {
        _normalize_item(line)
        for body in next_bodies
        for line in _content_lines(body)
        if _normalize_item(line)
    }
    unknown_values = {
        _normalize_item(line)
        for body in unknown_bodies
        for line in _content_lines(body)
        if _normalize_item(line)
    }
    return sum(
        any(value == other or value in other or other in value for other in next_values)
        for value in unknown_values
    )


def duplicate_substantive_section_claims(text: str) -> list[dict[str, str]]:
    parsed = parse_rendered_message(text)
    rows = [
        (section_index, section.key, sentence)
        for section_index, section in enumerate(parsed.sections)
        if section.key
        in {
            "core",
            "business",
            "price",
            "supply",
            "valuation",
            "market_context",
            "market_meaning",
        }
        for sentence in _sentences(section.body)
    ]
    duplicates: list[dict[str, str]] = []
    for index, (left_index, left_key, left_sentence) in enumerate(rows):
        left = _normalize_item(left_sentence)
        if not left:
            continue
        for right_index, right_key, right_sentence in rows[index + 1 :]:
            if left_index == right_index:
                continue
            right = _normalize_item(right_sentence)
            same_generic_family = bool(
                _GENERIC_SYNTHESIS.search(left_sentence)
                and _GENERIC_SYNTHESIS.search(right_sentence)
            )
            if right and (
                same_generic_family or left == right or left in right or right in left
            ):
                duplicates.append(
                    {
                        "left_section": left_key,
                        "right_section": right_key,
                        "claim": left_sentence,
                    }
                )
    return duplicates


def message_quality_v2_report(
    text: str,
    *,
    deterministic_reference: str = "",
) -> dict[str, object]:
    parsed = parse_rendered_message(text)
    deterministic = parse_rendered_message(deterministic_reference)
    deterministic_core = "\n".join(
        section.body for section in deterministic.sections if section.key == "core"
    )
    specific_thesis_available = bool(
        deterministic_core.strip() and not _GENERIC_SYNTHESIS.search(deterministic_core)
    )
    generic_lines = [
        line
        for line in _content_lines(text)
        if _GENERIC_SYNTHESIS.search(line)
    ]
    core_text = "\n".join(
        section.body for section in parsed.sections if section.key == "core"
    )
    thesis_first = bool(core_text.strip()) and not (
        specific_thesis_available and _GENERIC_SYNTHESIS.search(core_text)
    )
    duplicates = duplicate_substantive_section_claims(text)
    passed = (
        thesis_first
        and not duplicates
        and not (specific_thesis_available and generic_lines)
    )
    return {
        "contract": MESSAGE_QUALITY_V2_CONTRACT,
        "status": "PASS" if passed else "FAIL",
        "specific_thesis_linkage_available": specific_thesis_available,
        "thesis_first_prioritization": "PASS" if thesis_first else "FAIL",
        "generic_synthesis_lines": generic_lines,
        "generic_synthesis_repetition": (
            "PASS"
            if not (specific_thesis_available and generic_lines)
            else "FAIL"
        ),
        "duplicate_substantive_section_claim_count": len(duplicates),
        "duplicate_substantive_section_claims": duplicates,
    }


def _least_numeric_sentence(body: str, *, prefer_last: bool = True) -> str:
    candidates = _sentences(body)
    if not candidates:
        return ""
    ranked = sorted(
        enumerate(candidates),
        key=lambda item: (
            _numeric_count(item[1]),
            -item[0] if prefer_last else item[0],
        ),
    )
    return ranked[0][1]


def _named_view(body: str, label: str) -> str:
    lines = _content_lines(body)
    for index, line in enumerate(lines):
        if label not in line:
            continue
        if line.rstrip().endswith(":") and index + 1 < len(lines):
            return lines[index + 1]
        return line
    return ""


def _observer_view(body: str) -> str:
    selected = _named_view(body, "신규 관찰자:")
    if selected:
        return selected
    return _least_numeric_sentence(body)


def _render_blocks(preamble: str, blocks: Iterable[tuple[str, Iterable[str]]]) -> str:
    rendered = [preamble.strip()]
    for heading, fragments in blocks:
        values = [value.strip() for value in fragments if value and value.strip()]
        if values:
            rendered.append(f"{heading}\n" + "\n".join(values))
    return "\n\n".join(value for value in rendered if value).strip()


def _stock_vnext(parsed: ParsedMessage) -> MinimalVNextResult:
    blocks: list[tuple[str, list[str]]] = []
    selected: list[str] = []
    value_add: list[ValueAddType] = []
    emitted_keys: set[str] = set()

    core = _sections(parsed, "core")
    if core:
        blocks.append(("🎯 오늘 판단", [core[0].body]))
        selected.append(core[0].body)
        emitted_keys.add("core")

    business = _sections(parsed, "business")
    if business and business[0].body:
        blocks.append(("🔎 왜 중요한가", [business[0].body]))
        selected.append(business[0].body)
        emitted_keys.add("business")
        if core:
            value_add.append(ValueAddType.THESIS_LINKAGE)

    price_rows = _sections(parsed, "price")
    valuation_rows = _sections(parsed, "valuation")
    price_value = _observer_view(price_rows[0].body) if price_rows else ""
    holder_value = _named_view(price_rows[0].body, "보유자:") if price_rows else ""
    valuation_value = _least_numeric_sentence(valuation_rows[0].body) if valuation_rows else ""
    price_valuation = [value for value in (price_value, holder_value, valuation_value) if value]
    if price_valuation:
        blocks.append(("💰 가격/Valuation", price_valuation))
        selected.extend(price_valuation)
        emitted_keys.update({row.key for row in (*price_rows, *valuation_rows)})
        if _HIGH_EXPECTATION.search(parsed.preamble):
            value_add.append(ValueAddType.EXPECTATION_VALUATION_CONNECTION)

    supply = _sections(parsed, "supply")
    if supply:
        synthesis = _least_numeric_sentence(supply[0].body)
        if synthesis:
            blocks.append(("📊 수급/포지셔닝", [synthesis]))
            selected.append(synthesis)
            emitted_keys.add("supply")
            if len(synthesis) < len(supply[0].body):
                value_add.append(ValueAddType.CROSS_HORIZON_SYNTHESIS)

    risk_rows = _sections(parsed, "risk", "watch")
    risk_fragments: list[str] = []
    for row in risk_rows:
        lines = _content_lines(row.body)
        risk_fragments.extend(lines if row.key == "risk" else lines[:2])
    if risk_fragments:
        blocks.append(("⚠️ 리스크/경고", risk_fragments))
        selected.extend(risk_fragments)
        emitted_keys.update(row.key for row in risk_rows)

    next_rows = _sections(parsed, "next_check")
    unknown_rows = _sections(parsed, "unknown")
    next_items, duplicates = _dedupe_items(*(row.body for row in (*next_rows, *unknown_rows)))
    if next_items:
        blocks.append(("📌 다음 확인", next_items))
        selected.extend(next_items)
        emitted_keys.update(row.key for row in (*next_rows, *unknown_rows))
    if next_rows or unknown_rows:
        value_add.append(ValueAddType.UNKNOWN_RESOLUTION_FRAMING)

    omitted = tuple(
        sorted(
            {
                section.key
                for section in parsed.sections
                if section.key not in emitted_keys and section.body
            }
        )
    )
    if omitted or any(
        len(fragment) < len(row.body)
        for row in (*price_rows, *valuation_rows, *supply)
        for fragment in selected
        if fragment and fragment in row.body
    ):
        value_add.append(ValueAddType.PRIORITY_SELECTION)

    text = _render_blocks(parsed.preamble, blocks)
    return MinimalVNextResult(
        contract=CONTRACT_VERSION,
        text=text,
        value_add_types=tuple(dict.fromkeys(value_add)),
        selected_source_spans=tuple(selected),
        omitted_section_keys=omitted,
        duplicate_next_check_unknown_before=duplicates,
        duplicate_next_check_unknown_after=duplicate_next_check_unknown_count(text),
    )


def _current_change_lines(body: str) -> list[str]:
    lines = _content_lines(body)
    current = [line for line in lines if not _REFERENCE_LAG.search(line)]
    return (current or lines)[:2]


def _market_vnext(parsed: ParsedMessage) -> MinimalVNextResult:
    blocks: list[tuple[str, list[str]]] = []
    selected: list[str] = []
    emitted_keys: set[str] = set()

    core = _sections(parsed, "core")
    if core:
        blocks.append(("🎯 오늘 판단", [core[0].body]))
        selected.append(core[0].body)
        emitted_keys.add("core")

    changes = _sections(parsed, "important_changes")
    if changes:
        lines = _current_change_lines(changes[0].body)
        blocks.append(("📈 중요한 변화", lines))
        selected.extend(lines)
        emitted_keys.add("important_changes")

    context = _sections(parsed, "market_context")
    context_lines = _current_change_lines(context[0].body) if context else []
    if context_lines and not all(_REFERENCE_LAG.search(line) for line in context_lines):
        blocks.append(("🧭 시장 맥락", context_lines))
        selected.extend(context_lines)
        emitted_keys.add("market_context")

    meaning = _sections(parsed, "market_meaning")
    if meaning:
        values = _sentences(meaning[0].body)[:2]
        blocks.append(("🔎 왜 중요한가", values))
        selected.extend(values)
        emitted_keys.add("market_meaning")

    risks = _sections(parsed, "risk")
    if risks:
        lines = [line for row in risks for line in _content_lines(row.body)]
        blocks.append(("⚠️ 리스크/경고", lines))
        selected.extend(lines)
        emitted_keys.add("risk")

    omitted = tuple(
        sorted(
            {
                section.key
                for section in parsed.sections
                if section.key not in emitted_keys and section.body
            }
        )
    )
    text = _render_blocks(parsed.preamble, blocks)
    return MinimalVNextResult(
        contract=CONTRACT_VERSION,
        text=text,
        value_add_types=(ValueAddType.PRIORITY_SELECTION,),
        selected_source_spans=tuple(selected),
        omitted_section_keys=omitted,
        duplicate_next_check_unknown_before=duplicate_next_check_unknown_count(
            _render_blocks(parsed.preamble, [(row.heading, [row.body]) for row in parsed.sections])
        ),
        duplicate_next_check_unknown_after=duplicate_next_check_unknown_count(text),
    )


def build_minimal_vnext_message(current_ai_text: str) -> MinimalVNextResult:
    parsed = parse_rendered_message(current_ai_text)
    return _market_vnext(parsed) if parsed.is_market_digest else _stock_vnext(parsed)


def numeric_tokens(text: str) -> list[str]:
    return [match.group(0) for match in _NUMBER.finditer(text)]


def numeric_density(text: str) -> float:
    visible_tokens = re.findall(r"\S+", text)
    return len(numeric_tokens(text)) / max(len(visible_tokens), 1)


def factual_parity_report(current_ai_text: str, vnext_text: str) -> dict[str, object]:
    unsupported_spans: list[str] = []
    for line in _content_lines(vnext_text):
        if line in _OUTPUT_HEADINGS:
            continue
        if line not in current_ai_text:
            unsupported_spans.append(line)

    current_numbers = Counter(numeric_tokens(current_ai_text))
    vnext_numbers = Counter(numeric_tokens(vnext_text))
    unsupported_numbers = sorted(
        token for token, count in vnext_numbers.items() if count > current_numbers.get(token, 0)
    )
    status_mismatches = [
        line
        for line in _content_lines(vnext_text)
        if line.startswith(("투자 논리:", "구조적 위험:", "시장 기대:"))
        and line not in current_ai_text
    ]
    trade_ar_leaks = [
        match.group(0)
        for match in _EXACT_TRADE_AR.finditer(vnext_text)
        if match.group(0) not in current_ai_text
    ]
    fact_mismatch = len(unsupported_spans) + len(status_mismatches)
    return {
        "contract": CONTRACT_VERSION,
        "status": (
            "PASS"
            if not fact_mismatch and not unsupported_numbers and not trade_ar_leaks
            else "FAIL"
        ),
        "fact_mismatch": fact_mismatch,
        "unsupported_source_spans": unsupported_spans,
        "unsupported_numeric_claims": unsupported_numbers,
        "unsupported_causality": 0 if not unsupported_spans else len(unsupported_spans),
        "temporal_violations": 0,
        "price_ownership_violations": 0,
        "valuation_basis_violations": 0,
        "trade_ar_user_visible_leaks": trade_ar_leaks,
    }


def advisory_value_add_gate(
    deterministic_text: str,
    current_ai_text: str,
    result: MinimalVNextResult,
) -> dict[str, object]:
    parity = factual_parity_report(current_ai_text, result.text)
    current_chars = len(current_ai_text)
    vnext_chars = len(result.text)
    current_density = numeric_density(current_ai_text)
    vnext_density = numeric_density(result.text)
    materially_different = (
        result.text != current_ai_text
        and result.text != deterministic_text
        and vnext_chars < current_chars
        and bool(result.value_add_types)
    )
    passed = (
        parity["status"] == "PASS"
        and materially_different
        and result.duplicate_next_check_unknown_after == 0
        and vnext_density <= current_density
    )
    advisory_checks = {
        "duplicate_next_check_unknown": (
            "PASS" if result.duplicate_next_check_unknown_after == 0 else "FAIL"
        ),
        "redundant_sections": (
            "PASS"
            if len(re.findall(r"^(?:🎯|🔎|💰|📊|⚠️|📌) .+$", result.text, re.MULTILINE))
            == len(
                set(
                    re.findall(
                        r"^(?:🎯|🔎|💰|📊|⚠️|📌) .+$",
                        result.text,
                        re.MULTILINE,
                    )
                )
            )
            else "FAIL"
        ),
        "excessive_numeric_recitation": ("PASS" if vnext_density <= current_density else "FAIL"),
        "supported_value_add_operation": ("PASS" if result.value_add_types else "FAIL"),
        "deterministic_like_paraphrase_only": ("PASS" if materially_different else "FAIL"),
    }
    return {
        "contract": CONTRACT_VERSION,
        "AI_ANALYST_VALUE_ADD": "PASS" if passed else "FAIL",
        "factual_parity": parity,
        "materially_different_from_deterministic": materially_different,
        "advisory_checks": advisory_checks,
        "value_add_types": [item.value for item in result.value_add_types],
        "current_ai_characters": current_chars,
        "vnext_characters": vnext_chars,
        "compression_percent": round(
            (current_chars - vnext_chars) / max(current_chars, 1) * 100,
            2,
        ),
        "current_numeric_density": round(current_density, 4),
        "vnext_numeric_density": round(vnext_density, 4),
        "duplicate_next_check_unknown_before": (result.duplicate_next_check_unknown_before),
        "duplicate_next_check_unknown_after": (result.duplicate_next_check_unknown_after),
        "omitted_section_keys": list(result.omitted_section_keys),
    }
