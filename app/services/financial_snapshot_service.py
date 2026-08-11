import json
from calendar import monthrange
from datetime import date
import re

from sqlmodel import Session, select

from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.services.financial_validation import normalize_standalone_quarter


def _json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _fact_line(
    facts: list[str],
    account_name: str,
    *,
    cumulative: bool = False,
    share: bool = False,
) -> str | None:
    kind = "share" if share else "financial cumulative" if cumulative else "financial"
    prefix = f"OpenDART {kind} fact: {account_name} ="
    return next((fact for fact in facts if fact.startswith(prefix)), None)


def _amount(fact: str | None) -> float | None:
    if fact is None:
        return None
    match = re.search(r"=\s*([-\d,]+(?:\.\d+)?)\s*(?:KRW|shares)", fact)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _named_amount(facts: list[str], name: str) -> float | None:
    prefix = f"OpenDART dividend fact: {name} ="
    fact = next((item for item in facts if item.startswith(prefix)), None)
    if fact is None:
        return None
    match = re.search(r"=\s*([-\d,]+(?:\.\d+)?)", fact)
    return float(match.group(1).replace(",", "")) if match else None


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


def _period_type(title: str, period: str, report_code: str | None = None) -> str:
    if report_code == "11011":
        return "FY"
    if report_code == "11012":
        return "H1"
    if report_code == "11014":
        return "Q3"
    if report_code == "11013":
        return "Q1"
    if "사업보고서" in title or re.search(r"제\s*\d+\s*기$", period):
        return "FY"
    if "반기보고서" in title or "반기" in period:
        return "H1"
    if "3분기" in title or "3분기" in period:
        return "Q3"
    if "1분기" in title or "1분기" in period:
        return "Q1"
    if "분기보고서" in title:
        return "Q"
    return "UNKNOWN"


def _fiscal_year(event: Event, period: str) -> int | None:
    match = re.search(r"(20\d{2})", f"{event.title} {period}")
    if match:
        return int(match.group(1))
    return event.date.year if event.date else None


def _prior_cumulative(
    session: Session,
    ticker: str,
    provider: str,
    fiscal_year: int | None,
    period_type: str,
) -> FinancialSnapshot | None:
    previous_type = {"H1": "Q1", "Q3": "H1", "FY": "Q3"}.get(period_type)
    if previous_type is None:
        return None
    query = select(FinancialSnapshot).where(
        FinancialSnapshot.ticker == ticker,
        FinancialSnapshot.provider == provider,
        FinancialSnapshot.period_type == previous_type,
    )
    if fiscal_year is not None:
        query = query.where(FinancialSnapshot.fiscal_year == fiscal_year)
    return session.exec(query.order_by(FinancialSnapshot.reported_date.desc())).first()


def _standalone_value(
    reported: float | None,
    cumulative: float | None,
    prior_cumulative: float | None,
    period_scope: str,
) -> tuple[float | None, str]:
    if period_scope == "single-quarter":
        return reported, "reported_single_quarter"
    if cumulative is not None:
        normalized = normalize_standalone_quarter(
            cumulative,
            prior_cumulative,
            period_scope,
        )
        if normalized.valid:
            return normalized.value, normalized.method
    if period_scope in {"half-year", "ytd"} and reported is not None:
        return reported, "reported_current_period"
    return None, "normalization_unavailable"


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
    query = select(FinancialSnapshot).where(
        FinancialSnapshot.ticker == snapshot.ticker,
        FinancialSnapshot.provider == snapshot.provider,
        FinancialSnapshot.reported_date < snapshot.reported_date,
    )
    if snapshot.period_type:
        query = query.where(FinancialSnapshot.period_type == snapshot.period_type)
    return session.exec(query.order_by(FinancialSnapshot.reported_date.desc())).first()


