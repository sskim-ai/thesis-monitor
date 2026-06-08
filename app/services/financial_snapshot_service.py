import json
import re

from sqlmodel import Session, select

from app.models.event import Event
from app.models.financial import FinancialSnapshot


def _facts(event: Event) -> list[str]:
    try:
        parsed = json.loads(event.confirmed_facts)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _unknowns(event: Event) -> list[str]:
    try:
        parsed = json.loads(event.unknowns)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _fact_line(facts: list[str], account_name: str) -> str | None:
    needle = f"OpenDART financial fact: {account_name} ="
    for fact in facts:
        if fact.startswith(needle):
            return fact
    return None


def _amount_from_fact(fact: str | None) -> float | None:
    if fact is None:
        return None
    match = re.search(r"=\s*([-\d,]+(?:\.\d+)?)\s*KRW", fact)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _basis_from_fact(fact: str | None) -> str | None:
    if fact is None:
        return None
    match = re.search(r"\((.*)\)\s*$", fact)
    return match.group(1) if match else None


def _basis_value(basis: str | None, key: str) -> str | None:
    if basis is None:
        return None
    match = re.search(rf"{re.escape(key)}=([^;)]*)", basis)
    return match.group(1).strip() if match else None


def _period_from_basis(facts: list[str], fallback: str) -> str:
    revenue_basis = _basis_from_fact(_fact_line(facts, "매출액"))
    period = _basis_value(revenue_basis, "thstrm_nm")
    return period or fallback


def _operating_margin(revenue: float | None, operating_income: float | None) -> float | None:
    if revenue in {None, 0} or operating_income is None:
        return None
    return operating_income / revenue * 100


def _pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in {None, 0}:
        return None
    return (current / previous - 1) * 100


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def upsert_financial_snapshot_from_event(session: Session, event: Event) -> FinancialSnapshot | None:
    if event.provider != "opendart" or event.event_type != "guidance_change":
        return None

    facts = _facts(event)
    revenue_fact = _fact_line(facts, "매출액")
    operating_income_fact = _fact_line(facts, "영업이익")
    if revenue_fact is None and operating_income_fact is None:
        return None

    assets_fact = _fact_line(facts, "자산총계")
    liabilities_fact = _fact_line(facts, "부채총계")
    equity_fact = _fact_line(facts, "자본총계")
    net_income_fact = _fact_line(facts, "당기순이익")

    revenue = _amount_from_fact(revenue_fact)
    operating_income = _amount_from_fact(operating_income_fact)
    assets = _amount_from_fact(assets_fact)
    liabilities = _amount_from_fact(liabilities_fact)
    equity = _amount_from_fact(equity_fact)
    period = _period_from_basis(facts, event.title)
    revenue_basis = _basis_from_fact(revenue_fact)
    operating_income_basis = _basis_from_fact(operating_income_fact)
    balance_sheet_basis = _basis_from_fact(assets_fact) or _basis_from_fact(liabilities_fact) or _basis_from_fact(equity_fact)

    snapshot = session.exec(
        select(FinancialSnapshot).where(
            FinancialSnapshot.ticker == event.ticker,
            FinancialSnapshot.period == period,
            FinancialSnapshot.provider == event.provider,
        )
    ).first()
    if snapshot is None:
        snapshot = FinancialSnapshot(ticker=event.ticker, period=period)
        session.add(snapshot)

    snapshot.reported_date = event.date
    snapshot.source = event.source
    snapshot.provider = event.provider
    snapshot.fs_div = _basis_value(revenue_basis, "fs_div") or _basis_value(operating_income_basis, "fs_div")
    snapshot.sj_div = _basis_value(revenue_basis, "sj_div") or _basis_value(operating_income_basis, "sj_div")
    snapshot.revenue_basis = revenue_basis
    snapshot.operating_income_basis = operating_income_basis
    snapshot.balance_sheet_basis = balance_sheet_basis
    snapshot.quality_warnings = "; ".join(item for item in _unknowns(event) if "quality warning" in item.lower()) or None
    snapshot.revenue = revenue
    snapshot.operating_income = operating_income
    snapshot.net_income = _amount_from_fact(net_income_fact)
    snapshot.operating_margin = _operating_margin(revenue, operating_income)
    snapshot.debt = liabilities
    snapshot.cash = None
    snapshot.guidance = event.title
    if assets is not None and liabilities is not None:
        snapshot.dilution_notes = f"liabilities/assets={liabilities / assets * 100:.1f}%"
    elif equity is not None and liabilities is not None:
        snapshot.dilution_notes = f"liabilities/equity={liabilities / equity * 100:.1f}%"
    return snapshot


def previous_financial_snapshot(session: Session, snapshot: FinancialSnapshot) -> FinancialSnapshot | None:
    if snapshot.reported_date is None:
        return None
    return session.exec(
        select(FinancialSnapshot)
        .where(
            FinancialSnapshot.ticker == snapshot.ticker,
            FinancialSnapshot.provider == snapshot.provider,
            FinancialSnapshot.reported_date < snapshot.reported_date,
        )
        .order_by(FinancialSnapshot.reported_date.desc())
    ).first()


def comparison_implications(
    current: FinancialSnapshot | None,
    previous: FinancialSnapshot | None,
) -> tuple[list[str], list[str]]:
    implications: list[str] = []
    unknowns: list[str] = []
    if current is None:
        return implications, ["Historical financial comparison unavailable because no current snapshot was stored."]
    if previous is None:
        return implications, ["Historical financial comparison unavailable because no prior snapshot exists for this ticker/provider yet."]

    revenue_change = _pct_change(current.revenue, previous.revenue)
    operating_income_change = _pct_change(current.operating_income, previous.operating_income)
    if revenue_change is not None:
        _append_unique(implications, f"Revenue changed {revenue_change:+.1f}% versus prior stored snapshot period {previous.period}.")
    else:
        _append_unique(unknowns, "Revenue comparison unavailable because current or prior revenue is missing/zero.")
    if operating_income_change is not None:
        _append_unique(implications, f"Operating income changed {operating_income_change:+.1f}% versus prior stored snapshot period {previous.period}.")
    else:
        _append_unique(unknowns, "Operating income comparison unavailable because current or prior operating income is missing/zero.")
    if current.operating_margin is not None and previous.operating_margin is not None:
        margin_delta = current.operating_margin - previous.operating_margin
        _append_unique(implications, f"Operating margin changed {margin_delta:+.1f} percentage points versus prior stored snapshot.")
    else:
        _append_unique(unknowns, "Operating margin comparison unavailable because current or prior margin is missing.")
    if current.quality_warnings or previous.quality_warnings:
        _append_unique(unknowns, "Financial comparison has quality warnings; verify basis consistency before treating growth rates as thesis evidence.")
    return implications, unknowns


def add_financial_comparison_to_event(
    session: Session,
    event: Event,
    snapshot: FinancialSnapshot | None,
) -> None:
    if event.provider != "opendart" or event.event_type != "guidance_change":
        return
    current_implications = json.loads(event.inferred_implications)
    current_unknowns = json.loads(event.unknowns)
    previous = previous_financial_snapshot(session, snapshot) if snapshot else None
    implications, unknowns = comparison_implications(snapshot, previous)
    for item in implications:
        _append_unique(current_implications, item)
    for item in unknowns:
        _append_unique(current_unknowns, item)
    event.inferred_implications = json.dumps(current_implications)
    event.unknowns = json.dumps(current_unknowns)
