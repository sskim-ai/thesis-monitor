from __future__ import annotations

import json
from copy import deepcopy

import pytest

from scripts.m12cq_two_pass_contract import (
    build_pass_a_subject_context,
    build_pass_b_subject_context,
    canonical_sha256 as context_sha256,
    canonical_source_metadata_sha256,
    pass_b_prompt,
)
from scripts.m12cv_pass_b_capability_contract import (
    build_pass_b_capability_catalog,
    validate_capability_selection,
)
from scripts.m12da_source_use_contract import (
    SourceUse,
    build_source_use_projection,
    build_trusted_source_authority_manifest,
    canonical_sha256,
    freeze_source_use_binding,
    freeze_source_use_input_expectation,
    projection_permission_derivation_sha256,
    validate_source_use_current_input,
    validate_source_use_projection_binding,
)


TICKER = "RENAMED"
SOURCE_GENERATION = "source-generation"
EXECUTION_GENERATION = "execution-generation"


def _claim(claim_ref: str, parent_ref: str, polarity: str) -> dict[str, object]:
    return {
        "claim_ref": claim_ref,
        "ticker": TICKER,
        "claim": {
            "text": "동결된 구조화 근거 주장입니다.",
            "polarity": polarity,
            "logical_condition": None,
        },
        "parent_source_refs": [parent_ref],
    }


def _catalog() -> dict[str, object]:
    claims = [
        _claim("claim:bull", "source:business", "BULLISH"),
        _claim("claim:wc", "canonical:working-capital-relation:fixture", "BEARISH"),
    ]
    return {
        "ticker": TICKER,
        "all_evidence_refs": [
            "source:business",
            "canonical:working-capital-relation:fixture",
            "canonical:valuation",
            "canonical:price",
            "canonical:security_basis:current",
        ],
        "core_evidence_refs": [
            "source:business",
            "canonical:working-capital-relation:fixture",
            "canonical:valuation",
        ],
        "timing_evidence_refs": ["canonical:price"],
        "valuation_evidence_refs": ["canonical:valuation"],
        "security_valuation_basis_refs": ["canonical:security_basis:current"],
        "positive_quality_refs": [],
        "business_quality_confidence_refs": [],
        "claim_refs": [str(row["claim_ref"]) for row in claims],
        "atomic_claims": claims,
        "entry_catalog": {
            "ticker": TICKER,
            "current_price": {
                "value": 90.0,
                "as_of": "2026-09-18",
                "currency": "USD",
                "ref_id": "canonical:price",
            },
            "tactical_candidates": [],
            "unresolved_policy": {"tactical_unresolved_reason": "unavailable"},
        },
    }


def _metadata() -> list[dict[str, object]]:
    return [
        {
            "ref_id": "source:business",
            "category": "thesis",
            "label": "핵심 투자 논리",
            "as_of": "2026-09-18",
            "statement": "동결된 사업 근거",
            "runtime_only_field": "not-model-visible",
        },
        {
            "ref_id": "canonical:working-capital-relation:fixture",
            "category": "earnings_quality",
            "label": "working_capital_inventory_relation",
            "as_of": "2026-06-30",
            "statement": {
                "relation_semantics_contract": "working-capital-relation-semantics-v1",
                "relation_id": "working-capital-relation:fixture",
                "semantic_scope": "exact_total_inventory",
            },
        },
        {
            "ref_id": "canonical:valuation",
            "category": "valuation",
            "label": "valuation",
            "as_of": "2026-09-18",
            "statement": "동결된 밸류에이션 근거",
        },
        {
            "ref_id": "canonical:price",
            "category": "price_structure",
            "label": "price",
            "as_of": "2026-09-18",
            "statement": "동결된 가격 근거",
        },
        {
            "ref_id": "canonical:security_basis:current",
            "category": "quality",
            "label": "security_basis",
            "as_of": "2026-09-18",
            "statement": "동결된 증권 기준",
        },
    ]


