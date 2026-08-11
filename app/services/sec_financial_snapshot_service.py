from datetime import date

import httpx
from sqlmodel import Session, select

from app.models.financial import FinancialSnapshot


_CONCEPTS = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"),
    "common_net_income": ("NetIncomeLossAvailableToCommonStockholdersBasic", "NetIncomeLoss"),
    "diluted_eps": ("EarningsPerShareDiluted",),
    "common_equity": ("StockholdersEquity",),
    "common_shares_outstanding": ("CommonStockSharesOutstanding",),
    "diluted_shares": ("WeightedAverageNumberOfDilutedSharesOutstanding",),
    "common_dividends": ("PaymentsOfDividendsCommonStock", "PaymentsOfDividends"),
    "buybacks": ("PaymentsForRepurchaseOfCommonStock",),
    "equity_issuance": ("ProceedsFromStockOptionsExercised", "ProceedsFromIssuanceOfCommonStock"),
    "other_comprehensive_income": ("OtherComprehensiveIncomeLossNetOfTax",),
}
_IFRS_CONCEPTS = {
    "revenue": ("Revenue",),
    "common_net_income": ("ProfitLossAttributableToOwnersOfParent", "ProfitLoss"),
    "diluted_eps": ("DilutedEarningsLossPerShare",),
    "common_equity": ("EquityAttributableToOwnersOfParent", "Equity"),
    "common_shares_outstanding": ("NumberOfSharesOutstanding",),
    "diluted_shares": ("WeightedAverageNumberOfSharesOutstandingDiluted",),
    "common_dividends": ("DividendsPaid",),
    "buybacks": ("PaymentsToAcquireOrRedeemEntitysShares",),
    "equity_issuance": ("ProceedsFromIssuingShares",),
    "other_comprehensive_income": ("OtherComprehensiveIncome",),
}
_UNITS = {
    "diluted_eps": ("USD/shares", "USD / shares"),
    "common_shares_outstanding": ("shares",),
    "diluted_shares": ("shares",),
}


def _parse_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _facts(payload: dict[str, object], field: str) -> list[dict[str, object]]:
    taxonomy = payload.get("facts", {})
    if not isinstance(taxonomy, dict):
        return []
    taxonomies = (("us-gaap", _CONCEPTS[field]), ("ifrs-full", _IFRS_CONCEPTS[field]))
    for taxonomy_name, concepts in taxonomies:
        taxonomy_facts = taxonomy.get(taxonomy_name, {})
        if not isinstance(taxonomy_facts, dict):
            continue
        for concept in concepts:
            raw = taxonomy_facts.get(concept)
            if not isinstance(raw, dict):
                continue
            units = raw.get("units", {})
            if not isinstance(units, dict):
                continue
            preferred = _UNITS.get(field, ("USD", "TWD", "CNY"))
            for unit in preferred:
                entries = units.get(unit)
                if isinstance(entries, list) and entries:
                    return [item for item in entries if isinstance(item, dict)]
            for entries in units.values():
                if isinstance(entries, list) and entries:
                    return [item for item in entries if isinstance(item, dict)]
    return []


def _duration_days(item: dict[str, object]) -> int:
    start = _parse_date(item.get("start"))
    end = _parse_date(item.get("end"))
    return (end - start).days if start and end else 9999


def _period_entries(payload: dict[str, object]) -> list[dict[str, object]]:
    candidates = [*_facts(payload, "diluted_eps"), *_facts(payload, "common_net_income"), *_facts(payload, "revenue")]
    periods: dict[tuple[int, str, date, date], dict[str, object]] = {}
    for item in candidates:
        fy = item.get("fy")
        fp = str(item.get("fp", ""))
        filed = _parse_date(item.get("filed"))
        end = _parse_date(item.get("end"))
        if not isinstance(fy, int) or fp not in {"Q1", "Q2", "Q3", "FY"} or not filed or not end:
            continue
        if str(item.get("form", "")) not in {"10-Q", "10-K", "20-F", "6-K"}:
            continue
        periods[(fy, fp, filed, end)] = item
    return list(periods.values())


def _select_value(
    entries: list[dict[str, object]],
    fy: int,
    fp: str,
    filed: date,
    end: date,
) -> float | None:
    candidates = [
        item for item in entries
        if item.get("fy") == fy
        and str(item.get("fp", "")) == fp
        and _parse_date(item.get("filed")) == filed
        and _parse_date(item.get("end")) == end
        and isinstance(item.get("val"), (int, float))
    ]
    if not candidates:
        return None
    selected = max(candidates, key=_duration_days) if fp == "FY" else min(candidates, key=_duration_days)
    if fp != "FY" and _duration_days(selected) > 130:
        return None
    return float(selected["val"])


def _select_instant_value(
    entries: list[dict[str, object]], filed: date, end: date
) -> float | None:
    candidates = [
        item for item in entries
        if _parse_date(item.get("end")) == end
        and (_parse_date(item.get("filed")) or date.max) <= filed
        and isinstance(item.get("val"), (int, float))
    ]
    if not candidates:
        return None
    selected = max(candidates, key=lambda item: _parse_date(item.get("filed")) or date.min)
    return float(selected["val"])


