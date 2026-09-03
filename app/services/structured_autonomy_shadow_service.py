from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Literal

from pydantic import Field

from app.services.cross_market_decision_engine_service import (
    Confidence,
    Decision,
    DecisionEvidencePacket,
    EvidenceClaim,
    FrozenModel,
)
from app.services.directional_balance_service import (
    DirectionalBalance,
    decision_from_directional_balance,
    directional_balance_language_errors,
    render_directional_balance,
)


CONTRACT_VERSION = "structured-autonomy-decision-v2-shadow"
OUTPUT_CONTRACT = "structured-autonomy-decision-v2-shadow-output"
VALIDATOR_CONTRACT = "structured-autonomy-decision-v2-shadow-validator"
RENDERER_CONTRACT = "structured-autonomy-decision-v2-shadow-renderer"

BusinessThesisChange = Literal["STRENGTHENED", "UNCHANGED", "WEAKENED", "UNRESOLVED"]
NewBuyerStance = Literal["ATTRACTIVE", "WAIT", "AVOID"]
PreferredEntryMode = Literal["PULLBACK", "CONFIRMATION", "BOTH", "NONE"]
HolderStance = Literal["HOLDABLE", "REVIEW", "REDUCE"]
SellDriverClass = Literal[
    "SECTOR_NORMAL",
    "DETERIORATION_SIGNAL",
    "STRUCTURAL_RISK",
    "OTHER_EVIDENCE",
]
UnknownTreatmentKind = Literal[
    "CONFIDENCE_LIMIT",
    "CONFIRMATION_REQUIRED",
    "DIRECTIONAL_NEGATIVE",
]


class HoldLean(StrEnum):
    BUY_LEAN = "BUY_LEAN"
    NEUTRAL = "NEUTRAL"
    SELL_LEAN = "SELL_LEAN"
    NOT_HOLD = "NOT_HOLD"


class ClassifiedSellDriver(EvidenceClaim):
    classification: SellDriverClass


class UnknownTreatment(FrozenModel):
    summary: str = Field(min_length=1, max_length=420)
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=6)
    treatment: UnknownTreatmentKind
    directional_negative_basis: tuple[str, ...] = Field(max_length=6)


class NewBuyerViewV2(FrozenModel):
    stance: NewBuyerStance
    summary: str = Field(min_length=1, max_length=420)
    pullback_entry_zone_low: float | None
    pullback_entry_zone_high: float | None
    pullback_entry_basis: tuple[str, ...] = Field(max_length=6)
    breakout_confirmation_level: float | None
    breakout_confirmation_basis: tuple[str, ...] = Field(max_length=6)
    currency: str | None
    preferred_entry_mode: PreferredEntryMode
    preferred_entry_reason: str = Field(min_length=1, max_length=420)
    confirmation_condition: str = Field(min_length=1, max_length=420)


class HolderViewV2(FrozenModel):
    stance: HolderStance
    summary: str = Field(min_length=1, max_length=420)
    upside_trim_zone_low: float | None
    upside_trim_zone_high: float | None
    upside_trim_basis: tuple[str, ...] = Field(max_length=6)
    downside_review_level: float | None
    downside_review_basis: tuple[str, ...] = Field(max_length=6)
    currency: str | None
    business_invalidation_condition: str = Field(min_length=1, max_length=420)


class StructuredAutonomyCandidate(FrozenModel):
    ticker: str
    decision: Decision
    directional_balance: DirectionalBalance
    decision_confidence: Confidence
    business_thesis_change: BusinessThesisChange
    business_thesis_context: EvidenceClaim
    earnings_estimate_context: EvidenceClaim
    market_expectation_context: EvidenceClaim
    valuation_context: EvidenceClaim
    price_timing_context: EvidenceClaim
    risk_context: EvidenceClaim
    sector_interpretation: EvidenceClaim
    buy_drivers: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=4)
    sell_drivers: tuple[ClassifiedSellDriver, ...] = Field(min_length=1, max_length=4)
    dominant_evidence: EvidenceClaim
    uncertainty_limit: EvidenceClaim
    core_judgment: EvidenceClaim
    unknown_treatments: tuple[UnknownTreatment, ...] = Field(min_length=1, max_length=4)
    new_buyer_view: NewBuyerViewV2
    holder_view: HolderViewV2
    reevaluation_up: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)
    reevaluation_down: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)


