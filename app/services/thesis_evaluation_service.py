import json
import hashlib
import re
from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, select

from app.models.event import Event
from app.models.macro import ThesisMacroImpact
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.services.canonical_fact_service import event_user_fields
from app.services.event_identity import (
    event_fingerprint,
    event_is_eligible_for_current_analysis,
)
from app.schemas.thesis import (
    AssessmentStatus,
    AssessmentState,
    ExpectationLevel,
    PriceDecisionContext,
    PriceContext,
    PriceLevelCheck,
    PriceRuleEvaluation,
    EarningsEstimateImpact,
    MarketExpectationAssessment,
    StructuralRiskLevel,
    ValuationContext,
    ValuationImpact,
    ValuationSnapshot,
)


POSITIVE_EVENT_TYPES = {
    "new_customer",
    "large_order",
    "production_order",
    "revenue_guidance_up",
    "margin_improvement",
    "inventory_normalization",
    "partnership_to_revenue",
    "earnings_surprise",
    "earnings_beat",
    "major_customer_win",
}

NEGATIVE_EVENT_TYPES = {
    "revenue_guidance_down",
    "margin_deterioration",
    "fcf_deterioration",
    "inventory_increase",
    "receivables_increase",
    "capital_raise",
    "convertible_bond",
    "warrant",
    "stock_compensation_increase",
    "customer_loss",
    "customer_concentration_risk",
    "competitor_price_cut",
    "regulatory_risk",
    "export_control",
    "antitrust",
    "accounting_issue",
    "debt_liquidity_risk",
    "earnings_miss",
    "production_delay",
    "dilution",
    "debt_liquidity",
    "regulatory_material",
}

TRUSTED_INVALIDATION_PROVIDERS = {"opendart", "sec_edgar", "company_ir"}
TRUSTED_FACT_PROVIDERS = TRUSTED_INVALIDATION_PROVIDERS | {"fred", "ecos", "eia"}
EARNINGS_UP_EVENT_TYPES = {
    "earnings_surprise",
    "earnings_beat",
    "revenue_guidance_up",
    "margin_improvement",
}
EARNINGS_DOWN_EVENT_TYPES = {
    "earnings_miss",
    "revenue_guidance_down",
    "margin_deterioration",
    "fcf_deterioration",
}


def _json_list(value: str) -> list[str]:
    parsed = json.loads(value)
    return parsed if isinstance(parsed, list) else []


def _json_dict(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _terms(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9가-힣]+", value.lower())
        if len(token) >= 2
    }


def _matching_signals(text: str, signals: list[str]) -> list[str]:
    event_terms = _terms(text)
    matches: list[str] = []
    for signal in signals:
        signal_terms = _terms(signal)
        if not signal_terms:
            continue
        overlap = len(event_terms & signal_terms)
        required = len(signal_terms) if len(signal_terms) <= 2 else 2
        if overlap >= required and overlap / len(signal_terms) >= 0.25:
            matches.append(signal)
    return matches


def _event_text(event: Event) -> str:
    return " ".join(
        [
            event.title,
            event.raw_summary or "",
            " ".join(_json_list(event.confirmed_facts)),
            " ".join(_json_list(event.inferred_implications)),
        ]
    )


def _substantive_facts(event: Event) -> list[str]:
    return [
        fact
        for fact in _json_list(event.confirmed_facts)
        if not any(
            marker in fact.lower()
            for marker in (
                "filing title:",
                "receipt number:",
                "recent filing form:",
                "accession number:",
            )
        )
    ]


def _price_position(context: PriceContext) -> float | None:
    daily = context.periods.get("daily")
    return daily.range_position_pct if daily else None


def _price_view(context: PriceContext) -> str:
    if not context.available:
        return "가격 데이터가 없어 합리적인 가격대 여부를 판단 보류합니다."
    position = _price_position(context)
    if position is None:
        base = "확보된 가격 데이터가 짧아 현재 가격의 장기 범위상 위치를 판단 보류합니다."
    else:
        if position <= 35:
            zone = "확보된 일봉 범위의 하단부"
        elif position >= 75:
            zone = "확보된 일봉 범위의 상단부"
        else:
            zone = "확보된 일봉 범위의 중간 구간"
        base = f"현재 가격은 {zone}({position:.1f}%)입니다."
    evaluation = context.rule_evaluation
    if evaluation is not None:
        rule_lines = [*evaluation.triggered_rules, *evaluation.active_rules]
        if rule_lines:
            base = f"{base} {' '.join(dict.fromkeys(rule_lines))}"
    return f"{base} 이는 기술적 위치이며 적정가치 판단은 별도 밸류에이션 근거가 필요합니다."


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _display_price(value: float, currency: object) -> str:
    rendered = f"{value:,.0f}" if value.is_integer() else f"{value:,.2f}"
    if currency == "KRW":
        return f"{rendered}원"
    if currency == "USD":
        return f"${rendered}"
    return f"{rendered} {currency}" if currency else rendered


def _price_position_text(context: PriceContext) -> str:
    position = _price_position(context)
    if position is None:
        return "확보된 가격 이력이 짧아 장기 범위상 위치를 판단하지 않습니다."
    if position <= 35:
        zone = "확보된 일봉 범위의 하단부"
    elif position >= 75:
        zone = "확보된 일봉 범위의 상단부"
    else:
        zone = "확보된 일봉 범위의 중간 구간"
    return f"{zone}({position:.1f}%)"


