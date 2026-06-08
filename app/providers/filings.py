from datetime import date, timedelta
import re

import httpx

from app.config import get_settings
from app.providers.base import FilingProvider, RawEvent
from app.providers.dart_text_fallback import (
    build_text_diagnostics,
    extract_supply_contract_facts_from_text,
    fetch_dart_document_text,
)
from app.providers.opendart_corp_codes import OpenDARTCompany, resolve_opendart_company


OPENDART_CORP_CODES = {
    # Seed fallback while corpCode.xml resolver is unavailable.
    "000660": "00164779",
    "000660.KS": "00164779",
    "SK하이닉스": "00164779",
}

OPENDART_SEED_COMPANY_NAMES = {
    "00164779": "SK하이닉스",
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

TREASURY_STOCK_COUNT_KEYS = (
    "dppln_stk_ostk",
    "dppln_stk_estk",
    "dpstk_ostk",
    "dpstk_estk",
    "trstk_qy",
    "acqsdl_stk_qy",
    "dppln_stk_qy",
    "stk_qy",
)
TREASURY_STOCK_AMOUNT_KEYS = (
    "dppln_prc_ostk",
    "dppln_prc_estk",
    "dppln_prc",
    "dpstk_prc",
    "tr_prc",
    "acqsdl_prc",
    "amount",
)
TREASURY_STOCK_PURPOSE_KEYS = ("dppln_pp", "dp_pp", "tr_pp", "acqsdl_pp", "prps")
TREASURY_STOCK_START_KEYS = ("dppln_pd_bgd", "dp_pd_bgd", "tr_pd_bgd", "acqsdl_pd_bgd")
TREASURY_STOCK_END_KEYS = ("dppln_pd_edd", "dp_pd_edd", "tr_pd_edd", "acqsdl_pd_edd")
TREASURY_STOCK_METHOD_KEYS = ("dppln_mth", "dp_mth", "tr_mth", "acqsdl_mth", "mth")

SUPPLY_CONTRACT_COUNTERPARTY_KEYS = ("cntrpt", "cntprt", "contractor", "spplytrdprt", "trdprt")
SUPPLY_CONTRACT_AMOUNT_KEYS = (
    "cntrct_amt",
    "cntrct_amount",
    "contract_amount",
    "supply_value",
    "amount",
)
SUPPLY_CONTRACT_SALES_RATIO_KEYS = (
    "sales_ratio",
    "cntrct_amt_vs_recent_sales",
    "ctrtamt_recent_sales_ratio",
    "recent_sales_ratio",
    "sl_vs",
)
SUPPLY_CONTRACT_START_KEYS = ("cntrct_begin", "cntrct_bgn", "contract_start", "bgn_de")
SUPPLY_CONTRACT_END_KEYS = ("cntrct_end", "cntrct_edd", "contract_end", "end_de")
SUPPLY_CONTRACT_NAME_KEYS = ("cntrct_nm", "contract_name", "supply_contract_name", "goods")
SUPPLY_CONTRACT_REGION_KEYS = ("rgn", "region", "supply_region", "supply_area")


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


def _financial_item_score(item: dict[str, str]) -> tuple[int, int, int, int, int]:
    fs_div = item.get("fs_div", "")
    sj_div = item.get("sj_div", "")
    sj_nm = item.get("sj_nm", "")
    account_id = item.get("account_id", "")
    thstrm_nm = item.get("thstrm_nm", "")
    consolidated_score = 2 if fs_div == "CFS" else 1 if fs_div == "OFS" else 0
    statement_score = 2 if sj_div == "IS" or "손익" in sj_nm else 1 if sj_div == "BS" or "재무상태" in sj_nm else 0
    account_score = 1 if account_id else 0
    period_score = 1 if "당기" in thstrm_nm or "분기" in thstrm_nm or "반기" in thstrm_nm else 0
    amount_score = 1 if _clean_number(item.get("thstrm_amount")) else 0
    return consolidated_score, statement_score, account_score, period_score, amount_score


def _financial_basis(item: dict[str, str]) -> str:
    metadata = {
        "fs_div": item.get("fs_div") or "unknown",
        "sj_div": item.get("sj_div") or "unknown",
        "account_id": item.get("account_id") or "unknown",
        "thstrm_nm": item.get("thstrm_nm") or "unknown",
        "frmtrm_nm": item.get("frmtrm_nm") or "unknown",
    }
    return "; ".join(f"{key}={value}" for key, value in metadata.items())


def _financial_basis_warnings(selected: dict[str, dict[str, str]]) -> list[str]:
    warnings: list[str] = []
    revenue = selected.get("revenue")
    operating_income = selected.get("operating_income")
    if revenue and operating_income:
        if revenue.get("fs_div") != operating_income.get("fs_div"):
            warnings.append("OpenDART financial quality warning: revenue and operating profit use different fs_div basis")
        if revenue.get("sj_div") != operating_income.get("sj_div"):
            warnings.append("OpenDART financial quality warning: revenue and operating profit use different sj_div basis")
        if revenue.get("thstrm_nm") != operating_income.get("thstrm_nm"):
            warnings.append("OpenDART financial quality warning: revenue and operating profit use different thstrm_nm period labels")
    return warnings


def _extract_financial_facts(items: list[dict[str, str]]) -> list[str]:
    selected: dict[str, dict[str, str]] = {}
    for item in items:
        account_name = item.get("account_nm", "")
        if _format_krw(item.get("thstrm_amount")) is None:
            continue
        for key, aliases in FINANCIAL_ACCOUNT_ALIASES.items():
            if account_name not in aliases:
                continue
            current = selected.get(key)
            if current is None or _financial_item_score(item) > _financial_item_score(current):
                selected[key] = item
            break

    facts: list[str] = []
    for key in ("assets", "liabilities", "equity", "revenue", "operating_income", "net_income"):
        item = selected.get(key)
        if item is None:
            continue
        account_name = item.get("account_nm", "")
        statement_name = item.get("sj_nm", "")
        amount = _format_krw(item.get("thstrm_amount"))
        if amount is None:
            continue
        facts.append(
            f"OpenDART financial fact: {account_name} = {amount} "
            f"({statement_name}; {_financial_basis(item)})"
        )
    facts.extend(_financial_basis_warnings(selected))
    return facts


def _first_non_empty(item: dict[str, str], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = item.get(key)
        if value not in {None, "", "-"}:
            return value
    return None


def _filter_items_by_receipt(items: list[dict[str, str]], receipt_no: str) -> list[dict[str, str]]:
    if not receipt_no:
        return items
    matched = [item for item in items if item.get("rcept_no") == receipt_no]
    return matched or items


def _available_keys_debug(items: list[dict[str, str]], label: str) -> str:
    if not items:
        return f"OpenDART {label} API returned empty list"
    keys = sorted({key for item in items[:3] for key in item.keys()})
    return f"OpenDART {label} API returned unmapped keys: {', '.join(keys[:50])}"


def _extract_treasury_stock_facts(items: list[dict[str, str]]) -> list[str]:
    facts: list[str] = []
    if not items:
        return facts
    item = items[0]
    stock_count = _first_non_empty(item, TREASURY_STOCK_COUNT_KEYS)
    amount = _first_non_empty(item, TREASURY_STOCK_AMOUNT_KEYS)
    purpose = _first_non_empty(item, TREASURY_STOCK_PURPOSE_KEYS)
    start_date = _first_non_empty(item, TREASURY_STOCK_START_KEYS)
    end_date = _first_non_empty(item, TREASURY_STOCK_END_KEYS)
    method = _first_non_empty(item, TREASURY_STOCK_METHOD_KEYS)

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


def _extract_supply_contract_facts(items: list[dict[str, str]]) -> list[str]:
    facts: list[str] = []
    if not items:
        return facts
    item = items[0]
    contract_name = _first_non_empty(item, SUPPLY_CONTRACT_NAME_KEYS)
    counterparty = _first_non_empty(item, SUPPLY_CONTRACT_COUNTERPARTY_KEYS)
    amount = _first_non_empty(item, SUPPLY_CONTRACT_AMOUNT_KEYS)
    sales_ratio = _first_non_empty(item, SUPPLY_CONTRACT_SALES_RATIO_KEYS)
    start_date = _first_non_empty(item, SUPPLY_CONTRACT_START_KEYS)
    end_date = _first_non_empty(item, SUPPLY_CONTRACT_END_KEYS)
    region = _first_non_empty(item, SUPPLY_CONTRACT_REGION_KEYS)

    formatted_amount = _format_krw(amount)
    if contract_name:
        facts.append(f"OpenDART supply contract fact: contract_name = {contract_name}")
    if counterparty:
        facts.append(f"OpenDART supply contract fact: counterparty = {counterparty}")
    if formatted_amount:
        facts.append(f"OpenDART supply contract fact: amount = {formatted_amount}")
    if sales_ratio:
        facts.append(f"OpenDART supply contract fact: recent_sales_ratio = {sales_ratio}")
    if start_date or end_date:
        facts.append(f"OpenDART supply contract fact: period = {start_date or 'unknown'} to {end_date or 'unknown'}")
    if region:
        facts.append(f"OpenDART supply contract fact: region = {region}")
    return facts


async def _resolve_opendart_company(api_key: str, query: str) -> OpenDARTCompany | None:
    seed_corp_code = OPENDART_CORP_CODES.get(query.upper()) or OPENDART_CORP_CODES.get(query)
    if seed_corp_code:
        return OpenDARTCompany(
            corp_code=seed_corp_code,
            corp_name=OPENDART_SEED_COMPANY_NAMES.get(seed_corp_code, query),
            stock_code=query.replace(".KS", "").replace(".KQ", "") if query[:6].isdigit() else "",
        )
    try:
        return await resolve_opendart_company(api_key, query)
    except (httpx.HTTPError, ValueError):
        return None


class OpenDARTProvider(FilingProvider):
    name = "opendart"
    endpoint = "https://opendart.fss.or.kr/api/list.json"
    financial_endpoint = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
    treasury_stock_endpoint = "https://opendart.fss.or.kr/api/tsstkDpDecsn.json"
    supply_contract_endpoint = "https://opendart.fss.or.kr/api/singleSaleSupplyContract.json"

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
        published: date,
        receipt_no: str,
    ) -> tuple[list[str], list[str]]:
        if "자기주식" not in title:
            return [], []
        start = published - timedelta(days=7)
