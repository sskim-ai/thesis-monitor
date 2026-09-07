from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from app.services.coldstart_fundamental_enrichment_service import (
    AnalysisFramework,
    FundamentalEvidenceFamily,
    FundamentalEvidenceQuality,
    OfficialFundamentalEnrichment,
    SourceSufficiencyStatus,
    classify_analysis_framework,
    enrich_assembled_packet,
    evaluate_source_sufficiency,
    resolve_financial_lifecycle_framework,
    us_bank_insurer_sector_fact,
)
from app.services.coldstart_source_assembly_service import (
    SourceAssemblyResult,
    SourceAssemblyStatus,
)


def _fact(
    family: FundamentalEvidenceFamily,
    quality: FundamentalEvidenceQuality = FundamentalEvidenceQuality.CURRENT,
) -> dict[str, object]:
    return {
        "fact_id": f"fixture:{family.value}",
        "fact_type": "fixture",
        "evidence_family": family.value,
        "evidence_quality": quality.value,
        "fields": {},
    }


IDENTITY = _fact(FundamentalEvidenceFamily.IDENTITY_SECURITY)
PRICE = _fact(FundamentalEvidenceFamily.PRICE_CONTEXT)
BUSINESS = _fact(FundamentalEvidenceFamily.BUSINESS_CURRENT)
EARNINGS = _fact(FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT)
REGULATORY = _fact(FundamentalEvidenceFamily.REGULATORY_CAPITAL_CURRENT)
CLINICAL = _fact(FundamentalEvidenceFamily.CLINICAL_REGULATORY_CURRENT)
LIQUIDITY = _fact(FundamentalEvidenceFamily.LIQUIDITY_CASHFLOW_CURRENT)


def _status(
    *facts: dict[str, object],
    framework: AnalysisFramework = AnalysisFramework.STANDARD_OPERATING,
) -> SourceSufficiencyStatus:
    return evaluate_source_sufficiency(
        facts,
        framework=framework,
    ).status


def test_source_sufficiency_synthetic_matrix() -> None:
    assert _status(IDENTITY, PRICE) == (
        SourceSufficiencyStatus.INSUFFICIENT_FUNDAMENTAL_EVIDENCE
    )
    assert _status(IDENTITY, BUSINESS) == (
        SourceSufficiencyStatus.SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY
    )
    assert _status(IDENTITY, EARNINGS) == (
        SourceSufficiencyStatus.SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY
    )
    assert _status(IDENTITY, BUSINESS, EARNINGS) == (
        SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT
    )
    assert _status(
        IDENTITY,
        EARNINGS,
        REGULATORY,
        framework=AnalysisFramework.BANK_INSURER,
    ) == SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT
    assert _status(
        IDENTITY,
        CLINICAL,
        LIQUIDITY,
        framework=AnalysisFramework.PRE_PROFIT_BIOTECH,
    ) == SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT


def test_stale_and_invalid_fundamentals_do_not_satisfy_gate() -> None:
    stale_business = _fact(
        FundamentalEvidenceFamily.BUSINESS_CURRENT,
        FundamentalEvidenceQuality.STALE,
    )
    stale_earnings = _fact(
        FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT,
        FundamentalEvidenceQuality.REFRESH_DUE,
    )
    invalid = _fact(
        FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT,
        FundamentalEvidenceQuality.VALIDATION_FAILED,
    )

    assert _status(IDENTITY, stale_business, stale_earnings) == (
        SourceSufficiencyStatus.SOURCE_FRESHNESS_BLOCK
    )
    assert _status(IDENTITY, BUSINESS, invalid) == (
        SourceSufficiencyStatus.SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY
    )