def _add_comparison(session: Session, event: Event, snapshot: FinancialSnapshot) -> None:
    implications = _json_list(event.inferred_implications)
    unknowns = _json_list(event.unknowns)
    previous = _previous(session, snapshot)
    comparable_label = snapshot.period_type or "same-period"
    if previous is None:
        _append(
            unknowns,
            f"Historical comparison unavailable: no prior comparable {comparable_label} snapshot for this ticker/provider.",
        )
    else:
        revenue_change = _pct(snapshot.revenue, previous.revenue)
        profit_change = _pct(snapshot.operating_income, previous.operating_income)
        if revenue_change is None:
            _append(unknowns, "Revenue comparison unavailable: missing current/prior revenue.")
        else:
            _append(
                implications,
                f"Revenue changed {revenue_change:+.1f}% vs prior comparable {previous.period_type or 'period'} snapshot {previous.period}.",
            )
        if profit_change is None:
            _append(unknowns, "Operating income comparison unavailable: missing current/prior operating income.")
        else:
            _append(
                implications,
                f"Operating income changed {profit_change:+.1f}% vs prior comparable {previous.period_type or 'period'} snapshot {previous.period}.",
            )
        if snapshot.operating_margin is None or previous.operating_margin is None:
            _append(unknowns, "Operating margin comparison unavailable: missing current/prior margin.")
        else:
            margin_delta = snapshot.operating_margin - previous.operating_margin
            _append(implications, f"Operating margin changed {margin_delta:+.1f}p vs prior comparable snapshot.")
        if snapshot.quality_warnings or previous.quality_warnings:
            _append(unknowns, "Financial comparison has quality warnings; verify basis consistency before using growth rates.")
    event.inferred_implications = json.dumps(implications)
    event.unknowns = json.dumps(unknowns)


