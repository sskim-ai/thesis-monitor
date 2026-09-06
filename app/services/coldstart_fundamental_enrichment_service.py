from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.models.watchlist import WatchlistItem
from app.services.coldstart_source_assembly_service import (
    SourceAssemblyResult,
    SourceAssemblyStatus,
    canonical_sha256,
)
from app.services.company_profile_service import (
    OpenDartCompanyProfileSource,
    OfficialProfile,
    SecCompanyProfileSource,
    normalize_official_industry,
)
from app.services.opendart_financial_recovery_service import (
    OpenDartRecoveryClient,
    promote_recovered_fields,
)
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from app.utils.tickers import normalize_ticker


CONTRACT_VERSION = "official-fundamental-enrichment-v1"
EVIDENCE_FAMILY_CONTRACT = "fundamental-evidence-family-v1"
SOURCE_SUFFICIENCY_CONTRACT = "pre-model-source-sufficiency-v1"
PACKET_CONTRACT = "fundamental-enriched-coldstart-packet-v1"

_US_BANK_SECTOR_CONCEPT_GROUPS = (
    ("InterestIncomeExpenseNet",),
    ("NoninterestIncome",),
)
_US_INSURANCE_SECTOR_CONCEPT_GROUPS = (
    (
        "LiabilityForFuturePolicyBenefits",
        "PolicyholderBenefitsAndClaimsPayableCurrent",
        "PolicyholderBenefitsAndClaimsPayable",
    ),
)


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class FundamentalEvidenceFamily(StrEnum):
    IDENTITY_SECURITY = "IDENTITY_SECURITY"
    BUSINESS_CURRENT = "BUSINESS_CURRENT"
    EARNINGS_FINANCIAL_CURRENT = "EARNINGS_FINANCIAL_CURRENT"
    LIQUIDITY_CASHFLOW_CURRENT = "LIQUIDITY_CASHFLOW_CURRENT"
    SECTOR_OPERATING_CURRENT = "SECTOR_OPERATING_CURRENT"
    REGULATORY_CAPITAL_CURRENT = "REGULATORY_CAPITAL_CURRENT"
    CLINICAL_REGULATORY_CURRENT = "CLINICAL_REGULATORY_CURRENT"
    CAPITAL_ALLOCATION_CURRENT = "CAPITAL_ALLOCATION_CURRENT"
    VALUATION_SAFE = "VALUATION_SAFE"
    PRICE_CONTEXT = "PRICE_CONTEXT"
    MARKET_CONTEXT = "MARKET_CONTEXT"


class FundamentalEvidenceQuality(StrEnum):
    CURRENT = "current"
    PARTIAL = "partial"
    STALE = "stale"
    REFRESH_DUE = "refresh_due"
    VALIDATION_FAILED = "validation_failed"
    UNAVAILABLE = "unavailable"
    CONFLICTING = "conflicting"


class AnalysisFramework(StrEnum):
    STANDARD_OPERATING = "standard_operating_company"
    BANK_INSURER = "bank_or_insurer"
    PRE_PROFIT_BIOTECH = "pre_profit_biotech"
    ASSET_HEAVY_CYCLICAL = "asset_heavy_or_cyclical"


class SourceSufficiencyStatus(StrEnum):
    SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT = "SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT"
    SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY = "SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY"
    INSUFFICIENT_FUNDAMENTAL_EVIDENCE = "INSUFFICIENT_FUNDAMENTAL_EVIDENCE"
    SECURITY_OR_ACCOUNTING_BASIS_BLOCK = "SECURITY_OR_ACCOUNTING_BASIS_BLOCK"
    SOURCE_FRESHNESS_BLOCK = "SOURCE_FRESHNESS_BLOCK"


class SourceSufficiencyResult(FrozenModel):
    contract: str = SOURCE_SUFFICIENCY_CONTRACT
    status: SourceSufficiencyStatus
    framework: AnalysisFramework
    directional_model_eligible: bool
    valid_families: tuple[FundamentalEvidenceFamily, ...] = ()
    stale_families: tuple[FundamentalEvidenceFamily, ...] = ()
    invalid_families: tuple[FundamentalEvidenceFamily, ...] = ()
    missing_required_families: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    price_direction_inputs_used: Literal[0] = 0
    hidden_weighted_score_used: Literal[0] = 0


class OfficialFundamentalEnrichment(FrozenModel):
    contract: str = CONTRACT_VERSION
    ticker: str
    market: Literal["kr", "us"]
    issuer_id: str | None = None
    official_profile: dict[str, object] = Field(default_factory=dict)
    analysis_framework: AnalysisFramework
    facts: tuple[dict[str, object], ...] = ()
    source_attempts: tuple[dict[str, object], ...] = ()
    source_quality: FundamentalEvidenceQuality
    errors: tuple[str, ...] = ()
    provider_audit: dict[str, object] = Field(default_factory=dict)
    source_payload_sha256: str | None = None
    production_db_mutation: Literal[0] = 0
    monitoring_registration: Literal[0] = 0
    ai_judgment_calls: Literal[0] = 0


