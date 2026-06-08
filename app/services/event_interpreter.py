import re

from app.providers.base import RawEvent
from app.schemas.event import EventType
from app.services.event_classifier import classify_event


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


def _to_int(value: str | None) -> int | None:
    parsed = _to_float(value)
    return int(parsed) if parsed is not None else None


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _interpret_supply_contract(raw_event: RawEvent, implications: list[str], unknowns: list[str]) -> None:
    facts = raw_event.confirmed_facts
    contract_name = _fact_value(facts, "supply contract fact: contract_name")
    counterparty = _fact_value(facts, "supply contract fact: counterparty")
    amount = _to_int(_fact_value(facts, "supply contract fact: amount"))
    ratio = _to_float(_fact_value(facts, "supply contract fact: recent_sales_ratio"))
    region = _fact_value(facts, "supply contract fact: region")
    period = _fact_value(facts, "supply contract fact: period")

    if amount is not None:
        _append_unique(implications, f"Confirmed order/contract amount is about {amount:,} KRW.")
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
    shares = _fact_value(facts, "treasury stock fact: shares")
    amount = _fact_value(facts, "treasury stock fact: amount")
    purpose = _fact_value(facts, "treasury stock fact: purpose")
    if shares:
        _append_unique(implications, f"Treasury stock transaction involves {shares}; check dilution/shareholder-return context.")
    if amount:
        _append_unique(implications, f"Treasury stock transaction amount is {amount}; compare with market cap and cash position.")
    if purpose:
        _append_unique(implications, f"Disclosed purpose is {purpose}; classify as shareholder return, compensation, or other capital allocation.")
    _append_unique(unknowns, "Per-share dilution or accretion cannot be concluded without share-count and treasury-stock treatment details.")


def _interpret_earnings(raw_event: RawEvent, implications: list[str], unknowns: list[str]) -> None:
    facts = raw_event.confirmed_facts
    revenue = _to_int(_fact_value(facts, "financial fact: 매출액"))
    operating_income = _to_int(_fact_value(facts, "financial fact: 영업이익"))
    if revenue is not None:
        _append_unique(implications, f"Reported revenue fact parsed at about {revenue:,} KRW; compare against guidance and consensus.")
    if operating_income is not None:
        _append_unique(implications, f"Reported operating profit fact parsed at about {operating_income:,} KRW; margin trend should be reviewed.")
    if revenue and operating_income:
        margin = operating_income / revenue * 100
        _append_unique(implications, f"Implied operating margin from parsed facts is about {margin:.1f}%; verify against reported consolidated basis.")
    _append_unique(unknowns, "YoY/QoQ growth, consensus comparison, and segment mix are not calculated from single-period facts yet.")


def enrich_raw_event(raw_event: RawEvent) -> RawEvent:
    event_type = classify_event(raw_event)
    implications = list(raw_event.inferred_implications)
    unknowns = list(raw_event.unknowns)

    if event_type == EventType.large_order:
        _interpret_supply_contract(raw_event, implications, unknowns)
    elif event_type == EventType.capital_allocation:
        _interpret_capital_allocation(raw_event, implications, unknowns)
    elif event_type == EventType.guidance_change:
        _interpret_earnings(raw_event, implications, unknowns)

    raw_event.inferred_implications = implications
    raw_event.unknowns = unknowns
    return raw_event
