import json
import re
from dataclasses import asdict, dataclass

from sqlmodel import Session, select

from app.config import get_settings
from app.models.event import Event
from app.models.financial import FinancialSnapshot


_EMPLOYEE_OR_ADMIN_PURPOSES = (
    "employee",
    "compensation",
    "incentive",
    "임직원",
    "직원",
    "보상",
    "성과급",
    "우리사주",
)


@dataclass(frozen=True)
class CapitalActionMateriality:
    level: str
    transaction_shares: float | None
    share_denominator: float | None
    share_denominator_source: str | None
    share_ratio_pct: float | None
    transaction_amount: float | None
    market_cap: float | None
    market_cap_ratio_pct: float | None
    purpose: str | None
    reason: str

    def audit_dict(self) -> dict[str, object]:
        return asdict(self)


def _facts(event: Event) -> list[str]:
    try:
        parsed = json.loads(event.confirmed_facts)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _fact_value(facts: list[str], label: str) -> str | None:
    for fact in facts:
        if label not in fact.lower():
            continue
        value = fact.split("=", 1)[-1].strip()
        return value or None
    return None


def _number(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", value)
    if match is None:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def _latest_full_snapshot(session: Session, ticker: str) -> FinancialSnapshot | None:
    return session.exec(
        select(FinancialSnapshot)
        .where(
            FinancialSnapshot.ticker == ticker,
            FinancialSnapshot.snapshot_type == "full_statement",
        )
        .order_by(
            FinancialSnapshot.filing_date.desc(),
            FinancialSnapshot.financial_period_end.desc(),
            FinancialSnapshot.id.desc(),
        )
    ).first()


def treasury_stock_materiality(
    session: Session,
    event: Event,
    current_price: float | None,
) -> CapitalActionMateriality | None:
    facts = _facts(event)
    transaction_shares = _number(_fact_value(facts, "treasury stock fact: shares"))
    transaction_amount = _number(_fact_value(facts, "treasury stock fact: amount"))
    purpose = _fact_value(facts, "treasury stock fact: purpose")
    if event.event_type != "capital_allocation" or not any(
        "treasury stock fact:" in fact.lower() for fact in facts
    ):
        return None

    snapshot = _latest_full_snapshot(session, event.ticker)
    denominator = None
    denominator_source = None
    if snapshot is not None and snapshot.common_shares_outstanding:
        denominator = float(snapshot.common_shares_outstanding)
        denominator_source = "common_shares_outstanding"
    elif snapshot is not None and snapshot.issued_common_shares:
        denominator = float(snapshot.issued_common_shares)
        denominator_source = "issued_common_shares_fallback"

    share_ratio = (
        transaction_shares / denominator * 100
        if transaction_shares is not None and denominator and denominator > 0
        else None
    )
    market_cap = (
        float(current_price) * denominator
        if current_price is not None and current_price > 0 and denominator and denominator > 0
        else None
    )
    market_cap_ratio = (
        transaction_amount / market_cap * 100
        if transaction_amount is not None and market_cap and market_cap > 0
        else None
    )
    settings = get_settings()
    ratios = [ratio for ratio in (share_ratio, market_cap_ratio) if ratio is not None]
    material = (
        share_ratio is not None
        and share_ratio >= settings.capital_action_material_share_pct
    ) or (
        market_cap_ratio is not None
        and market_cap_ratio >= settings.capital_action_material_market_cap_pct
    )
    review = (
        share_ratio is not None
        and share_ratio >= settings.capital_action_review_share_pct
    ) or (
        market_cap_ratio is not None
        and market_cap_ratio >= settings.capital_action_review_market_cap_pct
    )
    administrative = bool(purpose) and any(
        marker in purpose.lower() for marker in _EMPLOYEE_OR_ADMIN_PURPOSES
    )
    if material:
        level = "material"
        reason = "transaction exceeds a material capital-action threshold"
    elif review:
        level = "review"
        reason = "transaction exceeds a review capital-action threshold"
    elif ratios and administrative:
        level = "immaterial"
        reason = "small employee or administrative treasury-stock transaction"
    elif ratios:
        level = "review"
        reason = "small transaction without a clearly administrative purpose"
    else:
        level = "unknown"
        reason = "share-count or market-cap denominator is unavailable"
    return CapitalActionMateriality(
        level=level,
        transaction_shares=transaction_shares,
        share_denominator=denominator,
        share_denominator_source=denominator_source,
        share_ratio_pct=round(share_ratio, 4) if share_ratio is not None else None,
        transaction_amount=transaction_amount,
        market_cap=market_cap,
        market_cap_ratio_pct=(
            round(market_cap_ratio, 4) if market_cap_ratio is not None else None
        ),
        purpose=purpose,
        reason=reason,
    )
