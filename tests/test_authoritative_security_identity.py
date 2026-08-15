import asyncio
import json

import httpx
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.security import ProviderResponseCache, SecurityMaster
from app.providers.identity import OpenFigiProvider, canonicalize_openfigi_candidates
from app.services.financial_quality_service import build_financial_quality_state
from app.services.official_security_identity_service import (
    ADR_RATIO_DIRECTION,
    OfficialSecurityIdentityService,
    load_official_identity_provenance,
    parse_sec_ads_prospectus_identity,
    parse_sec_cover_page_identity,
)
from app.services.security_identity_service import (
    IDENTITY_UNKNOWN,
    TIER_A_AUTHORITATIVE,
    VERIFIED_DEPOSITARY,
    VERIFIED_NON_DEPOSITARY,
    resolve_security_identity,
)
from app.services.security_master_service import SecurityMasterService


GOOGL_COVER = """
<ix:nonNumeric contextRef="issuer" name="dei:EntityRegistrantName">Alphabet Inc.</ix:nonNumeric>
<ix:nonNumeric contextRef="a" name="dei:Security12bTitle">Class A Common Stock, $0.001 par value</ix:nonNumeric>
<ix:nonNumeric contextRef="a" name="dei:TradingSymbol">GOOGL</ix:nonNumeric>
<ix:nonNumeric contextRef="a" name="dei:SecurityExchangeName">Nasdaq Stock Market LLC</ix:nonNumeric>
<ix:nonNumeric contextRef="c" name="dei:Security12bTitle">Class C Capital Stock</ix:nonNumeric>
<ix:nonNumeric contextRef="c" name="dei:TradingSymbol">GOOG</ix:nonNumeric>
<ix:nonNumeric contextRef="c" name="dei:SecurityExchangeName">Nasdaq Stock Market LLC</ix:nonNumeric>
"""

SKHY_PROSPECTUS = """
Filed pursuant to Rule 424(b)(4), Registration No. 333-296987.
American Depositary Shares, or ADSs, representing common shares of SK hynix Inc.
Each ADS represents one-tenth of a share of our common stock.
We have been approved to list the ADSs on the Nasdaq Global Select Market under the symbol
“SKHY.” Our common shares are listed on the KRX KOSPI Market under identification code “000660.”
"""

IBM_SPLIT_COVER = """
<ix:nonNumeric contextRef="issuer" name="dei:EntityRegistrantName">International Business Machines Corporation</ix:nonNumeric>
<ix:nonNumeric contextRef="symbol" name="dei:TradingSymbol">IBM</ix:nonNumeric>
<ix:nonNumeric contextRef="symbol" name="dei:SecurityExchangeName">NYSETX</ix:nonNumeric>
<ix:nonNumeric contextRef="stock" name="dei:Security12bTitle">Capital stock, par value $.20 per share</ix:nonNumeric>
<ix:nonNumeric contextRef="stock" name="dei:SecurityExchangeName">New York Stock Exchange</ix:nonNumeric>
<ix:nonNumeric contextRef="note" name="dei:Security12bTitle">0.300% Notes due 2026</ix:nonNumeric>
<ix:nonNumeric contextRef="note" name="dei:TradingSymbol">IBM 26B</ix:nonNumeric>
<ix:nonNumeric contextRef="note" name="dei:SecurityExchangeName">New York Stock Exchange</ix:nonNumeric>
"""


def _engine():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return engine


def _security(**overrides: object) -> SecurityMaster:
    values: dict[str, object] = {
        "canonical_company_id": "company:fixture",
        "canonical_security_id": "security:fixture:nasdaq",
        "ticker": "FIX",
        "exchange": "NASDAQ",
        "country": "US",
        "company_name": "Fixture Corp",
        "legal_name": "Fixture Corp",
        "security_type": "common_stock",
        "issuer_type": "domestic_us",
        "identity_quality": "inferred",
        "identity_provider": "local",
    }
    values.update(overrides)
    return SecurityMaster(**values)


