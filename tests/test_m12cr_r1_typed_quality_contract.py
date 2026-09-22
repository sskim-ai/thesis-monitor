from __future__ import annotations

import inspect
import json

import pytest

from scripts import m12cr_r1_typed_quality_contract as contract
from scripts.m12cr_r1_typed_quality_contract import (
    build_r1_pass_a_context,
    gate_policy_option_for_security_basis,
    project_business_evidence_quality,
    project_security_valuation_basis,
    r1_semantic_rule_inventory,
    validate_quality_basis_decision_ownership,
    validate_security_valuation_basis_gate,
)
from scripts.m12cr_shadow_contract import semantic_rule_inventory


def _business_context(
    *,
    state: str = "verified_usable",
    reasons: tuple[str, ...] = (),
    include: bool = True,
) -> dict[str, object]:
    evidence: list[dict[str, object]] = [
        {
            "ref_id": "canonical:security_identity:current",
            "category": "quality",
            "label": "security_identity",
            "statement": {"eligibility_decision": "provider_native_multiple_may_be_eligible"},
        }
    ]
    if include:
        evidence.append(
            {
                "ref_id": "canonical:financial_quality:2026-06-30",
                "category": "earnings",
                "label": "financial_quality",
                "statement": {
                    "decision_version": "financial-quality-taint-v2",
                    "reason_codes": list(reasons),
                    "source_period": "2026-06-30",
                    "source_type": "full_statement",
                    "state": state,
                },
            }
        )
    return {
        "ticker": "GENERIC",
        "eligible_non_price_evidence": evidence,
        "data_quality_catalog": {
            "evidence_refs": [row["ref_id"] for row in evidence],
            "material_disclosure_failure_refs": [],
            "positive_quality_refs": [],
        },
    }


def _security_packet(
    *,
    identity_decision: str = "provider_native_multiple_may_be_eligible",
    basis_decision: str = "provider_native_multiple_may_be_eligible",
    identity_state: str = "verified_non_depositary",
    security_type: str = "common_stock",
    depositary: bool = False,
    book_currency: str | None = "USD",
    eps_currency: str | None = "USD",
    price_currency: str | None = "USD",
    serialized: bool = False,
) -> dict[str, object]:
    identity = {
        "decision_version": "security-identity-v2",
        "depositary_evidence_present": depositary,
        "depositary_ratio": None,
        "depositary_ratio_direction": None,
        "depositary_ratio_source": None,
        "eligibility_decision": identity_decision,
        "identity_state": identity_state,
        "selected_security_type": security_type,
        "verification_status": (
            "verified" if identity_state.startswith("verified_") else "unverified"
        ),
    }
    basis = {
        "book_value_currency": book_currency,
        "depositary_ratio_state": "unknown" if depositary else "not_applicable",
        "earnings_per_share_currency": eps_currency,
        "earnings_per_share_security_basis": ("unknown" if depositary else "current_security"),
        "eligibility_decision": basis_decision,
        "price_currency": price_currency,
        "security_identity_state": identity_state,
    }
    if serialized:
        identity_value: object = json.dumps(identity, sort_keys=True)
        basis_value: object = json.dumps(basis, sort_keys=True)
    else:
        identity_value = identity
        basis_value = basis
    return {
        "ticker": "GENERIC",
        "evidence": [
            {
                "ref_id": "canonical:security_identity:current",
                "statement": identity_value,
            },
            {
                "ref_id": "canonical:security_basis:current",
                "statement": basis_value,
            },
        ],
    }


def _catalog() -> dict[str, object]:
    return {
        "atomic_claims": [
            {
                "claim_ref": "claim:security",
                "parent_source_refs": ["canonical:security_basis:current"],
            },
            {
                "claim_ref": "claim:business-quality",
                "parent_source_refs": ["canonical:financial_quality:2026-06-30"],
            },
            {
                "claim_ref": "claim:directional-quality",
                "parent_source_refs": ["quality:directional"],
            },
            {
                "claim_ref": "claim:business",
                "parent_source_refs": ["core:business"],
            },
        ]
    }


def _typed_states() -> dict[str, dict[str, object]]:
    return {
        "business_evidence_quality": {
            "state": "CONFIDENCE_ONLY",
            "source_refs": ["canonical:financial_quality:2026-06-30"],
        },
        "security_valuation_basis": {
            "state": "UNRESOLVED",
            "source_refs": ["canonical:security_basis:current"],
        },
        "directional_disclosure_refs": ["quality:directional"],
    }


def _decision(
    *,
    overall: str = "BUY",
    overall_refs: tuple[str, ...] = ("claim:business",),
    holder: str = "HOLDABLE",
    holder_refs: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "ticker": "GENERIC",
        "overall_direction": overall,
        "decisive_supporting_claim_refs": list(overall_refs),
        "holder": holder,
        "holder_reason_evidence_refs": list(holder_refs),
        "new_buyer": "WAIT",
    }