def _business_owner(
    catalog: dict[str, object], metadata: list[dict[str, object]]
) -> list[dict[str, object]]:
    row = next(item for item in metadata if item["ref_id"] == "source:business")
    return [
        {
            "ref_id": "source:business",
            "catalog_sha256": canonical_sha256(catalog),
            "source_metadata_sha256": canonical_sha256(row),
            "source_type": "frozen_legacy_business_evidence",
            "source_scope": "exact_source_business_decision_owner",
            "authority_basis": "explicit_frozen_legacy_business_owner",
            "allowed_uses": [
                SourceUse.CONTEXT,
                SourceUse.BUSINESS_CONTEXT,
                SourceUse.PASS_A_ARCHETYPE,
                SourceUse.PASS_A_VALUATION_TIER,
                SourceUse.OVERALL_DIRECTION,
                SourceUse.HOLDER_STANCE,
                SourceUse.NEW_BUYER_EXECUTION_RISK,
            ],
            "prohibited_uses": [SourceUse.VALUATION],
        }
    ]


def _bundle(*, owner: list[dict[str, object]] | None = None) -> dict[str, object]:
    catalog = _catalog()
    metadata = _metadata()
    manifest = build_trusted_source_authority_manifest(
        ticker=TICKER,
        source_generation_id=SOURCE_GENERATION,
        catalog=catalog,
        source_metadata=metadata,
        trusted_owner_overrides=owner or _business_owner(catalog, metadata),
    )
    expectation = freeze_source_use_input_expectation(
        ticker=TICKER,
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        catalog=catalog,
        source_metadata=metadata,
        authority_manifest=manifest,
    )
    projection = build_source_use_projection(
        ticker=TICKER,
        input_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        catalog=catalog,
        authority_manifest=manifest,
        current_input_expectation=expectation,
    )
    binding = freeze_source_use_binding(
        projection=projection,
        authority_manifest=manifest,
        current_input_expectation=expectation,
    )
    return {
        "catalog": catalog,
        "metadata": metadata,
        "manifest": manifest,
        "expectation": expectation,
        "projection": projection,
        "binding": binding,
    }


def _context(metadata: list[dict[str, object]]) -> dict[str, object]:
    catalog = _catalog()
    return {
        "ticker": TICKER,
        "decision_evidence": deepcopy(metadata),
        "evidence_packets": [{"ticker": TICKER, "evidence": deepcopy(metadata)}],
        "current_price": deepcopy(catalog["entry_catalog"]["current_price"]),
        "tactical_candidates": [],
        "security_valuation_basis_state": {
            "state": "RESOLVED",
            "new_buyer_price_resolution_use_allowed": True,
            "source_refs": ["canonical:security_basis:current"],
        },
    }


def _pass_a() -> dict[str, object]:
    return {"ticker": TICKER, "archetype": "DURABLE_FRANCHISE"}


def _option() -> dict[str, object]:
    return {
        "ticker": TICKER,
        "status": "RESOLVED",
        "low": 80.0,
        "high": 100.0,
        "currency": "USD",
        "evidence_refs": ["canonical:valuation"],
        "unresolved_reasons": [],
    }


def _common(bundle: dict[str, object]) -> dict[str, object]:
    return {
        "source_use_view": bundle["projection"],
        "source_use_binding": bundle["binding"],
        "source_use_expectation": bundle["expectation"],
        "source_generation_id": SOURCE_GENERATION,
        "execution_generation_id": EXECUTION_GENERATION,
        "require_source_use": True,
    }


@pytest.fixture
def dual_identity_bundle(monkeypatch):
    metadata = _metadata()
    metadata[0]["logical_condition"] = "영업이익 확인 후에만 적용"
    metadata[0]["source_ref"] = "official:조건"
    monkeypatch.setattr(__import__(__name__), "_metadata", lambda: deepcopy(metadata))
    bundle = _bundle()
    context = build_pass_b_subject_context(
        context=_context(bundle["metadata"]),
        ticker=TICKER,
        catalog=bundle["catalog"],
        pass_a=_pass_a(),
        policy_option=_option(),
        **_common(bundle),
    )
    context["security_valuation_basis_state"] = _context(bundle["metadata"])[
        "security_valuation_basis_state"
    ]
    return bundle, context


