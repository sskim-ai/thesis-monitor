from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m12da_source_use_contract import (
    SourceUse,
    build_source_use_projection,
    build_trusted_source_authority_manifest,
    canonical_sha256,
    freeze_source_use_binding,
    freeze_source_use_input_expectation,
)
from scripts.m12dj_source_authority_preflight import (
    INSUFFICIENT,
    preflight_current_pass_a_cohort,
    preflight_current_pass_a_subject,
)


def fixture(*, ticker="RENAMED", grant=False, rows=None, parent_uses=None):
    """Exact-owner fixtures exercise the gate, not a fresh-source permission mapping."""
    rows = rows or [
        {
            "ref_id": "source:renamed",
            "category": "thesis",
            "label": "neutral",
            "statement": "Demand remains supported.",
        }
    ]
    refs = [row["ref_id"] for row in rows]
    catalog = {
        "ticker": ticker,
        "all_evidence_refs": refs,
        "core_evidence_refs": refs,
        "timing_evidence_refs": [],
        "valuation_evidence_refs": [],
        "material_disclosure_failure_refs": [],
        "positive_quality_refs": [],
        "claim_refs": ["claim:renamed"],
        "atomic_claims": [
            {
                "claim_ref": "claim:renamed",
                "ticker": ticker,
                "claim": {"text": "Demand remains supported.", "polarity": "BULLISH"},
                "parent_source_refs": refs,
            }
        ],
    }
    default = [
        SourceUse.CONTEXT,
        SourceUse.BUSINESS_CONTEXT,
        SourceUse.PASS_A_ARCHETYPE,
        SourceUse.PASS_A_VALUATION_TIER,
    ]
    overrides = []
    if grant:
        for index, row in enumerate(rows):
            allowed = parent_uses[index] if parent_uses else default
            overrides.append(
                {
                    "ref_id": row["ref_id"],
                    "catalog_sha256": canonical_sha256(catalog),
                    "source_metadata_sha256": canonical_sha256(row),
                    "source_type": "frozen_legacy_business_evidence",
                    "source_scope": "exact_source_business_decision_owner",
                    "authority_basis": "test_only_explicit_exact_legacy_owner",
                    "allowed_uses": allowed,
                    "prohibited_uses": [use for use in SourceUse if use not in allowed],
                }
            )
    authority = build_trusted_source_authority_manifest(
        ticker=ticker,
        source_generation_id="source-frozen",
        catalog=catalog,
        source_metadata=rows,
        trusted_owner_overrides=overrides,
    )
    expectation = freeze_source_use_input_expectation(
        ticker=ticker,
        source_generation_id="source-frozen",
        execution_generation_id="offline",
        catalog=catalog,
        source_metadata=rows,
        authority_manifest=authority,
    )
    projection = build_source_use_projection(
        ticker=ticker,
        input_generation_id="source-frozen",
        execution_generation_id="offline",
        catalog=catalog,
        authority_manifest=authority,
        current_input_expectation=expectation,
    )
    binding = freeze_source_use_binding(
        projection=projection, authority_manifest=authority, current_input_expectation=expectation
    )
    return {
        "ticker": ticker,
        "source_generation_id": "source-frozen",
        "execution_generation_id": "offline",
        "catalog": catalog,
        "source_packet": {"ticker": ticker, "decision_evidence": rows},
        "authority": authority,
        "expectation": expectation,
        "projection": projection,
        "binding": binding,
    }


def test_explicit_exact_owner_fixture_runs_actual_builder_without_mutation():
    inputs = fixture(grant=True)
    original = deepcopy(inputs)
    result = preflight_current_pass_a_subject(**inputs)
    assert inputs == original
    assert result["receipt"]["status"] == "PASS"
    assert result["receipt"]["claims_after_typed_filter"] == 1
    assert result["model_context"]["eligible_claim_refs"] == ["claim:renamed"]


@pytest.mark.parametrize("ticker", ["RENAMED", "OTHER_ISSUER"])
def test_core_and_atomic_membership_do_not_create_authority(ticker):
    result = preflight_current_pass_a_subject(**fixture(ticker=ticker))
    assert result["receipt"]["manifest_binding_status"] == "PASS"
    assert result["receipt"]["parents_status"] == "PASS"
    assert result["receipt"]["denied_or_unknown_claims"] == 1
    assert result["receipt"]["status"] == INSUFFICIENT
    assert result["model_context"] is None


@pytest.mark.parametrize(
    "statement",
    [{}, {"contract": "invented-business-v1"}, {"provider": "SEC", "contract_version": 1}],
)
def test_missing_or_unknown_provider_contract_cannot_grant_authority(statement):
    rows = [
        {
            "ref_id": "source:new",
            "category": "earnings",
            "label": "verified",
            "statement": statement,
        }
    ]
    assert (
        preflight_current_pass_a_subject(**fixture(rows=rows))["receipt"]["status"] == INSUFFICIENT
    )


@pytest.mark.parametrize(
    "field,value",
    [("ticker", "WRONG"), ("source_generation_id", "other"), ("execution_generation_id", "other")],
)
def test_identity_mismatch_is_rejected(field, value):
    inputs = fixture(grant=True)
    inputs[field] = value
    assert preflight_current_pass_a_subject(**inputs)["model_context"] is None