class EnrichedSourceAssemblyResult(FrozenModel):
    contract: str = PACKET_CONTRACT
    ticker: str
    market: Literal["kr", "us"]
    status: SourceSufficiencyStatus
    packet: dict[str, object] | None = None
    packet_sha256: str | None = None
    deterministic_base_context: str | None = None
    deterministic_base_context_sha256: str | None = None
    enrichment: OfficialFundamentalEnrichment
    source_sufficiency: SourceSufficiencyResult
    validation_errors: tuple[str, ...] = ()
    provider_audit: dict[str, object] = Field(default_factory=dict)
    production_db_mutation: Literal[0] = 0
    monitoring_registration: Literal[0] = 0
    ai_judgment_calls: Literal[0] = 0


def _as_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fact_id(ticker: str, family: FundamentalEvidenceFamily, source: object) -> str:
    digest = canonical_sha256(source)[:20]
    return f"fundamental:{ticker}:{family.value.lower()}:{digest}"


def _framework_text(*values: object) -> str:
    return " ".join(str(value or "") for value in values).lower()


def classify_analysis_framework(
    *, taxonomy_key: str | None, sector: str | None, industry: str | None
) -> AnalysisFramework:
    text = _framework_text(taxonomy_key, sector, industry)
    if any(token in text for token in ("bank", "insurance", "은행", "보험", "재보험")):
        return AnalysisFramework.BANK_INSURER
    if any(
        token in text
        for token in ("biotech", "biopharma", "pharmaceutical", "바이오", "신약")
    ):
        return AnalysisFramework.PRE_PROFIT_BIOTECH
    if any(
        token in text
        for token in (
            "semiconductor",
            "steel",
            "materials",
            "automotive",
            "construction",
            "transport",
            "shipping",
            "반도체",
            "철강",
            "소재",
            "자동차",
            "건설",
            "운송",
            "해운",
        )
    ):
        return AnalysisFramework.ASSET_HEAVY_CYCLICAL
    return AnalysisFramework.STANDARD_OPERATING


def resolve_financial_lifecycle_framework(
    framework: AnalysisFramework,
    *,
    revenue: object,
    earnings_values: Sequence[object],
) -> AnalysisFramework:
    if framework != AnalysisFramework.PRE_PROFIT_BIOTECH:
        return framework
    valid_earnings = [
        float(value) for value in earnings_values if isinstance(value, (int, float))
    ]
    if isinstance(revenue, (int, float)) and revenue > 0 and any(
        value > 0 for value in valid_earnings
    ):
        return AnalysisFramework.STANDARD_OPERATING
    return framework


def _family_quality(row: Mapping[str, object]) -> FundamentalEvidenceQuality:
    try:
        return FundamentalEvidenceQuality(str(row.get("evidence_quality") or ""))
    except ValueError:
        return FundamentalEvidenceQuality.UNAVAILABLE


def evaluate_source_sufficiency(
    facts: Sequence[Mapping[str, object]],
    *,
    framework: AnalysisFramework,
    identity_hard_valid: bool = True,
    accounting_basis_hard_valid: bool = True,
) -> SourceSufficiencyResult:
    if not identity_hard_valid or not accounting_basis_hard_valid:
        return SourceSufficiencyResult(
            status=SourceSufficiencyStatus.SECURITY_OR_ACCOUNTING_BASIS_BLOCK,
            framework=framework,
            directional_model_eligible=False,
            reasons=(
                "identity_security_basis_invalid"
                if not identity_hard_valid
                else "accounting_basis_invalid",
            ),
        )

    current: set[FundamentalEvidenceFamily] = set()
    stale: set[FundamentalEvidenceFamily] = set()
    invalid: set[FundamentalEvidenceFamily] = set()
    for row in facts:
        try:
            family = FundamentalEvidenceFamily(str(row.get("evidence_family") or ""))
        except ValueError:
            continue
        quality = _family_quality(row)
        if quality == FundamentalEvidenceQuality.CURRENT:
            current.add(family)
        elif quality in {
            FundamentalEvidenceQuality.STALE,
            FundamentalEvidenceQuality.REFRESH_DUE,
        }:
            stale.add(family)
        elif quality in {
            FundamentalEvidenceQuality.VALIDATION_FAILED,
            FundamentalEvidenceQuality.CONFLICTING,
        }:
            invalid.add(family)

    if FundamentalEvidenceFamily.IDENTITY_SECURITY not in current:
        return SourceSufficiencyResult(
            status=SourceSufficiencyStatus.SECURITY_OR_ACCOUNTING_BASIS_BLOCK,
            framework=framework,
            directional_model_eligible=False,
            valid_families=tuple(sorted(current, key=str)),
            stale_families=tuple(sorted(stale, key=str)),
            invalid_families=tuple(sorted(invalid, key=str)),
            missing_required_families=(FundamentalEvidenceFamily.IDENTITY_SECURITY.value,),
            reasons=("current_identity_security_evidence_missing",),
        )

    if framework == AnalysisFramework.BANK_INSURER:
        required_groups = (
            (FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT,),
            (
                FundamentalEvidenceFamily.REGULATORY_CAPITAL_CURRENT,
                FundamentalEvidenceFamily.SECTOR_OPERATING_CURRENT,
            ),
        )
    elif framework == AnalysisFramework.PRE_PROFIT_BIOTECH:
        required_groups = (
            (FundamentalEvidenceFamily.CLINICAL_REGULATORY_CURRENT,),
            (FundamentalEvidenceFamily.LIQUIDITY_CASHFLOW_CURRENT,),
        )
    else:
        required_groups = (
            (
                FundamentalEvidenceFamily.BUSINESS_CURRENT,
                FundamentalEvidenceFamily.SECTOR_OPERATING_CURRENT,
            ),
            (
                FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT,
                FundamentalEvidenceFamily.LIQUIDITY_CASHFLOW_CURRENT,
                FundamentalEvidenceFamily.SECTOR_OPERATING_CURRENT,
            ),
        )

    missing_groups = [group for group in required_groups if not current.intersection(group)]
    if not missing_groups:
        return SourceSufficiencyResult(
            status=SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT,
            framework=framework,
            directional_model_eligible=True,
            valid_families=tuple(sorted(current, key=str)),
            stale_families=tuple(sorted(stale, key=str)),
            invalid_families=tuple(sorted(invalid, key=str)),
            reasons=("framework_required_current_evidence_present",),
        )

    missing = tuple("OR".join(item.value for item in group) for group in missing_groups)
    required_flat = {family for group in required_groups for family in group}
    if not current.intersection(required_flat) and stale.intersection(required_flat):
        status = SourceSufficiencyStatus.SOURCE_FRESHNESS_BLOCK
        reasons = ("required_fundamental_evidence_is_stale_or_refresh_due",)
    elif current.intersection(required_flat):
        status = SourceSufficiencyStatus.SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY
        reasons = ("only_one_required_framework_evidence_side_is_current",)
    else:
        status = SourceSufficiencyStatus.INSUFFICIENT_FUNDAMENTAL_EVIDENCE
        reasons = (
            "no_current_issuer_fundamental_anchor",
            "price_and_technical_context_do_not_satisfy_fundamental_gate",
        )
    return SourceSufficiencyResult(
        status=status,
        framework=framework,
        directional_model_eligible=False,
        valid_families=tuple(sorted(current, key=str)),
        stale_families=tuple(sorted(stale, key=str)),
        invalid_families=tuple(sorted(invalid, key=str)),
        missing_required_families=missing,
        reasons=reasons,
    )


