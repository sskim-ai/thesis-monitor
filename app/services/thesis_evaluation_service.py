import json
import re
from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, select

from app.models.event import Event
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.schemas.thesis import AssessmentStatus, PriceContext, PriceRuleEvaluation


POSITIVE_EVENT_TYPES = {
    "new_customer",
    "large_order",
    "production_order",
    "revenue_guidance_up",
    "margin_improvement",
    "inventory_normalization",
    "partnership_to_revenue",
    "earnings_surprise",
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
}

TRUSTED_INVALIDATION_PROVIDERS = {"opendart", "sec_edgar", "company_ir"}


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
    evidence: list[dict[str, object]]
    should_deactivate: bool = False


def evaluate_thesis(
    thesis: InvestmentThesis,
    events: list[Event],
    price_context: PriceContext,
) -> EvaluationResult:
    strengthen_signals = _json_list(thesis.strengthen_signals)
    weaken_signals = _json_list(thesis.weaken_signals)
    invalidation_signals = _json_list(thesis.invalidation_signals)
    positive_points = 0
    negative_points = 0
    invalidation_matches: list[tuple[Event, list[str]]] = []
    evidence: list[dict[str, object]] = []

    for event in events:
        text = _event_text(event)
        strengthen_matches = _matching_signals(text, strengthen_signals)
        weaken_matches = _matching_signals(text, weaken_signals)
        invalid_matches = _matching_signals(text, invalidation_signals)
        direction = "neutral"
        if invalid_matches:
            direction = "invalidation"
            negative_points += event.relevance_score
            invalidation_matches.append((event, invalid_matches))
        elif weaken_matches or event.event_type in NEGATIVE_EVENT_TYPES:
            direction = "weaken"
            negative_points += event.relevance_score
        elif strengthen_matches or event.event_type in POSITIVE_EVENT_TYPES:
            direction = "strengthen"
            positive_points += event.relevance_score

        if direction != "neutral" or event.requires_review:
            evidence.append(
                {
                    "date": str(event.date),
                    "title": event.title,
                    "url": event.url,
                    "provider": event.provider,
                    "event_type": event.event_type,
                    "direction": direction,
                    "relevance_score": event.relevance_score,
                    "matched_signals": [
                        *strengthen_matches,
                        *weaken_matches,
                        *invalid_matches,
                    ],
                }
            )

    price_result = _evaluate_price_rules(thesis, price_context)
    positive_points += price_result.positive_points
    negative_points += price_result.negative_points
    if price_result.evidence is not None:
        evidence.append(price_result.evidence)

    trusted_invalidation = any(
        event.provider in TRUSTED_INVALIDATION_PROVIDERS
        and event.relevance_score >= 80
        and bool(_json_list(event.confirmed_facts))
        for event, _matches in invalidation_matches
    )
    if price_result.invalidated or trusted_invalidation:
        status = AssessmentStatus.invalidated
    elif invalidation_matches:
        status = AssessmentStatus.invalidation_candidate
    elif positive_points >= 20 and negative_points >= 20:
        status = AssessmentStatus.mixed
    elif positive_points - negative_points >= 20:
        status = AssessmentStatus.strengthened
    elif negative_points - positive_points >= 20:
        status = AssessmentStatus.weakened
    elif evidence:
        status = AssessmentStatus.needs_review
    else:
        status = AssessmentStatus.no_material_change

    net_score = max(-100, min(100, positive_points - negative_points))
    confidence = 0.0
    if evidence:
        confidence = round(
            min(0.95, 0.45 + max(item["relevance_score"] for item in evidence) / 200), 2
        )
    price_view = _price_view(price_context)

    if status == AssessmentStatus.strengthened:
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

    return EvaluationResult(
        status=status,
        score=net_score,
        confidence=confidence,
        summary=summary,
        new_buyer_view=new_buyer_view,
        holder_view=holder_view,
        price_view=price_view,
        risk_level=risk_level,
        evidence=evidence,
        should_deactivate=status == AssessmentStatus.invalidated,
    )


def recent_events_for_assessment(
    session: Session,
    ticker: str,
    assessment_date: date,
) -> list[Event]:
    previous = session.exec(
        select(ThesisAssessment)
        .where(
            ThesisAssessment.ticker == ticker,
            ThesisAssessment.assessment_date < assessment_date,
        )
        .order_by(ThesisAssessment.assessment_date.desc())
    ).first()
    query = select(Event).where(Event.ticker == ticker)
    if previous is not None:
        query = query.where(Event.created_at > previous.created_at)
    return list(
        session.exec(query.order_by(Event.date.desc(), Event.relevance_score.desc())).all()
    )
