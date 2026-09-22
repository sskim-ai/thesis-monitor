from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.cross_market_decision_engine_service import EvidenceClaim
from app.services.evidence_maturity_pricing_service import (
    DriverEvidenceMaturity,
    EvidenceMaturity,
    MarketExpectation,
    MarketExpectationAssessment,
    OverallMaturityAssessment,
    PricingRequirement,
    PricingRequirementAssessment,
    decisive_maturities,
)


def _claim(ref: str, text: str = "검증된 근거에 따른 해석입니다.") -> EvidenceClaim:
    return EvidenceClaim(text=text, evidence_refs=(ref,))


def test_maturity_is_driver_first_and_not_a_decision_or_confidence() -> None:
    rows = (
        DriverEvidenceMaturity(
            driver="신규 제품 수익화",
            decisive=True,
            maturity=EvidenceMaturity.PARTIAL,
            supporting_evidence_refs=("ref:thesis",),
            what_remains_unproven=_claim("ref:unknown"),
            as_of="2026-08-30",
        ),
        DriverEvidenceMaturity(
            driver="기존 사업 현금창출",
            decisive=False,
            maturity=EvidenceMaturity.CONFIRMED,
            supporting_evidence_refs=("ref:earnings",),
            what_remains_unproven=_claim("ref:unknown", "지속성은 다음 공시에서 재확인합니다."),
            as_of="2026-08-30",
        ),
    )

    assert decisive_maturities(rows) == {EvidenceMaturity.PARTIAL}
    assert not hasattr(rows[0], "decision")
    assert not hasattr(rows[0], "confidence")


def test_existing_expectation_enum_and_pricing_requirement_remain_separate() -> None:
    expectation = MarketExpectationAssessment(
        level=MarketExpectation.LOW,
        basis=_claim("ref:expectations"),
    )
    pricing = PricingRequirementAssessment(
        requirement=PricingRequirement.BASE_CASE_REQUIRED,
        basis=_claim("ref:valuation"),
        valuation_basis=_claim("ref:valuation"),
        expectation_basis=_claim("ref:expectations"),
        key_assumption=_claim("ref:thesis"),
        unknowns=(_claim("ref:unknown"),),
    )
    overall = OverallMaturityAssessment(
        maturity=EvidenceMaturity.MIXED,
        basis=_claim("ref:thesis"),
    )

    assert expectation.level == "low"
    assert pricing.requirement == "BASE_CASE_REQUIRED"
    assert overall.maturity == "MIXED"


@pytest.mark.parametrize(
    "invalid_as_of",
    (
        "latest",
        "latest00000000000",
        "current",
        "today",
        "2026-9-15",
        "2026-99-99",
        "          ",
        "2026-08-30T00:00:00Z",
    ),
)
def test_driver_maturity_requires_a_real_iso_calendar_date(invalid_as_of: str) -> None:
    with pytest.raises(ValidationError):
        DriverEvidenceMaturity(
            driver="현금전환",
            decisive=True,
            maturity=EvidenceMaturity.PARTIAL,
            supporting_evidence_refs=("ref:earnings",),
            what_remains_unproven=_claim("ref:unknown"),
            as_of=invalid_as_of,
        )


def test_driver_and_reasoning_fields_remain_free_narrative_text() -> None:
    row = DriverEvidenceMaturity(
        driver="Cash conversion durability after the build-out phase",
        decisive=True,
        maturity=EvidenceMaturity.PARTIAL,
        supporting_evidence_refs=("ref:earnings",),
        what_remains_unproven=_claim(
            "ref:unknown",
            "다음 정식 공시에서 영업현금흐름과 재투자 부담의 지속성을 다시 확인합니다.",
        ),
        as_of="2026-08-30",
    )

    assert row.driver.startswith("Cash conversion")
    assert "다음 정식 공시" in row.what_remains_unproven.text


def test_driver_maturity_rejects_same_atomic_claim_on_both_sides() -> None:
    claim_ref = "maturity-claim:" + "a" * 64

    with pytest.raises(ValidationError, match="maturity_atomic_claim_polarity_overlap"):
        DriverEvidenceMaturity(
            driver="혼합 근거의 성숙도",
            decisive=True,
            maturity=EvidenceMaturity.MIXED,
            supporting_evidence_refs=("ref:mixed",),
            contradicting_evidence_refs=("ref:mixed",),
            supporting_claim_refs=(claim_ref,),
            contradicting_claim_refs=(claim_ref,),
            what_remains_unproven=_claim("ref:unknown"),
            as_of="2026-08-30",
        )