def _profile_payload(profile: OfficialProfile, normalized: object) -> dict[str, object]:
    return {
        "source": profile.source,
        "legal_name": profile.legal_name,
        "official_industry_code": profile.official_industry_code,
        "official_industry_description": profile.official_industry_description,
        "source_as_of": profile.source_as_of,
        "filings_url": profile.filings_url,
        "issuer_id": profile.cik or profile.corp_code,
        "industry": getattr(normalized, "industry", None),
        "sector": getattr(normalized, "sector", None),
        "taxonomy_key": getattr(normalized, "taxonomy_key", None),
        "quality": getattr(normalized, "quality", None),
        "classification_method": getattr(normalized, "classification_method", None),
        "classification_reason": getattr(normalized, "reason", None),
    }


def _identity_family_fact(
    ticker: str, profile: OfficialProfile, profile_payload: Mapping[str, object]
) -> dict[str, object]:
    source = {
        "ticker": ticker,
        "issuer_id": profile.cik or profile.corp_code,
        "profile": profile_payload,
    }
    return {
        "contract": EVIDENCE_FAMILY_CONTRACT,
        "fact_id": _fact_id(ticker, FundamentalEvidenceFamily.IDENTITY_SECURITY, source),
        "fact_type": "official_security_identity",
        "evidence_family": FundamentalEvidenceFamily.IDENTITY_SECURITY.value,
        "evidence_quality": FundamentalEvidenceQuality.CURRENT.value,
        "as_of_date": profile.source_as_of,
        "source": profile.source,
        "source_owned": True,
        "issuer_specific": True,
        "fields": source,
        "numeric_registry_eligible": False,
    }


def _official_fact(
    *,
    ticker: str,
    family: FundamentalEvidenceFamily,
    fact_type: str,
    as_of_date: str,
    source: str,
    source_document_id: str,
    source_payload_sha256: str,
    fields: Mapping[str, object],
) -> dict[str, object]:
    identity = {
        "ticker": ticker,
        "family": family,
        "fact_type": fact_type,
        "as_of_date": as_of_date,
        "source": source,
        "source_document_id": source_document_id,
        "fields": fields,
        "source_payload_sha256": source_payload_sha256,
    }
    return {
        "contract": EVIDENCE_FAMILY_CONTRACT,
        "fact_id": _fact_id(ticker, family, identity),
        "fact_type": fact_type,
        "evidence_family": family.value,
        "evidence_quality": FundamentalEvidenceQuality.CURRENT.value,
        "as_of_date": as_of_date,
        "source": source,
        "source_document_id": source_document_id,
        "source_payload_sha256": source_payload_sha256,
        "source_owned": True,
        "issuer_specific": True,
        "fields": dict(fields),
        "numeric_registry_eligible": False,
    }


def _bank_insurer_subframework(
    profile_payload: Mapping[str, object],
) -> Literal["bank", "insurance"] | None:
    text = _framework_text(
        profile_payload.get("taxonomy_key"),
        profile_payload.get("sector"),
        profile_payload.get("industry"),
        profile_payload.get("official_industry_description"),
    )
    if any(token in text for token in ("bank", "은행")):
        return "bank"
    if any(token in text for token in ("insurance", "insurer", "보험", "재보험")):
        return "insurance"
    return None


