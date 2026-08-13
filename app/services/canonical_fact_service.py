from __future__ import annotations

import json
import math
import re
from typing import Iterable

from app.models.event import Event


_INTERNAL_TEXT = re.compile(
    r"(?:opendart|\bfs_div\b|\bsj_div\b|\bperiod_scope\b|\bamount_scope\b|"
    r"\breport_code\b|\bprovider\s*(?:=|:)|\bparser\s*(?:=|:)|"
    r"\bselected_for_valuation\s*(?:=|:)|\bthstrm_nm\s*(?:=|:)|"
    r"\bunit\s*(?:=|:))",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")


def clean_user_text(value: object) -> str | None:
    text = str(value or "").strip()
    if not text or _INTERNAL_TEXT.search(text):
        return None
    return text


def compact_krw_amount(value: object) -> str | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    amount = float(value)
    if not math.isfinite(amount):
        return None
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    jo = int(amount // 1_000_000_000_000)
    eok = int(round((amount - jo * 1_000_000_000_000) / 100_000_000))
    if eok >= 10_000:
        jo += 1
        eok -= 10_000
    if jo and eok:
        return f"{sign}{jo}조{eok:,}억원"
    if jo:
        return f"{sign}{jo}조원"
    return f"{sign}{eok:,}억원"


def _fact_value(facts: Iterable[str], label: str) -> str | None:
    marker = label.lower()
    for fact in facts:
        if marker not in fact.lower():
            continue
        value = fact.split("=", 1)[-1].strip()
        return value or None
    return None


def _number(value: str | None) -> float | None:
    if not value or (match := _NUMBER.search(value)) is None:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def event_user_fields(event: Event) -> dict[str, object]:
    """Return verified, user-safe structured fields from a normalized event."""
    try:
        parsed = json.loads(event.confirmed_facts)
    except (TypeError, ValueError):
        return {}
    facts = [str(item) for item in parsed] if isinstance(parsed, list) else []
    contract_name = clean_user_text(
        _fact_value(facts, "supply contract fact: contract_name")
    )
    if contract_name is None:
        return {}
    fields: dict[str, object] = {"contract_name": contract_name}
    mappings = {
        "counterparty": "supply contract fact: counterparty",
        "contract_period": "supply contract fact: period",
        "region": "supply contract fact: region",
    }
    for key, label in mappings.items():
        if value := clean_user_text(_fact_value(facts, label)):
            fields[key] = value
    amount = _number(_fact_value(facts, "supply contract fact: amount"))
    if amount is not None:
        fields["contract_amount"] = amount
    ratio = _number(_fact_value(facts, "supply contract fact: recent_sales_ratio"))
    if ratio is not None:
        fields["sales_ratio_pct"] = ratio
    return fields


def canonical_event_fact(item: dict[str, object]) -> dict[str, object] | None:
    fingerprint = clean_user_text(item.get("event_fingerprint") or item.get("fingerprint"))
    title = clean_user_text(item.get("title") or item.get("contract_name"))
    if fingerprint is None or title is None:
        return None
    event_type = str(item.get("type") or item.get("event_type") or "event")
    fact_type = "contract_award" if item.get("contract_name") else event_type
    fields: dict[str, object] = {
        "title": title,
        "direction": str(item.get("direction") or "neutral"),
        "materiality": str(item.get("materiality") or "unknown"),
    }
    for key in (
        "contract_name",
        "contract_amount",
        "counterparty",
        "contract_period",
        "sales_ratio_pct",
        "region",
        "relevance_score",
    ):
        value = item.get(key)
        if isinstance(value, str):
            value = clean_user_text(value)
        if value is not None:
            fields[key] = (
                {"value": value, "currency": "KRW"}
                if key == "contract_amount"
                else value
            )
    return {
        "fact_id": f"event:{fingerprint}:{fact_type}",
        "fact_type": fact_type,
        "as_of_date": str(item.get("date") or item.get("event_date") or ""),
        "source_event_fingerprint": fingerprint,
        "fields": fields,
    }


def canonical_capital_action_fact(item: dict[str, object]) -> dict[str, object] | None:
    fingerprint = clean_user_text(item.get("event_fingerprint"))
    if fingerprint is None:
        return None
    fields: dict[str, object] = {}
    for key in (
        "transaction_shares",
        "share_denominator",
        "share_denominator_source",
        "share_ratio_pct",
        "transaction_amount",
        "market_cap",
        "market_cap_ratio_pct",
        "purpose",
        "level",
        "reason",
    ):
        value = item.get(key)
        if isinstance(value, str):
            value = clean_user_text(value)
        if value is not None:
            target = "materiality" if key == "level" else key
            fields[target] = (
                {"value": value, "currency": "KRW"}
                if key in {"transaction_amount", "market_cap"}
                else value
            )
    return {
        "fact_id": f"event:{fingerprint}:capital_allocation",
        "fact_type": "treasury_stock_transaction",
        "as_of_date": str(item.get("event_date") or ""),
        "source_event_fingerprint": fingerprint,
        "fields": fields,
    }