def _build_price_decision(
    thesis: InvestmentThesis,
    context: PriceContext,
) -> PriceDecisionContext:
    rules = _json_dict(thesis.price_rules)
    daily = context.periods.get("daily")
    decision = context.decision
    if decision.current_price is None and daily is not None:
        decision.current_price = daily.latest_close
    if decision.price_as_of is None and daily is not None:
        decision.price_as_of = daily.latest_date
    if not decision.currency:
        decision.currency = str(rules.get("currency") or "") or None
    if decision.price_basis == "unavailable" and daily and daily.latest_date:
        decision.price_basis = "close"
    decision.current_position = _price_position_text(context)
    decision.registered_rules_available = bool(rules)
    if not rules:
        decision.price_state = "no_price_rule"
        decision.price_state_confirmation = (
            "provisional"
            if decision.assessment_state == AssessmentState.provisional
            else "confirmed" if decision.current_price is not None else "unavailable"
        )
        context.decision = decision
        return decision

    confirmation = _number(rules.get("confirmation_price"))
    support_low = _number(rules.get("support_zone_low"))
    support_high = _number(rules.get("support_zone_high"))
    warning = _number(rules.get("warning_price"))
    invalidation = _number(rules.get("invalidation_price"))
    current = decision.current_price
    if current is None:
        decision.price_state = "unavailable"
        decision.price_state_confirmation = "unavailable"
    else:
        if invalidation is not None and current < invalidation:
            decision.price_state = "below_invalidation"
        elif warning is not None and current < warning:
            decision.price_state = "below_warning"
        elif support_low is not None and current < support_low:
            decision.price_state = "below_support"
        elif support_low is not None and support_high is not None and current <= support_high:
            decision.price_state = "inside_support"
        elif confirmation is not None and current > confirmation:
            decision.price_state = "above_confirmation"
        else:
            decision.price_state = "between_confirmation_and_support"
        decision.price_state_confirmation = (
            "provisional"
            if decision.assessment_state == AssessmentState.provisional
            else "confirmed"
        )
        decision.current_position = {
            "below_invalidation": "현재 재점검 가격을 하회하고 있습니다.",
            "below_warning": "현재 경고 가격을 하회해 투자 논리 재점검이 필요합니다.",
            "below_support": "현재 등록된 지지구간을 하회하고 있습니다.",
            "inside_support": "현재 등록된 지지구간 안에서 거래되고 있습니다.",
            "above_confirmation": "현재 상향 확인 가격을 넘어선 상태입니다.",
            "between_confirmation_and_support": "현재 지지구간 위, 상향 확인 가격 아래에 있습니다.",
        }[decision.price_state]
    if support_low is not None and support_high is not None:
        support = PriceLevelCheck(
            rule="support_zone",
            label="지지 확인 구간",
            meaning="가격이 버티는지와 사업 투자 논리의 핵심 근거가 함께 유지되는지 확인합니다.",
            price_low=support_low,
            price_high=support_high,
        )
        decision.new_observer_checks.append(support)
        decision.holder_checks.append(support.model_copy(deep=True))
    if confirmation is not None:
        decision.new_observer_checks.append(
            PriceLevelCheck(
                rule="confirmation_price",
                label="상향 확인 가격",
                meaning="가격 돌파만이 아니라 실적·주문·현금흐름 근거의 동반 강화를 확인합니다.",
                price=confirmation,
            )
        )
    if warning is not None:
        warning_check = PriceLevelCheck(
            rule="warning_price",
            label="재점검 시작 가격",
            meaning="종가 이탈 시 단순 조정인지 투자 논리 약화인지 다시 구분합니다.",
            price=warning,
        )
        decision.new_observer_checks.append(warning_check)
        decision.holder_checks.append(warning_check.model_copy(deep=True))
    if invalidation is not None:
        decision.holder_checks.append(
            PriceLevelCheck(
                rule="invalidation_price",
                label="재점검 가격",
                meaning="종가 이탈 시 가격 약화와 사업 투자 논리를 함께 다시 확인합니다.",
                price=invalidation,
            )
        )
    context.decision = decision
    return decision


def _price_basis_text(decision: PriceDecisionContext) -> str:
    if decision.price_as_of is None:
        return "기준일 확인 불가"
    if decision.price_basis == "intraday":
        return f"{decision.price_as_of} 장중 · 잠정"
    return f"{decision.price_as_of} 종가"


def _price_level_text(check: PriceLevelCheck, currency: str | None) -> str:
    if check.price_low is not None and check.price_high is not None:
        return (
            f"{_display_price(check.price_low, currency)}~"
            f"{_display_price(check.price_high, currency)}"
        )
    if check.price is not None:
        return _display_price(check.price, currency)
    return "등록값 없음"


def _price_audience_views(
    decision: PriceDecisionContext,
    expectation_level: ExpectationLevel,
) -> tuple[str, str]:
    if not decision.registered_rules_available:
        return (
            "등록된 구조적 확인 가격이 없습니다. 투자 논리 조건과 실적 데이터를 우선 확인합니다.",
            "등록된 가격 관리 기준이 없습니다. 사업 투자 논리의 약화·무효화 조건을 우선 확인합니다.",
        )
    observer_state, holder_state = {
        "above_confirmation": (
            "현재 상향 확인 가격을 넘어서고 있습니다. 가격 강세가 실제 실적·주문·현금흐름 개선과 동반되는지 확인합니다.",
            "상향 확인 가격 위에서 거래 중입니다. 종가 기준 안착 여부와 투자 논리 강화 조건의 실제 충족 여부를 확인합니다.",
        ),
        "inside_support": (
            "현재 지지구간 안에 있습니다. 가격 지지와 함께 핵심 실적·현금흐름 근거가 유지되는지 확인합니다.",
            "현재 핵심 지지구간에서 거래 중입니다. 종가 기준 방어 여부와 사업 투자 논리 훼손 여부를 함께 확인합니다.",
        ),
        "below_support": (
            "현재 지지구간 아래입니다. 가격이 낮아졌다는 이유만으로 매력도가 높아졌다고 판단하지 않고 종가 기준 지지 회복과 사업 투자 논리 유지 여부를 확인합니다.",
            "현재 지지구간을 이탈했습니다. 재점검 가격 도달 여부와 별개로 단순 가격 조정인지 사업 투자 논리 약화인지 분리해서 확인합니다.",
        ),
        "below_warning": (
            "현재 재점검 시작 가격 아래입니다. 사업 투자 논리와 Valuation을 다시 검증하기 전에는 가격 하락 자체를 매력으로 해석하지 않습니다.",
            "재점검 시작 가격을 하회했습니다. 가격 약화의 원인이 시장·업종인지 회사 실적·주문·현금흐름인지 우선 재평가합니다.",
        ),
        "below_invalidation": (
            "현재 가격 기반 투자 논리 재점검 기준 아래입니다. 가격만으로 자동 무효화하지 않고 핵심 사업 근거와 Valuation을 전면 재검증합니다.",
            "가격 기반 투자 논리 재점검 기준을 하회했습니다. 가격 약화와 사업 투자 논리 훼손 여부를 함께 다시 판단합니다.",
        ),
        "between_confirmation_and_support": (
            "현재 지지구간 위, 상향 확인 가격 아래에 있습니다. 다음 확인 가격과 핵심 사업 근거를 함께 봅니다.",
            "현재 지지구간 위에서 거래 중입니다. 상향 확인 가격 전까지 기존 관리 기준을 유지합니다.",
        ),
        "unavailable": (
            "현재가를 확인하지 못해 가격 상태 판단을 유보합니다.",
            "현재가를 확인하지 못해 등록 가격 기준의 상태 판단을 유보합니다.",
        ),
    }.get(decision.price_state, ("", ""))
    observer_lines = ([observer_state] if observer_state else []) + [
        f"{_price_level_text(item, decision.currency)}: {item.label}. {item.meaning}"
        for item in decision.new_observer_checks
    ]
    holder_lines = ([holder_state] if holder_state else []) + [
        f"{_price_level_text(item, decision.currency)}: {item.label}. {item.meaning}"
        for item in decision.holder_checks
    ]
    if expectation_level in {ExpectationLevel.very_high, ExpectationLevel.speculative}:
        if decision.price_state == "above_confirmation":
            observer_lines.append(
                "가격은 강하지만 기대 수준도 매우 높아 추가 실적 상향이 동반되는지 확인합니다."
            )
        elif decision.price_state in {"below_support", "below_warning", "below_invalidation"}:
            observer_lines.append(
                "시장 기대가 높아 가격 하락만으로 Valuation 완충을 판단하기 어렵습니다."
            )
        else:
            observer_lines.append(
                "시장 기대가 높아 가격 지지만으로 Valuation 매력이 높아졌다고 판단하지 않습니다."
            )
    elif expectation_level in {ExpectationLevel.balanced, ExpectationLevel.low}:
        if decision.price_state in {"inside_support", "below_support", "below_warning"}:
            observer_lines.append(
                "사업 투자 논리 훼손 없이 가격만 조정됐는지와 Valuation 완충 가능성을 함께 확인합니다."
            )
        elif decision.price_state == "above_confirmation":
            observer_lines.append(
                "가격 강세를 적정가치 상승으로 바로 해석하지 않고 이익 근거의 동반 개선을 확인합니다."
            )
    return "\n".join(observer_lines), "\n".join(holder_lines)


