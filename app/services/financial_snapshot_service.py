import json
import re

from sqlmodel import Session, select

from app.models.event import Event
from app.models.financial import FinancialSnapshot


def _json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _fact_line(facts: list[str], account_name: str) -> str | None:
    prefix = f"OpenDART financial fact: {account_name} ="
    return next((fact for fact in facts if fact.startswith(prefix)), None)


def _amount(fact: str | None) -> float | None:
    if fact is None:
        return None
    match = re.search(r"=\s*([-\d,]+(?:\.\d+)?)\s*KRW", fact)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _basis(fact: str | None) -> str | None:
    if fact is None:
        return None
    match = re.search(r"\((.*)\)\s*$", fact)
    return match.group(1) if match else None


def _basis_value(basis: str | None, key: str) -> str | None:
    if basis is None:
        return None
    match = re.search(rf"{re.escape(key)}=([^;)]*)", basis)
    return match.group(1).strip() if match else None


def _margin(revenue: float | None, profit: float | None) -> float | None:
    if revenue in {None, 0} or profit is None:
        return None
    return profit / revenue * 100


def _pct(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in {None, 0}:
        return None
    return (current / previous - 1) * 100


def _append(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _previous(session: Session, snapshot: FinancialSnapshot) -> FinancialSnapshot | None:
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


def _add_comparison(session: Session, event: Event, snapshot: FinancialSnapshot) -> None:
    implications = _json_list(event.inferred_implications)
    unknowns = _json_list(event.unknowns)
    previous = _previous(session, snapshot)
    if previous is None:
        _append(unknowns, "Historical comparison unavailable: no prior stored snapshot for this ticker/provider.")
    else:
        revenue_change = _pct(snapshot.revenue, previous.revenue)
        profit_change = _pct(snapshot.operating_income, previous.operating_income)
        if revenue_change is None:
            _append(unknowns, "Revenue comparison unavailable: missing current/prior revenue.")
        else:
            _append(implications, f"Revenue changed {revenue_change:+.1f}% vs prior stored period {previous.period}.")
        if profit_change is None:
            _append(unknowns, "Operating income comparison unavailable: missing current/prior operating income.")
        else:
            _append(implications, f"Operating income changed {profit_change:+.1f}% vs prior stored period {previous.period}.")
        if snapshot.operating_margin is None or previous.operating_margin is None:
            _append(unknowns, "Operating margin comparison unavailable: missing current/prior margin.")
        else:
            margin_delta = snapshot.operating_margin - previous.operating_margin
            _append(implications, f"Operating margin changed {margin_delta:+.1f}p vs prior stored period.")
        if snapshot.quality_warnings or previous.quality_warnings:
            _append(unknowns, "Financial comparison has quality warnings; verify basis consistency before using growth rates.")
    event.inferred_implications = json.dumps(implications)
    event.unknowns = json.dumps(unknowns)


def upsert_financial_snapshot_from_event(session: Session, event: Event) -> FinancialSnapshot | None:
    if event.provider != "opendart" or event.event_type != "guidance_change":
        return None

    facts = _json_list(event.confirmed_facts)
    revenue_fact = _fact_line(facts, "매출액")
    profit_fact = _fact_line(facts, "영업이익")
    if revenue_fact is None and profit_fact is None:
        return None

    assets_fact = _fact_line(facts, "자산총계")
    liabilities_fact = _fact_line(facts, "부채총계")
    equity_fact = _fact_line(facts, "자본총계")
    net_income_fact = _fact_line(facts, "당기순이익")
    revenue_basis = _basis(revenue_fact)
    profit_basis = _basis(profit_fact)
    balance_basis = _basis(assets_fact) or _basis(liabilities_fact) or _basis(equity_fact)
    period = _basis_value(revenue_basis, "thstrm_nm") or event.title

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

    revenue = _amount(revenue_fact)
    profit = _amount(profit_fact)
    liabilities = _amount(liabilities_fact)
    assets = _amount(assets_fact)
    equity = _amount(equity_fact)
    snapshot.reported_date = event.date
    snapshot.source = event.source
    snapshot.provider = event.provider
    snapshot.fs_div = _basis_value(revenue_basis, "fs_div") or _basis_value(profit_basis, "fs_div")
    snapshot.sj_div = _basis_value(revenue_basis, "sj_div") or _basis_value(profit_basis, "sj_div")
    snapshot.revenue_basis = revenue_basis
    snapshot.operating_income_basis = profit_basis
    snapshot.balance_sheet_basis = balance_basis
    snapshot.quality_warnings = "; ".join(item for item in _json_list(event.unknowns) if "quality warning" in item.lower()) or None
    snapshot.revenue = revenue
    snapshot.operating_income = profit
    snapshot.net_income = _amount(net_income_fact)
    snapshot.operating_margin = _margin(revenue, profit)
    snapshot.debt = liabilities
    snapshot.cash = None
    snapshot.guidance = event.title
    if assets is not None and liabilities is not None:
        snapshot.dilution_notes = f"liabilities/assets={liabilities / assets * 100:.1f}%"
    elif equity is not None and liabilities is not None:
        snapshot.dilution_notes = f"liabilities/equity={liabilities / equity * 100:.1f}%"
    _add_comparison(session, event, snapshot)
    return snapshot
