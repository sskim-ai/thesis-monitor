import hashlib
import json
import re
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.watchlist import WatchlistItem
from app.utils.tickers import COMPANY_NAME_ALIASES


SECURITY_ALIASES: dict[str, tuple[str, ...]] = {
    "000660": ("sk하이닉스", "sk hynix", "hynix"),
    "003690": ("코리안리", "korean re", "korean reinsurance"),
    "005490": ("posco홀딩스", "포스코홀딩스", "posco holdings"),
    "005930": ("삼성전자", "samsung electronics"),
    "086280": ("현대글로비스", "hyundai glovis"),
    "CRCL": ("circle internet", "circle internet group", "usdc"),
    "GOOGL": ("alphabet", "google", "youtube", "waymo", "deepmind", "gemini"),
    "IBM": ("international business machines", "ibm", "red hat"),
    "MU": ("micron technology", "micron"),
    "RXRX": ("recursion pharmaceuticals", "recursion"),
    "SNDK": ("sandisk", "san disk"),
    "TSLA": ("tesla", "cybercab", "robotaxi", "full self-driving", "fsd"),
    "TSM": ("taiwan semiconductor manufacturing", "taiwan semiconductor", "tsmc"),
    "WRD": ("weride", "we ride"),
}

SECURITY_PRODUCTS: dict[str, tuple[str, ...]] = {
    "000660": ("hbm", "hbm4"),
    "005930": ("galaxy", "exynos"),
    "GOOGL": ("google cloud", "android"),
    "MU": ("crucial",),
    "SNDK": ("high bandwidth flash", "hbf"),
    "TSM": ("cowos",),
}


def _json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _country(exchange: str | None, ticker: str) -> str:
    if ticker.isdigit() or (exchange or "").upper() in {"KRX", "KOSPI", "KOSDAQ"}:
        return "KR"
    return "US"


def _issuer_type(
    item: WatchlistItem | None,
    ticker: str,
    existing: SecurityMaster | None = None,
) -> str:
    if item and item.issuer_type:
        return item.issuer_type
    if existing and existing.issuer_type != "unknown":
        return existing.issuer_type
    return "krx" if ticker.isdigit() else "domestic_us"


class SecurityMasterService:
    def ensure(self, session: Session, ticker: str) -> SecurityMaster:
        ticker = ticker.upper()
        existing = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == ticker)
        ).first()
        company = session.exec(select(Company).where(Company.ticker == ticker)).first()
        item = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == ticker)
        ).first()
        company_name = (
            (company.company_name if company else None)
            or (item.company_name if item else None)
            or COMPANY_NAME_ALIASES.get(ticker)
            or ticker
        )
        exchange = (company.exchange if company else None) or (item.exchange if item else None)
        country = _country(exchange, ticker)
        aliases = list(dict.fromkeys((company_name.lower(), *SECURITY_ALIASES.get(ticker, ()))))
        search_aliases = [
            alias
            for alias in aliases
            if len(alias) > 3 or not alias.isascii() or " " in alias
        ]
        if company_name.lower() not in search_aliases:
            search_aliases.insert(0, company_name.lower())
        company_key = re.sub(r"[^a-z0-9가-힣]+", "-", company_name.lower()).strip("-")
        company_id = hashlib.sha256(f"{country}:{company_key}".encode()).hexdigest()[:20]
        security_id = hashlib.sha256(
            f"{exchange or country}:{ticker}".encode()
        ).hexdigest()[:20]
        row = existing or SecurityMaster(
            canonical_company_id=company_id,
            canonical_security_id=security_id,
            ticker=ticker,
            company_name=company_name,
        )
        row.company_name = company_name
        row.legal_name = row.legal_name or company_name
        row.exchange = exchange
        row.country = country
        row.issuer_type = _issuer_type(item, ticker, existing)
        row.ordinary_share_identifier = (
            item.ordinary_share_identifier if item else row.ordinary_share_identifier
        )
        row.adr_ratio = item.adr_ratio if item else row.adr_ratio
        depositary_evidence = (
            row.issuer_type == "adr"
            or (
                row.security_type.lower().replace("-", "_").replace(" ", "_")
                in {"adr", "ads", "depositary_receipt", "depositary_security"}
                and row.issuer_type not in {"domestic_us", "krx"}
            )
            or bool(row.adr_ratio and row.ordinary_share_identifier)
        )
        row.adr_identifier = ticker if depositary_evidence else None
        row.aliases = json.dumps(aliases, ensure_ascii=False)
        row.search_aliases = json.dumps(search_aliases, ensure_ascii=False)
        row.known_products = json.dumps(
            list(SECURITY_PRODUCTS.get(ticker, ())), ensure_ascii=False
        )
        row.identity_quality = "full" if exchange and company_name != ticker else "partial"
        row.updated_at = datetime.now(timezone.utc)
        session.add(row)
        session.flush()
        return row

    def search_aliases(self, security: SecurityMaster) -> list[str]:
        aliases = _json_list(security.search_aliases)
        if not aliases:
            aliases = [security.company_name, security.legal_name or ""]
        return list(dict.fromkeys(alias.strip() for alias in aliases if alias.strip()))

    def aliases(self, security: SecurityMaster) -> list[str]:
        return list(
            dict.fromkeys(
                [
                    security.ticker.lower(),
                    security.company_name.lower(),
                    security.legal_name.lower() if security.legal_name else "",
                    *_json_list(security.aliases),
                    *_json_list(security.known_subsidiaries),
                    *_json_list(security.known_brands),
                    *_json_list(security.known_products),
                ]
            )
        )