@dataclass
class PriceRuleResult:
    positive_points: int = 0
    negative_points: int = 0
    invalidated: bool = False
    evidence: dict[str, object] | None = None


def _evaluate_price_rules(thesis: InvestmentThesis, context: PriceContext) -> PriceRuleResult:
    rules = _json_dict(thesis.price_rules)
    if not rules:
        return PriceRuleResult()

    daily = context.periods.get("daily")
    latest = daily.latest_close if daily else None
    previous = daily.previous_close if daily else None
    latest_low = daily.latest_low if daily else None
    evaluation = PriceRuleEvaluation(
        status="unavailable" if latest is None else "within_rules",
        latest_close=latest,
        previous_close=previous,
    )
    context.rule_evaluation = evaluation
    if latest is None:
        return PriceRuleResult()

    currency = rules.get("currency")
    confirmation = _number(rules.get("confirmation_price"))
    support_low = _number(rules.get("support_zone_low"))
    support_high = _number(rules.get("support_zone_high"))
    warning = _number(rules.get("warning_price"))
    invalidation = _number(rules.get("invalidation_price"))
    direction = "neutral"
    relevance_score = 0
    result = PriceRuleResult()

    if invalidation is not None and latest < invalidation:
        evaluation.status = "invalidation_triggered"
        evaluation.triggered_rules.append(
            f"종가 {_display_price(latest, currency)}가 무효화 기준 "
            f"{_display_price(invalidation, currency)}을 이탈했습니다."
        )
        result.negative_points += 100
        result.invalidated = True
        direction = "invalidation"
        relevance_score = 100
    else:
        if warning is not None and latest <= warning:
            evaluation.active_rules.append(
                f"경고 기준 {_display_price(warning, currency)} 이하가 유지 중입니다."
            )
            if previous is not None and previous > warning:
                evaluation.status = "warning_triggered"
                evaluation.triggered_rules.append(
                    f"종가가 경고 기준 {_display_price(warning, currency)}을 하향 이탈했습니다."
                )
                result.negative_points += 50
                direction = "weaken"
                relevance_score = max(relevance_score, 70)

        if support_low is not None and support_high is not None:
            in_support = support_low <= latest <= support_high
            support_held = (
                latest_low is not None
                and support_low <= latest_low <= support_high
                and latest > support_high
            )
            if in_support:
                evaluation.active_rules.append(
                    f"종가가 지지구간 {_display_price(support_low, currency)}~"
                    f"{_display_price(support_high, currency)} 안에 있습니다."
                )
                if previous is not None and not support_low <= previous <= support_high:
                    if evaluation.status == "within_rules":
                        evaluation.status = "support_zone_entered"
                    evaluation.triggered_rules.append("종가가 등록된 지지구간에 진입했습니다.")
                    relevance_score = max(relevance_score, 45)
            elif support_held:
                evaluation.active_rules.append(
                    f"장중 지지구간 {_display_price(support_low, currency)}~"
                    f"{_display_price(support_high, currency)}을 확인하고 종가는 구간 위에서 마감했습니다."
                )
                if previous is not None and previous > support_high:
                    if evaluation.status == "within_rules":
                        evaluation.status = "support_zone_held"
                    evaluation.triggered_rules.append("등록된 지지구간의 종가 방어를 확인했습니다.")
                    result.positive_points += 20
                    if direction == "neutral":
                        direction = "strengthen"
                    relevance_score = max(relevance_score, 55)
            elif previous is not None and previous >= support_low and latest < support_low:
                if evaluation.status == "within_rules":
                    evaluation.status = "support_zone_broken"
                evaluation.triggered_rules.append(
                    f"종가가 지지구간 하단 {_display_price(support_low, currency)}을 이탈했습니다."
                )
                result.negative_points += 30
                direction = "weaken"
                relevance_score = max(relevance_score, 60)

        if confirmation is not None and latest >= confirmation:
            evaluation.active_rules.append(
                f"확인 기준 {_display_price(confirmation, currency)} 이상입니다."
            )
            if previous is not None and previous < confirmation:
                evaluation.status = "confirmation_triggered"
                evaluation.triggered_rules.append(
                    f"종가가 확인 기준 {_display_price(confirmation, currency)}을 상향 돌파했습니다."
                )
                result.positive_points += 50
                if direction == "neutral":
                    direction = "strengthen"
                relevance_score = max(relevance_score, 70)

    if evaluation.triggered_rules:
        result.evidence = {
            "date": daily.latest_date if daily else None,
            "title": "구조화된 가격 규칙 점검",
            "url": "",
            "provider": "ohlcv-analyst",
            "event_type": "price_rule",
            "direction": direction,
            "relevance_score": relevance_score,
            "matched_signals": evaluation.triggered_rules,
        }
    return result


@dataclass
class EvaluationResult:
    status: AssessmentStatus
    score: int
    confidence: float
    summary: str
    new_buyer_view: str
    holder_view: str
    price_view: str
    risk_level: str
    daily_change_severity: str
    structural_risk_level: StructuralRiskLevel
    assessment_state: AssessmentState
    market_session: str
    evidence: list[dict[str, object]]
    valuation_context: ValuationContext
    earnings_estimate_impact: EarningsEstimateImpact
    market_expectation_assessment: MarketExpectationAssessment
    confirmed_facts: list[str]
    background_confirmed_facts: list[str]
    inferred_implications: list[str]
    unknowns: list[str]
    confirmed_warnings: list[str]
    new_warnings: list[str]
    open_warnings: list[str]
    open_confirmed_warnings: list[str]
    persistent_watch_risks: list[str]
    warning_states: list[dict[str, object]]
    watch_items: list[str]
    new_buyer_price_view: str
    holder_price_view: str
    valuation_snapshot: ValuationSnapshot
    used_event_fingerprints: list[str]
    should_deactivate: bool = False


def _expectation_level(value: object) -> ExpectationLevel:
    try:
        return ExpectationLevel(str(value))
    except ValueError:
        return ExpectationLevel.unknown


def _valuation_summary(impact: ValuationImpact) -> str:
    summaries = {
        ValuationImpact.expansion: "새 근거가 멀티플 확장 조건과 연결됩니다.",
        ValuationImpact.compression: "새 근거가 멀티플 압축 조건과 연결됩니다.",
        ValuationImpact.mixed: "멀티플 확장과 압축 근거가 함께 확인됐습니다.",
        ValuationImpact.neutral: "멀티플을 바꿀 새로운 근거가 확인되지 않았습니다.",
        ValuationImpact.unknown: "평가 프레임이 없어 멀티플 영향을 판단할 수 없습니다.",
    }
    return summaries[impact]


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))


