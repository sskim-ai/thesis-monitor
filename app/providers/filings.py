from datetime import date, timedelta
import re

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

REPORT_CODE_BY_TITLE = {
    "1분기보고서": "11013",
    "분기보고서": "11013",
    "반기보고서": "11012",
    "3분기보고서": "11014",
    "사업보고서": "11011",
}

FINANCIAL_ACCOUNT_ALIASES = {
    "revenue": ("매출액", "수익(매출액)", "영업수익"),
    "operating_income": ("영업이익",),
    "net_income": ("당기순이익", "분기순이익", "반기순이익"),
    "assets": ("자산총계",),
    "liabilities": ("부채총계",),
    "equity": ("자본총계",),
}


def _yyyymmdd(value: date) -> str:
    return value.strftime("%Y%m%d")


def _clean_number(value: str | None) -> str | None:
    if not value or value in {"-", ""}:
        return None
    return value.replace(",", "").strip()


def _format_krw(value: str | None) -> str | None:
    cleaned = _clean_number(value)
    if cleaned is None:
        return None
    try:
        amount = int(cleaned)
    except ValueError:
        return cleaned
    return f"{amount:,} KRW"


def _format_shares(value: str | None) -> str | None:
    cleaned = _clean_number(value)
    if cleaned is None:
        return None
    try:
        amount = int(cleaned)
    except ValueError:
        return cleaned
    return f"{amount:,} shares"


def _filing_unknowns(extra: list[str] | None = None) -> list[str]:
    unknowns = [
        "Customer names are unknown unless explicitly disclosed in the filing title or body",
        "Order size is unknown unless disclosed in the filing",
        "Revenue impact is unknown unless parsed from financial statement API",
        "Margin impact is unknown unless parsed from financial statement API",
        "FCF impact is unknown",
    ]
    if extra:
        unknowns.extend(extra)
    return unknowns


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
        "분기보고서": "earnings",
        "반기보고서": "earnings",
        "사업보고서": "earnings",
        "공급계약": "supply_contract",
        "단일판매": "supply_contract",
        "자기주식": "treasury_stock",
        "자사주": "treasury_stock",
        "투자판단": "material_management_matter",
        "주요경영사항": "material_management_matter",
    }
    for needle, keyword in keyword_map.items():
        if needle.lower() in title_lower:
            keywords.append(keyword)
    return keywords


def _report_code_from_title(title: str) -> str | None:
    for needle, code in REPORT_CODE_BY_TITLE.items():
        if needle in title:
            if needle == "분기보고서" and "3분기" in title:
                return "11014"
            return code
    return None


def _business_year_from_title_or_date(title: str, published: date) -> str:
    match = re.search(r"(20\d{2})", title)
    if match:
        return match.group(1)
    return str(published.year)


def _extract_financial_facts(items: list[dict[str, str]]) -> list[str]:
    facts: list[str] = []
    captured: set[str] = set()
    for item in items:
        account_name = item.get("account_nm", "")
        statement_name = item.get("sj_nm", "")
        amount = _format_krw(item.get("thstrm_amount"))
        if amount is None:
            continue
        for key, aliases in FINANCIAL_ACCOUNT_ALIASES.items():
            if key in captured:
                continue
            if account_name in aliases:
                facts.append(f"OpenDART financial fact: {account_name} = {amount} ({statement_name})")
                captured.add(key)
                break
    return facts


