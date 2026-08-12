import re

from app.providers.base import RawEvent
from app.schemas.event import EventType
from app.services.event_classifier import classify_event


def _fact_value(facts: list[str], prefix: str) -> str | None:
    for fact in facts:
        if prefix in fact:
            return fact.split("=", 1)[-1].strip()
    return None


def _facts_containing(facts: list[str], text: str) -> list[str]:
    return [fact for fact in facts if text in fact]


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


def _to_int(value: str | None) -> int | None:
    parsed = _to_float(value)
    return int(parsed) if parsed is not None else None


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _format_krw(amount: int | None) -> str:
    if amount is None:
        return "unknown"
    return f"{amount:,} KRW"


def _basis_fragment(fact: str | None) -> str | None:
    if fact is None:
        return None
    match = re.search(r"\(([^)]*fs_div=[^)]+)\)", fact)
    return match.group(1) if match else None


def _basis_value(fragment: str | None, key: str) -> str | None:
    if fragment is None:
        return None
    match = re.search(rf"{re.escape(key)}=([^;)]*)", fragment)
    return match.group(1).strip() if match else None


def _metric_value(facts: list[str], labels: tuple[str, ...]) -> float | None:
    for label in labels:
        value = _fact_value(facts, label)
        if value is not None:
            return _to_float(value)
    return None


def _populate_structured_metrics(raw_event: RawEvent) -> None:
    facts = raw_event.confirmed_facts
    raw_event.revenue = _metric_value(
        facts, ("financial fact: 매출액", "financial fact: 수익(매출액)", "revenue")
    )
    raw_event.operating_income = _metric_value(
        facts, ("financial fact: 영업이익", "operating_income", "operating income")
    )
    raw_event.net_income = _metric_value(
        facts, ("financial fact: 당기순이익", "financial fact: 분기순이익", "net_income")
    )
    revenue_fact = next(iter(_facts_containing(facts, "financial fact: 매출액")), None)
    profit_fact = next(iter(_facts_containing(facts, "financial fact: 영업이익")), None)
    revenue_basis = _basis_fragment(revenue_fact)
    profit_basis = _basis_fragment(profit_fact)
    if (
        raw_event.revenue not in {None, 0}
        and raw_event.operating_income is not None
        and (not revenue_basis or not profit_basis or revenue_basis == profit_basis)
    ):
        raw_event.operating_margin = raw_event.operating_income / raw_event.revenue * 100
    raw_event.yoy_growth = _metric_value(
        facts, ("yoy_growth", "yoy growth", "전년동기대비")
    )
    raw_event.qoq_growth = _metric_value(
        facts, ("qoq_growth", "qoq growth", "전분기대비")
    )
    raw_event.capex_amount = _metric_value(
        facts,
        (
            "facility investment fact: amount",
            "capital expenditure fact: amount",
            "capex_amount",
        ),
    )
    raw_event.financing_amount = _metric_value(
        facts,
        (
            "capital raise fact: amount",
            "convertible bond fact: amount",
            "financing_amount",
        ),
    )
    raw_event.dilution_amount = _metric_value(
        facts,
        (
            "capital raise fact: new_shares",
            "convertible bond fact: convertible_shares",
            "dilution_amount",
        ),
    )


