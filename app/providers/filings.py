from datetime import date, timedelta
import re

import httpx

from app.config import get_settings
from app.providers.base import FilingProvider, RawEvent
from app.providers.dart_text_fallback import (
    PreliminaryEarningsFacts,
    build_text_diagnostics,
    extract_preliminary_earnings_facts_from_text,
    extract_supply_contract_facts_from_text,
    fetch_dart_document_text,
)
from app.providers.opendart_corp_codes import OpenDARTCompany, resolve_opendart_company

OPENDART_CORP_CODES = {
    "005930": "00126380",
    "005930.KS": "00126380",
    "삼성전자": "00126380",
    "000660": "00164779",
    "000660.KS": "00164779",
    "SK하이닉스": "00164779",
}
OPENDART_SEED_COMPANY_NAMES = {"00126380": "삼성전자", "00164779": "SK하이닉스"}
SEC_TICKER_CIK = {"NVDA": "0001045810", "AMD": "0000002488"}
REPORT_CODE_BY_TITLE = {"1분기보고서": "11013", "분기보고서": "11013", "반기보고서": "11012", "3분기보고서": "11014", "사업보고서": "11011"}
FINANCIAL_ACCOUNT_ALIASES = {
    "revenue": ("매출액", "수익(매출액)", "영업수익"),
    "operating_income": ("영업이익", "영업이익(손실)"),
    "net_income": (
        "당기순이익", "당기순이익(손실)", "분기순이익", "반기순이익", "연결당기순이익"
    ),
    "owners_parent_net_income": (
        "지배기업 소유주지분 순이익",
        "지배기업의 소유주에게 귀속되는 당기순이익",
        "지배기업 소유주에게 귀속되는 당기순이익",
        "지배기업 소유주 귀속 분기순이익",
        "지배기업 소유주 귀속 반기순이익",
        "지배기업 소유주 귀속 당기순이익",
    ),
    "basic_eps": (
        "기본주당이익", "기본주당순이익", "기본주당순이익(손실)",
        "지배기업 소유주 기본주당이익",
    ),
    "diluted_eps": (
        "희석주당이익", "희석주당순이익", "희석주당순이익(손실)",
        "지배기업 소유주 희석주당이익",
    ),
    "assets": ("자산총계",),
    "liabilities": ("부채총계",),
    "equity": ("자본총계",),
    "owners_parent_equity": (
        "지배기업 소유주지분",
        "지배기업의 소유주에게 귀속되는 자본",
        "지배기업소유주지분",
        "지배기업의 소유주지분",
    ),
}
FINANCIAL_CANONICAL_LABELS = {
    "revenue": "매출액",
    "operating_income": "영업이익",
    "net_income": "당기순이익",
    "owners_parent_net_income": "지배주주순이익",
    "basic_eps": "기본주당이익",
    "diluted_eps": "희석주당이익",
    "assets": "자산총계",
    "liabilities": "부채총계",
    "equity": "자본총계",
    "owners_parent_equity": "지배주주지분",
}
FINANCIAL_ACCOUNT_IDS = {
    "owners_parent_net_income": {
        "ifrs-full_profitlossattributabletoownersofparent",
    },
    "owners_parent_equity": {
        "ifrs-full_equityattributabletoownersofparent",
    },
    "basic_eps": {
        "ifrs-full_basicearningslosspershare",
    },
    "diluted_eps": {
        "ifrs-full_dilutedearningslosspershare",
    },
}
TREASURY_STOCK_COUNT_KEYS = ("dppln_stk_ostk", "dppln_stk_estk", "dpstk_ostk", "dpstk_estk", "trstk_qy", "acqsdl_stk_qy", "dppln_stk_qy", "stk_qy")
TREASURY_STOCK_AMOUNT_KEYS = ("dppln_prc_ostk", "dppln_prc_estk", "dppln_prc", "dpstk_prc", "tr_prc", "acqsdl_prc", "amount")
TREASURY_STOCK_PURPOSE_KEYS = ("dppln_pp", "dp_pp", "tr_pp", "acqsdl_pp", "prps")
TREASURY_STOCK_START_KEYS = ("dppln_pd_bgd", "dp_pd_bgd", "tr_pd_bgd", "acqsdl_pd_bgd")
TREASURY_STOCK_END_KEYS = ("dppln_pd_edd", "dp_pd_edd", "tr_pd_edd", "acqsdl_pd_edd")
TREASURY_STOCK_METHOD_KEYS = ("dppln_mth", "dp_mth", "tr_mth", "acqsdl_mth", "mth")
SUPPLY_CONTRACT_COUNTERPARTY_KEYS = ("cntrpt", "cntprt", "contractor", "spplytrdprt", "trdprt")
SUPPLY_CONTRACT_AMOUNT_KEYS = ("cntrct_amt", "cntrct_amount", "contract_amount", "supply_value", "amount")
SUPPLY_CONTRACT_SALES_RATIO_KEYS = ("sales_ratio", "cntrct_amt_vs_recent_sales", "ctrtamt_recent_sales_ratio", "recent_sales_ratio", "sl_vs")
SUPPLY_CONTRACT_START_KEYS = ("cntrct_begin", "cntrct_bgn", "contract_start", "bgn_de")
SUPPLY_CONTRACT_END_KEYS = ("cntrct_end", "cntrct_edd", "contract_end", "end_de")
SUPPLY_CONTRACT_NAME_KEYS = ("cntrct_nm", "contract_name", "supply_contract_name", "goods")
SUPPLY_CONTRACT_REGION_KEYS = ("rgn", "region", "supply_region", "supply_area")
FINANCING_PURPOSE_KEYS = (
    "fdpp_fclt",
    "fdpp_bsninh",
    "fdpp_op",
    "fdpp_dtrp",
    "fdpp_ocsa",
    "fdpp_etc",
)