def _dual_capability(bundle, context):
    return build_pass_b_capability_catalog(
        context=context,
        catalog=bundle["catalog"],
        pass_a=_pass_a(),
        policy_option=_option(),
        raw_source_metadata=bundle["metadata"],
        **_common(bundle),
    )


def test_dual_identity_preserves_condition_and_distinct_hash_owners(dual_identity_bundle):
    bundle, context = dual_identity_bundle
    receipt = context["source_evidence_binding"]
    assert (
        context["decision_evidence"][0]["logical_condition"]
        == bundle["metadata"][0]["logical_condition"]
    )
    assert "source_ref" not in context["decision_evidence"][0]
    assert receipt["raw_source_metadata_sha256"] == bundle["expectation"]["source_metadata_sha256"]
    assert receipt["emitted_evidence_sha256"] != receipt["raw_source_metadata_sha256"]
    assert receipt["emitted_evidence_serialized_sha256"] == context_sha256(
        context["decision_evidence"]
    )
    assert receipt["emitted_evidence_serialized_sha256"] != canonical_sha256(
        context["decision_evidence"]
    )
    capability = _dual_capability(bundle, context)
    assert (
        capability["source_use_validated_metadata_sha256"] == receipt["raw_source_metadata_sha256"]
    )
    assert capability["source_transformation_binding"]["status"] == "PASS"


@pytest.mark.parametrize(
    "mutation",
    [
        "raw_value",
        "raw_digest",
        "emitted_value",
        "subject",
        "generation",
        "stale_receipt",
        "ref_add",
        "ref_remove",
        "ref_order",
        "parent_remove",
        "parent_add",
        "permission_widen",
        "permission_digest",
        "condition_omit",
        "condition_change",
        "self_hash_forgery",
        "digest_substitution",
        "serializer_mismatch",
        "receipt_remove",
        "frozen_a_swap",
        "option_swap",
    ],
)
def test_dual_identity_fail_closed(dual_identity_bundle, mutation):
    bundle, context = deepcopy(dual_identity_bundle)
    receipt = context["source_evidence_binding"]
    if mutation == "raw_value":
        bundle["metadata"][0]["statement"] = "altered"
    elif mutation == "raw_digest":
        bundle["expectation"]["source_metadata_sha256"] = "altered"
    elif mutation in {"emitted_value", "self_hash_forgery"}:
        context["decision_evidence"][0]["statement"] = "altered"
        if mutation == "self_hash_forgery":
            receipt["emitted_evidence_sha256"] = canonical_source_metadata_sha256(
                context["decision_evidence"]
            )
            receipt["emitted_evidence_serialized_sha256"] = context_sha256(
                context["decision_evidence"]
            )
    elif mutation == "subject":
        context["ticker"] = "OTHER"
    elif mutation == "generation":
        receipt["execution_generation_id"] = "old-generation"
    elif mutation == "stale_receipt":
        receipt["transformation_version"] = "old-transform"
    elif mutation == "ref_add":
        context["decision_evidence"].append({**context["decision_evidence"][0], "ref_id": "extra"})
    elif mutation == "ref_remove":
        context["decision_evidence"].pop()
    elif mutation == "ref_order":
        context["decision_evidence"].reverse()
    elif mutation == "parent_remove":
        context["accepted_fundamental_claims"][1]["parent_source_refs"] = []
    elif mutation == "parent_add":
        context["accepted_fundamental_claims"][0]["parent_source_refs"].append(
            "canonical:working-capital-relation:fixture"
        )
    elif mutation == "permission_widen":
        context["source_use_projection"]["source_permissions"][0]["allowed_uses"].append("FORGED")
    elif mutation == "permission_digest":
        receipt["permission_derivation_sha256"] = "forged"
    elif mutation == "condition_omit":
        context["decision_evidence"][0].pop("logical_condition")
    elif mutation == "condition_change":
        context["decision_evidence"][0]["logical_condition"] = None
    elif mutation == "digest_substitution":
        receipt["raw_source_metadata_sha256"] = receipt["emitted_evidence_sha256"]
    elif mutation == "serializer_mismatch":
        receipt["emitted_evidence_serialized_sha256"] = canonical_sha256(
            context["decision_evidence"]
        )
    elif mutation == "receipt_remove":
        context.pop("source_evidence_binding")
    elif mutation == "frozen_a_swap":
        context["frozen_pass_a_classification"]["archetype"] = "OTHER"
    elif mutation == "option_swap":
        context["deterministic_fundamental_option"]["high"] = 999.0
    with pytest.raises(ValueError):
        _dual_capability(bundle, context)