@pytest.mark.parametrize(
    "target",
    [
        "metadata",
        "manifest",
        "projection",
        "binding",
        "expectation",
        "claim_ticker",
        "claim_parent",
    ],
)
def test_stale_or_wrong_binding_rejected(target):
    inputs = fixture(grant=True)
    if target == "metadata":
        inputs["source_packet"]["decision_evidence"][0]["statement"] = "Changed after freeze"
    elif target == "claim_ticker":
        inputs["catalog"]["atomic_claims"][0]["ticker"] = "WRONG_ENTITY"
    elif target == "claim_parent":
        inputs["catalog"]["atomic_claims"][0]["parent_source_refs"] = ["missing:source"]
    else:
        inputs["authority" if target == "manifest" else target]["ticker"] = "WRONG"
    result = preflight_current_pass_a_subject(**inputs)
    assert result["receipt"]["status"] == INSUFFICIENT
    assert result["model_context"] is None


@pytest.mark.parametrize(
    "restricted", ["wc", "malformed_wc", "expectations", "malformed_expectations", "quality"]
)
def test_restricted_families_retain_no_decisive_authority(restricted):
    wc = {
        "ref_id": "canonical:working-capital-relation:x",
        "category": "earnings_quality",
        "statement": {
            "relation_semantics_contract": "working-capital-relation-semantics-v1",
            "semantic_scope": "exact_total_inventory",
            "relation_id": "relation:x",
        },
    }
    expectation = {
        "ref_id": "decision-evidence:expectation",
        "category": "expectations",
        "statement": {"level": "high", "priced_in": "partly"},
    }
    row = deepcopy(wc if "wc" in restricted else expectation)
    if restricted.startswith("malformed"):
        row["statement"] = {"unsupported_field": "not an owner"}
    if restricted == "quality":
        row = {
            "ref_id": "canonical:financial_quality:current",
            "category": "quality",
            "statement": {},
        }
    row["label"] = "Verified decisive independent business evidence"
    result = preflight_current_pass_a_subject(**fixture(rows=[row]))
    assert result["receipt"]["status"] == INSUFFICIENT
    assert result["receipt"]["authorized_a_claims"] == 0


def test_multi_parent_permission_intersection_and_no_union():
    rows = [
        {"ref_id": f"source:{i}", "category": "thesis", "statement": "Demand remains supported."}
        for i in range(2)
    ]
    allowed = preflight_current_pass_a_subject(**fixture(rows=rows, grant=True))
    assert allowed["receipt"]["status"] == "PASS"
    disjoint = [
        [SourceUse.CONTEXT, SourceUse.PASS_A_ARCHETYPE],
        [SourceUse.CONTEXT, SourceUse.PASS_A_VALUATION_TIER],
    ]
    denied = preflight_current_pass_a_subject(
        **fixture(rows=rows, grant=True, parent_uses=disjoint)
    )
    assert denied["receipt"]["status"] == INSUFFICIENT
    assert denied["receipt"]["contextual_only_claims"] == 1


def test_cosmetic_labels_do_not_create_authority():
    first = fixture()
    row = deepcopy(first["source_packet"]["decision_evidence"][0])
    row["label"] = "official trusted business decision owner"
    second = fixture(rows=[row])
    assert preflight_current_pass_a_subject(**first)["receipt"]["authorized_a_claims"] == 0
    assert preflight_current_pass_a_subject(**second)["receipt"]["authorized_a_claims"] == 0


def test_all_subject_gate_withholds_successful_contexts_on_one_failure():
    result = preflight_current_pass_a_cohort(
        [fixture(ticker="A", grant=True), fixture(ticker="B")], expected_subjects=["A", "B"]
    )
    assert result["passed_subjects"] == 1
    assert not result["allow_model_calls"]
    assert result["model_contexts"] == {}


@pytest.mark.parametrize("expected", [[], ["RENAMED", "ABSENT"], ["RENAMED", "RENAMED"], ["WRONG"]])
def test_empty_missing_duplicate_or_wrong_population_blocks(expected):
    result = preflight_current_pass_a_cohort([fixture(grant=True)], expected_subjects=expected)
    assert not result["allow_model_calls"]
    assert result["model_contexts"] == {}


def test_complete_authorized_fixture_cohort_passes():
    result = preflight_current_pass_a_cohort(
        [fixture(ticker="A", grant=True), fixture(ticker="B", grant=True)],
        expected_subjects=["A", "B"],
    )
    assert result["allow_model_calls"]
    assert set(result["model_contexts"]) == {"A", "B"}


def test_explicit_source_visibility_exclusion_is_enforced_before_inference():
    result = preflight_current_pass_a_subject(
        **fixture(grant=True), prohibited_pass_a_source_refs=["source:renamed"]
    )
    assert result["model_context"] is None
    assert result["receipt"]["denial_reason_counts"]["source_policy_pass_a_visibility_leak"] == 1


def test_typed_filter_cannot_silently_zero_all_claims(monkeypatch):
    from scripts import m12db_model_view_readiness as final_owner
    from scripts import m12dj_source_authority_preflight as gate

    original = gate.build_r1_pass_a_context

    def remove_claims(base_context, *, source_packet):
        result = original(base_context, source_packet=source_packet)
        result["accepted_fundamental_claims"] = []
        result["eligible_claim_refs"] = []
        result["premium_eligible_claim_refs"] = []
        return result

    monkeypatch.setattr(gate, "build_r1_pass_a_context", remove_claims)
    monkeypatch.setattr(final_owner, "build_r1_pass_a_context", remove_claims)
    result = preflight_current_pass_a_subject(**fixture(grant=True))
    assert result["model_context"] is None
    assert result["receipt"]["claims_before_typed_filter"] == 1
    assert result["receipt"]["denial_reason_counts"]["typed_quality_filter_removed_all_claims"] == 1
