"""Offline current-A gate. Validate existing authority; never manufacture owners."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence

from scripts.m12cq_two_pass_contract import (
    _source_use_authorized_pass_a_uses,
    build_pass_a_subject_context,
    pass_a_leakage_scan,
)
from scripts.m12cr_r1_typed_quality_contract import build_r1_pass_a_context
from scripts.m12da_source_use_contract import (
    canonical_sha256,
    freeze_source_use_input_expectation,
    validate_source_use_current_input,
)
from scripts.m12db_model_view_readiness import M12DBFailure, bind_final_pass_a_model_view


INSUFFICIENT = "CURRENT_PASS_A_SOURCE_AUTHORITY_INSUFFICIENT"


def preflight_current_pass_a_subject(
    *,
    ticker: str,
    source_generation_id: str,
    execution_generation_id: str,
    catalog: Mapping[str, object],
    source_packet: Mapping[str, object],
    authority: Mapping[str, object],
    projection: Mapping[str, object],
    binding: Mapping[str, object],
    expectation: Mapping[str, object],
    prohibited_pass_a_source_refs: Sequence[str] = (),
) -> dict[str, object]:
    """Run the real builder/filter/binding path before exposing a request context."""
    claims = list(catalog.get("atomic_claims") or ())
    metadata = list(source_packet.get("decision_evidence") or ())
    reasons: Counter[str] = Counter()
    receipt = {
        "ticker": ticker,
        "source_generation_id": source_generation_id,
        "execution_generation_id": execution_generation_id,
        "total_claims": len(claims),
        "authorized_a_claims": 0,
        "contextual_only_claims": 0,
        "denied_or_unknown_claims": 0,
        "claims_before_typed_filter": 0,
        "claims_after_typed_filter": 0,
        "non_price_evidence_before_typed_filter": 0,
        "non_price_evidence_after_typed_filter": 0,
        "manifest_binding_status": "NOT_CHECKED",
        "parents_status": "NOT_CHECKED",
    }
    final = None
    try:
        if ticker != source_packet.get("ticker") or ticker != catalog.get("ticker"):
            raise ValueError("subject_identity_mismatch")
        expected = freeze_source_use_input_expectation(
            ticker=ticker,
            source_generation_id=source_generation_id,
            execution_generation_id=execution_generation_id,
            catalog=catalog,
            source_metadata=metadata,
            authority_manifest=authority,
        )
        if expected != expectation:
            raise ValueError("current_authority_expectation_mismatch")
        validation = validate_source_use_current_input(
            projection,
            binding,
            expectation,
            ticker=ticker,
            source_generation_id=source_generation_id,
            execution_generation_id=execution_generation_id,
            catalog=catalog,
            source_metadata=metadata,
        )
        if validation["status"] != "PASS":
            raise ValueError("current_source_binding_invalid")
        receipt["manifest_binding_status"] = "PASS"

        known = set(catalog.get("all_evidence_refs") or ())
        seen = set()
        for claim in claims:
            ref = claim.get("claim_ref")
            parents = list(claim.get("parent_source_refs") or ())
            if claim.get("ticker") != ticker:
                reasons["claim_subject_mismatch"] += 1
            if not ref or ref in seen:
                reasons["claim_identity_missing_or_duplicate"] += 1
            seen.add(ref)
            if not parents or not set(parents).issubset(known):
                reasons["claim_parent_missing_or_unknown"] += 1
            uses = _source_use_authorized_pass_a_uses(
                source_use_view=projection,
                source_use_binding=binding,
                claim_ref=str(ref or ""),
                parent_refs=parents,
            )
            record = projection.get("claim_records", {}).get(ref, {})
            if uses:
                receipt["authorized_a_claims"] += 1
            elif record.get("authority_state") == "RESOLVED":
                receipt["contextual_only_claims"] += 1
                reasons["parent_permission_intersection_has_no_decisive_a_use"] += 1
            else:
                receipt["denied_or_unknown_claims"] += 1
                reasons["unresolved_parent_authority"] += 1
        parent_errors = any(
            reasons[key]
            for key in (
                "claim_subject_mismatch",
                "claim_identity_missing_or_duplicate",
                "claim_parent_missing_or_unknown",
            )
        )
        receipt["parents_status"] = "FAIL" if parent_errors else "PASS"
        if parent_errors:
            raise ValueError("atomic_parent_integrity_failed")

        context = {"evidence_packets": [{"ticker": ticker, "evidence": metadata}]}
        base = build_pass_a_subject_context(
            context=context,
            ticker=ticker,
            catalog=catalog,
            source_use_view=projection,
            source_use_binding=binding,
            source_use_expectation=expectation,
            source_generation_id=source_generation_id,
            execution_generation_id=execution_generation_id,
            require_source_use=True,
        )
        filtered = build_r1_pass_a_context(base, source_packet=source_packet)
        final = bind_final_pass_a_model_view(
            intermediate_context=base, final_context=filtered, source_packet=source_packet
        )
        receipt["claims_before_typed_filter"] = len(base["eligible_claim_refs"])
        receipt["claims_after_typed_filter"] = len(final["eligible_claim_refs"])
        receipt["non_price_evidence_before_typed_filter"] = len(base["eligible_non_price_evidence"])
        receipt["non_price_evidence_after_typed_filter"] = len(final["eligible_non_price_evidence"])
        if not final["eligible_claim_refs"]:
            raise ValueError(
                "typed_quality_filter_removed_all_claims"
                if base["eligible_claim_refs"]
                else "no_authorized_builder_eligible_claims"
            )
        if not final["eligible_non_price_evidence"]:
            raise ValueError("no_eligible_non_price_evidence")
        visible_refs = {row["ref_id"] for row in final["eligible_non_price_evidence"]}
        if visible_refs & set(prohibited_pass_a_source_refs):
            raise ValueError("source_policy_pass_a_visibility_leak")
        if pass_a_leakage_scan([final])["status"] != "PASS":
            raise ValueError("pass_a_price_leakage")
        receipt["final_model_view_sha256"] = canonical_sha256(final)
        receipt["status"] = "PASS"
    except (ValueError, M12DBFailure) as exc:
        # Error categories only: no source statement or model judgment in audit output.
        reasons[str(exc).split(":", 1)[0]] += 1
        receipt["status"] = INSUFFICIENT
        final = None
    receipt["denial_reason_counts"] = dict(sorted((k, v) for k, v in reasons.items() if v))
    return {"receipt": receipt, "model_context": final}


def preflight_current_pass_a_cohort(
    subject_inputs: Sequence[Mapping[str, object]], *, expected_subjects: Sequence[str]
) -> dict[str, object]:
    """An incomplete/failed cohort exposes no contexts, including otherwise safe rows."""
    tickers = [str(row.get("ticker") or "") for row in subject_inputs]
    population_ok = (
        bool(expected_subjects)
        and len(set(expected_subjects)) == len(expected_subjects)
        and Counter(tickers) == Counter(expected_subjects)
    )
    identities = {
        (row.get("source_generation_id"), row.get("execution_generation_id"))
        for row in subject_inputs
    }
    results = [preflight_current_pass_a_subject(**row) for row in subject_inputs]
    receipts = [result["receipt"] for result in results]
    passed = sum(row["status"] == "PASS" for row in receipts)
    allow = population_ok and len(identities) == 1 and passed == len(expected_subjects)
    return {
        "status": "PASS" if allow else INSUFFICIENT,
        "allow_model_calls": allow,
        "expected_subjects": list(expected_subjects),
        "population_status": "PASS" if population_ok else "FAIL",
        "generation_parity_status": "PASS" if len(identities) == 1 else "FAIL",
        "passed_subjects": passed,
        "subjects": receipts,
        "model_contexts": (
            {row["receipt"]["ticker"]: row["model_context"] for row in results} if allow else {}
        ),
    }
