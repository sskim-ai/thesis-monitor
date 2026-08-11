from dataclasses import dataclass, field
from datetime import date, timedelta
import json

import httpx
from sqlmodel import Session

from app.config import get_settings
from app.models.event import Event
from app.providers.filings import OpenDARTProvider, _resolve_opendart_company, _yyyymmdd
from app.services.financial_snapshot_service import upsert_financial_snapshot_from_event

FINANCIAL_REPORT_KEYWORDS = ("분기보고서", "반기보고서", "사업보고서")


@dataclass
class FinancialBackfillResult:
    ticker: str
    provider: str
    years: int
    scanned_count: int = 0
    report_count: int = 0
    backfilled_count: int = 0
    skipped_count: int = 0
    periods: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _is_financial_report(title: str) -> bool:
    return any(keyword in title for keyword in FINANCIAL_REPORT_KEYWORDS)


def _published_date(value: str) -> date:
    try:
        return date.fromisoformat(f"{value[:4]}-{value[4:6]}-{value[6:8]}")
    except ValueError:
        return date.today()


def _event_from_facts(
    *,
    ticker: str,
    company_name: str | None,
    title: str,
    receipt_no: str,
    published: date,
    facts: list[str],
    unknowns: list[str],
) -> Event:
    confirmed_facts = [
        f"OpenDART filing title: {title}",
        f"OpenDART receipt number: {receipt_no}",
        *facts,
    ]
    return Event(
        ticker=ticker.upper(),
        company_name=company_name,
        date=published,
        source="OpenDART",
        provider="opendart",
        title=title,
        url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}",
        raw_summary="; ".join(confirmed_facts),
        event_type="guidance_change",
        keywords=json.dumps(["opendart", "filing", "earnings"]),
        confirmed_facts=json.dumps(confirmed_facts),
        inferred_implications="[]",
        unknowns=json.dumps(unknowns),
        requires_review=True,
        relevance_score=40,
        relevance_reason="financial report backfill snapshot",
    )


async def backfill_financial_snapshots(
    session: Session,
    ticker: str,
    years: int = 5,
    provider: str = "opendart",
) -> FinancialBackfillResult:
    result = FinancialBackfillResult(ticker=ticker.upper(), provider=provider, years=years)
    if provider != "opendart":
        result.warnings.append("Only opendart backfill is currently supported.")
        return result

    settings = get_settings()
    if not settings.opendart_api_key:
        result.warnings.append("OPENDART_API_KEY is not configured.")
        return result

    company = await _resolve_opendart_company(settings.opendart_api_key, ticker)
    if company is None:
        result.warnings.append("Unable to resolve OpenDART company code.")
        return result

    output_ticker = (company.stock_code or ticker).upper()
    provider_instance = OpenDARTProvider()
    start_date = date.today() - timedelta(days=years * 366)
    params = {
        "crtfc_key": settings.opendart_api_key,
        "corp_code": company.corp_code,
        "bgn_de": _yyyymmdd(start_date),
        "end_de": _yyyymmdd(date.today()),
        "page_count": 100,
        "page_no": 1,
    }

    report_rows: list[dict[str, str]] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            response = await client.get(provider_instance.endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") not in {None, "000"}:
                result.warnings.append(f"OpenDART list API status: {payload.get('status')}")
                break

            rows = payload.get("list", [])
            if not rows:
                break
            result.scanned_count += len(rows)

            for item in rows:
                title = item.get("report_nm") or "OpenDART filing"
                if not _is_financial_report(title):
                    continue
                result.report_count += 1
                report_rows.append(item)

            total_page = int(payload.get("total_page") or params["page_no"])
            if params["page_no"] >= total_page:
                break
            params["page_no"] += 1

        for item in sorted(report_rows, key=lambda row: row.get("rcept_dt") or ""):
            title = item.get("report_nm") or "OpenDART filing"
            receipt_no = item.get("rcept_no") or ""
            published = _published_date(item.get("rcept_dt") or "")
            facts, unknowns = await provider_instance._fetch_financial_facts(
                client=client,
                api_key=settings.opendart_api_key,
                corp_code=company.corp_code,
                title=title,
                published=published,
            )
            share_facts, share_unknowns = await provider_instance._fetch_share_status_facts(
                client=client,
                api_key=settings.opendart_api_key,
                corp_code=company.corp_code,
                title=title,
                published=published,
            )
            facts.extend(share_facts)
            unknowns.extend(share_unknowns)
            if not facts:
                result.skipped_count += 1
                result.warnings.extend(unknowns)
                continue

            event = _event_from_facts(
                ticker=output_ticker,
                company_name=item.get("corp_name") or company.corp_name,
                title=title,
                receipt_no=receipt_no,
                published=published,
                facts=facts,
                unknowns=unknowns,
            )
            snapshot = upsert_financial_snapshot_from_event(session, event)
            if snapshot is None:
                result.skipped_count += 1
                continue
            result.backfilled_count += 1
            if snapshot.period not in result.periods:
                result.periods.append(snapshot.period)

    session.commit()
    return result
