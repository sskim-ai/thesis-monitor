from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal, Protocol

import httpx
from sqlmodel import Session, select

from app.config import get_settings
from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.watchlist import WatchlistItem
from app.providers.opendart_corp_codes import resolve_opendart_company
from app.services.market_session import market_scope_for_security


ProfileQuality = Literal["verified", "partial", "ambiguous", "unavailable"]


@dataclass(frozen=True)
class OfficialProfile:
    ticker: str
    company_name: str
    market: str
    source: str
    official_industry_code: str
    official_industry_description: str | None
    source_as_of: str | None
    legal_name: str | None = None
    filings_url: str | None = None
    ir_url: str | None = None
    corp_code: str | None = None
    cik: str | None = None


@dataclass(frozen=True)
class NormalizedProfile:
    industry: str | None
    sector: str | None
    taxonomy_key: str | None
    quality: ProfileQuality
    classification_method: str
    reason: str | None = None


@dataclass(frozen=True)
class ProfilePopulationResult:
    ticker: str
    company_name: str
    market: str
    quality: ProfileQuality
    status: str
    source: str | None
    industry: str | None
    sector: str | None
    taxonomy_key: str | None
    reason: str | None
    provenance_path: str | None


class CompanyProfileSource(Protocol):
    async def fetch(
        self,
        item: WatchlistItem,
        security: SecurityMaster | None,
    ) -> OfficialProfile | None: ...


@dataclass(frozen=True)
class _IndustryRule:
    prefixes: tuple[str, ...]
    industry: str
    sector: str
    taxonomy_key: str | None = None


_KSIC_RULES = (
    _IndustryRule(("261",), "Semiconductors", "Technology", "semiconductor"),
    _IndustryRule(
        ("651", "652"),
        "Insurance and Reinsurance",
        "Financials",
        "insurance",
    ),
    _IndustryRule(("641",), "Banking", "Financials", "bank"),
    _IndustryRule(("41", "42"), "Construction and EPC", "Industrials", "epc"),
    _IndustryRule(
        ("491", "492", "501", "502", "511", "512", "52"),
        "Transportation and Logistics",
        "Industrials",
        "shipping",
    ),
    _IndustryRule(
        ("301", "302", "303"),
        "Automotive",
        "Consumer Discretionary",
        "automotive",
    ),
    _IndustryRule(
        ("211", "212"),
        "Biotechnology and Pharmaceuticals",
        "Health Care",
        "biotech",
    ),
    _IndustryRule(("241",), "Steel Manufacturing", "Materials", "steel_materials"),
    _IndustryRule(("264",), "Communications Equipment", "Technology"),
    _IndustryRule(("281",), "Electrical Equipment", "Industrials"),
    _IndustryRule(("313",), "Aerospace Manufacturing", "Industrials"),
)

_SIC_RULES = (
    _IndustryRule(("3674",), "Semiconductors", "Technology", "semiconductor"),
    _IndustryRule(
        ("2834", "2835", "2836"),
        "Biotechnology and Pharmaceuticals",
        "Health Care",
        "biotech",
    ),
    _IndustryRule(
        ("3711", "3713", "3714", "3715"),
        "Automotive",
        "Consumer Discretionary",
        "automotive",
    ),
    _IndustryRule(("6021", "6022", "6035", "6036"), "Banking", "Financials", "bank"),
    _IndustryRule(
        ("6311", "6321", "6331", "6351", "6361", "6399"),
        "Insurance and Reinsurance",
        "Financials",
        "insurance",
    ),
    _IndustryRule(
        ("152", "153", "154", "16", "17"),
        "Construction and EPC",
        "Industrials",
        "epc",
    ),
    _IndustryRule(
        ("401", "421", "422", "44", "45", "4731"),
        "Transportation and Logistics",
        "Industrials",
        "shipping",
    ),
    _IndustryRule(("6719",), "Holding Company", "Financials", "holding_company"),
    _IndustryRule(("3572",), "Computer Storage Devices", "Technology"),
    _IndustryRule(("3570",), "Computer and Office Equipment", "Technology"),
    _IndustryRule(("6199",), "Financial Services", "Financials"),
    _IndustryRule(("7370", "7371", "7372", "7373", "7374"), "Information Technology Services", "Technology"),
)


