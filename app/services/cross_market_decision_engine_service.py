from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.services.ohlcv_feature_engine_service import MultiTimeframeFeaturePacket


CONTRACT_VERSION = "cross-market-ai-decision-engine-v1"
EVIDENCE_CONTRACT = "decision-evidence-packet-v1"
VALIDATOR_CONTRACT = "decision-validator-ownership-v1"
RENDERER_CONTRACT = "decision-shadow-renderer-v1"

Decision = Literal["BUY", "HOLD", "SELL"]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]
Timing = Literal["FAVORABLE", "NEUTRAL", "UNFAVORABLE", "INSUFFICIENT"]


class EvidenceCategory(StrEnum):
    THESIS = "thesis"
    EARNINGS = "earnings"
    EARNINGS_QUALITY = "earnings_quality"
    EXPECTATIONS = "expectations"
    VALUATION = "valuation"
    CATALYSTS = "catalysts"
    RISKS = "risks"
    MACRO = "macro"
    MARKET = "market"
    FLOWS = "flows"
    PRICE_STRUCTURE = "price_structure"
    TECHNICAL_FEATURE = "technical_feature"
    UNKNOWN = "unknown"
    QUALITY = "quality"


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DecisionEvidenceRef(FrozenModel):
    ref_id: str
    category: EvidenceCategory
    label: str
    statement: str
    as_of: str | None = None
    value: Decimal | str | None = None
    unit: str | None = None
    source_ref: str
    numeric_prose_eligible: bool = False


class DecisionEvidencePacket(FrozenModel):
    contract: str = EVIDENCE_CONTRACT
    packet_id: str
    ticker: str
    company_name: str
    market: Literal["kr", "us"]
    assessment_date: str
    horizon: str
    reasoning_grade: Literal["VERY_HIGH"] = "VERY_HIGH"
    backend_reasoning_effort: Literal["xhigh"] = "xhigh"
    evidence: tuple[DecisionEvidenceRef, ...]
    prohibited_claims: tuple[str, ...]
    data_quality_cautions: tuple[str, ...] = ()
    evidence_sha256: str


class EvidenceClaim(FrozenModel):
    text: str = Field(min_length=1, max_length=420)
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=6)


class DecisionCandidate(FrozenModel):
    ticker: str
    decision: Decision
    reasoning_grade: Literal["VERY_HIGH"]
    confidence: Confidence
    horizon: str = Field(min_length=1, max_length=80)
    timing: Timing
    decisive_reason: EvidenceClaim
    supporting_evidence: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=4)
    opposing_evidence: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=4)
    unknowns: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=4)
    change_conditions: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=4)
    selected_numeric_fact_refs: tuple[str, ...] = Field(default=(), max_length=3)
    selected_evidence_plan: tuple[EvidenceCategory, ...] = Field(min_length=3, max_length=10)


class DecisionBatchOutput(FrozenModel):
    contract: Literal["cross-market-ai-decision-output-v1"]
    decisions: tuple[DecisionCandidate, ...]


class TemporalDecisionCandidate(FrozenModel):
    checkpoint_id: str
    source_packet_id: str
    source_cutoff: str
    candidate: DecisionCandidate


class TemporalDecisionBatchOutput(FrozenModel):
    contract: Literal["cross-market-ai-temporal-decision-output-v1"]
    checkpoints: tuple[TemporalDecisionCandidate, ...]


class DecisionValidationResult(FrozenModel):
    contract: str = VALIDATOR_CONTRACT
    valid: bool
    errors: tuple[str, ...]
    numeric_claim_count: int
    automatically_bound_numeric_count: int
    manual_numeric_count: int = 0
    unresolved_numeric_count: int = 0


class RenderedDecision(FrozenModel):
    contract: str = RENDERER_CONTRACT
    ticker: str
    decision: Decision
    text: str
    selected_numeric_fact_refs: tuple[str, ...]
    validation: DecisionValidationResult