def _googl_evidence():
    return parse_sec_cover_page_identity(
        GOOGL_COVER,
        ticker="GOOGL",
        source_url="https://www.sec.gov/Archives/example/googl.htm",
        filing_accession="0001652044-26-000071",
        filing_date="2026-07-23",
        cik="0001652044",
    )


def _skhy_evidence():
    return parse_sec_ads_prospectus_identity(
        SKHY_PROSPECTUS,
        ticker="SKHY",
        issuer_name="SK hynix Inc.",
        source_url="https://www.sec.gov/Archives/example/skhy.htm",
        filing_accession="0001193125-26-299963",
        filing_date="2026-07-10",
        cik="0002120882",
        registration_number="333-296987",
    )


def test_local_defaults_and_exchange_name_do_not_verify_identity() -> None:
    engine = _engine()
    with Session(engine) as session:
        row = _security()
        session.add(row)
        session.commit()
        refreshed = SecurityMasterService().ensure(session, row.ticker)
        result = resolve_security_identity(
            company_name=refreshed.company_name,
            security_master=refreshed,
        )

    assert refreshed.identity_quality == "inferred"
    assert result["identity_state"] == IDENTITY_UNKNOWN
    assert result["source_tier"] == "tier_d_inferred_default"


def test_official_cover_corrects_wrong_googl_depositary_identity_idempotently() -> None:
    engine = _engine()
    service = OfficialSecurityIdentityService()
    with Session(engine) as session:
        session.add(
            _security(
                ticker="GOOGL",
                canonical_security_id="security:googl:nasdaq",
                company_name="Alphabet Inc.",
                legal_name="Alphabet Inc.",
                security_type="Depositary Receipt",
                share_class="DR",
                identity_quality="full",
                identity_provider="local+openfigi",
                identity_warnings=json.dumps(["legacy identity conflict"]),
            )
        )
        session.commit()
        dry_run = service.ingest(session, _googl_evidence(), dry_run=True)
        session.rollback()
        unchanged = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == "GOOGL")
        ).one()
        assert unchanged.security_type == "Depositary Receipt"

        applied = service.ingest(session, _googl_evidence(), dry_run=False)
        session.commit()
        corrected = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == "GOOGL")
        ).one()
        provenance = load_official_identity_provenance(session, "GOOGL")
        result = resolve_security_identity(
            company_name=corrected.company_name,
            security_master=corrected,
            identity_provenance=provenance,
        )
        second = service.ingest(session, _googl_evidence(), dry_run=False)

    assert dry_run["mutated"] is False
    assert dry_run["rollback_snapshot"]["security_type"] == "Depositary Receipt"
    assert applied["mutated"] is True
    assert corrected.security_type == "common_stock"
    assert corrected.share_class == "Class A"
    assert corrected.identity_provider == "sec_official_identity"
    assert result["identity_state"] == VERIFIED_NON_DEPOSITARY
    assert result["source_tier"] == TIER_A_AUTHORITATIVE
    assert provenance["field_provenance"]["security_type"]["source_url"]
    assert second["action"] == "no_op_already_authoritative"
    assert second["mutated"] is False


def test_official_cover_joins_unique_split_symbol_and_stock_title_contexts() -> None:
    evidence = parse_sec_cover_page_identity(
        IBM_SPLIT_COVER,
        ticker="IBM",
        source_url="https://www.sec.gov/Archives/example/ibm.htm",
        filing_accession="0000051143-26-000078",
        filing_date="2026-07-23",
        cik="0000051143",
    )

    assert evidence.security_type == "common_stock"
    assert evidence.issuer_type == "domestic_us"
    assert evidence.exchange == "NYSE"