def _match_rule(code: str, rules: tuple[_IndustryRule, ...]) -> _IndustryRule | None:
    matches = [
        rule
        for rule in rules
        if any(code.startswith(prefix) for prefix in rule.prefixes)
    ]
    if not matches:
        return None
    return max(
        matches,
        key=lambda rule: max(
            len(prefix) for prefix in rule.prefixes if code.startswith(prefix)
        ),
    )


def normalize_official_industry(profile: OfficialProfile) -> NormalizedProfile:
    code = profile.official_industry_code.strip()
    rules = _KSIC_RULES if profile.source == "opendart_company" else _SIC_RULES
    rule = _match_rule(code, rules)
    if rule is not None:
        return NormalizedProfile(
            industry=rule.industry,
            sector=rule.sector,
            taxonomy_key=rule.taxonomy_key,
            quality="verified",
            classification_method="official_industry_code",
        )
    description = str(profile.official_industry_description or "").strip()
    if description:
        if any(
            marker in description.lower()
            for marker in ("diversified", "conglomerate", "복합기업")
        ):
            return NormalizedProfile(
                industry=description,
                sector=None,
                taxonomy_key=None,
                quality="ambiguous",
                classification_method="official_industry_description",
                reason="diversified_identity_without_dominant_segment_evidence",
            )
        return NormalizedProfile(
            industry=description,
            sector=None,
            taxonomy_key=None,
            quality="partial",
            classification_method="official_industry_description",
            reason="official_description_not_mapped_to_internal_taxonomy",
        )
    return NormalizedProfile(
        industry=None,
        sector=None,
        taxonomy_key=None,
        quality="partial",
        classification_method="official_industry_code_unmapped",
        reason="official_industry_code_not_mapped",
    )


class OpenDartCompanyProfileSource:
    name = "opendart_company"

    def __init__(self, api_key: str, *, timeout_seconds: float = 15.0) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def fetch(
        self,
        item: WatchlistItem,
        security: SecurityMaster | None,
    ) -> OfficialProfile | None:
        company = await resolve_opendart_company(self.api_key, item.ticker)
        if company is None or company.stock_code != item.ticker:
            return None
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                "https://opendart.fss.or.kr/api/company.json",
                params={"crtfc_key": self.api_key, "corp_code": company.corp_code},
            )
            response.raise_for_status()
            payload = response.json()
        if (
            payload.get("status") != "000"
            or str(payload.get("stock_code") or "") != item.ticker
        ):
            return None
        industry_code = str(payload.get("induty_code") or "").strip()
        if not industry_code:
            return None
        homepage = str(payload.get("hm_url") or "").strip()
        ir_url = str(payload.get("ir_url") or "").strip()
        return OfficialProfile(
            ticker=item.ticker,
            company_name=item.company_name,
            market="kr",
            source=self.name,
            official_industry_code=industry_code,
            official_industry_description=None,
            source_as_of=company.modify_date,
            legal_name=str(payload.get("corp_name") or company.corp_name).strip(),
            filings_url="https://dart.fss.or.kr/",
            ir_url=ir_url or homepage or None,
            corp_code=company.corp_code,
        )


class SecCompanyProfileSource:
    name = "sec_submissions"

    def __init__(self, user_agent: str, *, timeout_seconds: float = 15.0) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self._ticker_ciks: dict[str, str] | None = None

    async def _cik_map(self, client: httpx.AsyncClient) -> dict[str, str]:
        if self._ticker_ciks is None:
            response = await client.get("https://www.sec.gov/files/company_tickers.json")
            response.raise_for_status()
            payload = response.json()
            self._ticker_ciks = {
                str(item.get("ticker") or "").upper(): str(item.get("cik_str") or "").zfill(10)
                for item in payload.values()
                if isinstance(item, dict) and item.get("ticker") and item.get("cik_str")
            }
        return self._ticker_ciks

    async def fetch(
        self,
        item: WatchlistItem,
        security: SecurityMaster | None,
    ) -> OfficialProfile | None:
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            headers=headers,
        ) as client:
            ciks = await self._cik_map(client)
            cik = ciks.get(item.ticker.upper())
            if not cik:
                return None
            response = await client.get(f"https://data.sec.gov/submissions/CIK{cik}.json")
            response.raise_for_status()
            payload = response.json()
        tickers = {str(value).upper() for value in payload.get("tickers", [])}
        if item.ticker.upper() not in tickers:
            return None
        sic = str(payload.get("sic") or "").strip()
        if not sic:
            return None
        recent = payload.get("filings", {}).get("recent", {})
        filing_dates = recent.get("filingDate", []) if isinstance(recent, dict) else []
        source_as_of = str(filing_dates[0]) if filing_dates else None
        return OfficialProfile(
            ticker=item.ticker,
            company_name=item.company_name,
            market="us",
            source=self.name,
            official_industry_code=sic,
            official_industry_description=str(payload.get("sicDescription") or "").strip() or None,
            source_as_of=source_as_of,
            legal_name=str(payload.get("name") or item.company_name).strip(),
            filings_url=f"https://www.sec.gov/edgar/browse/?CIK={int(cik)}",
            cik=cik,
        )


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def profile_provenance_path(ticker: str, data_dir: str | Path | None = None) -> Path:
    safe_ticker = "".join(
        character
        for character in ticker.upper()
        if character.isalnum() or character in {"-", "_"}
    )
    root = Path(data_dir or get_settings().data_dir)
    return root / "company_profile_provenance" / f"{safe_ticker}.json"