def _first_non_empty(item: dict[str, str], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = item.get(key)
        if value not in {None, "", "-"}:
            return value
    return None


def _extract_treasury_stock_facts(items: list[dict[str, str]]) -> list[str]:
    facts: list[str] = []
    if not items:
        return facts
    item = items[0]
    stock_count = _first_non_empty(item, ("trstk_qy", "acqsdl_stk_qy", "dppln_stk_qy", "stk_qy"))
    amount = _first_non_empty(item, ("tr_prc", "acqsdl_prc", "dppln_prc", "amount"))
    purpose = _first_non_empty(item, ("tr_pp", "acqsdl_pp", "dppln_pp", "prps"))
    start_date = _first_non_empty(item, ("tr_pd_bgd", "acqsdl_pd_bgd", "dppln_pd_bgd"))
    end_date = _first_non_empty(item, ("tr_pd_edd", "acqsdl_pd_edd", "dppln_pd_edd"))
    method = _first_non_empty(item, ("tr_mth", "acqsdl_mth", "dppln_mth", "mth"))

    formatted_count = _format_shares(stock_count)
    formatted_amount = _format_krw(amount)
    if formatted_count:
        facts.append(f"OpenDART treasury stock fact: shares = {formatted_count}")
    if formatted_amount:
        facts.append(f"OpenDART treasury stock fact: amount = {formatted_amount}")
    if purpose:
        facts.append(f"OpenDART treasury stock fact: purpose = {purpose}")
    if start_date or end_date:
        facts.append(f"OpenDART treasury stock fact: period = {start_date or 'unknown'} to {end_date or 'unknown'}")
    if method:
        facts.append(f"OpenDART treasury stock fact: method = {method}")
    return facts


class OpenDARTProvider(FilingProvider):
    name = "opendart"
    endpoint = "https://opendart.fss.or.kr/api/list.json"
    financial_endpoint = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
    treasury_stock_endpoint = "https://opendart.fss.or.kr/api/tsstkDpDecsn.json"

    async def _fetch_financial_facts(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        corp_code: str,
        title: str,
        published: date,
    ) -> tuple[list[str], list[str]]:
        report_code = _report_code_from_title(title)
        if report_code is None:
            return [], []
        params = {
            "crtfc_key": api_key,
            "corp_code": corp_code,
            "bsns_year": _business_year_from_title_or_date(title, published),
            "reprt_code": report_code,
        }
        try:
            response = await client.get(self.financial_endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return [], ["OpenDART financial statement API request failed"]
        if payload.get("status") != "000":
            return [], [f"OpenDART financial statement API status: {payload.get('status')}"]
        facts = _extract_financial_facts(payload.get("list", []))
        if not facts:
            return [], ["OpenDART financial statement API returned no mapped financial facts"]
        return facts, []

    async def _fetch_treasury_stock_facts(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        corp_code: str,
        title: str,
    ) -> tuple[list[str], list[str]]:
        if "자기주식" not in title:
            return [], []
        params = {"crtfc_key": api_key, "corp_code": corp_code}
        try:
            response = await client.get(self.treasury_stock_endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return [], ["OpenDART treasury stock API request failed"]
        if payload.get("status") != "000":
            return [], [f"OpenDART treasury stock API status: {payload.get('status')}"]
        facts = _extract_treasury_stock_facts(payload.get("list", []))
        if not facts:
            return [], ["OpenDART treasury stock API returned no mapped facts"]
        return facts, []

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

                    extra_facts: list[str] = []
                    extra_unknowns: list[str] = []
                    financial_facts, financial_unknowns = await self._fetch_financial_facts(
                        client=client,
                        api_key=settings.opendart_api_key,
                        corp_code=corp_code,
                        title=title,
                        published=published,
                    )
                    extra_facts.extend(financial_facts)
                    extra_unknowns.extend(financial_unknowns)
                    treasury_facts, treasury_unknowns = await self._fetch_treasury_stock_facts(
                        client=client,
                        api_key=settings.opendart_api_key,
                        corp_code=corp_code,
                        title=title,
                    )
                    extra_facts.extend(treasury_facts)
                    extra_unknowns.extend(treasury_unknowns)

                    confirmed_facts = [
                        f"OpenDART filing title: {title}",
                        f"OpenDART receipt number: {receipt_no}",
                    ]
                    confirmed_facts.extend(extra_facts)
                    events.append(
                        RawEvent(
                            ticker=ticker.upper(),
                            company_name=item.get("corp_name"),
                            date=published,
                            source="OpenDART",
                            provider=self.name,
                            title=title,
                            url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}",
                            summary="; ".join(confirmed_facts),
                            keywords=_dart_keywords(title),
                            confirmed_facts=confirmed_facts,
                            inferred_implications=[],
                            unknowns=_filing_unknowns(extra_unknowns),
                        )
                    )
                return events
        except (httpx.HTTPError, ValueError):
            return []


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