PRELIMINARY_EARNINGS_TITLES = (
    "연결재무제표기준영업(잠정)실적",
    "영업(잠정)실적",
    "잠정영업실적",
    "매출액 또는 손익구조 변동",
    "매출액또는손익구조변동",
)


def _extract_dividend_facts(items: list[dict[str, str]]) -> list[str]:
    common_rows = [
        item for item in items
        if "보통주" in str(item.get("stock_knd", item.get("se", "")))
        or str(item.get("stock_knd", item.get("se", ""))).strip() in {"", "-"}
    ]
    rows = common_rows or items
    mappings = {
        "dps": ("주당 현금배당금", "주당현금배당금", "dps"),
        "total_dividend": ("현금배당금총액", "현금배당금 총액", "total_dividend"),
        "payout_ratio": ("현금배당성향", "배당성향", "payout_ratio"),
    }
    facts: list[str] = []
    for item in rows:
        label = str(item.get("se", "")).replace(" ", "")
        value = _clean_number(item.get("thstrm"))
        if value is None:
            continue
        field = next(
            (name for name, aliases in mappings.items() if any(alias.replace(" ", "") in label for alias in aliases)),
            None,
        )
        if field == "dps":
            facts.append(f"OpenDART dividend fact: dps = {value} KRW")
        elif field == "total_dividend":
            try:
                amount = float(value) * 1_000_000
                facts.append(f"OpenDART dividend fact: total_dividend = {amount:.0f} KRW")
            except ValueError:
                continue
        elif field == "payout_ratio":
            facts.append(f"OpenDART dividend fact: payout_ratio = {value} percent")
    return list(dict.fromkeys(facts))


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
        return f"{int(cleaned):,} KRW"
    except ValueError:
        return cleaned


def _format_shares(value: str | None) -> str | None:
    cleaned = _clean_number(value)
    if cleaned is None:
        return None
    try:
        return f"{int(cleaned):,} shares"
    except ValueError:
        return cleaned


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
    for needle, keyword in {
        "유상증자": "capital_raise",
        "전환사채": "convertible_bond",
        "cb": "convertible_bond",
        "신주인수권": "warrant",
        "bw": "warrant",
        "실적": "earnings",
        "영업(잠정)실적": "earnings",
        "잠정영업실적": "earnings",
        "매출액 또는 손익구조 변동": "earnings",
        "매출액또는손익구조변동": "earnings",
        "분기보고서": "earnings",
        "반기보고서": "earnings",
        "사업보고서": "earnings",
        "공급계약": "supply_contract",
        "단일판매": "supply_contract",
        "자기주식": "treasury_stock",
        "자사주": "treasury_stock",
        "신규시설투자": "facility_investment",
        "조회공시요구(풍문또는보도)에대한답변": "disclosure_clarification",
        "풍문또는보도에대한해명": "disclosure_clarification",
        "조회공시요구": "disclosure_inquiry",
        "투자판단": "material_management_matter",
        "주요경영사항": "material_management_matter",
    }.items():
        if needle.lower() in title_lower:
            keywords.append(keyword)
    return keywords


