from __future__ import annotations

from copy import deepcopy

from scripts.m12cq_two_pass_contract import (
    build_pass_a_subject_context,
    pass_a_leakage_scan,
)
from scripts.m12cr_shadow_contract import (
    future_pass_a_batch_schema,
    materialize_future_pass_a,
    validate_future_pass_a_shape,
)
from scripts.m12cr_r1_typed_quality_contract import build_r1_pass_a_context
from scripts.m12cs_r1_provider_schema import (
    project_provider_wire_schema,
    scan_provider_structured_output_schema,
)
from scripts.m12da_source_use_contract import (
    SourceUse,
    build_source_use_projection,
    build_trusted_source_authority_manifest,
    canonical_sha256,
    freeze_source_use_binding,
    freeze_source_use_input_expectation,
    model_source_use_projection,
)


TICKER = "RENAMED"
SOURCE_GENERATION = "frozen-source-generation"
EXECUTION_GENERATION = "offline-request-preparation"
CLAIM_REF = "maturity-claim:safe-business"
MIXED_PARENT = "decision-evidence:mixed-business"
SAFE_PARENT = "decision-evidence:safe-business"
VALUATION_REF = "canonical:valuation:per"


def _catalog() -> dict[str, object]:
    return {
        "ticker": TICKER,
        "all_evidence_refs": [MIXED_PARENT, SAFE_PARENT, VALUATION_REF],
        "core_evidence_refs": [MIXED_PARENT, SAFE_PARENT, VALUATION_REF],
        "timing_evidence_refs": [],
        "valuation_evidence_refs": [VALUATION_REF],
        "material_disclosure_failure_refs": [],
        "positive_quality_refs": [],
        "claim_refs": [CLAIM_REF],
        "atomic_claims": [
            {
                "contract": "maturity-atomic-claim-identity-v1",
                "claim_ref": CLAIM_REF,
                "ticker": TICKER,
                "claim": {
                    "text": "Verified demand supports medium-term profitability.",
                    "polarity": "BULLISH",
                    "logical_condition": "Demand remains converted into shipments.",
                },
                "parent_source_refs": [MIXED_PARENT, SAFE_PARENT],
            }
        ],
        "entry_catalog": {
            "ticker": TICKER,
            "current_price": None,
            "tactical_candidates": [],
            "unresolved_policy": {"tactical_unresolved_reason": "not applicable"},
        },
    }


def _metadata() -> list[dict[str, object]]:
    return [
        {
            "ref_id": MIXED_PARENT,
            "category": "thesis",
            "label": "business and valuation narrative",
            "as_of": "2026-09-17",
            "statement": (
                "Demand supports profitability, while PER and PBR remain valuation methods."
            ),
        },
        {
            "ref_id": SAFE_PARENT,
            "category": "macro",
            "label": "business transmission",
            "as_of": "2026-09-17",
            "statement": {"factor": "demand", "direction": "positive"},
        },
        {
            "ref_id": VALUATION_REF,
            "category": "valuation",
            "label": "valuation",
            "as_of": "2026-09-17",
            "statement": {"current_multiple": 20.0},
        },
    ]


def _owners(*, restrict_safe_parent: bool = False) -> list[dict[str, object]]:
    catalog = _catalog()
    metadata = {str(row["ref_id"]): row for row in _metadata()}
    decisive = [
        SourceUse.CONTEXT,
        SourceUse.BUSINESS_CONTEXT,
        SourceUse.PASS_A_ARCHETYPE,
        SourceUse.PASS_A_VALUATION_TIER,
        SourceUse.OVERALL_DIRECTION,
        SourceUse.HOLDER_STANCE,
        SourceUse.NEW_BUYER_EXECUTION_RISK,
    ]
    rows = []
    for ref_id in (MIXED_PARENT, SAFE_PARENT):
        allowed = (
            [SourceUse.CONTEXT] if restrict_safe_parent and ref_id == SAFE_PARENT else decisive
        )
        rows.append(
            {
                "ref_id": ref_id,
                "catalog_sha256": canonical_sha256(catalog),
                "source_metadata_sha256": canonical_sha256(metadata[ref_id]),
                "source_type": "frozen_legacy_business_evidence",
                "source_scope": "exact_source_business_decision_owner",
                "authority_basis": "generic_exact_frozen_owner_fixture",
                "allowed_uses": allowed,
                "prohibited_uses": [use for use in SourceUse if use not in allowed],
            }
        )
    return rows


def _bundle(*, restrict_safe_parent: bool = False) -> dict[str, object]:
    catalog = _catalog()
    metadata = _metadata()
    authority = build_trusted_source_authority_manifest(
        ticker=TICKER,
        source_generation_id=SOURCE_GENERATION,
        catalog=catalog,
        source_metadata=metadata,
        trusted_owner_overrides=_owners(restrict_safe_parent=restrict_safe_parent),
    )
    expectation = freeze_source_use_input_expectation(
        ticker=TICKER,
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        catalog=catalog,
        source_metadata=metadata,
        authority_manifest=authority,
    )
    projection = build_source_use_projection(
        ticker=TICKER,
        input_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        catalog=catalog,
        authority_manifest=authority,
        current_input_expectation=expectation,
    )
    binding = freeze_source_use_binding(
        projection=projection,
        authority_manifest=authority,
        current_input_expectation=expectation,
    )
    return {
        "catalog": catalog,
        "metadata": metadata,
        "authority": authority,
        "expectation": expectation,
        "projection": projection,
        "binding": binding,
    }


def _context(metadata: list[dict[str, object]]) -> dict[str, object]:
    return {
        "decision_evidence": deepcopy(metadata),
        "evidence_packets": [{"ticker": TICKER, "evidence": deepcopy(metadata)}],
    }