def test_official_prospectus_verifies_skhy_ads_and_ratio_direction() -> None:
    evidence = _skhy_evidence()
    engine = _engine()
    service = OfficialSecurityIdentityService()
    with Session(engine) as session:
        session.add(
            _security(
                ticker="SKHY",
                canonical_security_id="security:skhy:nasdaq",
                company_name="SK hynix Inc. ADR",
                legal_name="SK hynix Inc.",
            )
        )
        session.commit()
        service.ingest(session, evidence, dry_run=False)
        session.commit()
        corrected = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == "SKHY")
        ).one()
        provenance = load_official_identity_provenance(session, "SKHY")
        identity = resolve_security_identity(
            company_name=corrected.company_name,
            security_master=corrected,
            identity_provenance=provenance,
        )

    assert evidence.adr_ratio == 0.1
    assert evidence.adr_ratio_direction == ADR_RATIO_DIRECTION
    assert corrected.security_type == "ads"
    assert corrected.ordinary_share_identifier == "000660"
    assert corrected.adr_identifier == "SKHY"
    assert identity["identity_state"] == VERIFIED_DEPOSITARY
    assert identity["selected_adr_ratio"] == 0.1
    assert identity["adr_ratio_direction"] == ADR_RATIO_DIRECTION


def test_conflicting_authoritative_evidence_is_cached_without_overwrite() -> None:
    engine = _engine()
    service = OfficialSecurityIdentityService()
    with Session(engine) as session:
        session.add(
            _security(
                ticker="GOOGL",
                canonical_security_id="security:googl:nasdaq",
                company_name="Alphabet Inc.",
                legal_name="Alphabet Inc.",
                identity_provider="sec_official_identity",
                identity_quality="verified",
            )
        )
        session.commit()
        conflicting = _skhy_evidence()
        conflicting = conflicting.__class__(
            **{**conflicting.__dict__, "ticker": "GOOGL"}
        )
        result = service.ingest(session, conflicting, dry_run=False)
        session.commit()
        refreshed = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == "GOOGL")
        ).one()
        cache = session.exec(
            select(ProviderResponseCache).where(
                ProviderResponseCache.provider == "official_security_identity",
                ProviderResponseCache.ticker == "GOOGL",
                ProviderResponseCache.data_type == "identity_evidence_conflict",
            )
        ).one()

    assert result["action"] == "conflict_no_write_existing_authoritative"
    assert result["mutated"] is False
    assert refreshed.security_type == "common_stock"
    assert cache.status == "conflict"
    assert json.loads(cache.payload)["rollback_snapshot"]["security_type"] == "common_stock"


def test_verified_ads_does_not_unlock_provider_native_consensus_without_basis() -> None:
    quality = build_financial_quality_state(
        {
            "current_price": 166.33,
            "currency": "USD",
            "provider": "finnhub",
            "security_identity_state": VERIFIED_DEPOSITARY,
            "security_identity_decision_version": "security-identity-v2",
            "forward_pe": 6.95,
            "forward_pe_source": "consensus_forward",
            "forward_pe_input_period": "FY1",
            "forward_pe_basis_status": "not_applicable",
            "forward_pe_basis_conflict": False,
        }
    )

    assert quality["fields"]["forward_pe"]["state"] == "unknown"
    assert quality["fields"]["forward_pe"]["prose_eligible"] is False


def _openfigi_candidates() -> list[dict[str, object]]:
    return [
        {
            "figi": "BBG-DR",
            "ticker": "GOOGL",
            "name": "Alphabet Inc.",
            "micCode": "OTCM",
            "securityType2": "Depositary Receipt",
            "marketSector": "Equity",
        },
        {
            "figi": "BBG-CLASS-A",
            "ticker": "GOOGL",
            "name": "Alphabet Inc.",
            "micCode": "XNAS",
            "securityType2": "Common Stock",
            "securityDescription": "Class A",
            "marketSector": "Equity",
        },
    ]


def test_openfigi_selection_is_order_invariant_and_uses_exact_instrument() -> None:
    security = _security(
        ticker="GOOGL",
        canonical_security_id="security:googl:nasdaq",
        company_name="Alphabet Inc.",
        legal_name="Alphabet Inc.",
    )
    first = canonicalize_openfigi_candidates(security, _openfigi_candidates())
    second = canonicalize_openfigi_candidates(
        security, list(reversed(_openfigi_candidates()))
    )

    assert first["status"] == "selected"
    assert first["selected"]["figi"] == "BBG-CLASS-A"
    assert second["selected"]["figi"] == "BBG-CLASS-A"
    assert first["candidate_audit"] == second["candidate_audit"]