class StructuredAutonomyBatch(FrozenModel):
    contract: Literal["structured-autonomy-decision-v2-shadow-output"] = OUTPUT_CONTRACT
    packet_id: str
    candidates: tuple[StructuredAutonomyCandidate, ...] = Field(min_length=1, max_length=4)


class StructuredAutonomyValidation(FrozenModel):
    contract: str = VALIDATOR_CONTRACT
    valid: bool
    errors: tuple[str, ...]


class RenderedStructuredAutonomy(FrozenModel):
    contract: str = RENDERER_CONTRACT
    ticker: str
    decision: Decision
    lean: HoldLean
    text: str
    validation: StructuredAutonomyValidation


_ORDER_LANGUAGE = re.compile(
    r"시장가|지정가|(?:매수|매도)\s*주문|주문\s*실행|전량\s*(?:매도|매수)|"
    r"포지션\s*크기|buy\s+now|sell\s+now",
    re.IGNORECASE,
)
_MANDATORY_SELL = re.compile(r"자동\s*매도|반드시\s*매도|무조건\s*매도|매도\s*목표가")
_STOP_LOSS = re.compile(r"손절|stop[- ]?loss", re.IGNORECASE)
_TARGET_PRICE = re.compile(r"목표가|적정가|target\s*price", re.IGNORECASE)
_UNSUPPORTED_METRIC = re.compile(
    r"FCF\s*(?:yield|수익률|주당)|EV\s*/\s*FCF|P\s*/\s*FCF|"
    r"\b(?:ROIC|CCC|DSO|DPO)\b|runway\s*(?:개월|months?)",
    re.IGNORECASE,
)
_NEGATED_PROHIBITED_LANGUAGE = re.compile(
    r"아니다|아니며|아니고|아니라|아닌|않는다|않으며|않고|금지"
)
_PROSE_NUMBER = re.compile(r"(?<![A-Za-z])[-+]?\d[\d,.]*(?:\.\d+)?")
_KOREAN_PROSE = re.compile(r"[가-힣]")
_DETAIL_JUDGMENT = re.compile(
    r"AI\s*분석\s*판단|종합\s*방향|판단\s*균형|판단\s*방향|판단\s*확신도|"
    r"투자\s*논리\s*:|사업\s*논리\s*상태|신규진입\s*관점|보유자\s*관점|"
    r"재평가\s*조건|핵심\s*판단"
)
_DETAIL_HEADINGS = (
    "📈 사업·실적",
    "👁 핵심 감시",
    "📐 현재 가격 구조",
    "🧭 기존 등록 가격 규칙",
    "📐 Valuation",
    "📊 수급",
    "⚠️ 데이터 주의",
    "📌 다음 확인",
)


def derive_hold_lean(decision: Decision, balance: DirectionalBalance) -> HoldLean:
    if decision != "HOLD":
        return HoldLean.NOT_HOLD
    if balance.buy == 5.5 and balance.sell == 4.5:
        return HoldLean.BUY_LEAN
    if balance.buy == 4.5 and balance.sell == 5.5:
        return HoldLean.SELL_LEAN
    return HoldLean.NEUTRAL


def hold_lean_flip(prior: HoldLean, current: HoldLean) -> bool:
    return {prior, current} == {HoldLean.BUY_LEAN, HoldLean.SELL_LEAN}


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _same(left: float, right: float) -> bool:
    return math.isclose(left, right, abs_tol=1e-6)


def allowed_price_refs(price_map: Mapping[str, object]) -> set[str]:
    refs: set[str] = set()
    for name in ("nearest_supports", "nearest_resistances"):
        rows = price_map.get(name)
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
            for row in rows:
                if not isinstance(row, Mapping):
                    continue
                if row.get("basis_ref"):
                    refs.add(str(row["basis_ref"]))
                refs.update(str(value) for value in row.get("source_refs") or ())
    for name in ("major_support", "major_resistance", "registered_price_rules", "chart_invalidation"):
        row = price_map.get(name)
        if not isinstance(row, Mapping):
            continue
        if row.get("basis_ref"):
            refs.add(str(row["basis_ref"]))
        refs.update(str(value) for value in row.get("source_refs") or ())
    if price_map.get("current_price_ref"):
        refs.add(str(price_map["current_price_ref"]))
    return refs