def test_valuation_is_not_required_and_price_direction_is_never_read() -> None:
    strong_price = {**PRICE, "fields": {"direction": "strong", "rsi": 90}}
    weak_price = {**PRICE, "fields": {"direction": "weak", "rsi": 10}}

    sufficient = evaluate_source_sufficiency(
        (IDENTITY, BUSINESS, EARNINGS),
        framework=AnalysisFramework.STANDARD_OPERATING,
    )
    strong = evaluate_source_sufficiency(
        (IDENTITY, strong_price),
        framework=AnalysisFramework.STANDARD_OPERATING,
    )
    weak = evaluate_source_sufficiency(
        (IDENTITY, weak_price),
        framework=AnalysisFramework.STANDARD_OPERATING,
    )

    assert sufficient.directional_model_eligible is True
    assert FundamentalEvidenceFamily.VALUATION_SAFE not in sufficient.valid_families
    assert strong.status == weak.status == (
        SourceSufficiencyStatus.INSUFFICIENT_FUNDAMENTAL_EVIDENCE
    )
    assert strong.price_direction_inputs_used == weak.price_direction_inputs_used == 0


def test_identity_and_accounting_basis_fail_closed() -> None:
    identity_block = evaluate_source_sufficiency(
        (BUSINESS, EARNINGS),
        framework=AnalysisFramework.STANDARD_OPERATING,
        identity_hard_valid=False,
    )
    accounting_block = evaluate_source_sufficiency(
        (IDENTITY, BUSINESS, EARNINGS),
        framework=AnalysisFramework.STANDARD_OPERATING,
        accounting_basis_hard_valid=False,
    )

    assert identity_block.status == (
        SourceSufficiencyStatus.SECURITY_OR_ACCOUNTING_BASIS_BLOCK
    )
    assert accounting_block.status == (
        SourceSufficiencyStatus.SECURITY_OR_ACCOUNTING_BASIS_BLOCK
    )
    assert not identity_block.directional_model_eligible
    assert not accounting_block.directional_model_eligible


def test_framework_classification_is_generic() -> None:
    assert classify_analysis_framework(
        taxonomy_key="bank", sector="Financials", industry="Banking"
    ) == AnalysisFramework.BANK_INSURER
    assert classify_analysis_framework(
        taxonomy_key="biotech", sector="Health Care", industry="Biotechnology"
    ) == AnalysisFramework.PRE_PROFIT_BIOTECH
    assert classify_analysis_framework(
        taxonomy_key="semiconductor", sector="Technology", industry="Semiconductors"
    ) == AnalysisFramework.ASSET_HEAVY_CYCLICAL
    assert classify_analysis_framework(
        taxonomy_key=None, sector="Technology", industry="Software"
    ) == AnalysisFramework.STANDARD_OPERATING


def _sector_payload(
    concepts: dict[str, list[dict[str, object]]],
    *,
    taxonomy: str = "us-gaap",
) -> dict[str, object]:
    return {
        "facts": {
            taxonomy: {
                concept: {
                    "label": concept,
                    "units": {"USD": rows},
                }
                for concept, rows in concepts.items()
            }
        }
    }


def _sector_row() -> SimpleNamespace:
    return SimpleNamespace(
        ticker="FICTIONAL",
        filing_date=date(2026, 8, 6),
        financial_period_end=date(2026, 6, 30),
        fiscal_year=2026,
        period="2026-Q2",
        period_scope="single-quarter",
    )


def _occurrence(
    value: int,
    *,
    start: str | None = "2026-04-01",
    filed: str = "2026-08-06",
    accession: str | None = "0000000000-26-000001",
) -> dict[str, object]:
    return {
        "start": start,
        "end": "2026-06-30",
        "filed": filed,
        "fy": 2026,
        "fp": "Q2",
        "form": "10-Q",
        "val": value,
        "accn": accession,
    }


def test_current_bank_sector_metrics_map_generically_with_exact_occurrences() -> None:
    payload = _sector_payload(
        {
            "InterestIncomeExpenseNet": [
                _occurrence(200, start="2026-01-01"),
                _occurrence(100),
            ],
            "NoninterestIncome": [
                _occurrence(80, start="2026-01-01"),
                _occurrence(40),
            ],
        }
    )

    fact = us_bank_insurer_sector_fact(
        ticker="FICTIONAL",
        payload=payload,
        profile_payload={"taxonomy_key": "bank", "industry": "Banking"},
        financial_row=_sector_row(),
        source_payload_sha256="source-sha",
    )

    assert fact is not None
    assert fact["evidence_family"] == "SECTOR_OPERATING_CURRENT"
    assert fact["fields"]["subframework"] == "bank"
    assert [row["value"] for row in fact["fields"]["metrics"]] == [100, 40]
    assert all(row["taxonomy"] == "us-gaap" for row in fact["fields"]["metrics"])
    assert all(row["accession_number"] for row in fact["fields"]["metrics"])


