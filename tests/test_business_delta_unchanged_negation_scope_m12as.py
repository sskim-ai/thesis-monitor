from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.business_delta_evidence_service import (
    BusinessDeltaCapability,
    BusinessDeltaEvidenceItem,
    BusinessDeltaEvidenceRole,
    BusinessDeltaEvidenceView,
    BusinessDeltaUnchangedClaimRole,
    classify_business_delta_unchanged_claims,
    validate_business_delta_candidate,
)
from app.services.direction_timing_ownership_service import EvidenceDomain


FIXTURES = Path("tests/fixtures/business_delta_unchanged_negation_scope_m12as.json")


def _view() -> BusinessDeltaEvidenceView:
    item = BusinessDeltaEvidenceItem(
        alias="E1",
        canonical_ref="fixture:baseline",
        source_ref="fixture:baseline",
        domain=EvidenceDomain.BUSINESS_CURRENT,
        role=BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT,
        reason="stored thesis baseline",
    )
    return BusinessDeltaEvidenceView(
        ticker="SNDK",
        capability=BusinessDeltaCapability.UNCHANGED_ONLY,
        baseline_context_refs=(item.alias,),
        items=(item,),
    )


def _fixtures() -> list[dict[str, str]]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda row: row["fixture_id"])
def test_unchanged_claim_scope_fixture(fixture: dict[str, str]) -> None:
    view = _view()
    claims = classify_business_delta_unchanged_claims(fixture["text"])
    result = validate_business_delta_candidate(
        {
            "ticker": view.ticker,
            "business_thesis_change": "UNCHANGED",
            "business_thesis_context": {
                "text": fixture["text"],
                "evidence_refs": ["E1"],
            },
        },
        view,
    )

    assert result["status"] == fixture["expected_status"]
    assert BusinessDeltaUnchangedClaimRole(fixture["expected_role"]) in {
        claim.role for claim in claims
    }
    assert result["unchanged_claim_unsafe_count"] == int(fixture["expected_status"] == "FAIL")


def test_model_facing_business_delta_view_contract_is_unchanged() -> None:
    payload = _view().model_context()
    assert payload["contract"] == "business-delta-evidence-view-v1"
    assert "unchanged_claims" not in payload