def read_profile_provenance(
    ticker: str,
    data_dir: str | Path | None = None,
) -> dict[str, object] | None:
    path = profile_provenance_path(ticker, data_dir)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


class CompanyProfilePopulationService:
    def __init__(
        self,
        *,
        kr_source: CompanyProfileSource | None = None,
        us_source: CompanyProfileSource | None = None,
        data_dir: str | Path | None = None,
    ) -> None:
        settings = get_settings()
        self.kr_source = kr_source or (
            OpenDartCompanyProfileSource(settings.opendart_api_key)
            if settings.opendart_api_key
            else None
        )
        self.us_source = us_source or (
            SecCompanyProfileSource(settings.sec_user_agent)
            if settings.sec_user_agent
            else None
        )
        self.data_dir = Path(data_dir or settings.data_dir)

    def active_items(self, session: Session) -> list[WatchlistItem]:
        return list(
            session.exec(
                select(WatchlistItem)
                .where(WatchlistItem.active.is_(True))
                .order_by(WatchlistItem.ticker)
            ).all()
        )

    async def populate_active(
        self,
        session: Session,
        *,
        verified_at: datetime | None = None,
        dry_run: bool = False,
    ) -> list[ProfilePopulationResult]:
        current = (verified_at or datetime.now(UTC)).astimezone(UTC)
        results: list[ProfilePopulationResult] = []
        for item in self.active_items(session):
            security = session.exec(
                select(SecurityMaster).where(SecurityMaster.ticker == item.ticker)
            ).first()
            market = market_scope_for_security(
                item.ticker,
                item.exchange or (security.exchange if security else None),
            )
            source = (
                self.kr_source
                if market == "kr"
                else self.us_source
                if market == "us"
                else None
            )
            company = session.exec(select(Company).where(Company.ticker == item.ticker)).first()
            existing_populated = bool(
                company
                and any(
                    value
                    for value in (
                        company.industry,
                        company.sector,
                        company.business_units,
                        company.revenue_sources,
                    )
                )
            )
            official: OfficialProfile | None = None
            reason: str | None = None
            if source is None:
                reason = "official_profile_source_not_configured"
            else:
                try:
                    official = await source.fetch(item, security)
                except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
                    reason = f"official_profile_fetch_failed:{type(exc).__name__}"
            if official is None:
                quality: ProfileQuality = "partial" if existing_populated else "unavailable"
                payload = {
                    "schema_version": "1",
                    "ticker": item.ticker,
                    "company_name": item.company_name,
                    "market": market,
                    "quality": quality,
                    "source": None,
                    "source_as_of": None,
                    "verified_at": current.isoformat(),
                    "classification_method": "preserved_existing" if existing_populated else "unavailable",
                    "reason": reason or "official_profile_unavailable",
                    "industry": company.industry if company else None,
                    "sector": company.sector if company else None,
                    "business_units": company.business_units if company else None,
                    "revenue_sources": company.revenue_sources if company else None,
                    "taxonomy_key": None,
                }
                path = profile_provenance_path(item.ticker, self.data_dir)
                if not dry_run:
                    _atomic_json(path, payload)
                results.append(
                    ProfilePopulationResult(
                        ticker=item.ticker,
                        company_name=item.company_name,
                        market=market,
                        quality=quality,
                        status="preserved" if existing_populated else "unavailable",
                        source=None,
                        industry=company.industry if company else None,
                        sector=company.sector if company else None,
                        taxonomy_key=None,
                    reason=str(payload["reason"]),
                        provenance_path=str(path) if not dry_run else None,
                    )
                )
                continue

            normalized = normalize_official_industry(official)
            row = company or Company(
                ticker=item.ticker,
                company_name=item.company_name,
                exchange=item.exchange,
            )
            if normalized.industry:
                row.industry = normalized.industry
            if normalized.sector:
                row.sector = normalized.sector
            row.ir_url = row.ir_url or official.ir_url
            row.filings_url = row.filings_url or official.filings_url
            payload = {
                "schema_version": "1",
                "ticker": item.ticker,
                "company_name": item.company_name,
                "market": market,
                "quality": normalized.quality,
                "source": official.source,
                "source_as_of": official.source_as_of,
                "verified_at": current.isoformat(),
                "classification_method": normalized.classification_method,
                "reason": normalized.reason,
                "official_industry_code": official.official_industry_code,
                "official_industry_description": official.official_industry_description,
                "industry": row.industry,
                "sector": row.sector,
                "business_units": row.business_units,
                "revenue_sources": row.revenue_sources,
                "taxonomy_key": normalized.taxonomy_key,
            }
            path = profile_provenance_path(item.ticker, self.data_dir)
            if not dry_run:
                session.add(row)
                if security is not None:
                    security.legal_name = official.legal_name or security.legal_name
                    security.cik = official.cik or security.cik
                    security.corp_code = official.corp_code or security.corp_code
                    session.add(security)
                _atomic_json(path, payload)
            results.append(
                ProfilePopulationResult(
                    ticker=item.ticker,
                    company_name=item.company_name,
                    market=market,
                    quality=normalized.quality,
                    status="populated" if normalized.industry or normalized.sector else "partial",
                    source=official.source,
                    industry=row.industry,
                    sector=row.sector,
                    taxonomy_key=normalized.taxonomy_key,
                    reason=normalized.reason,
                    provenance_path=str(path) if not dry_run else None,
                )
            )
        if not dry_run:
            session.commit()
        return results