def test_current_insurance_obligation_maps_to_sector_operating_not_capital() -> None:
    payload = _sector_payload(
        {"LiabilityForFuturePolicyBenefits": [_occurrence(500, start=None)]}
    )

    fact = us_bank_insurer_sector_fact(
        ticker="FICTIONAL",
        payload=payload,
        profile_payload={"taxonomy_key": "insurance", "industry": "Insurance"},
        financial_row=_sector_row(),
        source_payload_sha256="source-sha",
    )

    assert fact is not None
    assert fact["evidence_family"] == "SECTOR_OPERATING_CURRENT"
    assert fact["fields"]["subframework"] == "insurance"
    assert fact["fields"]["metrics"][0]["concept"] == (
        "LiabilityForFuturePolicyBenefits"
    )


def test_sector_mapping_rejects_standard_company_stale_wrong_taxonomy_and_missing_provenance() -> None:
    valid = {
        "InterestIncomeExpenseNet": [_occurrence(100)],
        "NoninterestIncome": [_occurrence(40)],
    }
    cases = (
        (
            _sector_payload(valid),
            {"taxonomy_key": "retail", "industry": "Retail"},
        ),
        (
            _sector_payload(
                {
                    "InterestIncomeExpenseNet": [
                        _occurrence(100, filed="2026-05-01")
                    ],
                    "NoninterestIncome": [_occurrence(40, filed="2026-05-01")],
                }
            ),
            {"taxonomy_key": "bank"},
        ),
        (
            _sector_payload(valid, taxonomy="issuer-extension"),
            {"taxonomy_key": "bank"},
        ),
        (
            _sector_payload(
                {
                    "InterestIncomeExpenseNet": [
                        _occurrence(100, accession=None)
                    ],
                    "NoninterestIncome": [_occurrence(40, accession=None)],
                }
            ),
            {"taxonomy_key": "bank"},
        ),
    )

    assert all(
        us_bank_insurer_sector_fact(
            ticker="FICTIONAL",
            payload=payload,
            profile_payload=profile,
            financial_row=_sector_row(),
            source_payload_sha256="source-sha",
        )
        is None
        for payload, profile in cases
    )


def test_profitable_life_sciences_company_uses_operating_company_gate() -> None:
    assert resolve_financial_lifecycle_framework(
        AnalysisFramework.PRE_PROFIT_BIOTECH,
        revenue=10_000,
        earnings_values=(1_000, None),
    ) == AnalysisFramework.STANDARD_OPERATING
    assert resolve_financial_lifecycle_framework(
        AnalysisFramework.PRE_PROFIT_BIOTECH,
        revenue=100,
        earnings_values=(-500, None),
    ) == AnalysisFramework.PRE_PROFIT_BIOTECH