def _report_code_from_title(title: str) -> str | None:
    if "분기보고서" in title:
        period_match = re.search(r"20\d{2}[.\-/](\d{1,2})", title)
        if period_match and int(period_match.group(1)) >= 9:
            return "11014"
    for needle, code in REPORT_CODE_BY_TITLE.items():
        if needle in title:
            return "11014" if needle == "분기보고서" and "3분기" in title else code
    return None


def _is_preliminary_earnings_title(title: str) -> bool:
    compact = re.sub(r"\s+", "", title)
    return any(re.sub(r"\s+", "", term) in compact for term in PRELIMINARY_EARNINGS_TITLES)


def _reporting_period_end(title: str, published: date) -> date | None:
    report_code = _report_code_from_title(title)
    if report_code is None:
        return None
    year = int(_business_year_from_title_or_date(title, published))
    month_day = {
        "11013": (3, 31),
        "11012": (6, 30),
        "11014": (9, 30),
        "11011": (12, 31),
    }.get(report_code)
    return date(year, *month_day) if month_day else None


def _business_year_from_title_or_date(title: str, published: date) -> str:
    match = re.search(r"(20\d{2})", title)
    return match.group(1) if match else str(published.year)


def _financial_item_score(item: dict[str, str]) -> tuple[int, int, int, int, int]:
    fs_div = item.get("fs_div", "")
    sj_div = item.get("sj_div", "")
    sj_nm = item.get("sj_nm", "")
    thstrm_nm = item.get("thstrm_nm", "")
    return (
        2 if fs_div == "CFS" else 1 if fs_div == "OFS" else 0,
        2 if sj_div == "IS" or "손익" in sj_nm else 1 if sj_div == "BS" or "재무상태" in sj_nm else 0,
        1 if item.get("account_id") else 0,
        1 if any(term in thstrm_nm for term in ("당기", "분기", "반기")) else 0,
        1 if _clean_number(item.get("thstrm_amount")) else 0,
    )


def _period_scope(report_code: str) -> str:
    return {
        "11013": "single-quarter",
        "11012": "half-year",
        "11014": "ytd",
        "11011": "annual",
    }.get(report_code, "cumulative")


def _financial_basis(item: dict[str, str], report_code: str, amount_scope: str) -> str:
    return "; ".join(
        [
            *(
                f"{key}={item.get(key) or 'unknown'}"
                for key in ("fs_div", "sj_div", "account_id", "thstrm_nm", "frmtrm_nm")
            ),
            "unit=KRW",
            f"period_scope={_period_scope(report_code)}",
            f"amount_scope={amount_scope}",
            f"report_code={report_code or 'unknown'}",
        ]
    )


def _financial_basis_warnings(selected: dict[str, dict[str, str]]) -> list[str]:
    warnings: list[str] = []
    revenue = selected.get("revenue")
    operating_income = selected.get("operating_income")
    if not (revenue and operating_income):
        return warnings
    if revenue.get("fs_div") != operating_income.get("fs_div"):
        warnings.append("OpenDART financial quality warning: revenue and operating profit use different fs_div basis")
    if revenue.get("sj_div") != operating_income.get("sj_div"):
        warnings.append("OpenDART financial quality warning: revenue and operating profit use different sj_div basis")
    if revenue.get("thstrm_nm") != operating_income.get("thstrm_nm"):
        warnings.append("OpenDART financial quality warning: revenue and operating profit use different thstrm_nm period labels")
    return warnings