def test_dual_identity_requires_actual_raw_input(dual_identity_bundle):
    bundle, context = dual_identity_bundle
    with pytest.raises(ValueError, match="raw_source_metadata_required"):
        build_pass_b_capability_catalog(
            context=context,
            catalog=bundle["catalog"],
            pass_a=_pass_a(),
            policy_option=_option(),
            **_common(bundle),
        )


def test_request_capture_rejects_stale_capability(dual_identity_bundle, tmp_path):
    from scripts import m12dc_fresh_source_use_two_pass_reproof as owner

    bundle, context = dual_identity_bundle
    capability = _dual_capability(bundle, context)
    capability["source_transformation_binding"]["emitted_evidence_serialized_sha256"] = "stale"
    context["pass_b_capability_catalog"] = capability
    chain = {
        "source_generation_id": SOURCE_GENERATION,
        "authority": bundle["manifest"],
        **{key: bundle[key] for key in ("projection", "binding", "expectation")},
    }
    with pytest.raises(owner.M12DCFailure, match="pass_b_untrusted_capability"):
        owner._request_capture(
            root=tmp_path,
            stage="pass-b",
            market="us",
            batch=1,
            subjects=(TICKER,),
            contexts={TICKER: context},
            catalogs={TICKER: bundle["catalog"]},
            chains={TICKER: chain},
            generation_id=EXECUTION_GENERATION,
            fixture_only=True,
            capabilities={TICKER: capability},
            raw_source_metadata_by_ticker={TICKER: bundle["metadata"]},
        )


def _selection() -> dict[str, object]:
    return {
        "decisions": {
            TICKER: {
                "overall_direction": "BUY",
                "directional_buy_score": 6.0,
                "decision_confidence": "MEDIUM",
                "decisive_supporting_claim_refs": ["claim:bull"],
                "decisive_contradicting_claim_refs": [],
                "thesis_state": "INTACT",
                "holder_decision": {
                    "holder": "HOLDABLE",
                    "reason_class": "NOT_APPLICABLE",
                    "reason": "핵심 논리를 훼손하는 근거가 없습니다.",
                    "evidence_refs": [],
                },
                "new_buyer_decision": {
                    "new_buyer": "ATTRACTIVE",
                    "reason_class": "ATTRACTIVE_WITHIN_RANGE",
                    "reason": "결정론적 범위 안입니다.",
                    "evidence_refs": ["canonical:valuation"],
                    "tactical_choice": "NOT_APPLICABLE",
                    "re_evaluate_conditions": [],
                },
                "policy_summary": "세 축을 분리해 판단했습니다.",
            }
        }
    }


def _forged_projection(bundle: dict[str, object]) -> dict[str, object]:
    projection = deepcopy(bundle["projection"])
    for record in (
        projection["source_records"]["canonical:working-capital-relation:fixture"],
        projection["claim_records"]["claim:wc"],
    ):
        record["allowed_uses"] = sorted({*record["allowed_uses"], SourceUse.OVERALL_DIRECTION})
        record["prohibited_uses"] = [
            use for use in record.get("prohibited_uses", []) if use != SourceUse.OVERALL_DIRECTION
        ]
    projection["permission_derivation_sha256"] = projection_permission_derivation_sha256(projection)
    projection.pop("projection_sha256")
    projection["projection_sha256"] = canonical_sha256(projection)
    return projection