def _interpret_supply_contract(raw_event: RawEvent, implications: list[str], unknowns: list[str]) -> None:
    facts = raw_event.confirmed_facts
    contract_name = _fact_value(facts, "supply contract fact: contract_name")
    counterparty = _fact_value(facts, "supply contract fact: counterparty")
    amount = _to_int(_fact_value(facts, "supply contract fact: amount"))
    ratio = _to_float(_fact_value(facts, "supply contract fact: recent_sales_ratio"))
    region = _fact_value(facts, "supply contract fact: region")
    period = _fact_value(facts, "supply contract fact: period")

    if amount is not None:
        _append_unique(implications, f"Confirmed order/contract amount is about {_format_krw(amount)}.")
    if ratio is not None:
        if ratio >= 10:
            _append_unique(implications, "Contract size is very material relative to recent revenue; valuation and revenue model should be reviewed.")
        elif ratio >= 5:
            _append_unique(implications, "Contract size is material relative to recent revenue and may strengthen the demand thesis.")
        elif ratio >= 1:
            _append_unique(implications, "Contract size is measurable relative to recent revenue but may not by itself reset the thesis.")
        else:
            _append_unique(implications, "Contract size appears modest relative to recent revenue.")
    if contract_name:
        _append_unique(implications, f"Contract subject is {contract_name}; verify whether it directly maps to the core investment thesis.")
    if counterparty:
        _append_unique(implications, f"Disclosed counterparty is {counterparty}; do not infer a different direct customer unless the filing states it.")
    if region:
        _append_unique(implications, f"Supply region is {region}; this may support geographic demand validation if aligned with the thesis.")
    if period:
        _append_unique(implications, f"Contract period is {period}; revenue recognition timing and margin should be checked separately.")
    if amount is None:
        _append_unique(unknowns, "Contract amount could not be parsed into a reliable numeric value.")
    if ratio is None:
        _append_unique(unknowns, "Recent-sales ratio could not be parsed; materiality should be checked manually.")
    _append_unique(unknowns, "Margin impact is not confirmed by contract disclosure unless explicitly stated.")
    _append_unique(unknowns, "Cash-flow timing is not confirmed by contract disclosure unless payment terms are parsed and reliable.")


def _interpret_capital_allocation(raw_event: RawEvent, implications: list[str], unknowns: list[str]) -> None:
    facts = raw_event.confirmed_facts
    if any("treasury stock fact:" in fact.lower() for fact in facts):
        _append_unique(
            unknowns,
            "Treasury-stock purpose and transaction size require share-count materiality review.",
        )


def _interpret_facility_investment(
    raw_event: RawEvent,
    implications: list[str],
    unknowns: list[str],
) -> None:
    amount = _metric_value(
        raw_event.confirmed_facts,
        ("facility investment fact: amount", "capital expenditure fact: amount"),
    )
    if amount is not None:
        _append_unique(
            implications,
            f"Confirmed facility investment amount is about {_format_krw(int(amount))}.",
        )
    _append_unique(
        implications,
        "A facility investment disclosure may change capacity, capex, cash-flow, and future earnings assumptions.",
    )
    if amount is None:
        _append_unique(unknowns, "Investment amount and funding source are not confirmed from the filing title alone.")
    _append_unique(unknowns, "Investment purpose, schedule, and incremental capacity require the filing body.")
    _append_unique(unknowns, "Demand visibility, utilization, and expected return on investment are not confirmed.")


def _interpret_disclosure_inquiry(
    raw_event: RawEvent,
    implications: list[str],
    unknowns: list[str],
) -> None:
    _append_unique(
        implications,
        "An exchange disclosure inquiry confirms that clarification was requested, not that the underlying rumor is true.",
    )
    _append_unique(unknowns, "The subject and factual basis of the rumor require the original inquiry and company response.")
    _append_unique(unknowns, "No investment-thesis change should be made before the company response is reviewed.")


def _interpret_disclosure_clarification(
    raw_event: RawEvent,
    implications: list[str],
    unknowns: list[str],
) -> None:
    title = raw_event.title.lower()
    if "미확정" in title:
        _append_unique(
            implications,
            "The company response remains unconfirmed; treat the rumored matter as unresolved rather than established fact.",
        )
        _append_unique(unknowns, "Final decision, terms, timing, and probability remain unconfirmed.")
        _append_unique(unknowns, "A follow-up disclosure is required before changing the investment thesis.")
        return
    _append_unique(
        implications,
        "The company issued a clarification, but the filing body must be reviewed before drawing an investment conclusion.",
    )
    _append_unique(unknowns, "The filing title alone does not establish the clarified facts or their financial impact.")