def allowed_pullback_zones(price_map: Mapping[str, object]) -> tuple[tuple[float, float, str], ...]:
    current = _as_float(price_map.get("current_close"))
    rows: list[tuple[float, float, str]] = []
    for name in ("nearest_supports",):
        values = price_map.get(name)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            continue
        for value in values:
            if not isinstance(value, Mapping):
                continue
            low = _as_float(value.get("zone_low"))
            high = _as_float(value.get("zone_high"))
            ref = value.get("basis_ref")
            if low is not None and high is not None and ref and (current is None or low <= current):
                rows.append((low, high, str(ref)))
    major = price_map.get("major_support")
    if isinstance(major, Mapping):
        low = _as_float(major.get("zone_low"))
        high = _as_float(major.get("zone_high"))
        ref = major.get("basis_ref")
        if low is not None and high is not None and ref and (current is None or low <= current):
            rows.append((low, high, str(ref)))
    registered = price_map.get("registered_price_rules")
    if isinstance(registered, Mapping):
        low = _as_float(registered.get("support_zone_low"))
        high = _as_float(registered.get("support_zone_high"))
        ref = registered.get("basis_ref")
        if low is not None and high is not None and ref and (current is None or low <= current):
            rows.append((low, high, str(ref)))
    return tuple(dict.fromkeys(rows))


def allowed_confirmation_levels(price_map: Mapping[str, object]) -> tuple[tuple[float, str], ...]:
    current = _as_float(price_map.get("current_close"))
    rows: list[tuple[float, str]] = []
    values = price_map.get("nearest_resistances")
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        for value in values:
            if not isinstance(value, Mapping):
                continue
            level = _as_float(value.get("zone_high"))
            ref = value.get("basis_ref")
            if level is not None and ref and (current is None or level > current):
                rows.append((level, str(ref)))
    major = price_map.get("major_resistance")
    if isinstance(major, Mapping):
        level = _as_float(major.get("zone_high"))
        ref = major.get("basis_ref")
        if level is not None and ref and (current is None or level > current):
            rows.append((level, str(ref)))
    registered = price_map.get("registered_price_rules")
    if isinstance(registered, Mapping):
        level = _as_float(registered.get("confirmation_price"))
        ref = registered.get("basis_ref")
        if level is not None and ref and (current is None or level > current):
            rows.append((level, str(ref)))
    return tuple(dict.fromkeys(rows))


def allowed_trim_zones(price_map: Mapping[str, object]) -> tuple[tuple[float, float, str], ...]:
    current = _as_float(price_map.get("current_close"))
    rows: list[tuple[float, float, str]] = []
    values = price_map.get("nearest_resistances")
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        for value in values:
            if not isinstance(value, Mapping):
                continue
            low = _as_float(value.get("zone_low"))
            high = _as_float(value.get("zone_high"))
            ref = value.get("basis_ref")
            if low is not None and high is not None and ref and (current is None or high > current):
                rows.append((low, high, str(ref)))
    major = price_map.get("major_resistance")
    if isinstance(major, Mapping):
        low = _as_float(major.get("zone_low"))
        high = _as_float(major.get("zone_high"))
        ref = major.get("basis_ref")
        if low is not None and high is not None and ref and (current is None or high > current):
            rows.append((low, high, str(ref)))
    return tuple(dict.fromkeys(rows))


def allowed_downside_levels(price_map: Mapping[str, object]) -> tuple[tuple[float, str], ...]:
    current = _as_float(price_map.get("current_close"))
    rows: list[tuple[float, str]] = []
    registered = price_map.get("registered_price_rules")
    if isinstance(registered, Mapping) and registered.get("basis_ref"):
        for name in ("warning_price", "invalidation_price"):
            level = _as_float(registered.get(name))
            if level is not None and (current is None or level <= current):
                rows.append((level, str(registered["basis_ref"])))
    invalidation = price_map.get("chart_invalidation")
    if isinstance(invalidation, Mapping) and invalidation.get("basis_ref"):
        level = _as_float(invalidation.get("price"))
        if level is not None and (current is None or level <= current):
            rows.append((level, str(invalidation["basis_ref"])))
    return tuple(dict.fromkeys(rows))


