from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.cross_market_decision_engine_service import EvidenceClaim
from app.services.stage2_maturity_polarity_adapter_service import (
    maturity_atomic_assignment_errors,
    stage2_maturity_atomic_claim_catalog,
)


def _claim(text: str, *refs: str) -> EvidenceClaim:
    return EvidenceClaim(text=text, evidence_refs=refs)


def _assignment(
    *,
    supporting_sources: tuple[str, ...],
    contradicting_sources: tuple[str, ...] = (),
    supporting_claims: tuple[str, ...] = (),
    contradicting_claims: tuple[str, ...] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        supporting_evidence_refs=supporting_sources,
        contradicting_evidence_refs=contradicting_sources,
        supporting_claim_refs=supporting_claims,
        contradicting_claim_refs=contradicting_claims,
    )


def test_mixed_parent_source_passes_with_distinct_atomic_claims() -> None:
    parent = "decision-evidence:mixed"
    catalog = stage2_maturity_atomic_claim_catalog(
        ticker="CORZ",
        buy_drivers=(_claim("운영 전환이 진전됐습니다.", parent),),
        sell_drivers=(_claim("부채와 희석 부담이 큽니다.", parent),),
    )
    bullish = next(row for row in catalog if row.claim.polarity == "BULLISH")
    bearish = next(row for row in catalog if row.claim.polarity == "BEARISH")

    errors = maturity_atomic_assignment_errors(
        (
            _assignment(
                supporting_sources=(parent,),
                contradicting_sources=(parent,),
                supporting_claims=(bearish.claim_ref,),
                contradicting_claims=(bullish.claim_ref,),
            ),
        ),
        catalog=catalog,
    )

    assert errors == ()
    assert bullish.claim_ref != bearish.claim_ref


def test_same_atomic_claim_on_both_sides_is_hard_failure() -> None:
    parent = "decision-evidence:single"
    catalog = stage2_maturity_atomic_claim_catalog(
        ticker="TEST",
        buy_drivers=(_claim("하나의 원자 주장입니다.", parent),),
        sell_drivers=(),
    )
    claim_ref = catalog[0].claim_ref

    errors = maturity_atomic_assignment_errors(
        (
            _assignment(
                supporting_sources=(parent,),
                contradicting_sources=(parent,),
                supporting_claims=(claim_ref,),
                contradicting_claims=(claim_ref,),
            ),
        ),
        catalog=catalog,
    )

    assert any(error.startswith("maturity_same_atomic_claim_overlap") for error in errors)
    assert any(error.startswith("maturity_unproven_parent_source_overlap") for error in errors)


def test_mixed_parent_without_atomic_identity_fails_closed() -> None:
    parent = "decision-evidence:mixed"
    catalog = stage2_maturity_atomic_claim_catalog(
        ticker="CORZ",
        buy_drivers=(_claim("운영 전환이 진전됐습니다.", parent),),
        sell_drivers=(_claim("부채와 희석 부담이 큽니다.", parent),),
    )

    errors = maturity_atomic_assignment_errors(
        (
            _assignment(
                supporting_sources=(parent,),
                contradicting_sources=(parent,),
            ),
        ),
        catalog=catalog,
    )

    assert "maturity_atomic_claim_identity_missing:0:supporting" in errors
    assert "maturity_supporting_source_claim_mismatch:0" in errors
    assert "maturity_contradicting_source_claim_mismatch:0" in errors
    assert any(error.startswith("maturity_unproven_parent_source_overlap") for error in errors)


def test_cross_source_assignment_preserves_exact_parent_provenance() -> None:
    supporting_source = "decision-evidence:positive"
    contradicting_source = "decision-evidence:negative"
    catalog = stage2_maturity_atomic_claim_catalog(
        ticker="TEST",
        buy_drivers=(_claim("운영 근거가 진전됐습니다.", supporting_source),),
        sell_drivers=(_claim("재무 위험이 남아 있습니다.", contradicting_source),),
    )
    bullish = next(row for row in catalog if row.claim.polarity == "BULLISH")
    bearish = next(row for row in catalog if row.claim.polarity == "BEARISH")

    errors = maturity_atomic_assignment_errors(
        (
            _assignment(
                supporting_sources=(supporting_source,),
                contradicting_sources=(contradicting_source,),
                supporting_claims=(bullish.claim_ref,),
                contradicting_claims=(bearish.claim_ref,),
            ),
        ),
        catalog=catalog,
    )

    assert errors == ()


def test_same_structured_claim_cannot_receive_conflicting_absolute_polarity() -> None:
    claim = _claim("동일한 구조화 주장입니다.", "decision-evidence:one")

    with pytest.raises(ValueError, match="maturity_atomic_claim_identity_conflict"):
        stage2_maturity_atomic_claim_catalog(
            ticker="TEST",
            buy_drivers=(claim,),
            sell_drivers=(claim,),
        )
