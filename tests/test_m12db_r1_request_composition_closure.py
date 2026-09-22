from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m12cr_r1_typed_quality_contract import build_r1_pass_a_context
from scripts.m12cq_two_pass_contract import canonical_sha256 as model_view_sha256
from scripts.m12cv_pass_b_capability_contract import build_pass_b_capability_catalog
from scripts.m12db_model_view_readiness import (
    M12DBFailure,
    _write_request_capture,
    bind_final_pass_a_model_view,
)


TICKER = "RENAMED"
CLAIM_REF = "claim:business"
CORE_REF = "evidence:business"
QUALITY_REF = "canonical:financial_quality:current"
VALUATION_REF = "canonical:valuation"
PRICE_REF = "canonical:price"


def _catalog() -> dict[str, object]:
    return {
        "ticker": TICKER,
        "all_evidence_refs": [CORE_REF, VALUATION_REF, PRICE_REF],
        "core_evidence_refs": [CORE_REF, VALUATION_REF],
        "timing_evidence_refs": [PRICE_REF],
        "valuation_evidence_refs": [VALUATION_REF],
        "claim_refs": [CLAIM_REF],
        "atomic_claims": [
            {
                "claim_ref": CLAIM_REF,
                "ticker": TICKER,
                "claim": {
                    "text": "The business evidence remains directionally relevant.",
                    "polarity": "BULLISH",
                    "logical_condition": None,
                },
                "parent_source_refs": [CORE_REF],
            }
        ],
        "entry_catalog": {
            "ticker": TICKER,
            "current_price": {
                "value": 90.0,
                "as_of": "2026-09-19",
                "currency": "USD",
                "ref_id": PRICE_REF,
            },
            "tactical_candidates": [],
            "unresolved_policy": {"tactical_unresolved_reason": "unavailable"},
        },
    }


def _pass_b_context() -> dict[str, object]:
    catalog = _catalog()
    return {
        "ticker": TICKER,
        "accepted_fundamental_claims": [
            {
                "claim_ref": CLAIM_REF,
                "text": "The business evidence remains directionally relevant.",
                "polarity": "BULLISH",
                "logical_condition": None,
                "parent_source_refs": [CORE_REF],
            }
        ],
        "decision_evidence": [],
        "frozen_pass_a_classification": {
            "ticker": TICKER,
            "archetype": "DURABLE_FRANCHISE",
        },
        "deterministic_fundamental_option": {
            "ticker": TICKER,
            "status": "UNRESOLVED",
            "low": None,
            "high": None,
            "currency": None,
            "evidence_refs": [],
        },
        "current_price": deepcopy(catalog["entry_catalog"]["current_price"]),
        "tactical_candidates": [],
        "tactical_unresolved_reason": "unavailable",
        "business_evidence_quality_state": {"state": "NONE"},
        "security_valuation_basis_state": {
            "state": "RESOLVED",
            "new_buyer_price_resolution_use_allowed": True,
        },
        "directional_disclosure_quality_refs": [],
    }


def _capability(*, resolved: bool, high: float = 80.0) -> dict[str, object]:
    context = _pass_b_context()
    option = deepcopy(context["deterministic_fundamental_option"])
    if resolved:
        option.update(
            {
                "status": "RESOLVED",
                "low": 70.0,
                "high": high,
                "currency": "USD",
                "evidence_refs": [VALUATION_REF],
            }
        )
    context["deterministic_fundamental_option"] = option
    return build_pass_b_capability_catalog(
        context=context,
        catalog=_catalog(),
        pass_a=context["frozen_pass_a_classification"],
        policy_option=option,
    )


def _chains() -> dict[str, dict[str, object]]:
    return {
        TICKER: {
            "source_generation_id": "source-generation",
            "authority": {"authority_manifest_sha256": "authority"},
            "expectation": {},
            "binding": {"binding_sha256": None},
            "projection": {
                "projection_sha256": "projection",
                "permission_derivation_sha256": "permission",
            },
        }
    }


def _quality_state() -> dict[str, object]:
    return {
        "contract": "m12cr-r1-typed-quality-security-basis-v1",
        "state": "NONE",
        "effect": "NONE",
        "reason_class": "NOT_APPLICABLE",
        "reason": None,
        "reason_codes": [],
        "source_refs": [],
        "source_presence": "PRESENT",
        "directional_use_allowed": False,
        "owner": "DETERMINISTIC_SOURCE_PROJECTION",
        "status": "MAPPED",
    }