def _claim_sequence(candidate: StructuredAutonomyCandidate) -> tuple[EvidenceClaim, ...]:
    return (
        candidate.business_thesis_context,
        candidate.earnings_estimate_context,
        candidate.market_expectation_context,
        candidate.valuation_context,
        candidate.price_timing_context,
        candidate.risk_context,
        candidate.sector_interpretation,
        *candidate.buy_drivers,
        *candidate.sell_drivers,
        candidate.dominant_evidence,
        candidate.uncertainty_limit,
        candidate.core_judgment,
        *candidate.reevaluation_up,
        *candidate.reevaluation_down,
    )


def _prose(candidate: StructuredAutonomyCandidate) -> tuple[str, ...]:
    buyer = candidate.new_buyer_view
    holder = candidate.holder_view
    return tuple(claim.text for claim in _claim_sequence(candidate)) + tuple(
        unknown.summary for unknown in candidate.unknown_treatments
    ) + (
        buyer.summary,
        buyer.preferred_entry_reason,
        buyer.confirmation_condition,
        holder.summary,
        holder.business_invalidation_condition,
    )


def _has_assertive_match(pattern: re.Pattern[str], text: str) -> bool:
    for sentence in re.split(r"(?<=[.!?。])\s+|\n+", text):
        if pattern.search(sentence) and not _NEGATED_PROHIBITED_LANGUAGE.search(sentence):
            return True
    return False