def _sec_current_occurrence(
    payload: Mapping[str, object],
    *,
    concept: str,
    filing_date: date,
    period_end: date,
    fiscal_year: int,
    fiscal_period: str,
    period_scope: str,
) -> dict[str, object] | None:
    facts = payload.get("facts")
    if not isinstance(facts, Mapping):
        return None
    taxonomy = facts.get("us-gaap")
    if not isinstance(taxonomy, Mapping):
        return None
    raw = taxonomy.get(concept)
    if not isinstance(raw, Mapping):
        return None
    units = raw.get("units")
    if not isinstance(units, Mapping):
        return None

    candidates: list[dict[str, object]] = []
    for unit, entries in units.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            if (
                _as_date(entry.get("filed")) != filing_date
                or _as_date(entry.get("end")) != period_end
                or entry.get("fy") != fiscal_year
                or str(entry.get("fp") or "") != fiscal_period
                or str(entry.get("form") or "") not in {"10-Q", "10-K"}
                or not isinstance(entry.get("val"), (int, float))
                or not entry.get("accn")
            ):
                continue
            start = _as_date(entry.get("start"))
            duration_days = (period_end - start).days if start is not None else None
            candidates.append(
                {
                    "taxonomy": "us-gaap",
                    "concept": concept,
                    "label": raw.get("label"),
                    "value": entry.get("val"),
                    "unit": str(unit),
                    "period_start": start,
                    "period_end": period_end,
                    "duration_days": duration_days,
                    "filing_date": filing_date,
                    "fiscal_year": fiscal_year,
                    "fiscal_period": fiscal_period,
                    "form": entry.get("form"),
                    "accession_number": entry.get("accn"),
                    "frame": entry.get("frame"),
                }
            )
    if not candidates:
        return None

    instant = [row for row in candidates if row["duration_days"] is None]
    if instant:
        unique = {(row["unit"], row["value"]) for row in instant}
        return instant[0] if len(unique) == 1 else None

    if fiscal_period == "FY":
        if period_scope != "annual":
            return None
        expected = [
            row
            for row in candidates
            if isinstance(row["duration_days"], int) and row["duration_days"] >= 300
        ]
        target_duration = max(
            (int(row["duration_days"]) for row in expected), default=None
        )
    else:
        expected = [
            row
            for row in candidates
            if isinstance(row["duration_days"], int) and row["duration_days"] <= 130
        ]
        target_duration = min(
            (int(row["duration_days"]) for row in expected), default=None
        )
    if target_duration is None:
        return None
    selected = [row for row in expected if row["duration_days"] == target_duration]
    unique = {(row["unit"], row["value"]) for row in selected}
    return selected[0] if len(unique) == 1 else None


def us_bank_insurer_sector_fact(
    *,
    ticker: str,
    payload: Mapping[str, object],
    profile_payload: Mapping[str, object],
    financial_row: object,
    source_payload_sha256: str,
) -> dict[str, object] | None:
    subframework = _bank_insurer_subframework(profile_payload)
    if subframework is None:
        return None
    filing_date = getattr(financial_row, "filing_date", None)
    period_end = getattr(financial_row, "financial_period_end", None)
    fiscal_year = getattr(financial_row, "fiscal_year", None)
    period = str(getattr(financial_row, "period", "") or "")
    fiscal_period = period.rsplit("-", 1)[-1]
    period_scope = str(getattr(financial_row, "period_scope", "") or "")
    if (
        not isinstance(filing_date, date)
        or not isinstance(period_end, date)
        or not isinstance(fiscal_year, int)
        or fiscal_period not in {"Q1", "Q2", "Q3", "FY"}
    ):
        return None
    concept_groups = (
        _US_BANK_SECTOR_CONCEPT_GROUPS
        if subframework == "bank"
        else _US_INSURANCE_SECTOR_CONCEPT_GROUPS
    )
    metrics: list[dict[str, object]] = []
    for group in concept_groups:
        selected = next(
            (
                occurrence
                for concept in group
                if (
                    occurrence := _sec_current_occurrence(
                        payload,
                        concept=concept,
                        filing_date=filing_date,
                        period_end=period_end,
                        fiscal_year=fiscal_year,
                        fiscal_period=fiscal_period,
                        period_scope=period_scope,
                    )
                )
                is not None
            ),
            None,
        )
        if selected is None:
            return None
        metrics.append(selected)
    source_document_id = (
        f"SEC-COMPANYFACTS:{getattr(financial_row, 'ticker', ticker)}:"
        f"{filing_date.isoformat()}:{period}"
    )
    return _official_fact(
        ticker=ticker,
        family=FundamentalEvidenceFamily.SECTOR_OPERATING_CURRENT,
        fact_type="official_current_sector_operating",
        as_of_date=filing_date.isoformat(),
        source="sec_edgar_companyfacts",
        source_document_id=source_document_id,
        source_payload_sha256=source_payload_sha256,
        fields={
            "subframework": subframework,
            "period": period,
            "period_scope": period_scope,
            "period_end": period_end,
            "filing_date": filing_date,
            "entity_scope": "issuer_level",
            "statement_basis": "issuer_reported_entity_wide",
            "security_basis": "issuer_not_per_share",
            "formal_filing": True,
            "metrics": metrics,
        },
    )