def _baseline_evidence(events: list[Event]) -> list[dict[str, object]]:
    priority = {
        "earnings": 0,
        "earnings_release": 0,
        "provisional_earnings": 0,
        "financial_report": 0,
        "major_order": 1,
        "large_order": 1,
        "customer_change": 1,
        "revenue_guidance_up": 2,
        "revenue_guidance_down": 2,
        "margin_guidance_up": 2,
        "margin_guidance_down": 2,
        "guidance_change": 2,
        "capital_allocation": 3,
    }
    ordered = sorted(
        [event for event in events if event.event_type != "non_thesis_noise"],
        key=lambda event: (
            priority.get(event.event_type, 4),
            -event.relevance_score,
            -event.date.toordinal(),
        ),
    )
    return [
        {
            "date": str(event.date),
            "title": event.title,
            "url": event.url,
            "provider": event.provider,
            "event_type": event.event_type,
            "direction": "baseline",
            "valuation_direction": "neutral",
            "relevance_score": event.relevance_score,
            "matched_signals": [],
            "matched_valuation_signals": [],
            "fingerprint": event_fingerprint(event),
            **event_user_fields(event),
        }
        for event in ordered
    ]


def _assessment_evidence_layers(
    events: list[Event],
) -> tuple[list[str], list[str], list[str]]:
    confirmed: list[str] = []
    inferred: list[str] = []
    unknowns: list[str] = []
    for event in events:
        event_facts = _substantive_facts(event)
        event_inferences = _json_list(event.inferred_implications)
        if event.provider in TRUSTED_FACT_PROVIDERS:
            confirmed.extend(event_facts)
            inferred.extend(event_inferences)
        elif event_facts or event_inferences:
            unknowns.append(
                "미확인 보도가 있으나 원문 근거와 투자 영향이 확인되지 않아 투자 논리에는 반영하지 않았습니다."
            )
        unknowns.extend(
            item
            for item in _json_list(event.unknowns)
            if not any(
                marker in item.lower()
                for marker in (
                    "unverified provider report",
                    "naver news search returned",
                    "linked source item",
                )
            )
        )
    return _unique(confirmed), _unique(inferred), _unique(unknowns)


def _warning_facts(event: Event) -> list[str]:
    facts = _substantive_facts(event)
    return facts or [event.title]


def _earnings_estimate_impact(events: list[Event]) -> EarningsEstimateImpact:
    up = any(
        event.provider in TRUSTED_FACT_PROVIDERS
        and event.event_type in EARNINGS_UP_EVENT_TYPES
        and bool(_substantive_facts(event))
        for event in events
    )
    down = any(
        event.provider in TRUSTED_FACT_PROVIDERS
        and event.event_type in EARNINGS_DOWN_EVENT_TYPES
        and bool(_substantive_facts(event))
        for event in events
    )
    if up and down:
        return EarningsEstimateImpact.mixed
    if up:
        return EarningsEstimateImpact.up
    if down:
        return EarningsEstimateImpact.down
    return EarningsEstimateImpact.unchanged


def _previous_facts(previous: ThesisAssessment | None) -> list[str]:
    if previous is None:
        return []
    return _unique(
        [
            *_json_list(previous.background_confirmed_facts),
            *_json_list(previous.confirmed_facts),
        ]
    )


def _watch_text(value: str) -> str:
    text = value.strip().rstrip(".")
    if not text:
        return ""
    if "확인 필요" in text:
        return text
    if text.endswith("여부"):
        return f"{text} 확인 필요"
    english = text.lower()
    if any(term in english for term in ("unknown", "unavailable", "require", "verify", "warning")):
        return f"{text} · 확인 필요"
    if re.search(r"[가-힣]", text):
        return f"{text}하는지 확인 필요"
    return f"{text} 여부 확인 필요"


def _previous_json_list(previous: ThesisAssessment | None, field: str) -> list[str]:
    if previous is None:
        return []
    return _json_list(str(getattr(previous, field, "[]") or "[]"))


def _warning_lifecycle(
    previous: ThesisAssessment | None,
    new_warnings: list[str],
    events: list[Event],
    baseline_warnings: list[dict[str, object]] | None = None,
    *,
    ticker: str,
    assessment_date: date,
) -> tuple[list[str], list[dict[str, object]]]:
    previous_states_raw: list[object] = []
    if previous is not None:
        try:
            parsed = json.loads(str(getattr(previous, "warning_states", "[]") or "[]"))
            if isinstance(parsed, list):
                previous_states_raw = parsed
        except json.JSONDecodeError:
            previous_states_raw = []
    baseline_by_warning = {
        str(item.get("warning")): dict(item)
        for item in baseline_warnings or []
        if isinstance(item, dict) and item.get("warning")
    }
    states: dict[str, dict[str, object]] = {
        str(item.get("warning")): dict(item)
        for item in previous_states_raw
        if isinstance(item, dict) and item.get("warning")
        and item.get("provenance_status") not in {"invalid", "invalid_provenance"}
        and not (
            item.get("source") == "canonical_issue"
            and str(item.get("warning")) not in baseline_by_warning
        )
    }
    for state in states.values():
        if "provenance_status" not in state:
            state["provenance_status"] = "legacy_previous_assessment"
            state["backfilled_warning"] = True
        if "opened_date" not in state and previous is not None:
            state["opened_date"] = previous.assessment_date.isoformat()
    legacy_open = _previous_json_list(previous, "open_warnings")
    if not legacy_open:
        legacy_open = _previous_json_list(previous, "confirmed_warnings")
    for warning in legacy_open:
        states.setdefault(
            warning,
            {
                "warning": warning,
                "status": "open",
                "backfilled_warning": True,
                "provenance_status": "legacy_previous_assessment",
            },
        )
    for warning, baseline in baseline_by_warning.items():
        states[warning] = dict(baseline)

    for warning in new_warnings:
        previous_state = states.get(warning)
        source_events = [event for event in events if warning in _warning_facts(event)]
        source_event_ids = [event_fingerprint(event) for event in source_events]
        if not source_event_ids:
            continue
        source_event = source_events[0]
        states[warning] = {
            **(previous_state or {}),
            "warning_id": hashlib.sha256(f"{ticker}|{warning}".encode()).hexdigest()[:16],
            "ticker": ticker,
            "warning": warning,
            "warning_type": "confirmed_fundamental",
            "opened_date": (previous_state or {}).get("opened_date", assessment_date.isoformat()),
            "last_confirmed_date": assessment_date.isoformat(),
            "status": "escalated" if previous_state else "open",
            "resolution_condition": (previous_state or {}).get(
                "resolution_condition", "반대 방향의 신뢰 가능한 확정 근거 확인"
            ),
            "source_event_ids": source_event_ids,
            "source": "thesis_event",
            "source_provider": source_event.provider,
            "source_title": source_event.title,
            "source_date": source_event.date.isoformat(),
            "source_event_type": source_event.event_type,
            "provenance_status": "valid",
            "backfilled_warning": False,
        }

    resolution_markers = {
        "회복",
        "개선",
        "정상화",
        "흑자 전환",
        "resolved",
        "recovered",
        "improved",
        "normalized",
    }
    positive_texts = [
        _event_text(event)
        for event in events
        if event.provider in TRUSTED_FACT_PROVIDERS
        and event.event_type in POSITIVE_EVENT_TYPES
        and any(marker in _event_text(event).lower() for marker in resolution_markers)
    ]
    for warning, state in states.items():
        state.setdefault("warning_id", hashlib.sha256(f"{ticker}|{warning}".encode()).hexdigest()[:16])
        state.setdefault("ticker", ticker)
        state.setdefault("warning_type", "confirmed_fundamental")
        state.setdefault("opened_date", assessment_date.isoformat())
        state.setdefault("last_confirmed_date", state.get("opened_date"))
        state.setdefault("resolution_condition", "반대 방향의 신뢰 가능한 확정 근거 확인")
        state.setdefault("source_event_ids", [])
        state.setdefault("provenance_status", "unverified")
        state.setdefault("backfilled_warning", False)
        if any(_matching_signals(text, [warning]) for text in positive_texts):
            state["status"] = "resolved"
        if (
            state.get("opened_date") == assessment_date.isoformat()
            and warning not in new_warnings
            and not state.get("backfilled_warning")
        ):
            state["status"] = "invalid_provenance"
            state["provenance_status"] = "warning_lifecycle_consistency_error"

    rendered_states = list(states.values())
    open_warnings = [
        str(item["warning"])
        for item in rendered_states
        if item.get("status") in {"open", "escalated"}
        and item.get("provenance_status")
        not in {"invalid", "invalid_provenance", "warning_lifecycle_consistency_error"}
    ]
    return _unique(open_warnings), rendered_states