def profile_population_summary(results: list[ProfilePopulationResult]) -> dict[str, object]:
    qualities = {quality: 0 for quality in ("verified", "partial", "ambiguous", "unavailable")}
    markets: dict[str, int] = {}
    for item in results:
        qualities[item.quality] += 1
        markets[item.market] = markets.get(item.market, 0) + 1
    return {
        "active_total": len(results),
        "markets": markets,
        "qualities": qualities,
        "populated": sum(item.status == "populated" for item in results),
        "specialized_taxonomy": sum(item.taxonomy_key is not None for item in results),
        "items": [asdict(item) for item in results],
    }


def company_profile_coverage(session: Session, data_dir: str | Path | None = None) -> dict[str, object]:
    service = CompanyProfilePopulationService(data_dir=data_dir)
    items: list[dict[str, object]] = []
    for watchlist_item in service.active_items(session):
        company = session.exec(
            select(Company).where(Company.ticker == watchlist_item.ticker)
        ).first()
        provenance = read_profile_provenance(watchlist_item.ticker, service.data_dir)
        quality = str((provenance or {}).get("quality") or "missing")
        reason = str((provenance or {}).get("reason") or "").strip() or None
        has_identity = bool(
            company
            and any(
                value
                for value in (
                    company.industry,
                    company.sector,
                    company.business_units,
                    company.revenue_sources,
                )
            )
        )
        complete = bool(
            provenance
            and quality in {"verified", "partial", "ambiguous"}
            and (has_identity or reason)
        )
        items.append(
            {
                "ticker": watchlist_item.ticker,
                "quality": quality,
                "has_structured_identity": has_identity,
                "reason": reason,
                "complete": complete,
            }
        )
    return {
        "active_total": len(items),
        "complete_count": sum(item["complete"] is True for item in items),
        "missing_count": sum(item["quality"] == "missing" for item in items),
        "unavailable_count": sum(
            item["quality"] == "unavailable" for item in items
        ),
        "ready": all(item["complete"] is True for item in items),
        "items": items,
    }