def upsert_financial_snapshot_from_event(session: Session, event: Event) -> FinancialSnapshot | None:
    if event.provider != "opendart" or event.event_type not in {"guidance_change", "financial_report"}:
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
    owners_net_income_fact = _fact_line(facts, "지배주주순이익")
    basic_eps_fact = _fact_line(facts, "기본주당이익")
    diluted_eps_fact = _fact_line(facts, "희석주당이익")
    owners_equity_fact = _fact_line(facts, "지배주주지분")
    cumulative_revenue_fact = _fact_line(facts, "매출액", cumulative=True)
    cumulative_profit_fact = _fact_line(facts, "영업이익", cumulative=True)
    cumulative_net_income_fact = _fact_line(
        facts,
        "지배주주순이익",
        cumulative=True,
    )
    cumulative_basic_eps_fact = _fact_line(facts, "기본주당이익", cumulative=True)
    cumulative_diluted_eps_fact = _fact_line(facts, "희석주당이익", cumulative=True)
    issued_shares_fact = _fact_line(facts, "보통주발행주식수", share=True)
    treasury_shares_fact = _fact_line(facts, "자기주식수", share=True)
    outstanding_shares_fact = _fact_line(facts, "보통주유통주식수", share=True)
    revenue_basis = _basis(revenue_fact)
    profit_basis = _basis(profit_fact)
    balance_basis = _basis(assets_fact) or _basis(liabilities_fact) or _basis(equity_fact)
    period = (
        _basis_value(revenue_basis, "thstrm_nm")
        or _basis_value(profit_basis, "thstrm_nm")
        or event.title
    )
    report_code = _basis_value(revenue_basis, "report_code") or _basis_value(profit_basis, "report_code")
    period_scope = (
        _basis_value(revenue_basis, "period_scope")
        or _basis_value(profit_basis, "period_scope")
        or "cumulative"
    )
    period_type = _period_type(event.title, period, report_code)
    fiscal_year = _fiscal_year(event, period)
    snapshot_type = (
        "preliminary_earnings"
        if any(term in event.title for term in ("잠정실적", "잠정영업실적", "영업(잠정)실적"))
        else "full_statement"
    )

    snapshot = session.exec(
        select(FinancialSnapshot).where(
            FinancialSnapshot.ticker == event.ticker,
            FinancialSnapshot.reported_date == event.date,
            FinancialSnapshot.provider == event.provider,
        )
    ).first()
    if snapshot is None:
        snapshot = FinancialSnapshot(ticker=event.ticker, period=period)
        session.add(snapshot)

    reported_revenue = _amount(revenue_fact)
    reported_profit = _amount(profit_fact)
    reported_net_income = _amount(net_income_fact)
    reported_owners_net_income = _amount(owners_net_income_fact)
    cumulative_revenue = _amount(cumulative_revenue_fact)
    cumulative_profit = _amount(cumulative_profit_fact)
    cumulative_net_income = _amount(cumulative_net_income_fact)
    cumulative_basic_eps = _amount(cumulative_basic_eps_fact)
    cumulative_diluted_eps = _amount(cumulative_diluted_eps_fact)
    if period_type == "Q1":
        cumulative_revenue = cumulative_revenue or reported_revenue
        cumulative_profit = cumulative_profit or reported_profit
        cumulative_net_income = cumulative_net_income or reported_owners_net_income
        cumulative_basic_eps = cumulative_basic_eps or _amount(basic_eps_fact)
        cumulative_diluted_eps = cumulative_diluted_eps or _amount(diluted_eps_fact)
    elif period_type == "FY":
        cumulative_revenue = cumulative_revenue or reported_revenue
        cumulative_profit = cumulative_profit or reported_profit
        cumulative_net_income = cumulative_net_income or reported_owners_net_income
        cumulative_basic_eps = cumulative_basic_eps or _amount(basic_eps_fact)
        cumulative_diluted_eps = cumulative_diluted_eps or _amount(diluted_eps_fact)
    prior = _prior_cumulative(
        session,
        event.ticker,
        event.provider,
        fiscal_year,
        period_type,
    )
    revenue, revenue_method = _standalone_value(
        reported_revenue,
        cumulative_revenue,
        prior.cumulative_revenue if prior else None,
        period_scope,
    )
    profit, profit_method = _standalone_value(
        reported_profit,
        cumulative_profit,
        prior.cumulative_operating_income if prior else None,
        period_scope,
    )
    owners_net_income, net_income_method = _standalone_value(
        reported_owners_net_income,
        cumulative_net_income,
        prior.cumulative_net_income if prior else None,
        period_scope,
    )
    basic_eps, basic_eps_method = _standalone_value(
        _amount(basic_eps_fact),
        cumulative_basic_eps,
        prior.cumulative_basic_eps if prior else None,
        period_scope,
    )
    diluted_eps, diluted_eps_method = _standalone_value(
        _amount(diluted_eps_fact),
        cumulative_diluted_eps,
        prior.cumulative_diluted_eps if prior else None,
        period_scope,
    )
    liabilities = _amount(liabilities_fact)
    assets = _amount(assets_fact)
    equity = _amount(equity_fact)
    snapshot.period_type = period_type
    snapshot.snapshot_type = snapshot_type
    snapshot.source_event_date = event.date
    snapshot.fiscal_year = fiscal_year
    snapshot.period_scope = period_scope
    snapshot.is_cumulative = period_scope != "single-quarter"
    snapshot.normalization_method = ";".join(
        dict.fromkeys((revenue_method, profit_method, net_income_method, diluted_eps_method))
    )
    snapshot.financial_period_end = _financial_period_end(fiscal_year, period_type)
    snapshot.filing_date = event.date
    snapshot.financials_as_of = snapshot.financial_period_end
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
    snapshot.net_income = reported_net_income
    snapshot.owners_parent_net_income = owners_net_income
    snapshot.common_net_income = owners_net_income
    snapshot.basic_eps = basic_eps
    snapshot.diluted_eps = diluted_eps or basic_eps
    snapshot.eps = snapshot.diluted_eps
    snapshot.cumulative_revenue = cumulative_revenue
    snapshot.cumulative_operating_income = cumulative_profit
    snapshot.cumulative_net_income = cumulative_net_income
    snapshot.cumulative_basic_eps = cumulative_basic_eps
    snapshot.cumulative_diluted_eps = cumulative_diluted_eps
    snapshot.operating_margin = _margin(revenue, profit)
    if snapshot_type == "full_statement":
        snapshot.debt = liabilities
        snapshot.total_equity = equity
        snapshot.owners_parent_equity = _amount(owners_equity_fact)
        snapshot.common_equity = snapshot.owners_parent_equity
        snapshot.issued_common_shares = _amount(issued_shares_fact)
        snapshot.treasury_shares = _amount(treasury_shares_fact)
        snapshot.common_shares_outstanding = _amount(outstanding_shares_fact)
        snapshot.diluted_shares = snapshot.common_shares_outstanding
        snapshot.common_dividends = _named_amount(facts, "total_dividend")
        snapshot.dividends = snapshot.common_dividends
    snapshot.financial_statement_basis_warning = event.financial_statement_basis_warning
    snapshot.margin_quality_review = event.margin_quality_review
    snapshot.cash = None
    snapshot.guidance = event.title
    if assets is not None and liabilities is not None:
        snapshot.dilution_notes = f"liabilities/assets={liabilities / assets * 100:.1f}%"
    elif equity is not None and liabilities is not None:
        snapshot.dilution_notes = f"liabilities/equity={liabilities / equity * 100:.1f}%"
    if any(method == "normalization_unavailable" for method in (
        revenue_method, profit_method, net_income_method
    )):
        warning = "Standalone quarter normalization is incomplete."
        snapshot.quality_warnings = "; ".join(
            item for item in (snapshot.quality_warnings, warning) if item
        )
    _add_comparison(session, event, snapshot)
    return snapshot


def _financial_period_end(fiscal_year: int | None, period_type: str | None) -> date | None:
    if fiscal_year is None:
        return None
    month = {"Q1": 3, "H1": 6, "Q3": 9, "FY": 12}.get(period_type or "")
    if month is None:
        return None
    return date(fiscal_year, month, monthrange(fiscal_year, month)[1])