_ORDER_LANGUAGE = re.compile(
    r"시장가|지정가|(?:매수|매도)\s*주문|주문\s*실행|전량\s*매도|전량\s*매수|"
    r"포지션\s*크기|(?:trade|position|brokerage)\s*(?:order\s*)?size|"
    r"buy\s+now|sell\s+now",
    re.IGNORECASE,
)
_UNSUPPORTED = re.compile(
    r"FCF\s*(?:yield|수익률|주당)|EV\s*/\s*FCF|P\s*/\s*FCF|"
    r"runway\s*(?:개월|months?)",
    re.IGNORECASE,
)
_EXACT_NUMBER = re.compile(
    r"(?<![A-Za-z])[-+]?\d[\d,.]*(?:\.\d+)?\s*(?:%|원|달러|USD|KRW|배|주|MW|GW)"
)


def _stable_ref(prefix: str, *parts: object) -> str:
    material = "|".join(str(part) for part in parts)
    return f"{prefix}:" + hashlib.sha256(material.encode()).hexdigest()[:20]


def _canonical_sha(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _compact(value: object, limit: int = 900) -> str:
    if isinstance(value, str):
        text = value.strip()
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _category_for_fact(row: Mapping[str, object]) -> EvidenceCategory:
    fact_type = str(row.get("fact_type") or "").lower()
    fact_id = str(row.get("fact_id") or "").lower()
    joined = f"{fact_type} {fact_id}"
    if "earning" in joined or "financial" in joined or "cash_flow" in joined:
        return EvidenceCategory.EARNINGS
    if "valuation" in joined or "multiple" in joined:
        return EvidenceCategory.VALUATION
    if "market" in joined or "macro" in joined:
        return EvidenceCategory.MARKET
    if "flow" in joined or "supply" in joined or "position" in joined:
        return EvidenceCategory.FLOWS
    if "price" in joined or "chart" in joined or "structure" in joined:
        return EvidenceCategory.PRICE_STRUCTURE
    if "quality" in joined or "identity" in joined or "basis" in joined:
        return EvidenceCategory.QUALITY
    return EvidenceCategory.EARNINGS_QUALITY


def _add_text_refs(
    refs: list[DecisionEvidenceRef],
    *,
    ticker: str,
    category: EvidenceCategory,
    label: str,
    values: object,
    source_ref: str,
    as_of: str | None,
) -> None:
    rows = values if isinstance(values, list) else [values]
    for index, value in enumerate(rows):
        if value is None or not str(value).strip():
            continue
        refs.append(
            DecisionEvidenceRef(
                ref_id=_stable_ref("decision-evidence", ticker, category, label, index, _compact(value)),
                category=category,
                label=label,
                statement=_compact(value),
                as_of=as_of,
                source_ref=source_ref,
            )
        )


def build_decision_evidence_packet(
    *,
    packet: Mapping[str, object],
    stock: Mapping[str, object],
    technical_features: MultiTimeframeFeaturePacket,
) -> DecisionEvidencePacket:
    ticker = str(stock.get("ticker") or "")
    if not ticker or technical_features.ticker != ticker:
        raise ValueError("ticker_mismatch")
    packet_id = str(packet.get("packet_id") or "")
    market = str(packet.get("market") or "").lower()
    if market not in {"kr", "us"}:
        raise ValueError("unsupported_market")
    assessment_date = str(packet.get("assessment_date") or packet.get("generated_at") or "")[:10]
    thesis = stock.get("thesis") if isinstance(stock.get("thesis"), Mapping) else {}
    assert isinstance(thesis, Mapping)
    horizon = str(thesis.get("time_horizon") or "6-24개월")
    refs: list[DecisionEvidenceRef] = []

    _add_text_refs(refs, ticker=ticker, category=EvidenceCategory.THESIS, label="핵심 투자 논리", values=thesis.get("core_thesis"), source_ref="stock.thesis.core_thesis", as_of=assessment_date)
    _add_text_refs(refs, ticker=ticker, category=EvidenceCategory.THESIS, label="논리 강화 조건", values=thesis.get("strengthen_signals") or [], source_ref="stock.thesis.strengthen_signals", as_of=assessment_date)
    _add_text_refs(refs, ticker=ticker, category=EvidenceCategory.RISKS, label="논리 약화 조건", values=thesis.get("weaken_signals") or [], source_ref="stock.thesis.weaken_signals", as_of=assessment_date)
    _add_text_refs(refs, ticker=ticker, category=EvidenceCategory.RISKS, label="무효화 조건", values=thesis.get("invalidation_signals") or [], source_ref="stock.thesis.invalidation_signals", as_of=assessment_date)
    expectations = thesis.get("market_expectations") if isinstance(thesis.get("market_expectations"), Mapping) else {}
    _add_text_refs(refs, ticker=ticker, category=EvidenceCategory.EXPECTATIONS, label="시장 기대", values=expectations, source_ref="stock.thesis.market_expectations", as_of=str(expectations.get("as_of_date") or assessment_date))
    _add_text_refs(refs, ticker=ticker, category=EvidenceCategory.MACRO, label="거시 전달경로", values=thesis.get("macro_exposures") or [], source_ref="stock.thesis.macro_exposures", as_of=assessment_date)
    _add_text_refs(refs, ticker=ticker, category=EvidenceCategory.UNKNOWN, label="남은 미확인", values=stock.get("unknowns") or [], source_ref="stock.unknowns", as_of=assessment_date)
    _add_text_refs(refs, ticker=ticker, category=EvidenceCategory.MARKET, label="시장 전달", values=stock.get("market_transmission") or {}, source_ref="stock.market_transmission", as_of=assessment_date)
    _add_text_refs(refs, ticker=ticker, category=EvidenceCategory.PRICE_STRUCTURE, label="가격 구조", values=stock.get("current_price_context") or {}, source_ref="stock.current_price_context", as_of=assessment_date)

    fact_catalog = stock.get("fact_catalog")
    if isinstance(fact_catalog, list):
        for row in fact_catalog:
            if not isinstance(row, Mapping):
                continue
            fact_id = str(row.get("fact_id") or "")
            if not fact_id:
                continue
            refs.append(
                DecisionEvidenceRef(
                    ref_id=f"canonical:{fact_id}",
                    category=_category_for_fact(row),
                    label=str(row.get("fact_type") or fact_id),
                    statement=_compact(row.get("fields") or {}),
                    as_of=str(row.get("as_of_date") or assessment_date),
                    source_ref=f"stock.fact_catalog.{fact_id}",
                )
            )

    for timeframe in (technical_features.monthly, technical_features.weekly, technical_features.daily):
        for fact in timeframe.facts:
            refs.append(
                DecisionEvidenceRef(
                    ref_id=fact.fact_id,
                    category=EvidenceCategory.TECHNICAL_FEATURE,
                    label=f"{fact.timeframe}:{fact.semantic}",
                    statement=f"{fact.timeframe} {fact.semantic}",
                    as_of=fact.as_of,
                    value=fact.value,
                    unit=fact.unit,
                    source_ref=f"technical_features.{fact.timeframe}.{fact.semantic}",
                    numeric_prose_eligible=isinstance(fact.value, Decimal),
                )
            )

    unique = {ref.ref_id: ref for ref in refs}
    normalized = tuple(unique[key] for key in sorted(unique))
    cautions = tuple(str(value) for value in stock.get("data_cautions") or ())
    payload = [ref.model_dump(mode="json") for ref in normalized]
    return DecisionEvidencePacket(
        packet_id=packet_id,
        ticker=ticker,
        company_name=str(stock.get("company_name") or ticker),
        market=market,
        assessment_date=assessment_date,
        horizon=horizon,
        evidence=normalized,
        prohibited_claims=(
            "automated_trade_or_order",
            "fixed_weight_score_decision",
            "unsupported_numeric_calculation",
            "valuation_from_technical_indicator",
            "future_evidence_or_lookahead",
        ),
        data_quality_cautions=cautions,
        evidence_sha256=_canonical_sha(payload),
    )


def compact_ai_context(packet: DecisionEvidencePacket) -> dict[str, object]:
    """Strip formulas and parser details while preserving every safe evidence value."""
    return {
        "contract": packet.contract,
        "packet_id": packet.packet_id,
        "ticker": packet.ticker,
        "company_name": packet.company_name,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "horizon": packet.horizon,
        "reasoning_grade": packet.reasoning_grade,
        "backend_reasoning_effort": packet.backend_reasoning_effort,
        "evidence": [
            {
                "ref_id": ref.ref_id,
                "category": ref.category,
                "label": ref.label,
                "statement": ref.statement,
                "as_of": ref.as_of,
                "value": str(ref.value) if ref.value is not None else None,
                "unit": ref.unit,
                "numeric_prose_eligible": ref.numeric_prose_eligible,
            }
            for ref in packet.evidence
        ],
        "prohibited_claims": packet.prohibited_claims,
        "data_quality_cautions": packet.data_quality_cautions,
    }


def _candidate_texts(candidate: DecisionCandidate) -> tuple[str, ...]:
    claims = (
        candidate.decisive_reason,
        *candidate.supporting_evidence,
        *candidate.opposing_evidence,
        *candidate.unknowns,
        *candidate.change_conditions,
    )
    return tuple(claim.text for claim in claims) + (candidate.horizon,)


def validate_decision_candidate(
    packet: DecisionEvidencePacket,
    candidate: DecisionCandidate,
) -> DecisionValidationResult:
    errors: list[str] = []
    refs = {ref.ref_id: ref for ref in packet.evidence}
    if candidate.ticker != packet.ticker:
        errors.append("ticker_mismatch")
    if candidate.horizon != packet.horizon:
        errors.append("horizon_not_owned_by_monitoring_thesis")
    all_claims = (
        candidate.decisive_reason,
        *candidate.supporting_evidence,
        *candidate.opposing_evidence,
        *candidate.unknowns,
        *candidate.change_conditions,
    )
    for claim in all_claims:
        for ref_id in claim.evidence_refs:
            if ref_id not in refs:
                errors.append(f"unknown_evidence_ref:{ref_id}")
    selected_categories = set(candidate.selected_evidence_plan)
    used_categories = {
        refs[ref_id].category
        for claim in all_claims
        for ref_id in claim.evidence_refs
        if ref_id in refs
    }
    if not used_categories.issubset(selected_categories):
        errors.append("selected_evidence_plan_incomplete")
    for text in _candidate_texts(candidate):
        if _ORDER_LANGUAGE.search(text):
            errors.append("automated_trade_or_order_language")
        if _UNSUPPORTED.search(text):
            errors.append("unsupported_metric_or_inference")
        if _EXACT_NUMBER.search(text):
            errors.append("freeform_exact_numeric_claim")

    numeric_refs: list[str] = []
    for ref_id in candidate.selected_numeric_fact_refs:
        ref = refs.get(ref_id)
        if ref is None:
            errors.append(f"unknown_numeric_fact_ref:{ref_id}")
            continue
        numeric_value = decimal_value(ref.value)
        if not ref.numeric_prose_eligible or numeric_value is None:
            errors.append(f"numeric_fact_not_prose_eligible:{ref_id}")
            continue
        numeric_refs.append(ref_id)
    if len(numeric_refs) != len(set(numeric_refs)):
        errors.append("duplicate_numeric_fact_ref")
    return DecisionValidationResult(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
        numeric_claim_count=len(candidate.selected_numeric_fact_refs),
        automatically_bound_numeric_count=len(numeric_refs),
        unresolved_numeric_count=len(candidate.selected_numeric_fact_refs) - len(numeric_refs),
    )


def _format_numeric(ref: DecisionEvidenceRef) -> str:
    value = decimal_value(ref.value)
    if value is None:
        raise ValueError("non_numeric_ref")
    if ref.unit == "percent":
        return f"{value.quantize(Decimal('0.01'))}%"
    if ref.unit in {"index", "ratio"}:
        return str(value.quantize(Decimal("0.01")))
    if ref.unit == "count":
        return str(int(value))
    return str(value.normalize())


def render_shadow_decision(
    packet: DecisionEvidencePacket,
    candidate: DecisionCandidate,
) -> RenderedDecision:
    validation = validate_decision_candidate(packet, candidate)
    if not validation.valid:
        raise ValueError("decision_candidate_invalid:" + ",".join(validation.errors))
    refs = {ref.ref_id: ref for ref in packet.evidence}
    decision_labels = {"BUY": "BUY", "HOLD": "HOLD", "SELL": "SELL"}
    confidence_labels = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}
    timing_labels = {
        "FAVORABLE": "우호적",
        "NEUTRAL": "중립",
        "UNFAVORABLE": "불리",
        "INSUFFICIENT": "판단 근거 부족",
    }
    lines = [
        f"🏢 {packet.company_name}({packet.ticker})",
        f"🧠 AI 종합 판단: {decision_labels[candidate.decision]}",
        f"추론등급: 매우 높음 | 신뢰도: {confidence_labels[candidate.confidence]}",
        f"분석 시계열: {candidate.horizon} | 단기 타이밍: {timing_labels[candidate.timing]}",
        "",
        "🎯 결정적 이유",
        f"• {candidate.decisive_reason.text}",
        "",
        "✅ 지지 근거",
        *(f"• {claim.text}" for claim in candidate.supporting_evidence),
        "",
        "⚠️ 반대 근거",
        *(f"• {claim.text}" for claim in candidate.opposing_evidence),
    ]
    if candidate.selected_numeric_fact_refs:
        lines.extend(["", "📊 확인된 기술 상태"])
        for ref_id in candidate.selected_numeric_fact_refs:
            ref = refs[ref_id]
            lines.append(f"• {ref.label}: {_format_numeric(ref)}")
    lines.extend(
        [
            "",
            "❓ 남은 미확인",
            *(f"• {claim.text}" for claim in candidate.unknowns),
            "",
            "🔄 판단 변경 조건",
            *(f"• {claim.text}" for claim in candidate.change_conditions),
            "",
            "※ 분석 등급이며 주문 또는 자동매매 지시가 아닙니다.",
        ]
    )
    return RenderedDecision(
        ticker=packet.ticker,
        decision=candidate.decision,
        text="\n".join(lines),
        selected_numeric_fact_refs=candidate.selected_numeric_fact_refs,
        validation=validation,
    )