def _assessment_confidence(
    events: list[Event],
    price_context: PriceContext,
    valuation_snapshot: ValuationSnapshot | None,
    unknowns: list[str],
) -> float:
    confidence = 0.88
    if not price_context.available:
        confidence -= 0.10
    if price_context.warnings:
        confidence -= min(0.10, len(price_context.warnings) * 0.03)
    if valuation_snapshot is None or valuation_snapshot.quality == "unavailable":
        confidence -= 0.08
    elif valuation_snapshot.quality == "stale":
        confidence -= 0.10
    elif valuation_snapshot.quality == "partial":
        confidence -= 0.04
    confidence -= min(0.12, len(unknowns) * 0.015)
    confidence -= min(
        0.12,
        sum(1 for event in events if event.provider not in TRUSTED_FACT_PROVIDERS) * 0.03,
    )
    if events and all(
        event.provider in TRUSTED_FACT_PROVIDERS
        and not event.financial_statement_basis_warning
        for event in events
    ):
        confidence += 0.03
    return round(max(0.35, min(0.95, confidence)), 2)


def _persistent_watch_risks(thesis: InvestmentThesis) -> list[str]:
    expectations = _json_dict(thesis.market_expectations)
    framework = _json_dict(thesis.valuation_framework)
    candidates: list[str] = []
    for source in (
        expectations.get("downside_surprises", []),
        framework.get("valuation_caveats", []),
        _json_list(thesis.validation_metrics),
    ):
        if isinstance(source, list):
            candidates.extend(str(item).strip() for item in source if str(item).strip())
    risk_markers = (
        "적자", "미확인", "미증명", "저하", "둔화", "의존", "부담",
        "위험", "cash burn", "unproven",
    )
    for clause in re.split(r"[,.]\s*|\s+및\s+|\s+and\s+|와\s+|과\s+", thesis.core_thesis):
        cleaned = clause.strip().rstrip("다")
        if 4 <= len(cleaned) <= 90 and any(
            marker in cleaned.lower() for marker in risk_markers
        ):
            candidates.append(cleaned)
    return _unique(candidates)[:5]


def _daily_change_severity(status: AssessmentStatus) -> str:
    return {
        AssessmentStatus.no_material_change: "none",
        AssessmentStatus.strengthened: "moderate",
        AssessmentStatus.weakened: "moderate",
        AssessmentStatus.mixed: "moderate",
        AssessmentStatus.needs_review: "moderate",
        AssessmentStatus.invalidation_candidate: "high",
        AssessmentStatus.invalidated: "critical",
    }[status]


def _structural_risk_level(
    status: AssessmentStatus,
    expectation_level: ExpectationLevel,
    open_warnings: list[str],
    previous: ThesisAssessment | None,
) -> StructuralRiskLevel:
    rank = {
        StructuralRiskLevel.low: 0,
        StructuralRiskLevel.normal: 1,
        StructuralRiskLevel.elevated: 2,
        StructuralRiskLevel.high: 3,
        StructuralRiskLevel.critical: 4,
    }
    risk = (
        StructuralRiskLevel.elevated
        if expectation_level == ExpectationLevel.speculative
        else StructuralRiskLevel.normal
    )
    if len(open_warnings) >= 3:
        risk = StructuralRiskLevel.elevated
    elif any(
        marker in warning.lower()
        for warning in open_warnings
        for marker in (
            "유상증자", "희석", "적자", "영업이익률", "부채", "유동성",
            "고객 이탈", "회계", "dilution", "negative fcf", "margin deterioration",
        )
    ):
        risk = StructuralRiskLevel.elevated
    if status in {AssessmentStatus.weakened, AssessmentStatus.mixed}:
        risk = max(risk, StructuralRiskLevel.elevated, key=rank.get)
    elif status == AssessmentStatus.invalidation_candidate:
        risk = max(risk, StructuralRiskLevel.high, key=rank.get)
    elif status == AssessmentStatus.invalidated:
        risk = StructuralRiskLevel.critical
    if previous is not None and status == AssessmentStatus.no_material_change:
        try:
            previous_risk = StructuralRiskLevel(
                str(getattr(previous, "structural_risk_level", "normal") or "normal")
            )
        except ValueError:
            previous_risk = StructuralRiskLevel.normal
        risk = max(risk, previous_risk, key=rank.get)
    return risk


def _transition_guard(
    previous: ThesisAssessment | None,
    status: AssessmentStatus,
    material_positive: bool,
    material_invalidation: bool,
) -> AssessmentStatus:
    if previous is None:
        return status
    previous_status = previous.business_thesis_change or previous.status
    if (
        previous_status in {"weakened", "invalidation_candidate"}
        and status == AssessmentStatus.strengthened
        and not material_positive
    ):
        return AssessmentStatus.no_material_change
    if (
        previous_status == "strengthened"
        and status == AssessmentStatus.invalidated
        and not material_invalidation
    ):
        return AssessmentStatus.mixed
    return status


def _expectation_assessment(
    expectations: dict[str, object],
    valuation_context: ValuationContext,
) -> MarketExpectationAssessment:
    level = _expectation_level(expectations.get("level", "unknown"))
    if valuation_context.impact == ValuationImpact.expansion:
        assessment = "upside_evidence"
    elif valuation_context.impact == ValuationImpact.compression:
        assessment = "downside_or_discount_rate_pressure"
    elif valuation_context.impact == ValuationImpact.mixed:
        assessment = "mixed"
    elif valuation_context.impact == ValuationImpact.neutral:
        assessment = "no_material_change"
    else:
        assessment = "unknown"
    evidence_basis = [
        *valuation_context.matched_expansion_conditions,
        *valuation_context.matched_compression_conditions,
    ]
    if valuation_context.macro_valuation_effect != "neutral":
        evidence_basis.append(
            f"macro valuation effect: {valuation_context.macro_valuation_effect}"
        )
    return MarketExpectationAssessment(
        level=level,
        assessment=assessment,
        summary=str(expectations.get("summary", "")),
        evidence_basis=_unique(evidence_basis),
    )


