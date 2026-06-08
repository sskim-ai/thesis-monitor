from app.providers.base import RawEvent
from app.schemas.event import EventType


KEYWORD_EVENT_TYPES: list[tuple[EventType, tuple[str, ...]]] = [
    (EventType.production_order, ("production order", "production schedule")),
    (EventType.large_order, ("large order", "major order", "large purchase")),
    (EventType.new_customer, ("new customer", "customer name was disclosed", "named customer")),
    (EventType.mass_production_change, ("mass production change", "production schedule change")),
    (EventType.revenue_guidance_up, ("guidance raised", "raises revenue guidance", "guidance up")),
    (EventType.revenue_guidance_down, ("guidance lowered", "cuts revenue guidance", "guidance down")),
    (EventType.margin_improvement, ("margin improvement", "margin expansion")),
    (EventType.margin_deterioration, ("margin deterioration", "margin compression")),
    (EventType.fcf_deterioration, ("free cash flow deterioration", "fcf deterioration")),
    (EventType.inventory_increase, ("inventory increase", "inventory build")),
    (EventType.inventory_normalization, ("inventory normalization", "inventory normalisation")),
    (EventType.receivables_increase, ("receivables increase", "days sales outstanding")),
    (EventType.capital_raise, ("capital raise", "equity offering", "secondary offering")),
    (EventType.convertible_bond, ("convertible bond", "convertible note")),
    (EventType.warrant, ("warrant",)),
    (EventType.stock_compensation_increase, ("stock compensation increase", "stock-based compensation increase")),
    (EventType.partnership_to_revenue, ("partnership revenue", "commercialized partnership")),
    (EventType.partnership, ("partnership", "collaboration")),
    (EventType.customer_loss, ("customer loss", "lost customer")),
    (EventType.competitor_price_cut, ("competitor price cut", "price cut")),
    (EventType.competitor_new_product, ("competitor new product", "new product launch")),
    (EventType.antitrust, ("antitrust",)),
    (EventType.export_control, ("export control",)),
    (EventType.regulatory_risk, ("regulatory risk", "regulator")),
    (EventType.accounting_issue, ("accounting issue", "restatement")),
    (EventType.debt_liquidity_risk, ("liquidity risk", "debt covenant")),
    (EventType.earnings_surprise, ("earnings surprise", "beat expectations")),
    (EventType.earnings_miss, ("earnings miss", "missed expectations")),
]

NOISE_TERMS = (
    "conference",
    "price target",
    "target price",
    "social media rumor",
    "rumor",
)


def classify_event(raw_event: RawEvent) -> EventType:
    text = " ".join(
        [
            raw_event.title,
            raw_event.summary,
            raw_event.source,
            " ".join(raw_event.keywords),
            " ".join(raw_event.confirmed_facts),
        ]
    ).lower()

    if any(term in text for term in NOISE_TERMS) and not any(
        term in text for term in ("production order", "guidance", "customer disclosed")
    ):
        return EventType.non_thesis_noise

    for event_type, keywords in KEYWORD_EVENT_TYPES:
        if any(keyword in text for keyword in keywords):
            return event_type

    return EventType.non_thesis_noise