class OfficialFundamentalEnricher:
    def __init__(
        self,
        cache_dir: Path,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.transport = transport
        self.settings = get_settings()
        self._sec_profile = SecCompanyProfileSource(self.settings.sec_user_agent or "")
        self._dart_profile = OpenDartCompanyProfileSource(
            self.settings.opendart_api_key or ""
        )

    async def enrich(
        self,
        *,
        ticker: str,
        company_name: str,
        exchange: str,
        sector: str,
        industry: str,
        as_of: datetime,
    ) -> OfficialFundamentalEnrichment:
        normalized = normalize_ticker(ticker)
        market: Literal["kr", "us"] = "kr" if normalized.isdigit() else "us"
        item = WatchlistItem(
            ticker=normalized,
            company_name=company_name,
            exchange=exchange,
            active=False,
            monitoring_requested=False,
            production_eligible=False,
        )
        try:
            profile = await (
                self._dart_profile.fetch(item, None)
                if market == "kr"
                else self._sec_profile.fetch(item, None)
            )
        except (httpx.HTTPError, TypeError, ValueError) as exc:
            return OfficialFundamentalEnrichment(
                ticker=normalized,
                market=market,
                analysis_framework=classify_analysis_framework(
                    taxonomy_key=None, sector=sector, industry=industry
                ),
                source_quality=FundamentalEvidenceQuality.UNAVAILABLE,
                source_attempts=(
                    {"source": "official_profile", "status": "failed", "error": type(exc).__name__},
                ),
                errors=(f"official_profile:{type(exc).__name__}",),
                provider_audit={"profile_requests": 1, "profile_successes": 0},
            )
        if profile is None:
            return OfficialFundamentalEnrichment(
                ticker=normalized,
                market=market,
                analysis_framework=classify_analysis_framework(
                    taxonomy_key=None, sector=sector, industry=industry
                ),
                source_quality=FundamentalEvidenceQuality.UNAVAILABLE,
                source_attempts=(
                    {"source": "official_profile", "status": "unavailable"},
                ),
                errors=("official_profile_unavailable",),
                provider_audit={"profile_requests": 1, "profile_successes": 0},
            )
        profile_classification = normalize_official_industry(profile)
        profile_payload = _profile_payload(profile, profile_classification)
        framework = classify_analysis_framework(
            taxonomy_key=profile_classification.taxonomy_key,
            sector=profile_classification.sector or sector,
            industry=profile_classification.industry or industry,
        )
        if market == "us":
            return await self._enrich_us(
                item=item,
                profile=profile,
                profile_payload=profile_payload,
                framework=framework,
                as_of=as_of,
            )
        return await self._enrich_kr(
            item=item,
            profile=profile,
            profile_payload=profile_payload,
            framework=framework,
            as_of=as_of,
        )

    async def _enrich_us(
        self,
        *,
        item: WatchlistItem,
        profile: OfficialProfile,
        profile_payload: Mapping[str, object],
        framework: AnalysisFramework,
        as_of: datetime,
    ) -> OfficialFundamentalEnrichment:
        if not profile.cik:
            raise ValueError("sec_cik_required")
        path = self.cache_dir / "sec_companyfacts" / f"{item.ticker}.json"
        cache_hit = path.exists()
        if cache_hit:
            payload_bytes = path.read_bytes()
        else:
            headers = {
                "User-Agent": self.settings.sec_user_agent or "thesis-monitor research",
                "Accept": "application/json",
            }
            async with httpx.AsyncClient(
                timeout=20.0, headers=headers, transport=self.transport
            ) as client:
                response = await client.get(
                    f"https://data.sec.gov/api/xbrl/companyfacts/CIK{profile.cik}.json"
                )
                response.raise_for_status()
                payload_bytes = response.content
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload_bytes)
        source_sha = _sha256_bytes(payload_bytes)
        try:
            payload = json.loads(payload_bytes)
        except json.JSONDecodeError as exc:
            return OfficialFundamentalEnrichment(
                ticker=item.ticker,
                market="us",
                issuer_id=profile.cik,
                official_profile=dict(profile_payload),
                analysis_framework=framework,
                facts=(_identity_family_fact(item.ticker, profile, profile_payload),),
                source_quality=FundamentalEvidenceQuality.VALIDATION_FAILED,
                source_attempts=(
                    {"source": "sec_companyfacts", "status": "validation_failed"},
                ),
                errors=(f"sec_companyfacts:{type(exc).__name__}",),
                provider_audit={
                    "profile_requests": 1,
                    "profile_successes": 1,
                    "companyfacts_requests": 0 if cache_hit else 1,
                    "companyfacts_successes": 0,
                    "cache_hits": int(cache_hit),
                },
                source_payload_sha256=source_sha,
            )
        rows = [
            row
            for row in _companyfacts_snapshots(payload, item.ticker)
            if row.filing_date is not None
            and row.filing_date <= as_of.astimezone(UTC).date()
            and row.currency is not None
        ]
        rows.sort(
            key=lambda row: (
                row.filing_date or date.min,
                row.financial_period_end or date.min,
                row.fiscal_year or 0,
            ),
            reverse=True,
        )
        row = next(
            (
                candidate
                for candidate in rows
                if candidate.revenue is not None
                and any(
                    value is not None
                    for value in (
                        candidate.net_income,
                        candidate.owners_parent_net_income,
                        candidate.common_net_income,
                        candidate.diluted_eps,
                    )
                )
            ),
            None,
        )
        framework = resolve_financial_lifecycle_framework(
            framework,
            revenue=row.revenue if row is not None else None,
            earnings_values=(
                row.net_income if row is not None else None,
                row.owners_parent_net_income if row is not None else None,
                row.common_net_income if row is not None else None,
            ),
        )
        facts: list[dict[str, object]] = [
            _identity_family_fact(item.ticker, profile, profile_payload)
        ]
        errors: list[str] = []
        quality = FundamentalEvidenceQuality.UNAVAILABLE
        if row is not None and row.filing_date is not None:
            document_id = (
                f"SEC-COMPANYFACTS:{profile.cik}:{row.filing_date.isoformat()}:{row.period}"
            )
            common = {
                "period": row.period,
                "period_type": row.period_type,
                "period_scope": row.period_scope,
                "period_end": row.financial_period_end,
                "filing_date": row.filing_date,
                "currency": row.currency,
                "unit_scale": 1,
                "entity_scope": "issuer_level",
                "statement_basis": "issuer_reported_entity_wide",
                "security_basis": "issuer_not_per_share",
                "formal_filing": True,
            }
            facts.append(
                _official_fact(
                    ticker=item.ticker,
                    family=FundamentalEvidenceFamily.BUSINESS_CURRENT,
                    fact_type="official_current_business_revenue",
                    as_of_date=row.filing_date.isoformat(),
                    source="sec_edgar_companyfacts",
                    source_document_id=document_id,
                    source_payload_sha256=source_sha,
                    fields={**common, "reported_revenue": row.revenue},
                )
            )
            earnings = {
                key: value
                for key, value in {
                    "reported_net_income": row.net_income,
                    "reported_owners_parent_net_income": row.owners_parent_net_income,
                    "reported_common_net_income": row.common_net_income,
                    "reported_diluted_eps": row.diluted_eps,
                }.items()
                if value is not None
            }
            facts.append(
                _official_fact(
                    ticker=item.ticker,
                    family=FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT,
                    fact_type="official_current_earnings_financial",
                    as_of_date=row.filing_date.isoformat(),
                    source="sec_edgar_companyfacts",
                    source_document_id=document_id,
                    source_payload_sha256=source_sha,
                    fields={**common, **earnings},
                )
            )
            if framework == AnalysisFramework.BANK_INSURER:
                sector_fact = us_bank_insurer_sector_fact(
                    ticker=item.ticker,
                    payload=payload,
                    profile_payload=profile_payload,
                    financial_row=row,
                    source_payload_sha256=source_sha,
                )
                if sector_fact is not None:
                    facts.append(sector_fact)
            quality = FundamentalEvidenceQuality.CURRENT
        else:
            errors.append("validated_current_sec_financial_occurrence_unavailable")
        return OfficialFundamentalEnrichment(
            ticker=item.ticker,
            market="us",
            issuer_id=profile.cik,
            official_profile=dict(profile_payload),
            analysis_framework=framework,
            facts=tuple(facts),
            source_quality=quality,
            source_attempts=(
                {
                    "source": "sec_submissions",
                    "status": "success",
                    "issuer_id": profile.cik,
                },
                {
                    "source": "sec_companyfacts",
                    "status": "success" if row is not None else "unavailable",
                    "cache_hit": cache_hit,
                },
            ),
            errors=tuple(errors),
            provider_audit={
                "profile_requests": 1,
                "profile_successes": 1,
                "companyfacts_requests": 0 if cache_hit else 1,
                "companyfacts_successes": int(row is not None),
                "cache_hits": int(cache_hit),
            },
            source_payload_sha256=source_sha,
        )

    async def _enrich_kr(
        self,
        *,
        item: WatchlistItem,
        profile: OfficialProfile,
        profile_payload: Mapping[str, object],
        framework: AnalysisFramework,
        as_of: datetime,
    ) -> OfficialFundamentalEnrichment:
        if not profile.corp_code or not self.settings.opendart_api_key:
            raise ValueError("opendart_corp_code_and_api_key_required")
        client = OpenDartRecoveryClient(
            self.settings.opendart_api_key,
            self.cache_dir / "opendart",
            transport=self.transport,
        )
        cutoff = as_of.astimezone(UTC).date()
        selected, _history = await client.discover(
            ticker=item.ticker,
            corp_code=profile.corp_code,
            begin=cutoff - timedelta(days=550),
            end=cutoff,
            limit=1,
        )
        facts: list[dict[str, object]] = [
            _identity_family_fact(item.ticker, profile, profile_payload)
        ]
        if not selected:
            return OfficialFundamentalEnrichment(
                ticker=item.ticker,
                market="kr",
                issuer_id=profile.corp_code,
                official_profile=dict(profile_payload),
                analysis_framework=framework,
                facts=tuple(facts),
                source_quality=FundamentalEvidenceQuality.UNAVAILABLE,
                source_attempts=(
                    {"source": "opendart_formal_filings", "status": "unavailable"},
                ),
                errors=("opendart_formal_filing_unavailable",),
                provider_audit={
                    "profile_requests": 1,
                    "profile_successes": 1,
                    "statement_requests": client.provider_calls,
                    "statement_successes": 0,
                    "cache_hits": 0,
                },
            )
        filing = selected[0]
        statement_paths = {
            basis: self.cache_dir
            / "opendart"
            / item.ticker
            / filing.receipt_no
            / f"{basis}.json"
            for basis in ("CFS", "OFS")
        }
        statement_cache_hit = all(path.exists() for path in statement_paths.values())
        if statement_cache_hit:
            rows = {
                basis: [
                    dict(row)
                    for row in json.loads(path.read_text(encoding="utf-8")).get("rows", [])
                    if isinstance(row, Mapping)
                ]
                for basis, path in statement_paths.items()
            }
        else:
            rows = await client.statements(filing)
        recovered = promote_recovered_fields(filing, rows)
        source_payload = json.dumps(
            rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        source_sha = _sha256_bytes(source_payload)
        fields = recovered.get("fields")
        fields = fields if isinstance(fields, Mapping) else {}
        revenue = fields.get("revenue") if isinstance(fields.get("revenue"), Mapping) else {}
        operating = (
            fields.get("operating_income")
            if isinstance(fields.get("operating_income"), Mapping)
            else {}
        )
        net_income = (
            fields.get("net_income")
            if isinstance(fields.get("net_income"), Mapping)
            else {}
        )
        verified_revenue = revenue.get("status") == "verified_usable"
        verified_earnings = any(
            row.get("status") == "verified_usable" for row in (operating, net_income)
        )
        framework = resolve_financial_lifecycle_framework(
            framework,
            revenue=revenue.get("value") if verified_revenue else None,
            earnings_values=(
                operating.get("value") if operating.get("status") == "verified_usable" else None,
                net_income.get("value") if net_income.get("status") == "verified_usable" else None,
            ),
        )
        lineage = revenue.get("lineage") if isinstance(revenue.get("lineage"), Mapping) else {}
        common = {
            "period_type": lineage.get("amount_period_type"),
            "period_start": lineage.get("amount_period_start"),
            "period_end": lineage.get("amount_period_end"),
            "filing_date": filing.receipt_date,
            "currency": lineage.get("currency"),
            "unit_scale": 1,
            "entity_scope": "issuer_level",
            "statement_basis": lineage.get("statement_basis"),
            "security_basis": "issuer_not_per_share",
            "formal_filing": True,
            "report_code": filing.report_code,
        }
        if verified_revenue:
            facts.append(
                _official_fact(
                    ticker=item.ticker,
                    family=FundamentalEvidenceFamily.BUSINESS_CURRENT,
                    fact_type="official_current_business_revenue",
                    as_of_date=filing.receipt_date.isoformat(),
                    source="opendart_formal_statement",
                    source_document_id=filing.receipt_no,
                    source_payload_sha256=source_sha,
                    fields={
                        **common,
                        "reported_revenue": revenue.get("value"),
                        "source_row_identity": lineage.get("source_row_identity"),
                    },
                )
            )
        if verified_earnings:
            earnings_fields = {
                "reported_operating_income": operating.get("value")
                if operating.get("status") == "verified_usable"
                else None,
                "reported_net_income": net_income.get("value")
                if net_income.get("status") == "verified_usable"
                else None,
            }
            facts.append(
                _official_fact(
                    ticker=item.ticker,
                    family=FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT,
                    fact_type="official_current_earnings_financial",
                    as_of_date=filing.receipt_date.isoformat(),
                    source="opendart_formal_statement",
                    source_document_id=filing.receipt_no,
                    source_payload_sha256=source_sha,
                    fields={**common, **earnings_fields},
                )
            )
        quality = (
            FundamentalEvidenceQuality.CURRENT
            if verified_revenue and verified_earnings
            else FundamentalEvidenceQuality.PARTIAL
            if verified_revenue or verified_earnings
            else FundamentalEvidenceQuality.UNAVAILABLE
        )
        errors = tuple(
            reason
            for present, reason in (
                (verified_revenue, "validated_current_opendart_revenue_unavailable"),
                (verified_earnings, "validated_current_opendart_earnings_unavailable"),
            )
            if not present
        )
        return OfficialFundamentalEnrichment(
            ticker=item.ticker,
            market="kr",
            issuer_id=profile.corp_code,
            official_profile=dict(profile_payload),
            analysis_framework=framework,
            facts=tuple(facts),
            source_quality=quality,
            source_attempts=(
                {
                    "source": "opendart_company",
                    "status": "success",
                    "issuer_id": profile.corp_code,
                },
                {
                    "source": "opendart_formal_statement",
                    "status": "success" if verified_revenue or verified_earnings else "unavailable",
                    "source_document_id": filing.receipt_no,
                },
            ),
            errors=errors,
            provider_audit={
                "profile_requests": 1,
                "profile_successes": 1,
                "statement_requests": client.provider_calls,
                "statement_successes": int(verified_revenue or verified_earnings),
                "cache_hits": int(statement_cache_hit),
            },
            source_payload_sha256=source_sha,
        )


def enrich_assembled_packet(
    base: SourceAssemblyResult,
    enrichment: OfficialFundamentalEnrichment,
) -> EnrichedSourceAssemblyResult:
    if base.status != SourceAssemblyStatus.ASSEMBLED or base.packet is None:
        sufficiency = evaluate_source_sufficiency(
            enrichment.facts,
            framework=enrichment.analysis_framework,
            identity_hard_valid=False,
        )
        return EnrichedSourceAssemblyResult(
            ticker=base.ticker,
            market=base.market,
            status=sufficiency.status,
            enrichment=enrichment,
            source_sufficiency=sufficiency,
            validation_errors=base.validation_errors,
            provider_audit={"base": base.provider_audit, "fundamental": enrichment.provider_audit},
        )
    if base.ticker != enrichment.ticker or base.market != enrichment.market:
        raise ValueError("base_enrichment_identity_mismatch")
    packet = json.loads(json.dumps(base.packet, ensure_ascii=False, default=str))
    stocks = packet.get("stocks")
    if not isinstance(stocks, list) or len(stocks) != 1 or not isinstance(stocks[0], dict):
        raise ValueError("single_stock_packet_required")
    stock = stocks[0]
    facts = stock.get("fact_catalog")
    if not isinstance(facts, list):
        raise ValueError("fact_catalog_required")
    enriched_facts = []
    for row in facts:
        if not isinstance(row, dict):
            continue
        copied = dict(row)
        if copied.get("fact_type") == "security_identity":
            copied["evidence_family"] = FundamentalEvidenceFamily.IDENTITY_SECURITY.value
            copied["evidence_quality"] = FundamentalEvidenceQuality.CURRENT.value
        elif copied.get("fact_type") in {"price", "chart"} or str(
            copied.get("fact_id") or ""
        ).startswith("chart:"):
            copied["evidence_family"] = FundamentalEvidenceFamily.PRICE_CONTEXT.value
            copied["evidence_quality"] = FundamentalEvidenceQuality.CURRENT.value
        enriched_facts.append(copied)
    known_ids = {str(row.get("fact_id")) for row in enriched_facts}
    enriched_facts.extend(
        row for row in enrichment.facts if str(row.get("fact_id")) not in known_ids
    )
    sufficiency = evaluate_source_sufficiency(
        enriched_facts,
        framework=enrichment.analysis_framework,
        identity_hard_valid=True,
        accounting_basis_hard_valid=enrichment.source_quality
        not in {
            FundamentalEvidenceQuality.VALIDATION_FAILED,
            FundamentalEvidenceQuality.CONFLICTING,
        },
    )
    stock["fact_catalog"] = enriched_facts
    stock["company_profile"] = enrichment.official_profile
    stock["industry"] = enrichment.official_profile.get("industry") or stock.get(
        "industry"
    )
    stock["sector"] = enrichment.official_profile.get("sector") or stock.get("sector")
    stock["business_model"] = enrichment.official_profile.get("taxonomy_key")
    stock["knowledge_routing"] = {
        "industry_key": enrichment.official_profile.get("taxonomy_key") or "general",
        "industry_routing": {
            "confidence": enrichment.official_profile.get("quality") or "partial",
            "source": enrichment.official_profile.get("source"),
            "evidence": [
                f"official_industry_code={enrichment.official_profile.get('official_industry_code')}"
            ],
        },
    }
    unknowns = [
        str(value)
        for value in stock.get("unknowns", [])
        if "기업별 실적 또는 사업 이벤트" not in str(value)
        and "검증된 최신 실적" not in str(value)
    ]
    if sufficiency.directional_model_eligible:
        unknowns.extend(
            (
                "공식 재무 근거는 확보됐지만 세부 사업 KPI와 향후 실행은 추가 확인이 필요합니다.",
                "안전한 밸류에이션 근거가 packet에 없으면 가격 매력도는 Unknown입니다.",
            )
        )
    else:
        unknowns.append(
            "현재 공식 source 조합은 방향성 투자 판단에 필요한 issuer fundamentals를 충족하지 못합니다."
        )
    stock["unknowns"] = list(dict.fromkeys(unknowns))
    stock.setdefault("data_cautions", []).extend(
        [
            "official_fundamental_enrichment_coldstart",
            f"source_sufficiency={sufficiency.status}",
        ]
    )
    packet["contract"] = PACKET_CONTRACT
    packet["source_sufficiency"] = sufficiency.model_dump(mode="json")
    source_assembly = packet.get("source_assembly")
    if isinstance(source_assembly, dict):
        source_assembly["fundamental_source_contract"] = enrichment.contract
        source_assembly["fundamental_source_payload_sha256"] = (
            enrichment.source_payload_sha256
        )
        source_assembly["issuer_id"] = enrichment.issuer_id
        source_assembly["source_sufficiency_status"] = sufficiency.status
        source_assembly["directional_model_eligible"] = int(
            sufficiency.directional_model_eligible
        )
    packet_without_id = {key: value for key, value in packet.items() if key != "packet_id"}
    packet["packet_id"] = (
        f"coldstart-fundamental-{base.ticker}-{canonical_sha256(packet_without_id)[:20]}"
    )
    packet_sha = canonical_sha256(packet)
    financial_facts = [
        row
        for row in enrichment.facts
        if row.get("evidence_family")
        in {
            FundamentalEvidenceFamily.BUSINESS_CURRENT,
            FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT,
        }
    ]
    latest = max(
        (str(row.get("as_of_date") or "") for row in financial_facts), default="확인 불가"
    )
    base_context = "\n".join(
        (
            str(base.deterministic_base_context or ""),
            f"공식 fundamental source 기준일: {latest}",
            f"사전 source 충분성: {sufficiency.status}",
            "가격 방향은 source 충분성 판정에 사용하지 않았습니다.",
        )
    )
    return EnrichedSourceAssemblyResult(
        ticker=base.ticker,
        market=base.market,
        status=sufficiency.status,
        packet=packet,
        packet_sha256=packet_sha,
        deterministic_base_context=base_context,
        deterministic_base_context_sha256=hashlib.sha256(base_context.encode()).hexdigest(),
        enrichment=enrichment,
        source_sufficiency=sufficiency,
        validation_errors=base.validation_errors,
        provider_audit={"base": base.provider_audit, "fundamental": enrichment.provider_audit},
    )