def test_clean_verified_quality_ref_does_not_create_limitation() -> None:
    result = project_business_evidence_quality(_business_context())
    assert result["state"] == "NONE"
    assert result["effect"] == "NONE"
    assert result["source_refs"] == []


@pytest.mark.parametrize(
    ("state", "reasons", "reason_class"),
    [
        ("verified_usable", ("reporting_cadence_exceeded",), "STALE_OR_UNSUPPORTED"),
        ("caution_usable", (), "PROVIDER_LIMITATION"),
        ("denied", ("financial_hard_error",), "PROVIDER_LIMITATION"),
        ("unknown", (), "PROVIDER_LIMITATION"),
    ],
)
def test_business_quality_typed_states_limit_confidence_only(
    state: str,
    reasons: tuple[str, ...],
    reason_class: str,
) -> None:
    result = project_business_evidence_quality(_business_context(state=state, reasons=reasons))
    assert result["state"] == "CONFIDENCE_ONLY"
    assert result["effect"] == "CONFIDENCE_ONLY"
    assert result["reason_class"] == reason_class
    assert result["directional_use_allowed"] is False


def test_security_only_financial_reason_does_not_degrade_business_quality() -> None:
    result = project_business_evidence_quality(
        _business_context(reasons=("per_share_basis_insufficient",))
    )
    assert result["state"] == "NONE"
    assert result["excluded_security_basis_reason_codes"] == ["per_share_basis_insufficient"]


def test_missing_expected_business_quality_record_is_distinct_and_fail_closed() -> None:
    result = project_business_evidence_quality(_business_context(include=False))
    assert result["state"] == "CONFIDENCE_ONLY"
    assert result["source_presence"] == "EXPECTED_RECORD_ABSENT"


def test_legitimately_not_applicable_business_quality_is_clean() -> None:
    context = _business_context(include=False)
    context["business_quality_expected"] = False
    result = project_business_evidence_quality(context)
    assert result["state"] == "NONE"
    assert result["source_presence"] == "LEGITIMATELY_NOT_APPLICABLE"


def test_pass_a_context_hides_ordinary_quality_and_security_metadata() -> None:
    context = _business_context(state="caution_usable")
    context["accepted_fundamental_claims"] = [
        {
            "claim_ref": "claim:security",
            "parent_source_refs": ["canonical:security_identity:current"],
        },
        {
            "claim_ref": "claim:business",
            "parent_source_refs": ["core:business"],
        },
    ]
    context["eligible_claim_refs"] = ["claim:security", "claim:business"]
    context["premium_eligible_claim_refs"] = ["claim:security", "claim:business"]
    context["eligible_non_price_evidence"].append(
        {
            "ref_id": "canonical:security_basis:current",
            "category": "quality",
            "label": "security_basis",
            "statement": {"eligibility_decision": "provider_native_multiple_may_be_eligible"},
        }
    )
    projected = build_r1_pass_a_context(context)
    refs = {row["ref_id"] for row in projected["eligible_non_price_evidence"]}
    assert "canonical:financial_quality:2026-06-30" not in refs
    assert "canonical:security_identity:current" not in refs
    assert "canonical:security_basis:current" not in refs
    assert projected["eligible_claim_refs"] == ["claim:business"]
    assert projected["premium_eligible_claim_refs"] == ["claim:business"]
    assert projected["business_evidence_quality_state"]["state"] == "CONFIDENCE_ONLY"


def test_pass_a_context_projects_from_full_packet_before_model_filtering() -> None:
    base = _business_context(include=False)
    packet = _business_context(state="verified_usable", reasons=("per_share_basis_insufficient",))
    projected = build_r1_pass_a_context(base, source_packet=packet)
    result = project_business_evidence_quality(projected)
    assert result["state"] == "NONE"
    assert result["reason_codes"] == []
    assert "excluded_security_basis_reason_codes" not in result
    assert "financial_quality_state" not in result


def test_verified_non_depositary_provider_native_basis_is_resolved() -> None:
    result = project_security_valuation_basis(_security_packet())
    assert result["state"] == "RESOLVED"
    assert result["unresolved_reasons"] == []


@pytest.mark.parametrize(
    "decision",
    [
        "security_share_basis_dependent_valuation_denied",
        "unverified_depositary_evidence_requires_authoritative_resolution",
    ],
)
def test_unsafe_security_decisions_are_unresolved(decision: str) -> None:
    packet = _security_packet(
        identity_decision=decision,
        basis_decision=decision,
        identity_state="unknown",
    )
    result = project_security_valuation_basis(packet)
    assert result["state"] == "UNRESOLVED"
    assert result["unsafe_per_share_projection_blocked"] is True