def _interpret_earnings(raw_event: RawEvent, implications: list[str], unknowns: list[str]) -> None:
    facts = raw_event.confirmed_facts
    revenue_fact = next(iter(_facts_containing(facts, "financial fact: 매출액")), None)
    operating_income_fact = next(iter(_facts_containing(facts, "financial fact: 영업이익")), None)
    revenue = _to_int(_fact_value(facts, "financial fact: 매출액"))
    operating_income = _to_int(_fact_value(facts, "financial fact: 영업이익"))
    assets = _to_int(_fact_value(facts, "financial fact: 자산총계"))
    liabilities = _to_int(_fact_value(facts, "financial fact: 부채총계"))
    equity = _to_int(_fact_value(facts, "financial fact: 자본총계"))

    revenue_basis = _basis_fragment(revenue_fact)
    operating_basis = _basis_fragment(operating_income_fact)
    if revenue_basis:
        _append_unique(implications, f"Revenue basis metadata: {revenue_basis}.")
    if operating_basis:
        _append_unique(implications, f"Operating profit basis metadata: {operating_basis}.")
    if revenue_basis and operating_basis and revenue_basis != operating_basis:
        _append_unique(unknowns, "Financial quality warning: revenue and operating profit basis metadata differ; margin comparison needs manual verification.")

    if any("financial quality warning" in fact.lower() for fact in facts):
        for warning in facts:
            if "financial quality warning" in warning.lower():
                _append_unique(unknowns, warning)

    if revenue is not None:
        _append_unique(implications, f"Reported revenue fact parsed at about {_format_krw(revenue)}; compare against guidance and consensus.")
    if operating_income is not None:
        _append_unique(implications, f"Reported operating profit fact parsed at about {_format_krw(operating_income)}; margin trend should be reviewed.")
    if revenue and operating_income is not None:
        margin = operating_income / revenue * 100
        _append_unique(implications, f"Implied operating margin from parsed facts is about {margin:.1f}%; verify financial-statement basis before thesis judgment.")
        if margin >= 60 or margin < -20:
            _append_unique(unknowns, "Financial quality warning: implied operating margin is outside a normal operating range; verify whether OpenDART returned cumulative, separate, or mismatched statement items.")
        elif margin >= 20:
            _append_unique(implications, "Operating margin is high on parsed figures; check whether this reflects structural pricing power, cycle peak, or one-off mix effect.")
        elif margin < 5:
            _append_unique(implications, "Operating margin is thin on parsed figures; thesis quality depends heavily on margin recovery or volume leverage.")
    if assets and liabilities is not None:
        debt_to_assets = liabilities / assets * 100
        _append_unique(implications, f"Parsed liabilities/assets ratio is about {debt_to_assets:.1f}%; monitor balance-sheet risk if capex or working capital expands.")
    if equity and liabilities is not None:
        debt_to_equity = liabilities / equity * 100 if equity else None
        if debt_to_equity is not None:
            _append_unique(implications, f"Parsed liabilities/equity ratio is about {debt_to_equity:.1f}%; compare with sector capital intensity and cycle position.")
    if revenue is None:
        _append_unique(unknowns, "Revenue could not be parsed from this filing event.")
    if operating_income is None:
        _append_unique(unknowns, "Operating profit could not be parsed from this filing event.")
    _append_unique(unknowns, "YoY/QoQ growth, consensus comparison, and segment mix are not calculated from single-period facts yet.")
    _append_unique(unknowns, "Cash flow, capex, inventory, and receivables require separate statement parsing before earnings-quality judgment.")


def enrich_raw_event(raw_event: RawEvent) -> RawEvent:
    _populate_structured_metrics(raw_event)
    event_type = classify_event(raw_event)
    implications = list(raw_event.inferred_implications)
    unknowns = list(raw_event.unknowns)

    if event_type == EventType.large_order:
        _interpret_supply_contract(raw_event, implications, unknowns)
    elif event_type == EventType.capital_allocation:
        _interpret_capital_allocation(raw_event, implications, unknowns)
    elif event_type == EventType.facility_investment:
        _interpret_facility_investment(raw_event, implications, unknowns)
    elif event_type == EventType.disclosure_inquiry:
        _interpret_disclosure_inquiry(raw_event, implications, unknowns)
    elif event_type == EventType.disclosure_clarification:
        _interpret_disclosure_clarification(raw_event, implications, unknowns)
    elif event_type in {
        EventType.guidance_change,
        EventType.earnings_surprise,
        EventType.earnings_beat,
        EventType.earnings_miss,
        EventType.revenue_guidance_change,
        EventType.margin_guidance_change,
    }:
        _interpret_earnings(raw_event, implications, unknowns)

    raw_event.inferred_implications = implications
    raw_event.unknowns = unknowns
    return raw_event
