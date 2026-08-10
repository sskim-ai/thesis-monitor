import re

from app.providers.base import RawEvent
from app.schemas.event import EventType


KEYWORD_EVENT_TYPES: list[tuple[EventType, tuple[str, ...]]] = [
    (EventType.production_order, ("production order", "production schedule")),
    (
        EventType.large_order,
        (
            "large order",
            "major order",
            "large purchase",
            "supply contract",
            "공급계약",
            "단일판매",
            "판매ㆍ공급계약",
            "공사수주",
        ),
    ),
    (EventType.new_customer, ("new customer", "customer name was disclosed", "named customer")),
    (EventType.mass_production_change, ("mass production change", "production schedule change")),
    (EventType.revenue_guidance_up, ("guidance raised", "raises revenue guidance", "guidance up", "guidance increase")),
    (EventType.revenue_guidance_down, ("guidance lowered", "cuts revenue guidance", "guidance down", "guidance decrease")),
    (EventType.margin_improvement, ("margin improvement", "margin expansion")),
    (EventType.margin_deterioration, ("margin deterioration", "margin compression")),
    (EventType.fcf_deterioration, ("free cash flow deterioration", "fcf deterioration")),
    (EventType.inventory_increase, ("inventory increase", "inventory build")),
    (EventType.inventory_normalization, ("inventory normalization", "inventory normalisation")),
    (EventType.receivables_increase, ("receivables increase", "days sales outstanding")),
    (EventType.capital_raise, ("capital raise", "equity offering", "secondary offering", "유상증자")),
    (EventType.convertible_bond, ("convertible bond", "convertible note", "전환사채", "cb")),
    (EventType.warrant, ("warrant", "신주인수권", "bw")),
    (EventType.stock_compensation_increase, ("stock compensation increase", "stock-based compensation increase")),
    (EventType.capital_allocation, ("자기주식", "자사주", "배당", "현금ㆍ현물배당")),
    (EventType.facility_investment, ("신규시설투자", "시설투자결정", "facility investment")),
    (
        EventType.disclosure_clarification,
        (
            "조회공시요구(풍문또는보도)에대한답변",
            "조회공시요구에대한답변",
            "풍문또는보도에대한해명",
            "clarification of rumor",
        ),
    ),
    (EventType.disclosure_inquiry, ("조회공시요구", "disclosure inquiry")),
    (EventType.partnership_to_revenue, ("partnership revenue", "commercialized partnership")),
    (EventType.partnership, ("partnership", "collaboration", "업무협약")),
    (EventType.customer_loss, ("customer loss", "lost customer", "거래중단")),
    (EventType.customer_concentration_risk, ("특수관계인과의내부거래", "내부거래")),
    (EventType.competitor_price_cut, ("competitor price cut", "price cut")),
    (EventType.competitor_new_product, ("competitor new product", "new product launch")),
    (EventType.management_governance, ("기업지배구조보고서", "임원ㆍ주요주주", "임원･주요주주", "최대주주", "대표이사")),
    (EventType.guidance_change, ("분기보고서", "반기보고서", "사업보고서", "영업(잠정)실적", "잠정실적")),
    (EventType.earnings_surprise, ("earnings surprise", "beat expectations")),
    (EventType.earnings_miss, ("earnings miss", "missed expectations", "missed guidance")),
    (EventType.antitrust, ("antitrust",)),
    (EventType.export_control, ("export control", "수출통제")),
    (EventType.regulatory_risk, ("regulatory risk", "regulator", "제재", "과징금")),
    (EventType.accounting_issue, ("accounting issue", "restatement", "감사보고서", "의견거절")),
    (EventType.debt_liquidity_risk, ("liquidity risk", "debt covenant", "채무", "유동성")),
]

NOISE_TERMS = (
    "conference",
    "price target",
    "target price",
    "ai beneficiary",
    "ai tailwind",
    "social media rumor",
    "rumor",
    "목표주가",
    "컨퍼런스",
    "루머",
)


def _has_standalone_mou(text: str) -> bool:
    return re.search(r"\bmou\b", text) is not None


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
        term in text
        for term in (
            "production order",
            "guidance",
            "customer disclosed",
            "공급계약",
            "실적",
            "분기보고서",
            "사업보고서",
        )
    ):
        return EventType.non_thesis_noise

    for event_type, keywords in KEYWORD_EVENT_TYPES:
        if any(keyword in text for keyword in keywords):
            return event_type

    if _has_standalone_mou(text):
        return EventType.partnership

    return EventType.non_thesis_noise
