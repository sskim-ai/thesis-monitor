import json
import re
from sqlmodel import Session, select

from app.models.event import Event
from app.models.financial import CapitalReturnHistory, DividendHistory, FinancialSnapshot


def _json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _fact_number(facts: list[str], name: str) -> float | None:
    prefix = f"OpenDART dividend fact: {name} ="
    fact = next((item for item in facts if item.startswith(prefix)), None)
    if fact is None:
        return None
    match = re.search(r"=\s*([-\d,]+(?:\.\d+)?)", fact)
    return float(match.group(1).replace(",", "")) if match else None


def _filing_id(facts: list[str]) -> str | None:
    for fact in facts:
        if "receipt number:" in fact.lower() or "accession number:" in fact.lower():
            return fact.split(":", 1)[-1].strip()
    return None


class DividendHistoryService:
    def ingest_event(self, session: Session, event: Event) -> DividendHistory | None:
        if "배당" not in event.title and event.event_type != "capital_allocation":
            return None
        facts = _json_list(event.confirmed_facts)
        dps = _fact_number(facts, "dps")
        total = _fact_number(facts, "total_dividend")
        payout = _fact_number(facts, "payout_ratio")
        filing_id = _filing_id(facts) or event.url
        record = session.exec(
            select(DividendHistory).where(
                DividendHistory.ticker == event.ticker,
                DividendHistory.source_filing_id == filing_id,
            )
        ).first()
        if record is None:
            record = DividendHistory(
                ticker=event.ticker,
                fiscal_year=event.date.year,
                record_date=event.date,
                source=event.source,
                provider=event.provider,
                source_filing_id=filing_id,
            )
        record.dividend_per_share = dps
        record.total_dividend = total
        record.payout_ratio = payout / 100 if payout is not None and payout > 1 else payout
        record.quality = "fresh" if any(value is not None for value in (dps, total, payout)) else "partial"
        session.add(record)
        return record

    def sync_financial_snapshots(
        self, session: Session, ticker: str, rows: list[FinancialSnapshot]
    ) -> list[DividendHistory]:
        for row in rows:
            total = row.common_dividends if row.common_dividends is not None else row.dividends
            if row.period_type != "FY" or total is None:
                continue
            filing_id = f"financial:{row.provider}:{row.id or row.period}"
            record = session.exec(
                select(DividendHistory).where(
                    DividendHistory.ticker == ticker,
                    DividendHistory.source_filing_id == filing_id,
                )
            ).first()
            if record is None:
                record = DividendHistory(
                    ticker=ticker,
                    fiscal_year=row.fiscal_year,
                    record_date=row.filing_date or row.reported_date,
                    source=row.source or "financial statement",
                    provider=row.provider or "unknown",
                    source_filing_id=filing_id,
                )
            record.total_dividend = float(total)
            income = row.common_net_income or row.owners_parent_net_income
            record.payout_ratio = float(total) / float(income) if income and income > 0 else None
            record.quality = "fresh" if row.filing_date else "partial"
            session.add(record)
        session.flush()
        return list(
            session.exec(
                select(DividendHistory)
                .where(DividendHistory.ticker == ticker)
                .order_by(DividendHistory.fiscal_year)
            ).all()
        )

    def sync_capital_returns(
        self, session: Session, ticker: str, rows: list[FinancialSnapshot]
    ) -> list[CapitalReturnHistory]:
        for row in rows:
            if row.period_type != "FY" or row.buybacks is None:
                continue
            filing_id = f"financial:{row.provider}:{row.id or row.period}"
            record = session.exec(
                select(CapitalReturnHistory).where(
                    CapitalReturnHistory.ticker == ticker,
                    CapitalReturnHistory.source_filing_id == filing_id,
                    CapitalReturnHistory.return_type == "buyback",
                )
            ).first()
            if record is None:
                record = CapitalReturnHistory(
                    ticker=ticker,
                    period_end=row.financial_period_end or row.financials_as_of,
                    return_type="buyback",
                    source=row.source or "financial statement",
                    provider=row.provider or "unknown",
                    source_filing_id=filing_id,
                )
            record.actual_amount = float(row.buybacks)
            record.quality = "fresh" if row.filing_date else "partial"
            session.add(record)
        session.flush()
        return list(
            session.exec(
                select(CapitalReturnHistory)
                .where(CapitalReturnHistory.ticker == ticker)
                .order_by(CapitalReturnHistory.period_end)
            ).all()
        )