def validate_structured_autonomy_candidate(
    packet: DecisionEvidencePacket,
    candidate: StructuredAutonomyCandidate,
    *,
    price_map: Mapping[str, object],
    industry: str,
) -> StructuredAutonomyValidation:
    errors: list[str] = []
    if candidate.ticker != packet.ticker:
        errors.append("ticker_identity_mismatch")
    if decision_from_directional_balance(candidate.directional_balance) != candidate.decision:
        errors.append("decision_balance_mismatch")

    evidence_refs = {row.ref_id for row in packet.evidence}
    valid_refs = evidence_refs | allowed_price_refs(price_map)
    cited: list[str] = []
    for claim in _claim_sequence(candidate):
        cited.extend(claim.evidence_refs)
    for unknown in candidate.unknown_treatments:
        cited.extend(unknown.evidence_refs)
        cited.extend(unknown.directional_negative_basis)
        if unknown.treatment == "DIRECTIONAL_NEGATIVE" and not unknown.directional_negative_basis:
            errors.append("unknown_directional_negative_without_economic_basis")
        if unknown.treatment != "DIRECTIONAL_NEGATIVE" and unknown.directional_negative_basis:
            errors.append("unknown_nonnegative_has_directional_basis")
    buyer = candidate.new_buyer_view
    holder = candidate.holder_view
    cited.extend(buyer.pullback_entry_basis)
    cited.extend(buyer.breakout_confirmation_basis)
    cited.extend(holder.upside_trim_basis)
    cited.extend(holder.downside_review_basis)
    if any(ref not in valid_refs for ref in cited):
        errors.append("unsupported_evidence_ref")

    evidence_categories = {row.ref_id: row.category.value for row in packet.evidence}
    for unknown in candidate.unknown_treatments:
        if unknown.treatment != "DIRECTIONAL_NEGATIVE":
            continue
        if not any(
            evidence_categories.get(ref) not in {None, "unknown"}
            for ref in unknown.directional_negative_basis
        ):
            errors.append("unknown_directional_negative_without_non_unknown_evidence")

    pullbacks = allowed_pullback_zones(price_map)
    confirmations = allowed_confirmation_levels(price_map)
    trims = allowed_trim_zones(price_map)
    downside = allowed_downside_levels(price_map)
    p_low = buyer.pullback_entry_zone_low
    p_high = buyer.pullback_entry_zone_high
    if p_low is None or p_high is None:
        if p_low is not None or p_high is not None or buyer.pullback_entry_basis:
            errors.append("partial_pullback_zone")
        if pullbacks:
            errors.append("supported_pullback_zone_not_preserved")
    else:
        matching = [row for row in pullbacks if _same(p_low, row[0]) and _same(p_high, row[1])]
        if not matching:
            errors.append("unsupported_pullback_zone")
        elif not set(buyer.pullback_entry_basis).intersection(row[2] for row in matching):
            errors.append("pullback_basis_mismatch")

    confirmation = buyer.breakout_confirmation_level
    if confirmation is None:
        if buyer.breakout_confirmation_basis:
            errors.append("confirmation_basis_without_level")
        if confirmations:
            errors.append("supported_confirmation_level_not_preserved")
    else:
        matching_levels = [row for row in confirmations if _same(confirmation, row[0])]
        if not matching_levels:
            errors.append("unsupported_confirmation_level")
        elif not set(buyer.breakout_confirmation_basis).intersection(
            row[1] for row in matching_levels
        ):
            errors.append("confirmation_basis_mismatch")

    has_pullback = p_low is not None and p_high is not None
    has_confirmation = confirmation is not None
    expected_modes = {
        (True, True): {"PULLBACK", "CONFIRMATION", "BOTH"},
        (True, False): {"PULLBACK"},
        (False, True): {"CONFIRMATION"},
        (False, False): {"NONE"},
    }[(has_pullback, has_confirmation)]
    if buyer.preferred_entry_mode not in expected_modes:
        errors.append("preferred_entry_mode_inconsistent")

    t_low = holder.upside_trim_zone_low
    t_high = holder.upside_trim_zone_high
    if t_low is None or t_high is None:
        if t_low is not None or t_high is not None or holder.upside_trim_basis:
            errors.append("partial_trim_zone")
        if trims:
            errors.append("supported_trim_zone_not_preserved")
    else:
        matching_trims = [row for row in trims if _same(t_low, row[0]) and _same(t_high, row[1])]
        if not matching_trims:
            errors.append("unsupported_trim_zone")
        elif not set(holder.upside_trim_basis).intersection(row[2] for row in matching_trims):
            errors.append("trim_basis_mismatch")

    if holder.downside_review_level is None:
        if holder.downside_review_basis:
            errors.append("downside_basis_without_level")
    else:
        matching_downside = [row for row in downside if _same(holder.downside_review_level, row[0])]
        if not matching_downside:
            errors.append("unsupported_downside_review")
        elif not set(holder.downside_review_basis).intersection(
            row[1] for row in matching_downside
        ):
            errors.append("downside_basis_mismatch")

    prose = _prose(candidate)
    errors.extend(directional_balance_language_errors(prose))
    joined = "\n".join(prose)
    if _ORDER_LANGUAGE.search(joined):
        errors.append("mandatory_trade_language")
    if _has_assertive_match(_MANDATORY_SELL, joined):
        errors.append("mandatory_sell_language")
    if _has_assertive_match(_STOP_LOSS, joined):
        errors.append("invented_stop_loss")
    if _TARGET_PRICE.search(joined):
        errors.append("target_price_language")
    if _UNSUPPORTED_METRIC.search(joined):
        errors.append("unsupported_metric_or_inference")
    if _PROSE_NUMBER.search(joined):
        errors.append("numeric_prose_outside_structured_fields")
    if any(not _KOREAN_PROSE.search(text) for text in prose):
        errors.append("mixed_language_decision_prose")

    if "biotech" in industry.lower() or "biotechnology" in industry.lower():
        if candidate.decision == "SELL" and not any(
            row.classification in {"DETERIORATION_SIGNAL", "STRUCTURAL_RISK"}
            for row in candidate.sell_drivers
        ):
            errors.append("biotech_sell_without_deterioration_or_structural_risk")

    return StructuredAutonomyValidation(valid=not errors, errors=tuple(dict.fromkeys(errors)))