def evaluate_thesis(
    thesis: InvestmentThesis,
    events: list[Event],
    price_context: PriceContext,
    macro_impact: ThesisMacroImpact | None = None,
    previous_assessment: ThesisAssessment | None = None,
    valuation_snapshot: ValuationSnapshot | None = None,
    baseline_warning_states: list[dict[str, object]] | None = None,
    assessment_mode: str = "daily_delta",
    event_materiality: dict[str, str] | None = None,
) -> EvaluationResult:
    all_events = [event for event in events if event_is_eligible_for_current_analysis(event)]
    is_initial_baseline = assessment_mode == "initial_baseline"
    events = [] if is_initial_baseline else all_events
    event_materiality = event_materiality or {}
    strengthen_signals = _json_list(thesis.strengthen_signals)
    weaken_signals = _json_list(thesis.weaken_signals)
    invalidation_signals = _json_list(thesis.invalidation_signals)
    expansion_signals = _json_list(thesis.multiple_expansion_signals)
    compression_signals = _json_list(thesis.multiple_compression_signals)
    positive_points = 0
    negative_points = 0
    expansion_points = 0
    compression_points = 0
    matched_expansion: list[str] = []
    matched_compression: list[str] = []
    invalidation_matches: list[tuple[Event, list[str]]] = []
    evidence: list[dict[str, object]] = []
    core_review_evidence = False
    material_positive = False

    for event in events:
        if event.event_type == "non_thesis_noise":
            continue
        text = _event_text(event)
        strengthen_matches = _matching_signals(text, strengthen_signals)
        weaken_matches = _matching_signals(text, weaken_signals)
        invalid_matches = _matching_signals(text, invalidation_signals)
        raw_expansion_matches = _matching_signals(text, expansion_signals)
        raw_compression_matches = _matching_signals(text, compression_signals)
        direction = "neutral"
        valuation_direction = "neutral"
        trusted_confirmed = (
            event.provider in TRUSTED_FACT_PROVIDERS
            and bool(_substantive_facts(event))
            and not event.financial_statement_basis_warning
        )
        expansion_matches = raw_expansion_matches if trusted_confirmed else []
        compression_matches = raw_compression_matches if trusted_confirmed else []
        if invalid_matches and trusted_confirmed:
            direction = "invalidation"
            negative_points += event.relevance_score
            invalidation_matches.append((event, invalid_matches))
        elif trusted_confirmed and (weaken_matches or event.event_type in NEGATIVE_EVENT_TYPES):
            direction = "weaken"
            negative_points += event.relevance_score
        elif (
            trusted_confirmed
            and strengthen_matches
            and event.event_type in POSITIVE_EVENT_TYPES
        ):
            direction = "strengthen"
            positive_points += event.relevance_score
            material_positive = material_positive or event.relevance_score >= 20
        elif (
            (weaken_matches or event.event_type in NEGATIVE_EVENT_TYPES)
            and not trusted_confirmed
            and event.event_type != "non_thesis_noise"
            and event.relevance_score >= 70
        ):
            core_review_evidence = True

        if expansion_matches and compression_matches:
            valuation_direction = "mixed"
            expansion_points += event.relevance_score
            compression_points += event.relevance_score
        elif expansion_matches:
            valuation_direction = "expansion"
            expansion_points += event.relevance_score
        elif compression_matches:
            valuation_direction = "compression"
            compression_points += event.relevance_score
        matched_expansion.extend(expansion_matches)
        matched_compression.extend(compression_matches)

        requires_review = (
            event.requires_review
            and event.relevance_score >= 70
            and event_materiality.get(event_fingerprint(event)) not in {"immaterial", "unknown"}
        )
        if direction != "neutral" or requires_review:
            core_review_evidence = True
        if (
            direction != "neutral"
            or valuation_direction != "neutral"
            or requires_review
        ):
            evidence.append(
                {
                    "date": str(event.date),
                    "title": event.title,
                    "url": event.url,
                    "provider": event.provider,
                    "event_type": event.event_type,
                    "direction": direction,
                    "valuation_direction": valuation_direction,
                    "relevance_score": event.relevance_score,
                    "matched_signals": [
                        *strengthen_matches,
                        *weaken_matches,
                        *invalid_matches,
                    ],
                    "matched_valuation_signals": [
                        *expansion_matches,
                        *compression_matches,
                    ],
                    "fingerprint": event_fingerprint(event),
                    **event_user_fields(event),
                }
            )

    _evaluate_price_rules(thesis, price_context)
    price_decision = _build_price_decision(thesis, price_context)

    macro_valuation_effect = (
        "neutral"
        if is_initial_baseline
        else macro_impact.valuation_effect
        if macro_impact
        else "neutral"
    )
    if macro_valuation_effect == "strengthen":
        expansion_points += max(20, (macro_impact.magnitude if macro_impact else 0) * 10)
    elif macro_valuation_effect == "weaken":
        compression_points += max(20, (macro_impact.magnitude if macro_impact else 0) * 10)
    elif macro_valuation_effect == "mixed":
        expansion_points += 20
        compression_points += 20
    if macro_impact is not None and macro_valuation_effect != "neutral":
        evidence.append(
            {
                "date": str(macro_impact.assessment_date),
                "title": "거시환경의 Valuation 전달 경로",
                "url": "",
                "provider": "macro-monitor",
                "event_type": "macro_valuation",
                "direction": "neutral",
                "valuation_direction": macro_valuation_effect,
                "relevance_score": macro_impact.magnitude * 20,
                "matched_signals": [],
                "matched_valuation_signals": [],
                "rationale": macro_impact.rationale,
            }
        )

    earnings_estimate_impact = _earnings_estimate_impact(events)
    trusted_invalidation = any(
        event.provider in TRUSTED_INVALIDATION_PROVIDERS
        and event.relevance_score >= 80
        and bool(_substantive_facts(event))
        for event, _matches in invalidation_matches
    )
    if trusted_invalidation:
        status = AssessmentStatus.invalidated
    elif invalidation_matches:
        status = AssessmentStatus.invalidation_candidate
    elif positive_points >= 20 and negative_points >= 20:
        status = AssessmentStatus.mixed
    elif positive_points - negative_points >= 20:
        status = AssessmentStatus.strengthened
    elif negative_points - positive_points >= 20:
        status = AssessmentStatus.weakened
    elif core_review_evidence:
        status = AssessmentStatus.needs_review
    else:
        status = AssessmentStatus.no_material_change
    if is_initial_baseline:
        status = AssessmentStatus.no_material_change
        earnings_estimate_impact = EarningsEstimateImpact.unchanged
        evidence = _baseline_evidence(all_events)
    else:
        status = _transition_guard(
            previous_assessment,
            status,
            material_positive=material_positive,
            material_invalidation=trusted_invalidation,
        )

    expectations = _json_dict(thesis.market_expectations)
    framework = _json_dict(thesis.valuation_framework)
    expectation_level = _expectation_level(expectations.get("level", "unknown"))
    if earnings_estimate_impact == EarningsEstimateImpact.up:
        expansion_points += 20
    elif earnings_estimate_impact == EarningsEstimateImpact.down:
        compression_points += 20
    elif earnings_estimate_impact == EarningsEstimateImpact.mixed:
        expansion_points += 20
        compression_points += 20
    has_expansion = bool(matched_expansion) or earnings_estimate_impact in {
        EarningsEstimateImpact.up,
        EarningsEstimateImpact.mixed,
    }
    has_compression = bool(matched_compression) or earnings_estimate_impact in {
        EarningsEstimateImpact.down,
        EarningsEstimateImpact.mixed,
    }
    if macro_valuation_effect in {"strengthen", "mixed"}:
        has_expansion = True
    if macro_valuation_effect in {"weaken", "mixed"}:
        has_compression = True

    if has_expansion and has_compression:
        valuation_impact = ValuationImpact.mixed
    elif has_expansion:
        valuation_impact = ValuationImpact.expansion
    elif has_compression:
        valuation_impact = ValuationImpact.compression
    else:
        valuation_impact = ValuationImpact.neutral

    macro_valuation_effects: list[str] = []
    if macro_impact is not None and macro_valuation_effect != "neutral":
        try:
            macro_evidence = json.loads(macro_impact.evidence)
        except json.JSONDecodeError:
            macro_evidence = []
        macro_valuation_effects = _unique(
            str(item.get("factor"))
            for item in macro_evidence
            if isinstance(item, dict)
            and item.get("factor")
            and isinstance(item.get("exposure"), dict)
            and str(item["exposure"].get("channel"))
            in {"discount_rate", "risk_appetite"}
            and abs(float(item.get("contribution", 0) or 0)) > 0
        )
        if not macro_valuation_effects and macro_impact.rationale:
            macro_valuation_effects = [macro_impact.rationale]

    valuation_evidence = [
        *(f"확장 조건 확인: {item}" for item in _unique(matched_expansion)),
        *(f"압축 조건 확인: {item}" for item in _unique(matched_compression)),
    ]
    if earnings_estimate_impact != EarningsEstimateImpact.unchanged:
        valuation_evidence.append(
            f"이익 추정치 영향: {earnings_estimate_impact.value}"
        )
    valuation_evidence.extend(
        f"거시 Valuation 경로: {item}" for item in macro_valuation_effects
    )
    previous_impact: ValuationImpact | None = None
    if previous_assessment is not None:
        try:
            previous_impact = ValuationImpact(
                str(previous_assessment.valuation_change or "neutral")
            )
        except ValueError:
            previous_impact = None

    valuation_summary = _valuation_summary(valuation_impact)
    if (
        not matched_expansion
        and not matched_compression
        and earnings_estimate_impact == EarningsEstimateImpact.unchanged
        and macro_valuation_effect != "neutral"
    ):
        impact_text = {
            ValuationImpact.expansion: "확장",
            ValuationImpact.compression: "압축",
            ValuationImpact.mixed: "혼재",
            ValuationImpact.neutral: "중립",
            ValuationImpact.unknown: "판단 보류",
        }[valuation_impact]
        valuation_summary = (
            "사업 투자 논리를 바꿀 신규 근거는 없고, 오늘 할인율·위험선호의 "
            f"거시 전달 경로가 Valuation에 {impact_text} 영향을 줬습니다."
        )
    valuation_context = ValuationContext(
        impact=valuation_impact,
        summary=valuation_summary,
        market_expectation_level=expectation_level,
        market_expectation_summary=str(expectations.get("summary", "")),
        primary_method=str(framework.get("primary_method", "")),
        configured_expansion_signals=expansion_signals,
        configured_compression_signals=compression_signals,
        matched_expansion_signals=_unique(matched_expansion),
        matched_compression_signals=_unique(matched_compression),
        matched_expansion_conditions=_unique(matched_expansion),
        matched_compression_conditions=_unique(matched_compression),
        macro_valuation_effect=macro_valuation_effect,
        macro_valuation_effects=macro_valuation_effects,
        valuation_evidence=valuation_evidence,
        previous_impact=previous_impact,
        valuation_relative_position=(
            valuation_snapshot.valuation_relative_position
            if valuation_snapshot is not None
            else "unknown"
        ),
        valuation_relative_basis=(
            valuation_snapshot.valuation_relative_basis
            if valuation_snapshot is not None
            else None
        ),
        evidence_count=len(valuation_evidence),
    )
    market_expectation_assessment = _expectation_assessment(
        expectations, valuation_context
    )
    fact_events = all_events if is_initial_baseline else events
    confirmed_facts, inferred_implications, unknowns = _assessment_evidence_layers(fact_events)
    new_warnings = _unique(
        fact
        for event in events
        if event.provider in TRUSTED_FACT_PROVIDERS
        and event_is_eligible_for_current_analysis(event)
        and (
            event.event_type in NEGATIVE_EVENT_TYPES
            or bool(_matching_signals(_event_text(event), weaken_signals))
            or bool(_matching_signals(_event_text(event), invalidation_signals))
        )
        for fact in _warning_facts(event)
    )
    open_warnings, warning_states = _warning_lifecycle(
        previous_assessment,
        new_warnings,
        events,
        baseline_warnings=baseline_warning_states,
        ticker=thesis.ticker,
        assessment_date=(
            macro_impact.assessment_date
            if macro_impact is not None
            else date.today()
        ),
    )
    legacy_thesis_sentences = {
        thesis.core_thesis.strip(),
        *(item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", thesis.core_thesis)),
    }
    open_warnings = [
        item for item in open_warnings if item.strip() not in legacy_thesis_sentences
    ]
    persistent_watch_risks = _persistent_watch_risks(thesis)
    confirmed_warnings = new_warnings
    watch_items = _unique(_watch_text(item) for item in unknowns)
    background_confirmed_facts = _previous_facts(previous_assessment)
    used_event_fingerprints = [event_fingerprint(event) for event in all_events]

    net_score = max(-100, min(100, positive_points - negative_points))
    confidence = _assessment_confidence(
        events,
        price_context,
        valuation_snapshot,
        unknowns,
    )
    price_view = _price_view(price_context)
    new_buyer_price_view, holder_price_view = _price_audience_views(
        price_decision,
        expectation_level,
    )

    if is_initial_baseline:
        summary = "초기 투자 논리와 현재 가격·Valuation 기준선을 설정했습니다."
        new_buyer_view = "신규 관찰자는 저장된 투자 논리와 현재 가격·Valuation 기준을 출발점으로 봅니다."
        holder_view = "보유자는 초기 감시 항목과 무효화 조건을 기준선으로 확인합니다."
        risk_level = "watch"
        daily_change_severity = "none"
        valuation_context.impact = ValuationImpact.neutral
        valuation_context.summary = "초기 기준선에서는 일간 Valuation 변화를 평가하지 않습니다."
        valuation_context.macro_valuation_effect = "neutral"
        valuation_context.macro_valuation_effects = []
        valuation_context.matched_expansion_signals = []
        valuation_context.matched_compression_signals = []
        valuation_context.matched_expansion_conditions = []
        valuation_context.matched_compression_conditions = []
        valuation_context.valuation_evidence = []
        valuation_context.evidence_count = 0
        new_warnings = []
        confirmed_warnings = []
        should_deactivate = False
    elif status == AssessmentStatus.strengthened:
        summary = "새 근거가 현재 투자 논리를 강화했습니다."
        new_buyer_view = "신규 진입 관점에서는 가격 위치와 밸류에이션을 확인한 뒤 분할 접근을 검토할 수 있습니다."
        holder_view = "보유자 관점에서는 핵심 근거의 지속 여부를 확인하며 보유 논리를 유지할 수 있습니다."
        risk_level = "watch"
    elif status == AssessmentStatus.weakened:
        summary = "새 근거가 현재 투자 논리를 약화했습니다."
        new_buyer_view = "신규 진입은 약화 원인이 해소되거나 가격 안전마진이 확인될 때까지 주의가 필요합니다."
        holder_view = "보유자는 약화가 일시적인지 구조적인지 확인하고 비중과 손실 허용 범위를 재점검해야 합니다."
        risk_level = "caution"
    elif status == AssessmentStatus.invalidated:
        summary = "명시된 무효화 조건이 신뢰도 높은 근거로 확인되어 투자 판단 폐기 수준입니다."
        new_buyer_view = "신규 진입 근거가 소멸했으므로 기존 투자 논리로는 접근하지 않는 편이 합리적입니다."
        holder_view = "보유자는 기존 투자 논리를 폐기하고 독립적으로 포지션 정리를 검토해야 합니다."
        risk_level = "critical"
    elif status == AssessmentStatus.invalidation_candidate:
        summary = "무효화 조건과 연결되는 근거가 발견됐지만 자동 폐기 전 확인이 필요합니다."
        new_buyer_view = "무효화 여부가 확인될 때까지 신규 진입을 보류하는 편이 합리적입니다."
        holder_view = "보유자는 원문 근거를 우선 확인하고 위험 노출을 재점검해야 합니다."
        risk_level = "high"
    elif status == AssessmentStatus.mixed:
        summary = "투자 논리를 강화하는 근거와 약화하는 근거가 함께 확인됐습니다."
        new_buyer_view = "신규 진입은 상반된 근거의 중요도와 가격 안전마진을 함께 비교해야 합니다."
        holder_view = "보유자는 핵심 전제별로 긍정·부정 근거를 나눠 비중 유지 여부를 검토해야 합니다."
        risk_level = "caution"
    elif status == AssessmentStatus.needs_review:
        summary = "중요 이벤트가 있으나 투자 논리의 방향을 자동 판정하기에는 근거가 부족합니다."
        new_buyer_view = "신규 진입 전 원문 확인이 필요합니다."
        holder_view = "보유자는 판단을 바꾸기 전에 추가 근거를 확인해야 합니다."
        risk_level = "review"
    else:
        summary = "현재 투자 논리를 바꿀 만한 새로운 근거가 확인되지 않았습니다."
        new_buyer_view = "신규 진입 판단은 기존 투자 논리와 가격 기준을 유지합니다."
        holder_view = "보유자는 기존 모니터링 조건을 유지합니다."
        risk_level = "normal"

    structural_risk = _structural_risk_level(
        status,
        expectation_level,
        open_warnings,
        previous_assessment,
    )
    daily_change_severity = "none" if is_initial_baseline else _daily_change_severity(status)
    assessment_state = AssessmentState(price_decision.assessment_state)
    snapshot = valuation_snapshot or ValuationSnapshot(
        current_price=price_decision.current_price,
        currency=price_decision.currency,
        price_as_of=price_decision.price_as_of,
        price_basis=price_decision.price_basis,
        quality="unavailable",
        warnings=["Valuation 배수 provider 결과가 없어 배수는 자료 없음입니다."],
    )

    return EvaluationResult(
        status=status,
        score=net_score,
        confidence=confidence,
        summary=summary,
        new_buyer_view=new_buyer_view,
        holder_view=holder_view,
        price_view=price_view,
        risk_level=risk_level,
        daily_change_severity=daily_change_severity,
        structural_risk_level=structural_risk,
        assessment_state=assessment_state,
        market_session=price_decision.market_session,
        evidence=evidence,
        valuation_context=valuation_context,
        earnings_estimate_impact=earnings_estimate_impact,
        market_expectation_assessment=market_expectation_assessment,
        confirmed_facts=confirmed_facts,
        background_confirmed_facts=background_confirmed_facts,
        inferred_implications=inferred_implications,
        unknowns=unknowns,
        confirmed_warnings=confirmed_warnings,
        new_warnings=new_warnings,
        open_warnings=open_warnings,
        open_confirmed_warnings=open_warnings,
        persistent_watch_risks=persistent_watch_risks,
        warning_states=warning_states,
        watch_items=watch_items,
        new_buyer_price_view=new_buyer_price_view,
        holder_price_view=holder_price_view,
        valuation_snapshot=snapshot,
        used_event_fingerprints=used_event_fingerprints,
        should_deactivate=should_deactivate if is_initial_baseline else trusted_invalidation,
    )


def recent_events_for_assessment(
    session: Session,
    ticker: str,
    assessment_date: date,
    thesis_version: int | None = None,
) -> list[Event]:
    query = select(ThesisAssessment).where(
        ThesisAssessment.ticker == ticker,
        ThesisAssessment.assessment_date <= assessment_date,
    )
    if thesis_version is not None:
        query = query.where(ThesisAssessment.thesis_version == thesis_version)
    previous_assessments = session.exec(
        query.order_by(ThesisAssessment.assessment_date)
    ).all()
    used_fingerprints: set[str] = set()
    used_urls: set[str] = set()
    legacy_created_cutoff = None
    for previous in previous_assessments:
        previous_fingerprints = _json_list(previous.used_event_fingerprints)
        used_fingerprints.update(previous_fingerprints)
        if not previous_fingerprints and (
            legacy_created_cutoff is None or previous.created_at > legacy_created_cutoff
        ):
            legacy_created_cutoff = previous.created_at
        for item in _json_value_list(previous.evidence):
            url = str(item.get("url", ""))
            if url:
                used_urls.add(url)
    latest_assessment = previous_assessments[-1] if previous_assessments else None
    events = session.exec(
        select(Event)
        .where(Event.ticker == ticker, Event.date <= assessment_date)
        .order_by(Event.date.desc(), Event.relevance_score.desc())
    ).all()
    return [
        event
        for event in events
        if event_fingerprint(event) not in used_fingerprints
        and event_is_eligible_for_current_analysis(event)
        and event.url not in used_urls
        and (legacy_created_cutoff is None or event.created_at > legacy_created_cutoff)
        and (
            latest_assessment is None
            or event.date > latest_assessment.assessment_date
            or (
                event.date == latest_assessment.assessment_date
                and event.created_at > latest_assessment.created_at
            )
        )
    ]


def _json_value_list(value: str) -> list[dict[str, object]]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [item for item in parsed if isinstance(item, dict)] if isinstance(parsed, list) else []