class SecFinancialSnapshotService:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.transport = transport
        self._ticker_ciks: dict[str, str] | None = None

    async def _resolve_cik(self, client: httpx.AsyncClient, ticker: str) -> str | None:
        if self._ticker_ciks is None:
            response = await client.get("https://www.sec.gov/files/company_tickers.json")
            response.raise_for_status()
            payload = response.json()
            self._ticker_ciks = {
                str(item.get("ticker", "")).upper(): str(item.get("cik_str", "")).zfill(10)
                for item in payload.values()
                if isinstance(item, dict) and item.get("ticker") and item.get("cik_str")
            } if isinstance(payload, dict) else {}
        return self._ticker_ciks.get(ticker.upper())

    async def refresh(
        self,
        session: Session,
        ticker: str,
        user_agent: str,
    ) -> int:
        headers = {"User-Agent": user_agent, "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=20.0, headers=headers, transport=self.transport) as client:
            cik = await self._resolve_cik(client, ticker)
            if not cik:
                return 0
            response = await client.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("facts"), dict):
            return 0
        facts = {field: _facts(payload, field) for field in _CONCEPTS}
        built: list[FinancialSnapshot] = []
        for period in _period_entries(payload):
            fy = int(period["fy"])
            fp = str(period["fp"])
            filed = _parse_date(period.get("filed"))
            end = _parse_date(period.get("end"))
            if filed is None or end is None:
                continue
            period_type = {"Q1": "Q1", "Q2": "H1", "Q3": "Q3", "FY": "FY"}[fp]
            row = FinancialSnapshot(
                ticker=ticker.upper(),
                period=f"{fy}-{fp}",
                period_type=period_type,
                fiscal_year=fy,
                period_scope="annual" if fp == "FY" else "single-quarter",
                is_cumulative=fp == "FY",
                financial_period_end=end,
                financials_as_of=end,
                filing_date=filed,
                reported_date=filed,
                source="SEC Company Facts",
                provider="sec_companyfacts",
                quality_warnings=(
                    "foreign issuer filing coverage is partial; ADR ratio and currency mapping required"
                    if str(period.get("form", "")) in {"20-F", "6-K"}
                    else None
                ),
            )
            for field in ("revenue", "common_net_income", "diluted_eps"):
                setattr(row, field, _select_value(facts[field], fy, fp, filed, end))
            row.owners_parent_net_income = row.common_net_income
            row.net_income = row.common_net_income
            row.eps = row.diluted_eps
            row.common_equity = _select_instant_value(facts["common_equity"], filed, end)
            row.owners_parent_equity = row.common_equity
            row.common_shares_outstanding = _select_instant_value(
                facts["common_shares_outstanding"], filed, end
            )
            row.diluted_shares = _select_value(facts["diluted_shares"], fy, fp, filed, end)
            if row.common_shares_outstanding is None:
                row.common_shares_outstanding = row.diluted_shares
            if fp == "FY":
                row.cumulative_revenue = row.revenue
                row.cumulative_net_income = row.common_net_income
                row.cumulative_diluted_eps = row.diluted_eps
                row.common_dividends = _select_value(facts["common_dividends"], fy, fp, filed, end)
                row.dividends = row.common_dividends
                row.buybacks = _select_value(facts["buybacks"], fy, fp, filed, end)
                row.equity_issuance = _select_value(facts["equity_issuance"], fy, fp, filed, end)
                row.other_comprehensive_income = _select_value(
                    facts["other_comprehensive_income"], fy, fp, filed, end
                )
            built.append(row)

        by_year: dict[int, list[FinancialSnapshot]] = {}
        for row in built:
            by_year.setdefault(row.fiscal_year or 0, []).append(row)
        for year_rows in by_year.values():
            annual = next((row for row in year_rows if row.period_type == "FY"), None)
            quarters = [row for row in year_rows if row.period_type != "FY"]
            if annual and len(quarters) == 3:
                for field, cumulative_field in (
                    ("revenue", "cumulative_revenue"),
                    ("common_net_income", "cumulative_net_income"),
                    ("diluted_eps", "cumulative_diluted_eps"),
                ):
                    annual_value = getattr(annual, cumulative_field)
                    quarter_values = [getattr(row, field) for row in quarters]
                    if annual_value is not None and all(value is not None for value in quarter_values):
                        setattr(annual, field, float(annual_value) - sum(float(value) for value in quarter_values))
                annual.owners_parent_net_income = annual.common_net_income
                annual.net_income = annual.common_net_income
                annual.eps = annual.diluted_eps
                annual.period_scope = "single-quarter"
                annual.is_cumulative = False
                annual.normalization_method = "FY minus Q1-Q3 standalone"

        updated = 0
        for row in built:
            existing = session.exec(
                select(FinancialSnapshot).where(
                    FinancialSnapshot.ticker == row.ticker,
                    FinancialSnapshot.provider == "sec_companyfacts",
                    FinancialSnapshot.filing_date == row.filing_date,
                    FinancialSnapshot.period_type == row.period_type,
                    FinancialSnapshot.fiscal_year == row.fiscal_year,
                )
            ).first()
            if existing is None:
                session.add(row)
            else:
                for field in row.model_fields:
                    if field not in {"id", "created_at"}:
                        setattr(existing, field, getattr(row, field))
                session.add(existing)
            updated += 1
        session.flush()
        return updated