def test_openfigi_share_class_disambiguates_same_exchange_candidates() -> None:
    security = _security(
        ticker="GOOGL",
        canonical_security_id="security:googl:nasdaq",
        company_name="Alphabet Inc.",
        legal_name="Alphabet Inc.",
        share_class="Class A",
        identity_provider="explicit_local_identity",
        identity_quality="verified",
    )
    candidates = _openfigi_candidates()
    candidates[0]["micCode"] = "XNAS"
    candidates[0]["securityDescription"] = "Depositary Receipt"
    result = canonicalize_openfigi_candidates(security, candidates)

    assert result["status"] == "selected"
    assert result["selected"]["figi"] == "BBG-CLASS-A"
    rejected = next(
        item for item in result["candidate_audit"] if item["identity"]["figi"] == "BBG-DR"
    )
    assert "share_class_mismatch" in rejected["rejection_reasons"]


def test_openfigi_ambiguous_candidates_do_not_write_security_master() -> None:
    candidates = [
        {
            "figi": figi,
            "ticker": "FIX",
            "name": "Fixture Corp",
            "micCode": "XNAS",
            "securityType2": "Common Stock",
        }
        for figi in ("BBG-A", "BBG-B")
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"data": candidates}])

    engine = _engine()
    provider = OpenFigiProvider(transport=httpx.MockTransport(handler))
    with Session(engine) as session:
        session.add(_security())
        session.commit()
        security = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == "FIX")
        ).one()
        mapped, reason = asyncio.run(provider.enrich(session, security))
        session.commit()
        refreshed = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == "FIX")
        ).one()
        cache = session.exec(
            select(ProviderResponseCache).where(
                ProviderResponseCache.provider == "openfigi",
                ProviderResponseCache.ticker == "FIX",
            )
        ).one()

    assert mapped is False
    assert reason == "multiple_equal_exact_instrument_matches"
    assert refreshed.figi is None
    assert refreshed.identity_warnings == "[]"
    assert len(json.loads(cache.payload)["resolution"]["candidate_audit"]) == 2


def test_openfigi_enrich_applies_only_the_deterministic_common_stock_match() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"data": _openfigi_candidates()}])

    engine = _engine()
    provider = OpenFigiProvider(transport=httpx.MockTransport(handler))
    with Session(engine) as session:
        row = _security(
            ticker="GOOGL",
            canonical_security_id="security:googl:nasdaq",
            company_name="Alphabet Inc.",
            legal_name="Alphabet Inc.",
            security_type="Depositary Receipt",
            identity_provider="local",
            identity_quality="inferred",
        )
        session.add(row)
        session.commit()
        mapped, reason = asyncio.run(provider.enrich(session, row))
        session.commit()
        refreshed = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == "GOOGL")
        ).one()

    assert mapped is True
    assert reason == "mapped"
    assert refreshed.figi == "BBG-CLASS-A"
    assert refreshed.security_type == "common_stock"
    assert refreshed.identity_provider == "openfigi_deterministic_match"


def test_openfigi_cannot_overwrite_authoritative_identity() -> None:
    candidate = {
        "figi": "BBG-DR",
        "ticker": "GOOGL",
        "name": "Alphabet Inc.",
        "micCode": "XNAS",
        "securityType2": "Depositary Receipt",
    }

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"data": [candidate]}])

    engine = _engine()
    provider = OpenFigiProvider(transport=httpx.MockTransport(handler))
    with Session(engine) as session:
        row = _security(
            ticker="GOOGL",
            canonical_security_id="security:googl:nasdaq",
            company_name="Alphabet Inc.",
            legal_name="Alphabet Inc.",
            identity_provider="sec_official_identity",
            identity_quality="verified",
        )
        session.add(row)
        session.commit()
        mapped, reason = asyncio.run(provider.enrich(session, row))
        session.commit()
        refreshed = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == "GOOGL")
        ).one()

    assert mapped is False
    assert reason == "authoritative_identity_preserved"
    assert refreshed.security_type == "common_stock"
    assert refreshed.identity_provider == "sec_official_identity"
