from datetime import date, timedelta

import httpx

from app.config import get_settings
from app.providers.base import FilingProvider, RawEvent


OPENDART_CORP_CODES = {
    # TODO: Replace this seed map with cached corp_code.xml lookup from OpenDART.
    "000660": "00164779",
    "000660.KS": "00164779",
}

SEC_TICKER_CIK = {
    # TODO: Replace this seed map with SEC company_tickers.json lookup/cache.
    "NVDA": "0001045810",
    "AMD": "0000002488",
}


def _yyyymmdd(value: date) -> str:
    return value.strftime("%Y%m%d")


def _filing_unknowns() -> list[str]:
    return [
        "Customer names are unknown unless explicitly disclosed in the filing title or body",
        "Order size is unknown unless disclosed in the filing",
        "Revenue impact is unknown",
        "Margin impact is unknown",
        "FCF impact is unknown",
    ]


def _dart_keywords(title: str) -> list[str]:
    title_lower = title.lower()
    keywords = ["opendart", "filing"]
    keyword_map = {
        "유상증자": "capital_raise",
        "전환사채": "convertible_bond",
        "cb": "convertible_bond",
        "신주인수권": "warrant",
        "bw": "warrant",
        "실적": "earnings",
        "영업(잠정)실적": "earnings",
        "공급계약": "supply_contract",
        "단일판매": "supply_contract",
        "자사주": "buyback",
        "투자판단": "material_management_matter",
        "주요경영사항": "material_management_matter",
    }
    for needle, keyword in keyword_map.items():
        if needle.lower() in title_lower:
            keywords.append(keyword)
    return keywords


class OpenDARTProvider(FilingProvider):
    name = "opendart"
    endpoint = "https://opendart.fss.or.kr/api/list.json"

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        settings = get_settings()
        if not settings.opendart_api_key:
            return []

        corp_code = OPENDART_CORP_CODES.get(ticker.upper()) or OPENDART_CORP_CODES.get(
            ticker.replace(".KS", "")
        )
        if not corp_code:
            return []

        params = {
            "crtfc_key": settings.opendart_api_key,
            "corp_code": corp_code,
            "bgn_de": _yyyymmdd(date.today() - timedelta(days=lookback_days)),
            "page_count": 20,
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(self.endpoint, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            return []

        if payload.get("status") not in {None, "000"}:
            return []

        events: list[RawEvent] = []
        for item in payload.get("list", []):
            title = item.get("report_nm") or "OpenDART filing"
            receipt_no = item.get("rcept_no") or ""
            filing_date = item.get("rcept_dt") or ""
            try:
                published = date.fromisoformat(
                    f"{filing_date[:4]}-{filing_date[4:6]}-{filing_date[6:8]}"
                )
            except ValueError:
                published = date.today()
            events.append(
                RawEvent(
                    ticker=ticker.upper(),
                    company_name=item.get("corp_name"),
                    date=published,
                    source="OpenDART",
                    provider=self.name,
                    title=title,
                    url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}",
                    summary=title,
                    keywords=_dart_keywords(title),
                    confirmed_facts=[
                        f"OpenDART filing title: {title}",
                        f"OpenDART receipt number: {receipt_no}",
                    ],
                    inferred_implications=[],
                    unknowns=_filing_unknowns(),
                )
            )
        return events


class SecEdgarProvider(FilingProvider):
    name = "sec_edgar"
    endpoint_template = "https://data.sec.gov/submissions/CIK{cik}.json"

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        settings = get_settings()
        if not settings.sec_user_agent:
            return []
        cik = SEC_TICKER_CIK.get(ticker.upper())
        if not cik:
            return []

        headers = {"User-Agent": settings.sec_user_agent, "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                response = await client.get(self.endpoint_template.format(cik=cik))
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            return []

        recent = payload.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_documents = recent.get("primaryDocument", [])
        company_name = payload.get("name")
        cutoff = date.today() - timedelta(days=lookback_days)

        events: list[RawEvent] = []
        for form, filing_date, accession, primary_doc in zip(
            forms, filing_dates, accession_numbers, primary_documents, strict=False
        ):
            if form not in {"8-K", "10-Q", "10-K"}:
                continue
            try:
                published = date.fromisoformat(filing_date)
            except ValueError:
                published = date.today()
            if published < cutoff:
                continue
            accession_path = accession.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}/{primary_doc}"
            title = f"{company_name or ticker.upper()} filed {form}"
            events.append(
                RawEvent(
                    ticker=ticker.upper(),
                    company_name=company_name,
                    date=published,
                    source="SEC EDGAR",
                    provider=self.name,
                    title=title,
                    url=url,
                    summary=title,
                    keywords=["sec_edgar", form.lower(), "filing"],
                    confirmed_facts=[
                        f"SEC EDGAR recent filing form: {form}",
                        f"SEC accession number: {accession}",
                    ],
                    inferred_implications=[],
                    unknowns=_filing_unknowns(),
                )
            )
        return events
