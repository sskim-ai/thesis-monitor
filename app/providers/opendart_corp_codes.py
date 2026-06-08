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
    value = re.sub(r"\s+", "", value).lower()
    for suffix in ("주식회사", "(주)", "㈜"):
        value = value.replace(suffix, "")
    return value


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
        if corp_code and corp_name:
            companies.append(OpenDARTCompany(corp_code, corp_name, stock_code, modify_date))
    return companies


async def load_opendart_companies(api_key: str, force_refresh: bool = False) -> list[OpenDARTCompany]:
    global _cached_companies
    if _cached_companies is not None and not force_refresh:
        return _cached_companies

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://opendart.fss.or.kr/api/corpCode.xml",
            params={"crtfc_key": api_key},
        )
        response.raise_for_status()
    _cached_companies = _parse_corp_code_zip(response.content)
    return _cached_companies


def _name_score(company: OpenDARTCompany, query_compact: str) -> int:
    name = _compact(company.corp_name)
    listed_bonus = 10 if company.stock_code else 0
    if name == query_compact:
        return 100 + listed_bonus
    if name.startswith(query_compact):
        return 80 + listed_bonus
    if query_compact in name:
        return 60 + listed_bonus
    return 0


async def resolve_opendart_company(api_key: str, query: str) -> OpenDARTCompany | None:
    normalized = normalize_equity_input(query)
    normalized_upper = normalized.upper()
    query_compact = _compact(normalized)
    companies = await load_opendart_companies(api_key)

    if re.fullmatch(r"\d{6}", normalized):
        for company in companies:
            if company.stock_code == normalized:
                return company

    for company in companies:
        if company.corp_code == normalized_upper:
            return company

    scored = [(score, company) for company in companies if (score := _name_score(company, query_compact)) > 0]
    if not scored:
        return None
    scored.sort(key=lambda pair: (pair[0], pair[1].modify_date or ""), reverse=True)
    best_score = scored[0][0]
    best_matches = [company for score, company in scored if score == best_score]
    if len(best_matches) == 1:
        return best_matches[0]
    listed = [company for company in best_matches if company.stock_code]
    if len(listed) == 1:
        return listed[0]
    return None