def _intermediate_pass_a_context() -> dict[str, object]:
    evidence = [
        {
            "ref_id": CORE_REF,
            "category": "earnings",
            "label": "business evidence",
            "statement": {"direction": "positive"},
        },
        {
            "ref_id": QUALITY_REF,
            "category": "quality",
            "label": "financial_quality",
            "statement": {"state": "verified_usable"},
        },
    ]
    claims = [
        {
            "claim_ref": CLAIM_REF,
            "text": "The business evidence remains directionally relevant.",
            "polarity": "BULLISH",
            "logical_condition": None,
            "parent_source_refs": [CORE_REF],
        }
    ]
    return {
        "ticker": TICKER,
        "accepted_fundamental_claims": claims,
        "eligible_non_price_evidence": evidence,
        "eligible_claim_refs": [CLAIM_REF],
        "premium_eligible_claim_refs": [CLAIM_REF],
        "data_quality_catalog": {
            "evidence_refs": [QUALITY_REF],
            "material_disclosure_failure_refs": [],
            "positive_quality_refs": [],
        },
        "source_use_projection": {"model_permission_view_sha256": "permission-view"},
        "source_evidence_binding": {
            "contract": "m12cq-consumed-evidence-binding-v1",
            "validated_source_metadata_sha256": "metadata",
            "expected_source_metadata_sha256": "metadata",
            "emitted_evidence_serialized_sha256": model_view_sha256(evidence),
            "emitted_claims_sha256": model_view_sha256(claims),
            "permission_derivation_sha256": "permission",
            "source_use_binding_sha256": "binding",
            "model_permission_view_sha256": "permission-view",
            "surface_parity_checked": True,
        },
    }


def test_final_pass_a_view_rebinds_after_quality_filter() -> None:
    intermediate = _intermediate_pass_a_context()
    packet = {"business_evidence_quality_state": _quality_state()}
    filtered = build_r1_pass_a_context(intermediate, source_packet=packet)

    bound = bind_final_pass_a_model_view(
        intermediate_context=intermediate,
        final_context=filtered,
        source_packet=packet,
    )

    receipt = bound["source_evidence_binding"]
    assert receipt["view_stage"] == "FINAL_POST_TYPED_QUALITY_FILTER"
    assert receipt["intermediate_evidence_count"] == 2
    assert receipt["final_evidence_count"] == 1
    assert receipt["emitted_evidence_serialized_sha256"] == model_view_sha256(
        bound["eligible_non_price_evidence"]
    )
    assert receipt["expected_final_view_sha256"] == receipt["actual_final_view_sha256"]


def test_final_pass_a_view_rejects_altered_post_filter_row() -> None:
    intermediate = _intermediate_pass_a_context()
    packet = {"business_evidence_quality_state": _quality_state()}
    filtered = build_r1_pass_a_context(intermediate, source_packet=packet)
    filtered["eligible_non_price_evidence"][0]["label"] = "altered"

    with pytest.raises(M12DBFailure, match="pass_a_final_view_transform_mismatch"):
        bind_final_pass_a_model_view(
            intermediate_context=intermediate,
            final_context=filtered,
            source_packet=packet,
        )


def test_final_pass_b_capture_requires_capability(tmp_path) -> None:
    context = _pass_b_context()

    with pytest.raises(M12DBFailure, match="pass_b_capability_required"):
        _write_request_capture(
            root=tmp_path,
            stage="pass-b",
            market="us",
            batch=1,
            subjects=(TICKER,),
            contexts={TICKER: context},
            catalogs={TICKER: _catalog()},
            chains=_chains(),
            fixture_only=True,
        )


def test_final_pass_b_capture_uses_exact_context_capability(tmp_path) -> None:
    context = _pass_b_context()
    capability = _capability(resolved=False)
    context["pass_b_capability_catalog"] = deepcopy(capability)

    capture = _write_request_capture(
        root=tmp_path,
        stage="pass-b",
        market="us",
        batch=1,
        subjects=(TICKER,),
        contexts={TICKER: context},
        catalogs={TICKER: _catalog()},
        chains=_chains(),
        fixture_only=True,
        capabilities={TICKER: capability},
    )

    assert capture["status"] == "PASS"
    assert capture["request_composition"] == "CAPABILITY_AWARE_FINAL"
    assert "capability_catalog" in capture["file_sha256"]
    prompt = (tmp_path / "us/batch-01/prompt.txt").read_text(encoding="utf-8")
    assert "PASS_B_CAPABILITY_CATALOG" in prompt
    assert "pass_b_capability_catalog" in prompt


def test_final_pass_b_capture_rejects_context_capability_mismatch(tmp_path) -> None:
    context = _pass_b_context()
    unresolved = _capability(resolved=False)
    context["pass_b_capability_catalog"] = unresolved

    with pytest.raises(M12DBFailure, match="pass_b_context_capability_mismatch"):
        _write_request_capture(
            root=tmp_path,
            stage="pass-b",
            market="us",
            batch=1,
            subjects=(TICKER,),
            contexts={TICKER: context},
            catalogs={TICKER: _catalog()},
            chains=_chains(),
            fixture_only=True,
            capabilities={TICKER: _capability(resolved=True)},
        )


def test_generic_unresolved_and_resolved_above_high_branch_boundaries() -> None:
    unresolved = _capability(resolved=False)
    unresolved_pairs = {
        (row["stance"], row["reason_class"]) for row in unresolved["new_buyer"]["branches"]
    }
    resolved = _capability(resolved=True, high=80.0)
    resolved_pairs = {
        (row["stance"], row["reason_class"]) for row in resolved["new_buyer"]["branches"]
    }

    assert ("ATTRACTIVE", "ATTRACTIVE_WITHIN_RANGE") not in unresolved_pairs
    assert ("WAIT", "FUNDAMENTAL_RANGE_POSITION") not in unresolved_pairs
    assert ("WAIT", "FUNDAMENTAL_UNRESOLVED") in unresolved_pairs
    assert ("WAIT", "FUNDAMENTAL_RANGE_POSITION") in resolved_pairs