def decision_message_quality(
    rendered: Sequence[RenderedDecision],
) -> dict[str, object]:
    errors: list[str] = []
    texts = [row.text for row in rendered]
    tickers = [row.ticker for row in rendered]
    if len(tickers) != len(set(tickers)):
        errors.append("duplicate_ticker")
    if any(len(text) > 3500 for text in texts):
        errors.append("message_too_long")
    analyzable_texts = [
        "\n".join(
            line
            for line in text.splitlines()
            if not line.startswith("※ 분석 등급이며 주문 또는 자동매매 지시가 아닙니다.")
        )
        for text in texts
    ]
    if any(_ORDER_LANGUAGE.search(text) for text in analyzable_texts):
        errors.append("order_language")
    if any(_UNSUPPORTED.search(text) for text in analyzable_texts):
        errors.append("unsupported_metric_language")
    substantive = []
    for text in texts:
        for line in text.splitlines():
            normalized = re.sub(r"\s+", " ", line.strip().removeprefix("• "))
            if len(normalized) >= 36 and not normalized.startswith("분석 등급이며"):
                substantive.append(normalized)
    repeated = [value for value, count in Counter(substantive).items() if count >= 2]
    if repeated:
        errors.append("cross_ticker_substantive_repetition")
    numeric_total = sum(row.validation.numeric_claim_count for row in rendered)
    numeric_bound = sum(row.validation.automatically_bound_numeric_count for row in rendered)
    if numeric_total != numeric_bound:
        errors.append("numeric_binding_incomplete")
    return {
        "contract": "decision-message-quality-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "message_count": len(rendered),
        "average_character_count": round(sum(map(len, texts)) / len(texts), 2) if texts else 0,
        "max_character_count": max(map(len, texts), default=0),
        "numeric_claim_count": numeric_total,
        "automatically_bound_numeric_count": numeric_bound,
        "manual_numeric_count": 0,
        "unresolved_numeric_count": numeric_total - numeric_bound,
        "repeated_substantive_span_count": len(repeated),
    }


def decision_distribution(candidates: Sequence[DecisionCandidate]) -> dict[str, int]:
    counts = Counter(candidate.decision for candidate in candidates)
    return {decision: counts.get(decision, 0) for decision in ("BUY", "HOLD", "SELL")}


def canonicalize_candidate_metadata(
    packet: DecisionEvidencePacket,
    candidate: DecisionCandidate,
) -> DecisionCandidate:
    """Derive category-plan metadata from the AI-selected canonical references."""
    refs = {ref.ref_id: ref for ref in packet.evidence}
    claims = (
        candidate.decisive_reason,
        *candidate.supporting_evidence,
        *candidate.opposing_evidence,
        *candidate.unknowns,
        *candidate.change_conditions,
    )
    categories = {
        refs[ref_id].category
        for claim in claims
        for ref_id in claim.evidence_refs
        if ref_id in refs
    }
    return candidate.model_copy(
        update={"selected_evidence_plan": tuple(sorted(categories, key=str))}
    )


def decimal_value(value: object) -> Decimal | None:
    """Public helper for archive scripts restoring provider numeric values."""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None
