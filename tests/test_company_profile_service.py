import asyncio
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.models.company import Company
from app.models.watchlist import WatchlistItem
from app.services.ai_review_service import investment_framework_routing
from app.services.company_profile_service import (
    CompanyProfilePopulationService,
    OfficialProfile,
    company_profile_coverage,
    normalize_official_industry,
    read_profile_provenance,
)


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


class _ProfileSource:
    def __init__(self, profiles: dict[str, OfficialProfile | None]) -> None:
        self.profiles = profiles
        self.calls: list[str] = []

    async def fetch(self, item, security):
        del security
        self.calls.append(item.ticker)
        return self.profiles.get(item.ticker)


def _profile(
    ticker: str,
    market: str,
    source: str,
    code: str,
    description: str | None = None,
) -> OfficialProfile:
    return OfficialProfile(
        ticker=ticker,
        company_name=f"{ticker} Company",
        market=market,
        source=source,
        official_industry_code=code,
        official_industry_description=description,
        source_as_of="2026-08-13",
        legal_name=f"{ticker} Legal Name",
        cik="0000001234" if market == "us" else None,
        corp_code="00123456" if market == "kr" else None,
    )


def test_official_industry_normalization_is_generic_and_fail_safe() -> None:
    semiconductor = normalize_official_industry(
        _profile("USFIX", "us", "sec_submissions", "3674", "Semiconductors")
    )
    insurance = normalize_official_industry(
        _profile("KRFIX", "kr", "opendart_company", "65200")
    )
    ambiguous = normalize_official_industry(
        _profile(
            "MIXED",
            "us",
            "sec_submissions",
            "9999",
            "Diversified conglomerate",
        )
    )
    unknown = normalize_official_industry(
        _profile("UNKNOWN", "kr", "opendart_company", "99999")
    )

    assert semiconductor.taxonomy_key == "semiconductor"
    assert semiconductor.quality == "verified"
    assert insurance.taxonomy_key == "insurance"
    assert ambiguous.quality == "ambiguous"
    assert ambiguous.reason == "diversified_identity_without_dominant_segment_evidence"
    assert unknown.quality == "partial"
    assert unknown.industry is None


def test_population_discovers_only_active_companies_and_writes_provenance(
    tmp_path: Path,
) -> None:
    engine = _engine()
    us = _ProfileSource(
        {"USACTIVE": _profile("USACTIVE", "us", "sec_submissions", "3674")}
    )
    kr = _ProfileSource(
        {"KRACTIVE": _profile("KRACTIVE", "kr", "opendart_company", "65200")}
    )
    with Session(engine) as session:
        session.add_all(
            [
                WatchlistItem(
                    ticker="USACTIVE",
                    company_name="US Company",
                    exchange="NASDAQ",
                ),
                WatchlistItem(
                    ticker="KRACTIVE",
                    company_name="KR Company",
                    exchange="KRX",
                ),
                WatchlistItem(
                    ticker="INACTIVE",
                    company_name="Inactive",
                    exchange="NASDAQ",
                    active=False,
                ),
            ]
        )
        session.commit()
        service = CompanyProfilePopulationService(
            kr_source=kr,
            us_source=us,
            data_dir=tmp_path,
        )
        results = asyncio.run(
            service.populate_active(
                session,
                verified_at=datetime(2026, 8, 13, 6, 0, tzinfo=UTC),
            )
        )

        assert {item.ticker for item in results} == {"USACTIVE", "KRACTIVE"}
        assert us.calls == ["USACTIVE"]
        assert kr.calls == ["KRACTIVE"]
        companies = {
            item.ticker: item for item in session.exec(select(Company)).all()
        }
        assert companies["USACTIVE"].industry == "Semiconductors"
        assert companies["KRACTIVE"].industry == "Insurance and Reinsurance"
        coverage = company_profile_coverage(session, tmp_path)

    assert coverage["ready"] is True
    assert coverage["active_total"] == 2
    provenance = read_profile_provenance("USACTIVE", tmp_path)
    assert provenance is not None
    assert provenance["source"] == "sec_submissions"
    assert provenance["quality"] == "verified"


def test_existing_profile_is_preserved_when_official_source_is_unavailable(
    tmp_path: Path,
) -> None:
    engine = _engine()
    source = _ProfileSource({"PRESERVE": None})
    with Session(engine) as session:
        session.add(
            WatchlistItem(
                ticker="PRESERVE",
                company_name="Preserved Company",
                exchange="NASDAQ",
            )
        )
        session.add(
            Company(
                ticker="PRESERVE",
                company_name="Preserved Company",
                exchange="NASDAQ",
                industry="Insurance",
                sector="Financials",
            )
        )
        session.commit()
        service = CompanyProfilePopulationService(
            kr_source=None,
            us_source=source,
            data_dir=tmp_path,
        )
        result = asyncio.run(service.populate_active(session))[0]
        company = session.exec(
            select(Company).where(Company.ticker == "PRESERVE")
        ).one()

    assert result.status == "preserved"
    assert result.quality == "partial"
    assert result.reason == "official_profile_unavailable"
    assert company.industry == "Insurance"
    assert company.sector == "Financials"


def test_ambiguous_profile_stays_general_and_dominant_structured_mix_routes() -> None:
    ambiguous = investment_framework_routing(
        "Diversified conglomerate",
        "Semiconductors and cloud services",
        "AI demand beneficiary",
        profile_quality="ambiguous",
        has_earnings=False,
        preliminary_earnings=False,
        has_price_context=False,
        has_adr_basis_risk=False,
    )
    dominant = investment_framework_routing(
        None,
        "Memory 70%, cloud computing 30%",
        "AI demand beneficiary",
        profile_quality="verified",
        has_earnings=False,
        preliminary_earnings=False,
        has_price_context=False,
        has_adr_basis_risk=False,
    )
    normalized = investment_framework_routing(
        "Official description not covered by text aliases",
        None,
        "Recurring revenue theme",
        normalized_industry="biotech",
        profile_quality="verified",
        has_earnings=False,
        preliminary_earnings=False,
        has_price_context=False,
        has_adr_basis_risk=False,
    )

    assert ambiguous["industry_key"] == "general"
    assert ambiguous["industry_routing"]["confidence"] == "low"
    assert dominant["industry_key"] == "memory"
    assert dominant["industry_routing"]["confidence"] == "medium"
    assert normalized["industry_key"] == "biotech"
    assert normalized["industry_routing"]["source"] == "normalized_profile_taxonomy"