def test_enriched_packet_exposes_current_fundamentals_and_gate() -> None:
    base = SourceAssemblyResult(
        status=SourceAssemblyStatus.ASSEMBLED,
        ticker="GENERIC",
        market="us",
        packet={
            "contract": "coldstart-source-assembly-v1",
            "packet_id": "base",
            "market": "us",
            "assessment_date": "2026-09-06",
            "stocks": [
                {
                    "ticker": "GENERIC",
                    "company_name": "Generic Inc.",
                    "industry": "Software",
                    "sector": "Technology",
                    "business_model": None,
                    "unknowns": [
                        "기업별 실적 또는 사업 이벤트 확인이 다음 재평가 조건입니다."
                    ],
                    "fact_catalog": [
                        {
                            "fact_id": "security_identity:current",
                            "fact_type": "security_identity",
                            "fields": {},
                        },
                        {
                            "fact_id": "price:current",
                            "fact_type": "price",
                            "fields": {},
                        },
                    ],
                    "data_cautions": [],
                }
            ],
            "source_assembly": {"price_timing_readiness": "READY"},
        },
        deterministic_base_context="base context",
    )
    enrichment = OfficialFundamentalEnrichment(
        ticker="GENERIC",
        market="us",
        issuer_id="0000000001",
        official_profile={
            "source": "sec_submissions",
            "official_industry_code": "7372",
            "taxonomy_key": None,
            "quality": "partial",
        },
        analysis_framework=AnalysisFramework.STANDARD_OPERATING,
        facts=(BUSINESS, EARNINGS),
        source_quality=FundamentalEvidenceQuality.CURRENT,
    )

    result = enrich_assembled_packet(base, enrichment)

    assert result.status == SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT
    assert result.source_sufficiency.directional_model_eligible is True
    assert result.packet is not None
    stock = result.packet["stocks"][0]
    assert stock["fact_catalog"][0]["evidence_family"] == "IDENTITY_SECURITY"
    assert stock["fact_catalog"][1]["evidence_family"] == "PRICE_CONTEXT"
    assert all(
        "기업별 실적 또는 사업 이벤트" not in value for value in stock["unknowns"]
    )
    assert result.packet["source_assembly"]["full_e2e_readiness"] == "READY"


def test_directional_sufficiency_does_not_require_price_timing() -> None:
    base = SourceAssemblyResult(
        status=SourceAssemblyStatus.ASSEMBLED,
        ticker="GENERIC",
        market="us",
        packet={
            "contract": "coldstart-source-assembly-v1",
            "packet_id": "base-no-price",
            "market": "us",
            "assessment_date": "2026-09-06",
            "stocks": [
                {
                    "ticker": "GENERIC",
                    "company_name": "Generic Inc.",
                    "industry": "Software",
                    "sector": "Technology",
                    "business_model": None,
                    "unknowns": [],
                    "fact_catalog": [
                        {
                            "fact_id": "security_identity:current",
                            "fact_type": "security_identity",
                            "fields": {},
                        }
                    ],
                    "data_cautions": ["current_price_unavailable"],
                }
            ],
            "source_assembly": {
                "price_context_readiness": "UNAVAILABLE",
                "price_timing_readiness": "UNAVAILABLE_SAFE",
            },
        },
        deterministic_base_context="base context",
    )
    enrichment = OfficialFundamentalEnrichment(
        ticker="GENERIC",
        market="us",
        issuer_id="0000000001",
        official_profile={
            "source": "sec_submissions",
            "official_industry_code": "7372",
            "taxonomy_key": None,
            "quality": "partial",
        },
        analysis_framework=AnalysisFramework.STANDARD_OPERATING,
        facts=(BUSINESS, EARNINGS),
        source_quality=FundamentalEvidenceQuality.CURRENT,
    )

    result = enrich_assembled_packet(base, enrichment)

    assert result.status == SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT
    assert result.source_sufficiency.directional_model_eligible is True
    assert result.packet is not None
    source = result.packet["source_assembly"]
    assert source["directional_fundamental_readiness"] == "READY"
    assert source["price_timing_readiness"] == "UNAVAILABLE_SAFE"
    assert source["full_e2e_readiness"] == "READY"
    families = {
        fact.get("evidence_family")
        for fact in result.packet["stocks"][0]["fact_catalog"]
    }
    assert FundamentalEvidenceFamily.PRICE_CONTEXT.value not in families


def test_enriched_packet_does_not_create_decision_for_insufficient_source() -> None:
    base = SourceAssemblyResult(
        status=SourceAssemblyStatus.IDENTITY_UNRESOLVED,
        ticker="GENERIC",
        market="us",
    )
    enrichment = OfficialFundamentalEnrichment(
        ticker="GENERIC",
        market="us",
        analysis_framework=AnalysisFramework.STANDARD_OPERATING,
        facts=(),
        source_quality=FundamentalEvidenceQuality.UNAVAILABLE,
    )

    result = enrich_assembled_packet(base, enrichment)

    assert result.packet is None
    assert result.source_sufficiency.directional_model_eligible is False
    assert result.ai_judgment_calls == 0