def _manual_binding(bundle: dict[str, object], projection: dict[str, object]) -> dict[str, object]:
    binding = deepcopy(bundle["binding"])
    binding["permission_derivation_sha256"] = projection["permission_derivation_sha256"]
    binding["projection_sha256"] = projection["projection_sha256"]
    binding.pop("binding_sha256")
    binding["binding_sha256"] = canonical_sha256(binding)
    return binding


def test_coherent_forged_pair_fails_constructor_and_actual_consumer() -> None:
    bundle = _bundle()
    projection = _forged_projection(bundle)

    with pytest.raises(ValueError, match="source_use_binding_permission_derivation_mismatch"):
        freeze_source_use_binding(
            projection=projection,
            authority_manifest=bundle["manifest"],
            current_input_expectation=bundle["expectation"],
        )

    binding = _manual_binding(bundle, projection)
    assert validate_source_use_projection_binding(projection, binding)["status"] == "PASS"
    validation = validate_source_use_current_input(
        projection,
        binding,
        bundle["expectation"],
        ticker=TICKER,
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        catalog=bundle["catalog"],
        source_metadata=bundle["metadata"],
    )
    assert validation["status"] == "FAIL"
    assert "source_use_projection_expected_permission_derivation_mismatch" in validation["errors"]
    assert "source_use_binding_expected_permission_derivation_mismatch" in validation["errors"]

    common = _common(bundle)
    common.update(source_use_view=projection, source_use_binding=binding)
    with pytest.raises(ValueError, match="pass_b_source_use_current_input_invalid"):
        build_pass_b_subject_context(
            context=_context(bundle["metadata"]),
            ticker=TICKER,
            catalog=bundle["catalog"],
            pass_a=_pass_a(),
            policy_option=_option(),
            **common,
        )
    with pytest.raises(ValueError, match="capability_source_use_current_input_invalid"):
        build_pass_b_capability_catalog(
            context=_context(bundle["metadata"]),
            catalog=bundle["catalog"],
            pass_a=_pass_a(),
            policy_option=_option(),
            **common,
        )

    legitimate_capability = build_pass_b_capability_catalog(
        context=_context(bundle["metadata"]),
        catalog=bundle["catalog"],
        pass_a=_pass_a(),
        policy_option=_option(),
        **_common(bundle),
    )
    final = validate_capability_selection(
        _selection(),
        subjects=(TICKER,),
        catalogs={TICKER: bundle["catalog"]},
        capabilities={TICKER: legitimate_capability},
        source_use_views={TICKER: projection},
        source_use_bindings={TICKER: binding},
        source_use_expectations={TICKER: bundle["expectation"]},
        source_metadata_by_ticker={TICKER: bundle["metadata"]},
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        require_source_use=True,
    )
    assert final["status"] == "FAIL"
    assert any(
        "EXPECTED_PERMISSION_DERIVATION_MISMATCH" in error.upper() for error in final["errors"]
    )


def test_genuine_owner_derived_permission_change_builds_a_new_valid_chain() -> None:
    catalog = _catalog()
    metadata = _metadata()
    owner = _business_owner(catalog, metadata)
    owner[0]["allowed_uses"].append(SourceUse.VALUATION)
    owner[0]["prohibited_uses"] = []
    bundle = _bundle(owner=owner)
    validation = validate_source_use_current_input(
        bundle["projection"],
        bundle["binding"],
        bundle["expectation"],
        ticker=TICKER,
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        catalog=bundle["catalog"],
        source_metadata=bundle["metadata"],
    )
    assert validation["status"] == "PASS"
    assert (
        bundle["projection"]["permission_derivation_sha256"]
        == bundle["expectation"]["permission_derivation_sha256"]
    )