def _view(bundle: dict[str, object]) -> dict[str, object]:
    return build_pass_a_subject_context(
        context=_context(bundle["metadata"]),
        ticker=TICKER,
        catalog=bundle["catalog"],
        source_use_view=bundle["projection"],
        source_use_binding=bundle["binding"],
        source_use_expectation=bundle["expectation"],
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        require_source_use=True,
    )


def test_source_authorized_atomic_claim_survives_without_mixed_parent_narrative() -> None:
    bundle = _bundle()
    view = _view(bundle)

    assert view["eligible_claim_refs"] == [CLAIM_REF]
    assert view["accepted_fundamental_claims"] == [
        {
            "claim_ref": CLAIM_REF,
            "text": "Verified demand supports medium-term profitability.",
            "polarity": "BULLISH",
            "logical_condition": "Demand remains converted into shipments.",
            "parent_source_refs": [MIXED_PARENT, SAFE_PARENT],
        }
    ]
    assert MIXED_PARENT not in {row["ref_id"] for row in view["eligible_non_price_evidence"]}
    assert SAFE_PARENT in {row["ref_id"] for row in view["eligible_non_price_evidence"]}
    assert view["source_evidence_binding"]["emitted_claim_parent_refs"][CLAIM_REF] == [
        MIXED_PARENT,
        SAFE_PARENT,
    ]
    assert pass_a_leakage_scan([view])["status"] == "PASS"


def test_stage_projection_omits_out_of_stage_valuation_identifier() -> None:
    bundle = _bundle()
    view = _view(bundle)
    model_projection = view["source_use_projection"]

    assert model_projection["model_view_contract"] == (
        "m12db-stage-scoped-source-use-model-view-v1"
    )
    assert VALUATION_REF not in model_projection["model_source_refs"]
    assert set(model_projection["model_source_refs"]) == {MIXED_PARENT, SAFE_PARENT}

    full = deepcopy(view)
    full["source_use_projection"] = model_source_use_projection(
        bundle["projection"],
        binding=bundle["binding"],
    )
    assert pass_a_leakage_scan([full])["status"] == "FAIL"
    assert pass_a_leakage_scan([view])["status"] == "PASS"


def test_restricted_parent_cannot_be_deleted_or_rescued() -> None:
    bundle = _bundle(restrict_safe_parent=True)
    view = _view(bundle)

    assert view["eligible_claim_refs"] == []
    assert view["accepted_fundamental_claims"] == []


def test_real_forbidden_value_injection_still_fails_closed() -> None:
    view = _view(_bundle())
    view["current_price"] = 123.45

    scan = pass_a_leakage_scan([view])

    assert scan["status"] == "FAIL"
    assert any("current_price" in path for path in scan["errors"])


def test_current_raw_and_provider_schema_admit_honest_unresolved_tier() -> None:
    bundle = _bundle()
    view = _view(bundle)
    schema = future_pass_a_batch_schema(
        subjects=(TICKER,),
        subject_contexts={TICKER: view},
        source_use_inputs={TICKER: {
            "catalog": bundle["catalog"], "chain": bundle, "source_metadata": bundle["metadata"],
            "source_generation_id": SOURCE_GENERATION, "execution_generation_id": EXECUTION_GENERATION,
        }},
    )
    provider, _ = project_provider_wire_schema(schema)
    output = {
        "classifications": {
            TICKER: {
                "archetype": "UNRESOLVED",
                "archetype_confidence": "LOW",
                "archetype_supporting_claim_refs": [CLAIM_REF],
                "archetype_rationale": "The available claim does not resolve the archetype.",
                "valuation_regime_tier": "UNRESOLVED",
                "tier_supporting_claim_refs": [],
                "tier_rationale": "No valuation regime is forced.",
                "directional_data_quality_judgment": {
                    "effect": "NONE",
                    "reason_class": "NOT_APPLICABLE",
                    "reason": None,
                    "evidence_refs": [],
                },
                "classification_summary": "Diagnostic schema fixture only.",
            }
        }
    }

    assert (
        validate_future_pass_a_shape(
            output,
            subjects=(TICKER,),
            subject_contexts={TICKER: view},
        )["status"]
        == "PASS"
    )
    assert scan_provider_structured_output_schema(provider)["status"] == "PASS"


def test_frozen_typed_quality_projection_is_preserved_for_materialization() -> None:
    view = _view(_bundle())
    frozen_quality = {
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
    typed_view = build_r1_pass_a_context(
        view,
        source_packet={"business_evidence_quality_state": frozen_quality},
    )
    output = {
        "classifications": {
            TICKER: {
                "archetype": "UNRESOLVED",
                "archetype_confidence": "LOW",
                "archetype_supporting_claim_refs": [CLAIM_REF],
                "archetype_rationale": "The available claim does not resolve the archetype.",
                "valuation_regime_tier": "UNRESOLVED",
                "tier_supporting_claim_refs": [],
                "tier_rationale": "No valuation regime is forced.",
                "directional_data_quality_judgment": {
                    "effect": "NONE",
                    "reason_class": "NOT_APPLICABLE",
                    "reason": None,
                    "evidence_refs": [],
                },
                "classification_summary": "Diagnostic schema fixture only.",
            }
        }
    }

    rows, validation = materialize_future_pass_a(
        output,
        subjects=(TICKER,),
        subject_contexts={TICKER: typed_view},
    )

    assert typed_view["business_evidence_quality_state"] == frozen_quality
    assert validation["status"] == "PASS"
    assert rows[0]["data_quality_effect"] == "NONE"