def sanitize_detail_body(text: str) -> str:
    output: list[str] = []
    keep = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(_DETAIL_HEADINGS):
            keep = True
            output.extend(([""] if output and output[-1] else []) + [stripped])
            continue
        if stripped and re.match(r"^[^\w\s가-힣]", stripped) and not stripped.startswith("•"):
            keep = False
            continue
        if _DETAIL_JUDGMENT.search(stripped):
            continue
        if keep:
            output.append(line.rstrip())
    return "\n".join(output).strip()


def _judgment_owned_text(text: str) -> str:
    boundaries = [
        position
        for heading in _DETAIL_HEADINGS
        if (position := text.find(f"\n{heading}")) >= 0
    ]
    return text[: min(boundaries)] if boundaries else text


def _display_number(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _currency_value(value: float, currency: str | None) -> str:
    prefix = "$" if currency == "USD" else f"{currency} " if currency else ""
    return prefix + _display_number(value)


def _zone(low: float, high: float, currency: str | None) -> str:
    if _same(low, high):
        return _currency_value(low, currency)
    return f"{_currency_value(low, currency)}~{_currency_value(high, currency)}"


def _lean_language(lean: HoldLean) -> str:
    return {
        HoldLean.BUY_LEAN: "BUY 쪽 HOLD",
        HoldLean.NEUTRAL: "중립 HOLD",
        HoldLean.SELL_LEAN: "SELL 쪽 HOLD",
        HoldLean.NOT_HOLD: "해당 없음",
    }[lean]


def _thesis_language(value: BusinessThesisChange) -> str:
    return {
        "STRENGTHENED": "강화",
        "UNCHANGED": "유지",
        "WEAKENED": "약화",
        "UNRESOLVED": "미확정",
    }[value]


def render_structured_autonomy_message(
    packet: DecisionEvidencePacket,
    candidate: StructuredAutonomyCandidate,
    *,
    price_map: Mapping[str, object],
    industry: str,
    base_detail_text: str,
) -> RenderedStructuredAutonomy:
    validation = validate_structured_autonomy_candidate(
        packet, candidate, price_map=price_map, industry=industry
    )
    lean = derive_hold_lean(candidate.decision, candidate.directional_balance)
    buyer = candidate.new_buyer_view
    holder = candidate.holder_view
    confidence = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}[
        candidate.decision_confidence
    ]
    preferred = {
        "PULLBACK": "눌림",
        "CONFIRMATION": "추세 확인",
        "BOTH": "눌림과 추세 확인",
        "NONE": "현재 없음",
    }[buyer.preferred_entry_mode]
    lines = [
        f"🏢 {packet.company_name}({packet.ticker})",
        "",
        f"🧠 종합 방향: {candidate.decision}",
        f"판단 균형: {render_directional_balance(candidate.directional_balance)}",
    ]
    if lean != HoldLean.NOT_HOLD:
        lines.append(f"판단 방향: {_lean_language(lean)}")
    lines.extend(
        [
            f"판단 확신도: {confidence}",
            f"사업 논리 상태: {_thesis_language(candidate.business_thesis_change)}",
            f"현재 신규진입: {buyer.stance}",
            "",
            "🎯 핵심 판단",
            f"• {candidate.core_judgment.text}",
            "",
            "🆕 신규진입 관점",
            f"• {buyer.summary}",
        ]
    )
    if buyer.pullback_entry_zone_low is not None and buyer.pullback_entry_zone_high is not None:
        zone = _zone(
            buyer.pullback_entry_zone_low,
            buyer.pullback_entry_zone_high,
            buyer.currency,
        )
        if buyer.stance == "AVOID":
            lines.append(f"• 재검토 가격 조건: {zone} · 가격만으로 진입하지 않음")
        else:
            lines.append(f"• 눌림 진입 검토: {zone} · 지지 확인 시 재평가")
    if buyer.breakout_confirmation_level is not None:
        level = _currency_value(buyer.breakout_confirmation_level, buyer.currency)
        if buyer.stance == "AVOID":
            lines.append(f"• 상향 재검토 조건: {level} 돌파·안착과 사업 근거 확인")
        else:
            lines.append(f"• 추세 확인 가격: {level} · 돌파·안착 시 신규진입 재평가")
    lines.extend(
        [
            f"• 현재 선호: {preferred}",
            f"• 이유: {buyer.preferred_entry_reason}",
            f"• 확인 조건: {buyer.confirmation_condition}",
            "",
            "💼 보유자 관점",
            f"• 현재 관점: {holder.stance}",
            f"• {holder.summary}",
        ]
    )
    if holder.upside_trim_zone_low is not None and holder.upside_trim_zone_high is not None:
        lines.append(
            "• 상방 보유 관점 재검토: "
            + _zone(
                holder.upside_trim_zone_low,
                holder.upside_trim_zone_high,
                holder.currency,
            )
            + " · 저항 거부 시 기대·가치평가 재점검"
        )
    if holder.downside_review_level is not None:
        lines.append(
            "• 하방 재점검: "
            + _currency_value(holder.downside_review_level, holder.currency)
        )
    lines.extend(
        [
            f"• 기업가치 무효화 조건: {holder.business_invalidation_condition}",
            "",
            "🔄 재평가 조건",
            f"• BUY 쪽: {candidate.reevaluation_up[0].text}",
            f"• SELL 쪽: {candidate.reevaluation_down[0].text}",
        ]
    )
    detail = sanitize_detail_body(base_detail_text)
    if detail:
        lines.extend(["", detail])
    text = "\n".join(lines).rstrip() + "\n"
    message_errors: list[str] = []
    if _DETAIL_JUDGMENT.search(detail):
        message_errors.append("duplicate_judgment_authority")
    if text.count("🧠 종합 방향:") != 1 or text.count("🎯 핵심 판단") != 1:
        message_errors.append("duplicate_judgment_section")
    if text.count("현재 신규진입:") != 1:
        message_errors.append("top_label_entry_stance_ambiguity")
    if buyer.stance == "AVOID" and "눌림 진입 검토:" in text:
        message_errors.append("avoid_rendered_as_actionable_entry")
    if candidate.core_judgment.text in detail:
        message_errors.append("duplicated_judgment_paragraph")
    if _has_assertive_match(_MANDATORY_SELL, text) or _ORDER_LANGUAGE.search(text):
        message_errors.append("mandatory_trade_language")
    if message_errors:
        validation = validation.model_copy(
            update={
                "valid": False,
                "errors": tuple(dict.fromkeys((*validation.errors, *message_errors))),
            }
        )
    return RenderedStructuredAutonomy(
        ticker=packet.ticker,
        decision=candidate.decision,
        lean=lean,
        text=text,
        validation=validation,
    )


