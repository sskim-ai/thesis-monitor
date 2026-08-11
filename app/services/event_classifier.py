import re

from app.providers.base import RawEvent
from app.schemas.event import EventType
from app.services.corporate_action_terms import is_buyback_text


KEYWORD_EVENT_TYPES: list[tuple[EventType, tuple[str, ...]]] = [
    (EventType.earnings_beat, ("earnings beat", "beat estimates", "beat consensus")),
    (EventType.earnings_miss, ("earnings miss", "missed estimates", "missed consensus")),
    (EventType.production_delay, ("production delay", "ramp delay", "shipment delay")),
    (EventType.major_customer_win, ("major customer win", "strategic customer win")),
    (EventType.customer_loss, ("major customer loss", "lost customer", "customer loss")),
    (
        EventType.revenue_guidance_change,
        (
            "revenue guidance changed",
            "revenue outlook changed",
            "revenue forecast",
            "sales forecast",
            "revenue outlook",
        ),
    ),
    (EventType.margin_guidance_change, ("margin guidance changed", "margin outlook changed")),
    (EventType.operating_cash_flow_change, ("operating cash flow changed", "cash from operations changed")),
    (EventType.fcf_change, ("free cash flow changed", "fcf changed")),
    (EventType.capex_change, ("capex changed", "capital expenditure changed")),
    (EventType.order_change, ("order change", "orders changed", "backlog changed")),
    (EventType.dilution, ("share dilution", "dilutive financing")),
    (EventType.debt_liquidity, ("material liquidity", "liquidity shortfall", "debt maturity risk")),
    (EventType.regulatory_material, ("material regulatory", "regulatory order", "regulatory action")),
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
    (
        EventType.convertible_bond,
        ("convertible bond", "convertible note", "전환사채", "전환가액 조정", "cb"),
    ),
    (EventType.warrant, ("warrant", "신주인수권", "bw")),
    (EventType.stock_compensation_increase, ("stock compensation increase", "stock-based compensation increase")),
    (
        EventType.buyback,
        (
            "share repurchase",
            "stock repurchase",
            "buyback",
            "repurchase authorization",
            "accelerated share repurchase",
            "자사주 매입",
            "자기주식 취득",
        ),
    ),
    (EventType.share_retirement, ("share retirement", "주식 소각", "자기주식 소각")),
    (EventType.dividend, ("배당", "현금ㆍ현물배당", "cash dividend")),
    (EventType.stock_split, ("stock split", "주식분할")),
    (EventType.reverse_split, ("reverse split", "주식병합")),
    (EventType.capital_reduction, ("capital reduction", "감자")),
    (EventType.capital_allocation, ("자기주식", "자사주")),
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
    (
        EventType.guidance_change,
        (
            "분기보고서",
            "반기보고서",
            "사업보고서",
            "영업(잠정)실적",
            "잠정영업실적",
            "잠정실적",
            "매출액 또는 손익구조 변동",
            "매출액또는손익구조변동",
        ),
    ),
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

MATERIAL_PROVIDERS = {"opendart", "sec_edgar", "company_ir"}
KNOWN_ENTITY_ALIASES = {
    "GOOGL": ("alphabet", "google", "youtube", "waymo", "deepmind", "android", "gemini"),
    "TSLA": ("tesla", "robotaxi", "cybercab", "full self-driving", "fsd"),
    "TSM": ("tsmc", "taiwan semiconductor"),
    "MU": ("micron",),
    "SNDK": ("sandisk", "san disk"),
    "RXRX": ("recursion pharmaceuticals", "recursion"),
    "WRD": ("weride",),
    "CRCL": ("circle internet", "usdc"),
}


def _mentions_company(raw_event: RawEvent, text: str) -> bool:
    if raw_event.identity_status.startswith("rejected"):
        return False
    if raw_event.identity_validated:
        return True
    source = raw_event.source.lower()
    if (
        raw_event.provider in MATERIAL_PROVIDERS | {"mock"}
        or "company ir" in source
        or "company filing" in source
    ):
        return True
    ticker = raw_event.ticker.lower().strip()
    if ticker and re.search(rf"(?<![a-z0-9]){re.escape(ticker)}(?![a-z0-9])", text):
        return True
    company = (raw_event.company_name or "").lower().strip()
    if company and company in text:
        return True
    if any(alias in text for alias in KNOWN_ENTITY_ALIASES.get(raw_event.ticker.upper(), ())):
        return True
    generic_tokens = {
        "company",
        "corporation",
        "corp",
        "inc",
        "limited",
        "holdings",
        "technology",
        "technologies",
        "class",
    }
    company_tokens = {
        token
        for token in re.findall(r"[a-z0-9가-힣]+", company)
        if len(token) >= 4 and token not in generic_tokens
    }
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", text)
        for token in company_tokens
    )


def _flag_event_type(raw_event: RawEvent, text: str) -> EventType | None:
    if raw_event.confirmed_buyback:
        return EventType.buyback
    if raw_event.buyback_candidate or is_buyback_text(text):
        return EventType.capital_allocation
    if raw_event.financial_report_filed:
        return EventType.financial_report
    if raw_event.accounting_issue:
        return EventType.accounting_issue
    if raw_event.debt_liquidity_risk:
        return EventType.debt_liquidity
    if raw_event.regulatory_material:
        return EventType.regulatory_material
    if raw_event.production_delay:
        return EventType.production_delay
    if raw_event.major_order_change:
        return EventType.order_change
    if raw_event.dilution_risk:
        return EventType.dilution
    if raw_event.material_customer_change:
        if any(term in text for term in ("loss", "lost", "terminated", "해지", "중단")):
            return EventType.customer_loss
        return EventType.major_customer_win
    if raw_event.margin_guidance_changed:
        return EventType.margin_guidance_change
    if raw_event.fcf_impact_known:
        return EventType.fcf_change
    if raw_event.operating_cash_flow_impact_known:
        return EventType.operating_cash_flow_change
    if raw_event.revenue_guidance_changed:
        return EventType.revenue_guidance_change
    if raw_event.guidance_changed or raw_event.earnings_guidance_changed:
        return EventType.guidance_change
    return None


def _has_standalone_mou(text: str) -> bool:
    return re.search(r"\bmou\b", text) is not None


def classify_event(raw_event: RawEvent) -> EventType:
    relevance_text = " ".join(
        [raw_event.title, raw_event.summary, raw_event.source]
    ).lower()
    text = " ".join(
        [
            raw_event.title,
            raw_event.summary,
            raw_event.source,
            " ".join(raw_event.keywords),
            " ".join(raw_event.confirmed_facts),
        ]
    ).lower()

    if not _mentions_company(raw_event, relevance_text):
        return EventType.non_thesis_noise

    flagged_type = _flag_event_type(raw_event, text)
    if flagged_type is not None:
        return flagged_type

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
