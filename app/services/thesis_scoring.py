from app.providers.base import RawEvent
from app.schemas.event import EventType, ThesisRelevance


EVENT_TYPE_SCORES: dict[EventType, int] = {
    EventType.new_customer: 20,
    EventType.large_order: 25,
    EventType.production_order: 25,
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
    EventType.partnership: 5,
    EventType.non_thesis_noise: 0,
}


def score_event(raw_event: RawEvent, event_type: EventType) -> ThesisRelevance:
    text = " ".join(
        [
            raw_event.title,
            raw_event.summary,
            " ".join(raw_event.keywords),
            " ".join(raw_event.confirmed_facts),
        ]
    ).lower()
    score = EVENT_TYPE_SCORES.get(event_type, 10)
    reasons: list[str] = []

    if "customer name was disclosed" in text or "named customer" in text:
        score += 20
        reasons.append("named customer was disclosed")
    if "large order" in text or "major order" in text:
        score += 25
        reasons.append("large order language appears in source")
    if "production order" in text:
        if event_type != EventType.production_order:
            score += 25
        reasons.append("production order may validate demand thesis")
    if "guidance" in text and ("raised" in text or "lowered" in text or "cut" in text):
        if event_type not in {EventType.revenue_guidance_up, EventType.revenue_guidance_down}:
            score += 30
        reasons.append("guidance change may require model update")
    if "margin" in text:
        reasons.append("margin impact should be reviewed")
    if "fcf" in text or "free cash flow" in text:
        reasons.append("cash flow impact is thesis-relevant")
    if "inventory" in text:
        reasons.append("inventory change can signal demand or channel risk")
    if "receivables" in text:
        reasons.append("receivables change can signal collection risk")
    if event_type in {EventType.capital_raise, EventType.convertible_bond, EventType.warrant}:
        reasons.append("financing terms may create dilution risk")

    if event_type == EventType.non_thesis_noise:
        score = 0
        reasons = ["no confirmed thesis-relevant operating change detected"]

    score = min(score, 100)
    return ThesisRelevance(
        requires_review=score >= 40,
        relevance_score=score,
        reason="; ".join(reasons) if reasons else "rule-based baseline score",
    )

