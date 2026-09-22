"""Project Pass-A schema choices through existing, caller-bound source-use owners."""
from collections.abc import Mapping

from scripts.m12cq_two_pass_contract import PASS_A_SOURCE_USES, canonical_sha256 as model_view_sha256
from scripts.m12da_source_use_contract import (
    SourceUse, model_source_use_projection,
    validate_selected_refs, validate_source_use_current_input,
)


def pass_a_axis_refs(context: Mapping, inputs: Mapping) -> dict:
    ticker = str(context.get("ticker") or "")
    catalog, chain, metadata = inputs["catalog"], inputs["chain"], inputs["source_metadata"]
    projection, binding = chain["projection"], chain["binding"]
    validation = validate_source_use_current_input(
        projection, binding, chain["expectation"], ticker=ticker,
        source_generation_id=inputs["source_generation_id"],
        execution_generation_id=inputs["execution_generation_id"],
        catalog=catalog, source_metadata=metadata,
    )
    if validation["status"] != "PASS":
        raise ValueError("pass_a_schema_current_source_binding_invalid")
    registered = {r["claim_ref"]: r for r in catalog.get("atomic_claims", ())}
    claims = list(context.get("eligible_claim_refs") or ())
    if len(set(claims)) != len(claims) or not set(claims) <= set(registered):
        raise ValueError("pass_a_schema_unknown_or_duplicate_claim")
    if any(registered[r].get("ticker") != ticker for r in claims):
        raise ValueError("pass_a_schema_cross_subject_claim")
    receipt = context.get("source_evidence_binding") or {}
    visible = context.get("source_use_projection") or {}
    expected_view = model_source_use_projection(
        projection, binding=binding, uses=PASS_A_SOURCE_USES,
        claim_refs=visible.get("model_claim_refs"), source_refs=visible.get("model_source_refs"),
    )
    if expected_view != visible:
        raise ValueError("pass_a_schema_model_permission_view_invalid")
    if (
        receipt.get("source_use_binding_sha256") != binding["binding_sha256"]
        or receipt.get("expected_source_metadata_sha256") != chain["expectation"]["source_metadata_sha256"]
        or receipt.get("validated_source_metadata_sha256") != chain["expectation"]["source_metadata_sha256"]
        or receipt.get("emitted_claims_sha256") != model_view_sha256(context.get("accepted_fundamental_claims"))
        or receipt.get("emitted_evidence_serialized_sha256") != model_view_sha256(context.get("eligible_non_price_evidence"))
        or receipt.get("emitted_claim_refs") != claims
    ):
        raise ValueError("pass_a_schema_consumed_view_binding_invalid")
    if receipt.get("contract") == "m12db-r1-final-pass-a-model-view-binding-v1":
        from scripts.m12db_model_view_readiness import _pass_a_final_view_payload

        digest = model_view_sha256(_pass_a_final_view_payload(context))
        if receipt.get("actual_final_view_sha256") != digest or receipt.get("expected_final_view_sha256") != digest:
            raise ValueError("pass_a_schema_final_view_binding_invalid")

    def allowed(use):
        return [ref for ref in claims if validate_selected_refs(
            projection, refs=[ref], use=use, require_any=True, binding=binding,
        )["status"] == "PASS"]

    # Quality has a typed catalog role, not a separate SourceUse enum in the validator.
    quality = context.get("data_quality_catalog") or {}
    known = set(catalog.get("all_evidence_refs") or ())
    source_refs = {r["ref_id"] for r in metadata}
    if not set(quality.get("evidence_refs") or ()) <= known & source_refs:
        raise ValueError("pass_a_schema_unbound_quality_ref")
    result = {
        "archetype": allowed(SourceUse.PASS_A_ARCHETYPE),
        "tier": allowed(SourceUse.PASS_A_VALUATION_TIER),
    }
    for name in ("material_disclosure_failure_refs", "positive_quality_refs"):
        refs = set(quality.get(name) or ())
        if not refs <= known & source_refs & set(catalog.get(name) or ()):
            raise ValueError("pass_a_schema_unbound_quality_role")
        result[name] = sorted(refs & set(quality.get("evidence_refs") or ()))
    return result
