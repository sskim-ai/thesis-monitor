import re

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
    EventType.earnings_beat: 25,
    EventType.guidance_change: 40,
    EventType.revenue_guidance_change: 40,
    EventType.margin_guidance_change: 40,
    EventType.fcf_change: 40,
    EventType.operating_cash_flow_change: 40,
    EventType.capex_change: 35,
    EventType.major_customer_win: 45,
    EventType.order_change: 35,
    EventType.production_delay: 45,
    EventType.dilution: 45,
    EventType.debt_liquidity: 45,
    EventType.regulatory_material: 45,
    EventType.financial_report: 40,
    EventType.management_governance: 10,
    EventType.capital_allocation: 40,
    EventType.facility_investment: 45,
    EventType.disclosure_inquiry: 40,
    EventType.disclosure_clarification: 45,
    EventType.regulatory_risk: 25,
    EventType.export_control: 25,
    EventType.antitrust: 25,
    EventType.accounting_issue: 25,
    EventType.debt_liquidity_risk: 25,
    EventType.non_thesis_noise: 0,
}


def _fact_value(facts: list[str], prefix: str) -> str | None:
    for fact in facts:
        if prefix in fact:
            return fact.split("=", 1)[-1].strip()
    return None


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def score_event(raw_event: RawEvent, event_type: EventType) -> ThesisRelevance:
    text = " ".join(
        [
            raw_event.title,
            raw_event.summary,
            raw_event.source,
            " ".join(raw_event.keywords),
            " ".join(raw_event.confirmed_facts),
            " ".join(raw_event.inferred_implications),
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

    contract_amount = _to_float(_fact_value(raw_event.confirmed_facts, "supply contract fact: amount"))
    contract_ratio = _to_float(_fact_value(raw_event.confirmed_facts, "supply contract fact: recent_sales_ratio"))
    if contract_amount is not None:
        reasons.append("parsed contract amount is available")
        if contract_amount >= 1_000_000_000_000:
            score += 25
            reasons.append("contract amount exceeds 1 trillion KRW")
        elif contract_amount >= 100_000_000_000:
            score += 15
            reasons.append("contract amount exceeds 100 billion KRW")
    if contract_ratio is not None:
        if contract_ratio >= 10:
            score += 30
            reasons.append("contract exceeds 10% of recent revenue")
        elif contract_ratio >= 5:
            score += 20
            reasons.append("contract exceeds 5% of recent revenue")
        elif contract_ratio >= 1:
            score += 10
            reasons.append("contract exceeds 1% of recent revenue")

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
    if event_type == EventType.facility_investment:
        reasons.append("facility investment may affect capacity, capex, cash flow, and future earnings")
    if event_type == EventType.disclosure_inquiry:
        reasons.append("exchange disclosure inquiry requires follow-up but does not confirm the underlying rumor")
    if event_type == EventType.disclosure_clarification:
        reasons.append("company clarification requires source review before changing the investment thesis")
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
