from dataclasses import dataclass
from io import BytesIO
import re
from xml.etree import ElementTree
from zipfile import ZipFile

import httpx


@dataclass(frozen=True)
class OpenDARTCompany:
    corp_code: str
    corp_name: str
    stock_code: str
    modify_date: str | None = None


_cached_companies: list[OpenDARTCompany] | None = None


def normalize_equity_input(value: str) -> str:
    normalized = value.strip()
    normalized = re.sub(r"\.(ks|kq|kospi|kosdaq)$", "", normalized, flags=re.IGNORECASE)
    return normalized.strip()


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def _parse_corp_code_zip(content: bytes) -> list[OpenDARTCompany]:
    with ZipFile(BytesIO(content)) as archive:
        xml_name = next((name for name in archive.namelist() if name.lower().endswith(".xml")), None)
        if xml_name is None:
            return []
        root = ElementTree.fromstring(archive.read(xml_name))

    companies: list[OpenDARTCompany] = []
    for node in root.findall("list"):
        corp_code = (node.findtext("corp_code") or "").strip()
        corp_name = (node.findtext("corp_name") or "").strip()
        stock_code = (node.findtext("stock_code") or "").strip()
        modify_date = (node.findtext("modify_date") or "").strip() or None
        if not corp_code or not corp_name:
            continue
        companies.append(
            OpenDARTCompany(
                corp_code=corp_code,
                corp_name=corp_name,
                stock_code=stock_code,
                modify_date=modify_date,
            )
        )
    return companies


async def load_opendart_companies(api_key: str, force_refresh: bool = False) -> list[OpenDARTCompany]:
    global _cached_companies
    if _cached_companies is not None and not force_refresh:
        return _cached_companies

    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params={"crtfc_key": api_key})
        response.raise_for_status()
    _cached_companies = _parse_corp_code_zip(response.content)
    return _cached_companies


async def resolve_opendart_company(api_key: str, query: str) -> OpenDARTCompany | None:
    normalized = normalize_equity_input(query)
    normalized_upper = normalized.upper()
    normalized_compact = _compact(normalized)
    companies = await load_opendart_companies(api_key)

    # 1) Exact listed stock code match, e.g. 000660 or 000660.KS.
    if re.fullmatch(r"\d{6}", normalized):
        for company in companies:
            if company.stock_code == normalized:
                return company

    # 2) Exact company name match, e.g. SK하이닉스.
    for company in companies:
        if _compact(company.corp_name) == normalized_compact:
            return company

    # 3) Exact corp code match for advanced/manual calls.
    for company in companies:
        if company.corp_code == normalized_upper:
            return company

    # 4) Unique partial name match. Avoid ambiguous broad queries.
    partial_matches = [company for company in companies if normalized_compact in _compact(company.corp_name)]
    listed_matches = [company for company in partial_matches if company.stock_code]
    if len(listed_matches) == 1:
        return listed_matches[0]
    if len(partial_matches) == 1:
        return partial_matches[0]
    return None