def structured_autonomy_message_quality(
    rendered: Sequence[RenderedStructuredAutonomy],
) -> dict[str, object]:
    errors: list[str] = []
    if any(not row.validation.valid for row in rendered):
        errors.append("candidate_or_message_validation_failed")
    if any(len(row.text) > 4096 for row in rendered):
        errors.append("message_too_long")
    substantive: list[str] = []
    per_ticker: list[dict[str, object]] = []
    for row in rendered:
        local: list[str] = []
        judgment_text = _judgment_owned_text(row.text)
        for line in judgment_text.splitlines():
            normalized = re.sub(r"\s+", " ", line.strip().removeprefix("• "))
            if len(normalized) >= 36:
                local.append(normalized)
                substantive.append(normalized)
        duplicates = sorted({line for line, count in Counter(local).items() if count > 1})
        per_ticker.append(
            {
                "ticker": row.ticker,
                "character_count": len(row.text),
                "duplicate_substantive_lines": duplicates,
                "validation": "PASS" if row.validation.valid and not duplicates else "FAIL",
            }
        )
        if duplicates:
            errors.append("within_ticker_substantive_repetition")
    repeated = sorted({line for line, count in Counter(substantive).items() if count > 1})
    if repeated:
        errors.append("cross_ticker_substantive_repetition")
    return {
        "contract": "structured-autonomy-message-quality-v2-shadow",
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
        "message_count": len(rendered),
        "average_character_count": (
            round(sum(len(row.text) for row in rendered) / len(rendered), 2)
            if rendered
            else 0
        ),
        "max_character_count": max((len(row.text) for row in rendered), default=0),
        "repeated_substantive_span_count": len(repeated),
        "repeated_substantive_spans": repeated,
        "rows": per_ticker,
    }