def test_depositary_without_complete_conversion_basis_is_unresolved() -> None:
    packet = _security_packet(
        identity_decision="requires_verified_current_security_denominator",
        basis_decision="requires_verified_current_security_denominator",
        identity_state="verified_depositary",
        security_type="depositary_receipt",
        depositary=True,
    )
    result = project_security_valuation_basis(packet)
    assert result["state"] == "UNRESOLVED"
    assert result["depositary_affected"] is True
    assert "depositary_security_basis_unresolved" in result["unresolved_reasons"]


def test_reporting_trading_currency_mismatch_is_unresolved() -> None:
    result = project_security_valuation_basis(_security_packet(), trading_currency="KRW")
    assert result["state"] == "UNRESOLVED"
    assert "reporting_trading_currency_mismatch" in result["unresolved_reasons"]


def test_serialized_typed_records_are_parsed_without_prose_heuristics() -> None:
    result = project_security_valuation_basis(_security_packet(serialized=True))
    assert result["state"] == "RESOLVED"


def test_security_gate_blocks_resolved_option_for_unresolved_basis() -> None:
    option = {
        "ticker": "GENERIC",
        "status": "RESOLVED",
        "option_id": "option:one",
        "low": 10.0,
        "high": 12.0,
        "currency": "USD",
        "method_family": "HISTORICAL_TRAILING_PE_QUANTILE",
        "selection_basis": "PRIMARY_PE",
        "evidence_refs": ["valuation:one"],
        "source_candidate_ids": ["candidate:one"],
        "methods_averaged": False,
        "unresolved_reasons": [],
    }
    basis = {"state": "UNRESOLVED"}
    gated, receipt = gate_policy_option_for_security_basis(option, basis)
    assert gated["status"] == "UNRESOLVED"
    assert gated["low"] is None
    assert receipt["unsafe_projection_blocked"] is True
    gate = validate_security_valuation_basis_gate(
        policy_options={"GENERIC": gated},
        security_basis_by_ticker={"GENERIC": basis},
    )
    assert gate["status"] == "PASS"


def test_security_basis_cannot_be_sole_overall_downgrade_reason() -> None:
    result = validate_quality_basis_decision_ownership(
        [_decision(overall="HOLD", overall_refs=("claim:security",))],
        catalogs={"GENERIC": _catalog()},
        typed_states={"GENERIC": _typed_states()},
    )
    assert "GENERIC:security_basis_sole_overall_downgrade" in result["errors"]


def test_security_basis_cannot_be_sole_holder_downgrade_reason() -> None:
    result = validate_quality_basis_decision_ownership(
        [
            _decision(
                holder="REVIEW",
                holder_refs=("canonical:security_basis:current",),
            )
        ],
        catalogs={"GENERIC": _catalog()},
        typed_states={"GENERIC": _typed_states()},
    )
    assert "GENERIC:security_basis_sole_holder_downgrade" in result["errors"]


def test_business_confidence_cannot_be_sole_overall_or_holder_reason() -> None:
    result = validate_quality_basis_decision_ownership(
        [
            _decision(
                overall="SELL",
                overall_refs=("claim:business-quality",),
                holder="REDUCE",
                holder_refs=("canonical:financial_quality:2026-06-30",),
            )
        ],
        catalogs={"GENERIC": _catalog()},
        typed_states={"GENERIC": _typed_states()},
    )
    assert "GENERIC:business_confidence_sole_overall_downgrade" in result["errors"]
    assert "GENERIC:business_confidence_sole_holder_downgrade" in result["errors"]


def test_directional_disclosure_quality_can_support_existing_policy_axes() -> None:
    result = validate_quality_basis_decision_ownership(
        [
            _decision(
                overall="HOLD",
                overall_refs=("claim:directional-quality",),
                holder="REVIEW",
                holder_refs=("quality:directional",),
            )
        ],
        catalogs={"GENERIC": _catalog()},
        typed_states={"GENERIC": _typed_states()},
    )
    assert result["status"] == "PASS"


def test_unresolved_security_basis_does_not_block_new_buyer_wait_shape() -> None:
    result = validate_quality_basis_decision_ownership(
        [_decision()],
        catalogs={"GENERIC": _catalog()},
        typed_states={"GENERIC": _typed_states()},
    )
    assert result["status"] == "PASS"


def test_r1_rule_inventory_has_no_missing_upstream_enforcement() -> None:
    inventory = r1_semantic_rule_inventory(semantic_rule_inventory())
    assert inventory["base_rule_count"] == 115
    assert inventory["new_rule_count"] == 9
    assert any(
        row["rule"] == "source_use_projection_or_binding_required" for row in inventory["rules"]
    )
    assert inventory["missing_upstream_enforcement_count"] == 0
    assert inventory["status"] == "PASS"


def test_projection_source_contains_no_snapshot_ticker_allowlist() -> None:
    source = inspect.getsource(contract)
    for ticker in ("SKHY", "TSM", "WRD", "SNDK", "TSLA"):
        assert ticker not in source