def _extract_financial_facts(items: list[dict[str, str]], report_code: str = "") -> list[str]:
    selected: dict[str, dict[str, str]] = {}
    id_selected: set[str] = set()
    for item in items:
        account_name = item.get("account_nm", "")
        account_id = item.get("account_id", "").lower()
        if _format_krw(item.get("thstrm_amount")) is None:
            continue
        id_key = next(
            (
                key
                for key, account_ids in FINANCIAL_ACCOUNT_IDS.items()
                if account_id in account_ids
            ),
            None,
        )
        if id_key is not None:
            if id_key not in selected or _financial_item_score(item) > _financial_item_score(selected[id_key]):
                selected[id_key] = item
                id_selected.add(id_key)
            continue
        for key, aliases in FINANCIAL_ACCOUNT_ALIASES.items():
            if account_name in aliases:
                if key not in id_selected and (
                    key not in selected
                    or _financial_item_score(item) > _financial_item_score(selected[key])
                ):
                    selected[key] = item
                break
    facts: list[str] = []
    for key in (
        "assets", "liabilities", "equity", "owners_parent_equity", "revenue",
        "operating_income", "net_income", "owners_parent_net_income", "basic_eps",
        "diluted_eps",
    ):
        item = selected.get(key)
        if not item:
            continue
        amount = _format_krw(item.get("thstrm_amount"))
        if amount:
            facts.append(
                f"OpenDART financial fact: {FINANCIAL_CANONICAL_LABELS[key]} = {amount} "
                f"({item.get('sj_nm', '')}; {_financial_basis(item, report_code, 'standalone_or_balance')})"
            )
        cumulative = _format_krw(item.get("thstrm_add_amount"))
        if cumulative and key in {
            "revenue", "operating_income", "net_income", "owners_parent_net_income",
            "basic_eps", "diluted_eps",
        }:
            facts.append(
                f"OpenDART financial cumulative fact: {FINANCIAL_CANONICAL_LABELS[key]} = {cumulative} "
                f"({item.get('sj_nm', '')}; {_financial_basis(item, report_code, 'cumulative')})"
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
    if matched:
        return matched
    if any(item.get("rcept_no") for item in items):
        return []
    return items


def _available_keys_debug(items: list[dict[str, str]], label: str) -> str:
    if not items:
        return f"OpenDART {label} API returned empty list"
    keys = sorted({key for item in items[:3] for key in item})
    return f"OpenDART {label} API returned unmapped keys: {', '.join(keys[:50])}"


def _extract_treasury_stock_facts(items: list[dict[str, str]]) -> list[str]:
    if not items:
        return []
    item = items[0]
    facts: list[str] = []
    if value := _format_shares(_first_non_empty(item, TREASURY_STOCK_COUNT_KEYS)):
        facts.append(f"OpenDART treasury stock fact: shares = {value}")
    if value := _format_krw(_first_non_empty(item, TREASURY_STOCK_AMOUNT_KEYS)):
        facts.append(f"OpenDART treasury stock fact: amount = {value}")
    if value := _first_non_empty(item, TREASURY_STOCK_PURPOSE_KEYS):
        facts.append(f"OpenDART treasury stock fact: purpose = {value}")
    start = _first_non_empty(item, TREASURY_STOCK_START_KEYS)
    end = _first_non_empty(item, TREASURY_STOCK_END_KEYS)
    if start or end:
        facts.append(f"OpenDART treasury stock fact: period = {start or 'unknown'} to {end or 'unknown'}")
    if value := _first_non_empty(item, TREASURY_STOCK_METHOD_KEYS):
        facts.append(f"OpenDART treasury stock fact: method = {value}")
    return facts


def _extract_supply_contract_facts(items: list[dict[str, str]]) -> list[str]:
    if not items:
        return []
    item = items[0]
    facts: list[str] = []
    mappings = [
        ("contract_name", SUPPLY_CONTRACT_NAME_KEYS, None),
        ("counterparty", SUPPLY_CONTRACT_COUNTERPARTY_KEYS, None),
        ("amount", SUPPLY_CONTRACT_AMOUNT_KEYS, _format_krw),
        ("recent_sales_ratio", SUPPLY_CONTRACT_SALES_RATIO_KEYS, None),
        ("region", SUPPLY_CONTRACT_REGION_KEYS, None),
    ]
    for label, keys, formatter in mappings:
        value = _first_non_empty(item, keys)
        if value and formatter:
            value = formatter(value)
        if value:
            facts.append(f"OpenDART supply contract fact: {label} = {value}")
    start = _first_non_empty(item, SUPPLY_CONTRACT_START_KEYS)
    end = _first_non_empty(item, SUPPLY_CONTRACT_END_KEYS)
    if start or end:
        facts.append(f"OpenDART supply contract fact: period = {start or 'unknown'} to {end or 'unknown'}")
    return facts


def _sum_numeric_fields(item: dict[str, str], keys: tuple[str, ...]) -> int | None:
    values: list[int] = []
    for key in keys:
        cleaned = _clean_number(item.get(key))
        if cleaned is None:
            continue
        try:
            values.append(int(float(cleaned)))
        except ValueError:
            continue
    return sum(values) if values else None


def _extract_capital_raise_facts(items: list[dict[str, str]]) -> list[str]:
    if not items:
        return []
    item = items[0]
    facts: list[str] = []
    financing = _sum_numeric_fields(item, FINANCING_PURPOSE_KEYS)
    new_shares = _sum_numeric_fields(item, ("nstk_ostk_cnt", "nstk_estk_cnt"))
    capex = _sum_numeric_fields(item, ("fdpp_fclt",))
    if financing is not None:
        facts.append(f"OpenDART capital raise fact: amount = {_format_krw(str(financing))}")
    if new_shares is not None:
        facts.append(f"OpenDART capital raise fact: new_shares = {new_shares:,} shares")
    if capex is not None:
        facts.append(f"OpenDART facility investment fact: amount = {_format_krw(str(capex))}")
    return facts


def _extract_convertible_bond_facts(items: list[dict[str, str]]) -> list[str]:
    if not items:
        return []
    item = items[0]
    facts: list[str] = []
    amount = _first_non_empty(item, ("bd_fta", "ovis_fta"))
    convertible_shares = _first_non_empty(item, ("cvisstk_cnt",))
    conversion_price = _first_non_empty(item, ("cv_prc",))
    capex = _sum_numeric_fields(item, ("fdpp_fclt",))
    if amount:
        facts.append(
            f"OpenDART convertible bond fact: amount = {_format_krw(amount)}"
        )
    if convertible_shares:
        facts.append(
            "OpenDART convertible bond fact: convertible_shares = "
            f"{_format_shares(convertible_shares)}"
        )
    if conversion_price:
        facts.append(
            "OpenDART convertible bond fact: conversion_price = "
            f"{_format_krw(conversion_price)} per share"
        )
    if capex is not None:
        facts.append(f"OpenDART facility investment fact: amount = {_format_krw(str(capex))}")
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
    financial_all_endpoint = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    share_status_endpoint = "https://opendart.fss.or.kr/api/stockTotqySttus.json"
    treasury_stock_endpoint = "https://opendart.fss.or.kr/api/tsstkDpDecsn.json"
    supply_contract_endpoint = "https://opendart.fss.or.kr/api/singleSaleSupplyContract.json"
    capital_raise_endpoint = "https://opendart.fss.or.kr/api/piicDecsn.json"
    convertible_bond_endpoint = "https://opendart.fss.or.kr/api/cvbdIsDecsn.json"
    dividend_endpoint = "https://opendart.fss.or.kr/api/alotMatter.json"

    async def _fetch_preliminary_earnings(
        self,
        client: httpx.AsyncClient,
        title: str,
        receipt_no: str,
    ) -> tuple[PreliminaryEarningsFacts | None, list[str]]:
        if not _is_preliminary_earnings_title(title):
            return None, []
        try:
            document = await fetch_dart_document_text(client, receipt_no)
        except (httpx.HTTPError, ValueError):
            return None, ["OpenDART preliminary earnings document request failed"]
        if document is None:
            return None, ["OpenDART preliminary earnings document was unavailable"]
        parsed = extract_preliminary_earnings_facts_from_text(document.text)
        if not parsed.facts or parsed.period_end is None:
            return None, [
                "OpenDART preliminary earnings table parsing was incomplete",
                *build_text_diagnostics(document)[:2],
            ]
        return parsed, []

    async def _fetch_dividend_facts(
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
            response = await client.get(self.dividend_endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return [], ["OpenDART dividend API request failed"]
        if payload.get("status") != "000":
            return [], [f"OpenDART dividend API status: {payload.get('status')}"]
        facts = _extract_dividend_facts(payload.get("list", []))
        return (facts, []) if facts else ([], ["OpenDART dividend API returned no mapped common-share facts"])

    async def _fetch_decision_facts(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        corp_code: str,
        title: str,
        published: date,
        receipt_no: str,
    ) -> tuple[list[str], list[str]]:
        if "유상증자" in title:
            endpoint = self.capital_raise_endpoint
            label = "capital raise"
            extractor = _extract_capital_raise_facts
        elif any(term in title for term in ("전환사채", "전환가액")):
            endpoint = self.convertible_bond_endpoint
            label = "convertible bond"
            extractor = _extract_convertible_bond_facts
        else:
            return [], []
        params = {
            "crtfc_key": api_key,
            "corp_code": corp_code,
            "bgn_de": _yyyymmdd(published - timedelta(days=30)),
            "end_de": _yyyymmdd(published + timedelta(days=30)),
        }
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return [], [f"OpenDART {label} API request failed"]
        if payload.get("status") != "000":
            return [], [f"OpenDART {label} API status: {payload.get('status')}"]
        items = _filter_items_by_receipt(payload.get("list", []), receipt_no)
        facts = extractor(items)
        return (facts, []) if facts else ([], [_available_keys_debug(items, label)])

    async def _fetch_financial_facts(self, client: httpx.AsyncClient, api_key: str, corp_code: str, title: str, published: date) -> tuple[list[str], list[str]]:
        report_code = _report_code_from_title(title)
        if report_code is None:
            return [], []
        params = {"crtfc_key": api_key, "corp_code": corp_code, "bsns_year": _business_year_from_title_or_date(title, published), "reprt_code": report_code}
        try:
            response = await client.get(self.financial_endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return [], ["OpenDART financial statement API request failed"]
        if payload.get("status") != "000":
            return [], [f"OpenDART financial statement API status: {payload.get('status')}"]
        facts = _extract_financial_facts(payload.get("list", []), report_code)
        has_income_statement = any(
            marker in fact
            for fact in facts
            for marker in ("영업이익 =", "당기순이익 =", "지배주주순이익 =")
        )
        has_ownership_basis = any(
            marker in fact
            for fact in facts
            for marker in ("지배주주순이익 =", "지배주주지분 =", "희석주당이익 =")
        )
        if not has_income_statement or not has_ownership_basis:
            for fs_div in ("CFS", "OFS"):
                try:
                    detailed_response = await client.get(
                        self.financial_all_endpoint,
                        params={**params, "fs_div": fs_div},
                    )
                    detailed_response.raise_for_status()
                    detailed_payload = detailed_response.json()
                except (httpx.HTTPError, ValueError):
                    continue
                if detailed_payload.get("status") != "000":
                    continue
                detailed_facts = _extract_financial_facts(
                    detailed_payload.get("list", []), report_code
                )
                if detailed_facts:
                    facts = detailed_facts
                    break
        return (facts, []) if facts else ([], ["OpenDART financial statement API returned no mapped financial facts"])

    async def _fetch_share_status_facts(
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
            response = await client.get(self.share_status_endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return [], ["OpenDART share status API request failed"]
        if payload.get("status") != "000":
            return [], [f"OpenDART share status API status: {payload.get('status')}"]
        rows = payload.get("list", [])
        common = next(
            (
                row for row in rows
                if "보통주" in str(row.get("se", ""))
                or "common" in str(row.get("se", "")).lower()
            ),
            None,
        )
        if not isinstance(common, dict):
            return [], ["OpenDART share status API returned no mapped common-share row"]
        issued = _format_shares(common.get("istc_totqy"))
        treasury = _format_shares(common.get("tesstk_co"))
        outstanding = _format_shares(common.get("distb_stock_co"))
        if outstanding is None:
            issued_raw = _clean_number(common.get("istc_totqy"))
            treasury_raw = _clean_number(common.get("tesstk_co"))
            try:
                outstanding = f"{int(issued_raw or '0') - int(treasury_raw or '0'):,} shares"
            except ValueError:
                outstanding = None
        basis = f"report_code={report_code}; share_class=common"
        facts = []
        for label, value in (
            ("보통주발행주식수", issued),
            ("자기주식수", treasury),
            ("보통주유통주식수", outstanding),
        ):
            if value:
                facts.append(f"OpenDART share fact: {label} = {value} ({basis})")
        return (facts, []) if facts else ([], ["OpenDART share status values were unavailable"])

    async def _fetch_treasury_stock_facts(self, client: httpx.AsyncClient, api_key: str, corp_code: str, title: str, published: date, receipt_no: str) -> tuple[list[str], list[str]]:
        if "자기주식" not in title:
            return [], []
        start = published - timedelta(days=7)
        end = published + timedelta(days=7)
        params = {"crtfc_key": api_key, "corp_code": corp_code, "bgn_de": _yyyymmdd(start), "end_de": _yyyymmdd(end)}
        try:
            response = await client.get(self.treasury_stock_endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return [], ["OpenDART treasury stock API request failed"]
        if payload.get("status") != "000":
            return [], [f"OpenDART treasury stock API status: {payload.get('status')}"]
        items = _filter_items_by_receipt(payload.get("list", []), receipt_no)
        facts = _extract_treasury_stock_facts(items)
        return (facts, []) if facts else ([], [_available_keys_debug(items, "treasury stock")])

    async def _fetch_supply_contract_facts(self, client: httpx.AsyncClient, api_key: str, corp_code: str, title: str, published: date, receipt_no: str) -> tuple[list[str], list[str]]:
        if not any(term in title for term in ("공급계약", "단일판매", "판매ㆍ공급계약", "판매·공급계약")):
            return [], []
        start = published - timedelta(days=30)
        end = published + timedelta(days=30)
        params = {"crtfc_key": api_key, "corp_code": corp_code, "bgn_de": _yyyymmdd(start), "end_de": _yyyymmdd(end)}
        try:
            response = await client.get(self.supply_contract_endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            payload = {"status": "fallback"}
        if payload.get("status") == "000":
            items = _filter_items_by_receipt(payload.get("list", []), receipt_no)
            if facts := _extract_supply_contract_facts(items):
                return facts, []
        try:
            document = await fetch_dart_document_text(client, receipt_no)
        except (httpx.HTTPError, ValueError):
            document = None
        if document and (facts := extract_supply_contract_facts_from_text(document.text)):
            return facts, []
        diagnostics = build_text_diagnostics(document)
        status = payload.get("status")
        if status == "000":
            return [], [_available_keys_debug(payload.get("list", []), "supply contract"), *diagnostics]
        return [], [f"OpenDART supply contract API status: {status}", *diagnostics]

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        settings = get_settings()
        if not settings.opendart_api_key:
            return []
        company = await _resolve_opendart_company(settings.opendart_api_key, ticker)
        if company is None:
            return []
        params = {"crtfc_key": settings.opendart_api_key, "corp_code": company.corp_code, "bgn_de": _yyyymmdd(date.today() - timedelta(days=lookback_days)), "page_count": 20}
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
                        published = date.fromisoformat(f"{filing_date[:4]}-{filing_date[4:6]}-{filing_date[6:8]}")
                    except ValueError:
                        published = date.today()
                    extra_facts: list[str] = []
                    extra_unknowns: list[str] = []
                    preliminary, preliminary_unknowns = await self._fetch_preliminary_earnings(
                        client, title, receipt_no
                    )
                    if preliminary:
                        extra_facts.extend(preliminary.facts)
                    extra_unknowns.extend(preliminary_unknowns)
                    for facts, unknowns in (
                        await self._fetch_financial_facts(client, settings.opendart_api_key, company.corp_code, title, published),
                        await self._fetch_dividend_facts(client, settings.opendart_api_key, company.corp_code, title, published),
                        await self._fetch_share_status_facts(client, settings.opendart_api_key, company.corp_code, title, published),
                        await self._fetch_treasury_stock_facts(client, settings.opendart_api_key, company.corp_code, title, published, receipt_no),
                        await self._fetch_supply_contract_facts(client, settings.opendart_api_key, company.corp_code, title, published, receipt_no),
                        await self._fetch_decision_facts(client, settings.opendart_api_key, company.corp_code, title, published, receipt_no),
                    ):
                        extra_facts.extend(facts)
                        extra_unknowns.extend(unknowns)
                    confirmed_facts = [f"OpenDART filing title: {title}", f"OpenDART receipt number: {receipt_no}", *extra_facts]
                    output_ticker = company.stock_code or ticker.upper()
                    reporting_period_end = (
                        preliminary.period_end
                        if preliminary
                        else _reporting_period_end(title, published)
                    )
                    document_type = (
                        "preliminary_earnings"
                        if preliminary
                        else "full_statement"
                        if _report_code_from_title(title) is not None
                        else "regulatory_filing"
                    )
                    events.append(
                        RawEvent(
                            ticker=output_ticker.upper(),
                            company_name=item.get("corp_name") or company.corp_name,
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
                            reporting_period_end=reporting_period_end,
                            document_type=document_type,
                            financial_scope=(
                                "income_statement_partial"
                                if preliminary
                                else "full_statement"
                                if _report_code_from_title(title) is not None
                                else None
                            ),
                            revenue=preliminary.revenue if preliminary else None,
                            operating_income=(
                                preliminary.operating_income if preliminary else None
                            ),
                            net_income=preliminary.net_income if preliminary else None,
                            operating_margin=(
                                preliminary.operating_margin if preliminary else None
                            ),
                            yoy_growth=preliminary.yoy_growth if preliminary else None,
                            qoq_growth=preliminary.qoq_growth if preliminary else None,
                            financial_report_filed=(
                                _report_code_from_title(title) is not None
                                or preliminary is not None
                            ),
                        )
                    )
                return events
        except (httpx.HTTPError, ValueError):
            return []


class SecEdgarProvider(FilingProvider):
    name = "sec_edgar"
    endpoint_template = "https://data.sec.gov/submissions/CIK{cik}.json"

    async def _resolve_cik(self, client: httpx.AsyncClient, ticker: str) -> str | None:
        if ticker.upper() in SEC_TICKER_CIK:
            return SEC_TICKER_CIK[ticker.upper()]
        response = await client.get("https://www.sec.gov/files/company_tickers.json")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return None
        for item in payload.values():
            if isinstance(item, dict) and str(item.get("ticker", "")).upper() == ticker.upper():
                return str(item.get("cik_str", "")).zfill(10)
        return None

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        settings = get_settings()
        if not settings.sec_user_agent:
            return []
        headers = {"User-Agent": settings.sec_user_agent, "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                cik = await self._resolve_cik(client, ticker)
                if not cik:
                    return []
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
        for form, filing_date, accession, primary_doc in zip(forms, filing_dates, accession_numbers, primary_documents, strict=False):
            if form not in {"8-K", "10-Q", "10-K", "20-F", "6-K"}:
                continue
            try:
                published = date.fromisoformat(filing_date)
            except ValueError:
                published = date.today()
            if published < cutoff:
                continue
            accession_path = accession.replace("-", "")
            url = "https://www.sec.gov" + f"/Archives/edgar/data/{int(cik)}/{accession_path}/{primary_doc}"
            events.append(
                RawEvent(
                    ticker=ticker.upper(),
                    company_name=company_name,
                    date=published,
                    source="SEC EDGAR",
                    provider=self.name,
                    title=f"{company_name or ticker.upper()} filed {form}",
                    url=url,
                    summary=f"{company_name or ticker.upper()} filed {form}",
                    keywords=["sec_edgar", form.lower(), "filing"],
                    confirmed_facts=[f"SEC EDGAR recent filing form: {form}", f"SEC accession number: {accession}"],
                    inferred_implications=[],
                    unknowns=_filing_unknowns(),
                    financial_report_filed=form in {"10-Q", "10-K", "20-F", "6-K"},
                )
            )
        return events
