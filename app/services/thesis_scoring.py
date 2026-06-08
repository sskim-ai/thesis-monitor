from app.providers.base import RawEvent
from app.schemas.event import EventType, ThesisRelevance


EVENT_TYPE_SCORES: dict[EventType, int] = {
    EventType.new_customer: 20,
    EventType.large_order: 25,
    EventType.production_order: 25,
    EventType.mass_production_change: 25,
    EventType.revenue_guidance_up: 30,
    EventType.revenue_guidance_down: 30,
    EventType.margin_improvement: 20,
    EventType.margin_deterioration: 20,
    EventType.fcf_deterioration: 25,
    EventType.inventory_increase: 20,
    EventType.receivables_increase: 15,
    EventType.capital_raise: 30,
    EventType.convertible_bond: 30,
    EventType.warrant: 30,
    EventType.stock_compensation_increase: 15,
    EventType.partnership: 5,
    EventType.customer_loss: 30,
    EventType.customer_concentration_risk: 15,
    EventType.competitor_price_cut: 20,
    EventType.earnings_miss: 25,
    EventType.guidance_change: 20,
    EventType.management_governance: 10,
    EventType.capital_allocation: 15,
    EventType.regulatory_risk: 25,
    EventType.export_control: 25,
    EventType.antitrust: 25,
    EventType.accounting_issue: 25,
    EventType.debt_liquidity_risk: 25,
    EventType.non_thesis_noise: 0,
}


def score_event(raw_event: RawEvent, event_type: EventType) -> ThesisRelevance:
    text = " ".join(
        [
            raw_event.title,
            raw_event.summary,
            raw_event.source,
            " ".join(raw_event.keywords),
            " ".join(raw_event.confirmed_facts),
        ]
    ).lower()
    score = EVENT_TYPE_SCORES.get(event_type, 10)
    reasons: list[str] = []

    if "customer name was disclosed" in text or "named customer" in text:
        score += 20
        reasons.append("named customer was disclosed")
    if "new customer" in text and event_type != EventType.new_customer:
        score += 20
        reasons.append("new customer was disclosed")
    if (
        "large order" in text
        or "major order" in text
        or "supply contract" in text
        or "공급계약" in text
        or "단일판매" in text
    ):
        score += 25
        reasons.append("large order or supply contract language appears in source")
    if "production order" in text:
        if event_type != EventType.production_order:
            score += 25
        reasons.append("production order may validate demand thesis")
    if "mass production change" in text or "production schedule change" in text:
        if event_type != EventType.mass_production_change:
            score += 25
        reasons.append("mass production timing changed")
    if "guidance" in text and (
        "raised" in text
        or "lowered" in text
        or "cut" in text
        or "increase" in text
        or "decrease" in text
    ):
        if event_type not in {EventType.revenue_guidance_up, EventType.revenue_guidance_down}:
            score += 30
        reasons.append("guidance change may require model update")
    if any(term in text for term in ("분기보고서", "반기보고서", "사업보고서", "잠정실적", "영업(잠정)실적")):
        reasons.append("periodic or preliminary filing may require earnings checkpoint review")
    if "margin" in text:
        reasons.append("margin impact should be reviewed")
    if "fcf" in text or "free cash flow" in text:
        reasons.append("cash flow impact is thesis-relevant")
    if "inventory" in text or "재고" in text:
        reasons.append("inventory change can signal demand or channel risk")
    if "receivables" in text or "매출채권" in text:
        reasons.append("receivables change can signal collection risk")
    if event_type in {EventType.capital_raise, EventType.convertible_bond, EventType.warrant}:
        reasons.append("financing terms may affect shareholder value")
    if event_type == EventType.stock_compensation_increase:
        reasons.append("stock-based compensation expansion may affect per-share economics")
    if event_type == EventType.customer_loss:
        reasons.append("customer loss may impair demand or concentration thesis")
    if event_type == EventType.earnings_miss:
        reasons.append("earnings miss may require thesis review")
    if event_type == EventType.customer_concentration_risk:
        reasons.append("related-party or concentration disclosure may require governance review")
    if event_type == EventType.management_governance:
        reasons.append("governance or ownership disclosure should be reviewed if thesis depends on control quality")
    if event_type == EventType.capital_allocation:
        reasons.append("capital allocation disclosure may affect shareholder return assumptions")
    if event_type == EventType.competitor_price_cut:
        reasons.append("competitor price cut may pressure share or margin")
    if event_type in {EventType.regulatory_risk, EventType.export_control, EventType.accounting_issue}:
        reasons.append("regulatory or accounting issue may require review")

    if event_type == EventType.non_thesis_noise:
        score = 0
        reasons = ["no confirmed thesis-relevant operating change detected"]

    score = min(score, 100)
    return ThesisRelevance(
        requires_review=score >= 40,
        relevance_score=score,
        reason="; ".join(reasons) if reasons else "rule-based baseline score",
    )