@pytest.mark.parametrize("surface", ["packet", "top_level"])
def test_dual_evidence_surface_drift_is_rejected_before_materialization(surface: str) -> None:
    bundle = _bundle()
    context = _context(bundle["metadata"])
    target = (
        context["evidence_packets"][0]["evidence"]
        if surface == "packet"
        else context["decision_evidence"]
    )
    target[0]["statement"] = f"changed-{surface}-only"
    common = _common(bundle)

    with pytest.raises(ValueError, match="subject_evidence_surface_mismatch"):
        build_pass_a_subject_context(
            context=context,
            ticker=TICKER,
            catalog=bundle["catalog"],
            **common,
        )
    with pytest.raises(ValueError, match="subject_evidence_surface_mismatch"):
        build_pass_b_subject_context(
            context=context,
            ticker=TICKER,
            catalog=bundle["catalog"],
            pass_a=_pass_a(),
            policy_option=_option(),
            **common,
        )
    with pytest.raises(ValueError, match="subject_evidence_surface_mismatch"):
        build_pass_b_capability_catalog(
            context=context,
            catalog=bundle["catalog"],
            pass_a=_pass_a(),
            policy_option=_option(),
            **common,
        )


def test_order_stable_authoritative_view_is_compacted_bound_and_serialized() -> None:
    bundle = _bundle()
    context = _context(bundle["metadata"])
    context["evidence_packets"][0]["evidence"].reverse()
    common = _common(bundle)
    pass_a = build_pass_a_subject_context(
        context=context,
        ticker=TICKER,
        catalog=bundle["catalog"],
        **common,
    )
    pass_b = build_pass_b_subject_context(
        context=context,
        ticker=TICKER,
        catalog=bundle["catalog"],
        pass_a=_pass_a(),
        policy_option=_option(),
        **common,
    )
    capability = build_pass_b_capability_catalog(
        context=context,
        catalog=bundle["catalog"],
        pass_a=_pass_a(),
        policy_option=_option(),
        **common,
    )

    evidence_binding = pass_b["source_evidence_binding"]
    assert evidence_binding["surface_parity_checked"] is True
    assert (
        evidence_binding["validated_source_metadata_sha256"]
        == bundle["expectation"]["source_metadata_sha256"]
    )
    assert evidence_binding["emitted_evidence_sha256"] == canonical_source_metadata_sha256(
        pass_b["decision_evidence"]
    )
    assert evidence_binding["emitted_evidence_serialized_sha256"] == context_sha256(
        pass_b["decision_evidence"]
    )
    assert (
        evidence_binding["permission_derivation_sha256"]
        == bundle["expectation"]["permission_derivation_sha256"]
    )
    assert (
        capability["source_use_validated_metadata_sha256"]
        == bundle["expectation"]["source_metadata_sha256"]
    )
    assert (
        capability["source_use_permission_derivation_sha256"]
        == bundle["expectation"]["permission_derivation_sha256"]
    )
    assert all("runtime_only_field" not in row for row in pass_b["decision_evidence"])
    assert all("current_price" not in row for row in pass_a["eligible_non_price_evidence"])

    prompt = pass_b_prompt(
        identity={"generation_id": "offline", "subjects": [TICKER]},
        policy_principles={"scope": "offline"},
        subject_contexts=[pass_b],
    )
    serialized = json.dumps([pass_b], ensure_ascii=False, separators=(",", ":"), default=str)
    assert prompt.endswith(serialized)
    assert "runtime_only_field" in evidence_binding["removed_fields"]
    assert "not-model-visible" not in prompt
    assert evidence_binding["permission_derivation_sha256"] in prompt


def test_duplicate_ref_fails_before_model_context() -> None:
    bundle = _bundle()
    context = _context(bundle["metadata"])
    duplicate = deepcopy(bundle["metadata"][0])
    context["decision_evidence"].append(deepcopy(duplicate))
    context["evidence_packets"][0]["evidence"].append(deepcopy(duplicate))
    with pytest.raises(ValueError, match="subject_evidence_duplicate_ref"):
        build_pass_b_subject_context(
            context=context,
            ticker=TICKER,
            catalog=bundle["catalog"],
            pass_a=_pass_a(),
            policy_option=_option(),
            **_common(bundle),
        )
