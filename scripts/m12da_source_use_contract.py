from __future__ import annotations

import hashlib
import html
import json
import re
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum


LEGACY_SOURCE_USE_CONTRACT = "m12da-shadow-source-use-projection-v1"
SOURCE_USE_CONTRACT = "m12da-r3-source-use-projection-v4"
SOURCE_AUTHORITY_CONTRACT = "m12da-r2-trusted-metadata-authority-v2"
SOURCE_USE_BINDING_CONTRACT = "m12da-r3-source-use-binding-v3"
SOURCE_INPUT_EXPECTATION_CONTRACT = "m12da-r3-current-input-expectation-v2"
PERMISSION_DERIVATION_CONTRACT = "m12da-r3-authority-permission-derivation-v1"
LEGACY_DEFINITION_BINDING_CONTRACT = "m12da-legacy-metric-definition-binding-v1"
DEFINITION_BINDING_CONTRACT = "m12da-r1-metric-definition-binding-v2"
SECURITY_IDENTITY_CONTRACT = "m12da-r1-sec-traded-security-identity-v1"
TRUSTED_AUTHORITY_ORIGIN = "TRUSTED_FROZEN_SOURCE_METADATA"
TRUSTED_INPUT_EXPECTATION_ORIGIN = "CALLER_FROZEN_CURRENT_INPUT"


class SourceUse(StrEnum):
    CONTEXT = "CONTEXT"
    BUSINESS_CONTEXT = "BUSINESS_CONTEXT"
    EARNINGS_QUALITY_CONTEXT = "EARNINGS_QUALITY_CONTEXT"
    EXPECTATIONS_CONTEXT = "EXPECTATIONS_CONTEXT"
    PRICE_ENTRY_CONTEXT = "PRICE_ENTRY_CONTEXT"
    CONFIDENCE = "CONFIDENCE"
    PASS_A_ARCHETYPE = "PASS_A_ARCHETYPE"
    PASS_A_VALUATION_TIER = "PASS_A_VALUATION_TIER"
    OVERALL_DIRECTION = "OVERALL_DIRECTION"
    HOLDER_STANCE = "HOLDER_STANCE"
    NEW_BUYER_EXECUTION_RISK = "NEW_BUYER_EXECUTION_RISK"
    VALUATION = "VALUATION"
    ENTRY = "ENTRY"


DECISIVE_USES = frozenset(
    {
        SourceUse.PASS_A_ARCHETYPE.value,
        SourceUse.PASS_A_VALUATION_TIER.value,
        SourceUse.OVERALL_DIRECTION.value,
        SourceUse.HOLDER_STANCE.value,
        SourceUse.NEW_BUYER_EXECUTION_RISK.value,
        SourceUse.VALUATION.value,
    }
)

_QUALITY_PREFIXES = (
    "canonical:financial_quality:",
    "canonical:business_quality:",
    "canonical:security_identity:",
    "canonical:security_basis:",
)


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def canonical_source_metadata_sha256(
    source_metadata: Sequence[Mapping[str, object]],
) -> str:
    """Hash metadata by semantic row identity, independent of loader directory order."""
    normalized = sorted(
        (dict(row) for row in source_metadata),
        key=lambda row: (str(row.get("ref_id") or ""), canonical_sha256(row)),
    )
    return canonical_sha256(normalized)


def _ordered_unique(values: Sequence[object]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))


def _baseline_source_uses(ref_id: str, catalog: Mapping[str, object]) -> set[str]:
    valuation = {str(ref) for ref in catalog.get("valuation_evidence_refs") or ()}
    timing = {str(ref) for ref in catalog.get("timing_evidence_refs") or ()}
    confidence = (
        {str(ref) for ref in catalog.get("positive_quality_refs") or ()}
        | {str(ref) for ref in catalog.get("business_quality_confidence_refs") or ()}
        | {str(ref) for ref in catalog.get("security_valuation_basis_refs") or ()}
    )
    if ref_id in valuation:
        return {
            SourceUse.CONTEXT.value,
            SourceUse.PRICE_ENTRY_CONTEXT.value,
            SourceUse.VALUATION.value,
            SourceUse.ENTRY.value,
        }
    if ref_id in timing:
        return {
            SourceUse.CONTEXT.value,
            SourceUse.PRICE_ENTRY_CONTEXT.value,
            SourceUse.ENTRY.value,
        }
    if ref_id in confidence or ref_id.startswith(_QUALITY_PREFIXES):
        return {SourceUse.CONTEXT.value, SourceUse.CONFIDENCE.value}
    return {
        SourceUse.CONTEXT.value,
        SourceUse.BUSINESS_CONTEXT.value,
        SourceUse.PASS_A_ARCHETYPE.value,
        SourceUse.PASS_A_VALUATION_TIER.value,
        SourceUse.OVERALL_DIRECTION.value,
        SourceUse.HOLDER_STANCE.value,
        SourceUse.NEW_BUYER_EXECUTION_RISK.value,
    }


def _authority_index(
    rows: Sequence[Mapping[str, object]],
    *,
    expected_ticker: str,
    known_refs: set[str],
    kind: str,
) -> tuple[dict[str, Mapping[str, object]], list[str]]:
    indexed: dict[str, Mapping[str, object]] = {}
    errors: list[str] = []
    key = "claim_ref" if kind == "claim" else "ref_id"
    for row in rows:
        ref_id = str(row.get(key) or "")
        ticker = str(row.get("ticker") or "")
        if not ref_id:
            errors.append(f"{kind}_authority_ref_missing")
            continue
        if ticker != expected_ticker:
            errors.append(f"{kind}_authority_cross_subject:{ref_id}")
            continue
        if row.get("authority_origin") != TRUSTED_AUTHORITY_ORIGIN:
            errors.append(f"{kind}_authority_untrusted_origin:{ref_id}")
            continue
        if ref_id not in known_refs:
            errors.append(f"{kind}_authority_unknown_ref:{ref_id}")
            continue
        if ref_id in indexed:
            errors.append(f"{kind}_authority_duplicate:{ref_id}")
            continue
        indexed[ref_id] = row
    return indexed, errors


def _apply_authority(
    *,
    inherited_uses: set[str],
    authority: Mapping[str, object] | None,
    allow_expansion: bool,
) -> tuple[set[str], str, list[str]]:
    if authority is None:
        return inherited_uses, "FROZEN_PREEXISTING_SCOPE", []
    state = str(authority.get("authority_state") or "UNRESOLVED")
    allowed = {str(use) for use in authority.get("allowed_uses") or ()}
    prohibited = {str(use) for use in authority.get("prohibited_uses") or ()}
    reasons = _ordered_unique(authority.get("denial_reasons") or ())
    if state != "RESOLVED":
        allowed &= {
            SourceUse.CONTEXT.value,
            SourceUse.BUSINESS_CONTEXT.value,
            SourceUse.EARNINGS_QUALITY_CONTEXT.value,
            SourceUse.EXPECTATIONS_CONTEXT.value,
            SourceUse.PRICE_ENTRY_CONTEXT.value,
            SourceUse.CONFIDENCE.value,
        }
        reasons.append(str(authority.get("unresolved_cause") or "source_authority_unresolved"))
    # Trusted source authority may replace coarse legacy catalog scope. Claim-level authority can
    # only narrow the intersection of its parents, so a projected/model claim cannot grant itself.
    if "allowed_uses" in authority:
        effective = set(allowed) if allow_expansion else inherited_uses & allowed
    else:
        effective = set(inherited_uses)
    effective -= prohibited
    return effective, state, _ordered_unique(reasons)


def _build_legacy_source_use_projection(
    *,
    ticker: str,
    input_generation_id: str,
    catalog: Mapping[str, object],
    source_authorities: Sequence[Mapping[str, object]] = (),
    claim_authorities: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    """Create a deny-on-unknown, subject-local source-use view.

    Existing catalog scope is preserved only for refs already frozen in the subject catalog.
    Trusted source authority may replace that coarse scope; claim authority can only narrow the
    intersection of its parents. Model-authored fields in evidence or claims are ignored.
    """
    if not ticker or ticker != str(catalog.get("ticker") or ""):
        raise ValueError("source_use_subject_catalog_mismatch")
    if not input_generation_id:
        raise ValueError("source_use_generation_missing")

    evidence_refs = {str(ref) for ref in catalog.get("all_evidence_refs") or ()}
    claims = {
        str(row.get("claim_ref") or ""): row
        for row in catalog.get("atomic_claims") or ()
        if isinstance(row, Mapping) and str(row.get("claim_ref") or "")
    }
    claim_refs = set(claims)
    source_index, errors = _authority_index(
        source_authorities,
        expected_ticker=ticker,
        known_refs=evidence_refs,
        kind="source",
    )
    claim_index, claim_errors = _authority_index(
        claim_authorities,
        expected_ticker=ticker,
        known_refs=claim_refs,
        kind="claim",
    )
    errors.extend(claim_errors)

    source_records: dict[str, dict[str, object]] = {}
    for ref_id in sorted(evidence_refs):
        authority = source_index.get(ref_id)
        uses, state, reasons = _apply_authority(
            inherited_uses=_baseline_source_uses(ref_id, catalog),
            authority=authority,
            allow_expansion=True,
        )
        source_records[ref_id] = {
            "ref_id": ref_id,
            "ticker": ticker,
            "source_type": (
                authority.get("source_type") if authority is not None else "frozen_catalog_ref"
            ),
            "source_scope": (
                authority.get("source_scope")
                if authority is not None
                else "preexisting_subject_catalog_scope_only"
            ),
            "source_period": authority.get("source_period") if authority is not None else None,
            "authority_state": state,
            "authority_basis": (
                authority.get("authority_basis")
                if authority is not None
                else "frozen_preexisting_catalog_membership"
            ),
            "authority_origin": (
                authority.get("authority_origin") if authority is not None else None
            ),
            "allowed_uses": sorted(uses),
            "prohibited_uses": sorted(str(use) for use in (authority.get("prohibited_uses") or ()))
            if authority is not None
            else [],
            "denial_reasons": reasons,
            "independence_group": (
                str(authority.get("independence_group") or ref_id)
                if authority is not None
                else ref_id
            ),
            "fact_kind": (
                authority.get("fact_kind") if authority is not None else "frozen_evidence_ref"
            ),
            "definition_binding_ref": (
                authority.get("definition_binding_ref") if authority is not None else None
            ),
        }

    claim_records: dict[str, dict[str, object]] = {}
    for claim_ref, row in sorted(claims.items()):
        parents = _ordered_unique(row.get("parent_source_refs") or ())
        missing = [ref for ref in parents if ref not in source_records]
        if parents and not missing:
            parent_uses = [set(source_records[ref]["allowed_uses"]) for ref in parents]
            inherited = set.intersection(*parent_uses)
            parent_states = {str(source_records[ref]["authority_state"]) for ref in parents}
            inherited_state = (
                "RESOLVED" if parent_states == {"RESOLVED"} else "FROZEN_PREEXISTING_SCOPE"
            )
        else:
            inherited = set()
            inherited_state = "UNRESOLVED"
        authority = claim_index.get(claim_ref)
        uses, state, reasons = _apply_authority(
            inherited_uses=inherited,
            authority=authority,
            allow_expansion=False,
        )
        if authority is None:
            state = inherited_state
        if missing:
            reasons.append("claim_parent_authority_missing:" + ",".join(sorted(missing)))
        if not parents:
            reasons.append("claim_parent_refs_missing")
        claim_records[claim_ref] = {
            "claim_ref": claim_ref,
            "ticker": ticker,
            "parent_source_refs": parents,
            "authority_state": state,
            "authority_basis": (
                authority.get("authority_basis")
                if authority is not None
                else "intersection_of_parent_source_permissions"
            ),
            "authority_origin": (
                authority.get("authority_origin") if authority is not None else None
            ),
            "allowed_uses": sorted(uses),
            "prohibited_uses": sorted(str(use) for use in (authority.get("prohibited_uses") or ()))
            if authority is not None
            else [],
            "denial_reasons": _ordered_unique(reasons),
            "polarity": (
                row.get("claim", {}).get("polarity")
                if isinstance(row.get("claim"), Mapping)
                else None
            ),
            "compound_parent_count": len(parents),
        }

    projection: dict[str, object] = {
        "contract": LEGACY_SOURCE_USE_CONTRACT,
        "contract_version": 1,
        "ticker": ticker,
        "input_generation_id": input_generation_id,
        "source_records": source_records,
        "claim_records": claim_records,
        "projection_errors": sorted(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }
    projection["projection_sha256"] = canonical_sha256(projection)
    return projection


def _decoded_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return decoded if isinstance(decoded, Mapping) else {}
    return {}


def _trusted_metadata_scope(
    *,
    row: Mapping[str, object],
    ref_id: str,
    catalog: Mapping[str, object],
    atomic_parent_refs: set[str],
) -> dict[str, object]:
    """Recognize a source family before validating its admissibility.

    Display labels never identify or grant a family. Known restricted families retain their
    narrow contextual scope when metadata is malformed, while decisive uses fail closed.
    Unclassified Core/atomic membership is not an authority owner.
    """
    valuation = {str(ref) for ref in catalog.get("valuation_evidence_refs") or ()}
    timing = {str(ref) for ref in catalog.get("timing_evidence_refs") or ()}
    quality = (
        {str(ref) for ref in catalog.get("positive_quality_refs") or ()}
        | {str(ref) for ref in catalog.get("business_quality_confidence_refs") or ()}
        | {str(ref) for ref in catalog.get("security_valuation_basis_refs") or ()}
    )
    core = {str(ref) for ref in catalog.get("core_evidence_refs") or ()}
    category = str(row.get("category") or "").lower()
    statement = _decoded_mapping(row.get("statement"))
    all_uses = {item.value for item in SourceUse}

    def result(
        *,
        allowed: set[str],
        rule: str,
        source_type: str,
        scope: str,
        family: str,
        state: str = "RESOLVED",
        denial_reasons: Sequence[str] = (),
        required_metadata: Sequence[str] = (),
        compatible_versions: Sequence[str] = (),
    ) -> dict[str, object]:
        return {
            "allowed_uses": sorted(allowed),
            "prohibited_uses": sorted(all_uses - allowed),
            "authority_basis": rule,
            "source_type": source_type,
            "source_scope": scope,
            "source_family": family,
            "authority_state": state,
            "denial_reasons": _ordered_unique(denial_reasons),
            "required_metadata": list(required_metadata),
            "compatible_source_versions": list(compatible_versions),
        }

    if ref_id in valuation:
        return result(
            allowed={
                SourceUse.CONTEXT.value,
                SourceUse.PRICE_ENTRY_CONTEXT.value,
                SourceUse.VALUATION.value,
                SourceUse.ENTRY.value,
            },
            rule="catalog_typed_valuation_ref",
            source_type="typed_valuation_evidence",
            scope="valuation_and_entry_only",
            family="typed_valuation",
        )
    elif ref_id in timing:
        return result(
            allowed={
                SourceUse.CONTEXT.value,
                SourceUse.PRICE_ENTRY_CONTEXT.value,
                SourceUse.ENTRY.value,
            },
            rule="catalog_typed_timing_ref",
            source_type="typed_timing_evidence",
            scope="price_entry_context_only",
            family="typed_timing",
        )
    elif ref_id in quality or ref_id.startswith(_QUALITY_PREFIXES):
        return result(
            allowed={SourceUse.CONTEXT.value, SourceUse.CONFIDENCE.value},
            rule="catalog_typed_quality_ref",
            source_type="typed_quality_evidence",
            scope="context_and_confidence_only",
            family="typed_quality",
        )

    if ref_id.startswith("canonical:working-capital-relation:"):
        failures: list[str] = []
        if category != "earnings_quality":
            failures.append("working_capital_relation_category_mismatch")
        if statement.get("relation_semantics_contract") != (
            "working-capital-relation-semantics-v1"
        ):
            failures.append("working_capital_relation_contract_unsupported")
        if not statement.get("semantic_scope"):
            failures.append("working_capital_relation_semantic_scope_missing")
        if not statement.get("relation_family") and not statement.get("relation_id"):
            failures.append("working_capital_relation_identity_missing")
        return result(
            allowed={
                SourceUse.CONTEXT.value,
                SourceUse.EARNINGS_QUALITY_CONTEXT.value,
            },
            rule=(
                "typed_working_capital_relation_metadata"
                if not failures
                else "working_capital_relation_family_fail_closed"
            ),
            source_type="canonical_working_capital_relation",
            scope="typed_relation_and_earnings_quality_context_only",
            family="working_capital_relation",
            state="RESOLVED" if not failures else "UNRESOLVED_RESTRICTED",
            denial_reasons=failures,
            required_metadata=(
                "category=earnings_quality",
                "relation_semantics_contract",
                "semantic_scope",
                "relation_family_or_relation_id",
            ),
            compatible_versions=("working-capital-relation-semantics-v1",),
        )

    if ref_id.startswith(
        ("canonical:working-capital-derived:", "canonical:working-capital-reported:")
    ):
        failures = []
        if category != "earnings_quality":
            failures.append("working_capital_lineage_category_mismatch")
        if not statement.get("relation_id"):
            failures.append("working_capital_lineage_relation_id_missing")
        if not statement.get("semantic_scope"):
            failures.append("working_capital_lineage_semantic_scope_missing")
        return result(
            allowed={SourceUse.CONTEXT.value},
            rule=(
                "typed_working_capital_lineage_metadata"
                if not failures
                else "working_capital_lineage_family_fail_closed"
            ),
            source_type="canonical_working_capital_lineage",
            scope="lineage_context_only",
            family="working_capital_lineage",
            state="RESOLVED" if not failures else "UNRESOLVED_RESTRICTED",
            denial_reasons=failures,
            required_metadata=("category=earnings_quality", "relation_id", "semantic_scope"),
            compatible_versions=("working-capital-lineage-v1",),
        )

    if category == "expectations":
        allowed_fields = {
            "as_of_date",
            "level",
            "priced_in",
            "summary",
            "upside_surprises",
            "downside_surprises",
        }
        failures = []
        if not bool(set(statement) & {"level", "priced_in", "downside_surprises"}):
            failures.append("expectations_structured_signal_missing")
        if not set(statement).issubset(allowed_fields):
            failures.append("expectations_schema_unsupported")
        valid = not failures
        return result(
            allowed=(
                {
                    SourceUse.CONTEXT.value,
                    SourceUse.EXPECTATIONS_CONTEXT.value,
                    SourceUse.PRICE_ENTRY_CONTEXT.value,
                    SourceUse.CONFIDENCE.value,
                    SourceUse.ENTRY.value,
                }
                if valid
                else {SourceUse.CONTEXT.value, SourceUse.EXPECTATIONS_CONTEXT.value}
            ),
            rule=(
                "structured_expectations_metadata"
                if valid
                else "structured_expectations_family_fail_closed"
            ),
            source_type="structured_market_expectations",
            scope=(
                "expectations_price_confidence_entry_only"
                if valid
                else "expectations_context_only_until_schema_resolved"
            ),
            family="structured_expectations",
            state="RESOLVED" if valid else "UNRESOLVED_RESTRICTED",
            denial_reasons=failures,
            required_metadata=("category=expectations", "structured_expectation_fields"),
            compatible_versions=("structured-expectations-v1",),
        )

    membership_reasons = []
    if ref_id in core:
        membership_reasons.append("core_membership_not_authority")
    if ref_id in atomic_parent_refs:
        membership_reasons.append("atomic_parent_membership_not_authority")
    return result(
        allowed={SourceUse.CONTEXT.value},
        rule="explicit_source_owner_required",
        source_type="unclassified_frozen_evidence",
        scope="context_only_until_exact_owner_bound",
        family="unclassified",
        state="UNRESOLVED",
        denial_reasons=membership_reasons or ["trusted_source_family_unrecognized"],
        required_metadata=("explicit_existing_owner_mapping",),
    )


def build_trusted_source_authority_manifest(
    *,
    ticker: str,
    source_generation_id: str,
    catalog: Mapping[str, object],
    source_metadata: Sequence[Mapping[str, object]],
    trusted_owner_overrides: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    """Derive source-use authority only from caller-frozen metadata and catalog ownership."""
    if not ticker or ticker != str(catalog.get("ticker") or ""):
        raise ValueError("source_authority_subject_catalog_mismatch")
    if not source_generation_id:
        raise ValueError("source_authority_generation_missing")

    known_refs = {str(ref) for ref in catalog.get("all_evidence_refs") or ()}
    atomic_parent_refs = {
        str(ref)
        for claim in catalog.get("atomic_claims") or ()
        if isinstance(claim, Mapping)
        for ref in claim.get("parent_source_refs") or ()
    }
    rows_by_ref: dict[str, Mapping[str, object]] = {}
    errors: list[str] = []
    for row in source_metadata:
        ref_id = str(row.get("ref_id") or "")
        if not ref_id:
            errors.append("source_metadata_ref_missing")
            continue
        if ref_id not in known_refs:
            errors.append(f"source_metadata_unknown_ref:{ref_id}")
            continue
        if ref_id in rows_by_ref:
            errors.append(f"source_metadata_duplicate_ref:{ref_id}")
            continue
        rows_by_ref[ref_id] = row
    for ref_id in sorted(known_refs - set(rows_by_ref)):
        errors.append(f"source_metadata_missing_ref:{ref_id}")

    override_index: dict[str, Mapping[str, object]] = {}
    catalog_sha = canonical_sha256(catalog)
    for override in trusted_owner_overrides:
        ref_id = str(override.get("ref_id") or "")
        if ref_id not in known_refs:
            errors.append(f"trusted_owner_override_unknown_ref:{ref_id}")
            continue
        if ref_id in override_index:
            errors.append(f"trusted_owner_override_duplicate:{ref_id}")
            continue
        if override.get("catalog_sha256") != catalog_sha:
            errors.append(f"trusted_owner_override_catalog_hash_mismatch:{ref_id}")
            continue
        row = rows_by_ref.get(ref_id)
        if row is None or override.get("source_metadata_sha256") != canonical_sha256(row):
            errors.append(f"trusted_owner_override_metadata_hash_mismatch:{ref_id}")
            continue
        override_index[ref_id] = override

    authorities: list[dict[str, object]] = []
    for ref_id in sorted(known_refs):
        row = rows_by_ref.get(ref_id)
        if row is None:
            continue
        inferred = _trusted_metadata_scope(
            row=row,
            ref_id=ref_id,
            catalog=catalog,
            atomic_parent_refs=atomic_parent_refs,
        )
        override = override_index.get(ref_id)
        if override is not None and inferred["source_family"] != "unclassified":
            errors.append(f"trusted_owner_override_restricted_family_forbidden:{ref_id}")
            override = None
        if override is not None:
            allowed = sorted(str(use) for use in override.get("allowed_uses") or ())
            prohibited = sorted(str(use) for use in override.get("prohibited_uses") or ())
            rule = str(override.get("authority_basis") or "")
            source_type = str(override.get("source_type") or "")
            scope = str(override.get("source_scope") or "")
            if not rule or not source_type or not scope:
                errors.append(f"trusted_owner_override_required_field_missing:{ref_id}")
            overlap = set(allowed) & set(prohibited)
            if overlap:
                errors.append(f"trusted_owner_override_permission_conflict:{ref_id}")
            authority_state = "RESOLVED"
            source_family = "explicit_legacy_business_owner"
            denial_reasons = []
            required_metadata = ["exact_catalog_and_source_metadata_sha256"]
            compatible_versions = ["explicit-legacy-owner-v1"]
        else:
            allowed = list(inferred["allowed_uses"])
            prohibited = list(inferred["prohibited_uses"])
            rule = str(inferred["authority_basis"])
            source_type = str(inferred["source_type"])
            scope = str(inferred["source_scope"])
            authority_state = str(inferred["authority_state"])
            source_family = str(inferred["source_family"])
            denial_reasons = list(inferred["denial_reasons"])
            required_metadata = list(inferred["required_metadata"])
            compatible_versions = list(inferred["compatible_source_versions"])
        authorities.append(
            {
                "ticker": ticker,
                "ref_id": ref_id,
                "authority_origin": TRUSTED_AUTHORITY_ORIGIN,
                "authority_state": authority_state,
                "authority_basis": rule,
                "source_type": source_type,
                "source_scope": scope,
                "source_family": source_family,
                "source_period": row.get("as_of"),
                "fact_kind": str(row.get("category") or "frozen_evidence"),
                "allowed_uses": allowed,
                "prohibited_uses": prohibited,
                "denial_reasons": _ordered_unique(
                    [*denial_reasons, *([] if not prohibited else [f"not_authorized_by:{rule}"])]
                ),
                "required_metadata": required_metadata,
                "compatible_source_versions": compatible_versions,
                "independence_group": ref_id,
                "definition_binding_ref": None,
                "source_metadata_sha256": canonical_sha256(row),
            }
        )
    manifest: dict[str, object] = {
        "contract": SOURCE_AUTHORITY_CONTRACT,
        "contract_version": 2,
        "ticker": ticker,
        "source_generation_id": source_generation_id,
        "catalog_sha256": catalog_sha,
        "source_metadata_sha256": canonical_source_metadata_sha256(source_metadata),
        "authority_records": authorities,
        "authority_errors": sorted(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }
    manifest["authority_manifest_sha256"] = canonical_sha256(manifest)
    return manifest


def _valid_self_hash(value: Mapping[str, object], field: str) -> bool:
    expected = str(value.get(field) or "")
    payload = dict(value)
    payload.pop(field, None)
    return bool(expected) and expected == canonical_sha256(payload)


def _derive_source_use_permission_records(
    *,
    ticker: str,
    source_generation_id: str,
    catalog: Mapping[str, object],
    authority_manifest: Mapping[str, object],
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]], list[str]]:
    """Derive permission content only from the independently frozen authority inputs."""
    evidence_refs = {str(ref) for ref in catalog.get("all_evidence_refs") or ()}
    claims = {
        str(row.get("claim_ref") or ""): row
        for row in catalog.get("atomic_claims") or ()
        if isinstance(row, Mapping) and str(row.get("claim_ref") or "")
    }
    errors: list[str] = []
    if authority_manifest.get("contract") != SOURCE_AUTHORITY_CONTRACT:
        errors.append("authority_manifest_contract_mismatch")
    if authority_manifest.get("status") != "PASS":
        errors.append("authority_manifest_status_not_pass")
    if authority_manifest.get("authority_errors"):
        errors.append("authority_manifest_contains_errors")
    if str(authority_manifest.get("ticker") or "") != ticker:
        errors.append("authority_manifest_subject_mismatch")
    if str(authority_manifest.get("source_generation_id") or "") != source_generation_id:
        errors.append("authority_manifest_source_generation_mismatch")
    if authority_manifest.get("catalog_sha256") != canonical_sha256(catalog):
        errors.append("authority_manifest_catalog_hash_mismatch")
    if not _valid_self_hash(authority_manifest, "authority_manifest_sha256"):
        errors.append("authority_manifest_hash_invalid")

    source_index, index_errors = _authority_index(
        [
            row
            for row in authority_manifest.get("authority_records") or ()
            if isinstance(row, Mapping)
        ],
        expected_ticker=ticker,
        known_refs=evidence_refs,
        kind="source",
    )
    errors.extend(index_errors)
    for ref_id in sorted(evidence_refs - set(source_index)):
        errors.append(f"source_authority_missing:{ref_id}")

    source_records: dict[str, dict[str, object]] = {}
    for ref_id in sorted(evidence_refs):
        authority = source_index.get(ref_id)
        if authority is None:
            source_records[ref_id] = {
                "ref_id": ref_id,
                "ticker": ticker,
                "authority_state": "UNRESOLVED",
                "authority_origin": None,
                "allowed_uses": [],
                "prohibited_uses": sorted(item.value for item in SourceUse),
                "denial_reasons": ["source_authority_missing"],
                "independence_group": ref_id,
            }
            continue
        state = str(authority.get("authority_state") or "UNRESOLVED")
        allowed = {str(use) for use in authority.get("allowed_uses") or ()}
        prohibited = {str(use) for use in authority.get("prohibited_uses") or ()}
        if state not in {"RESOLVED", "UNRESOLVED", "UNRESOLVED_RESTRICTED"}:
            allowed = set()
            errors.append(f"source_authority_state_invalid:{ref_id}")
        source_records[ref_id] = {
            "ref_id": ref_id,
            "ticker": ticker,
            "source_type": authority.get("source_type"),
            "source_scope": authority.get("source_scope"),
            "source_family": authority.get("source_family"),
            "source_period": authority.get("source_period"),
            "authority_state": state,
            "authority_basis": authority.get("authority_basis"),
            "authority_origin": authority.get("authority_origin"),
            "allowed_uses": sorted(allowed - prohibited),
            "prohibited_uses": sorted(prohibited),
            "denial_reasons": _ordered_unique(authority.get("denial_reasons") or ()),
            "independence_group": str(authority.get("independence_group") or ref_id),
            "fact_kind": authority.get("fact_kind"),
            "definition_binding_ref": authority.get("definition_binding_ref"),
            "source_metadata_sha256": authority.get("source_metadata_sha256"),
        }

    claim_records: dict[str, dict[str, object]] = {}
    for claim_ref, row in sorted(claims.items()):
        parents = _ordered_unique(row.get("parent_source_refs") or ())
        missing = [ref for ref in parents if ref not in source_records]
        if parents and not missing:
            parent_uses = [set(source_records[ref]["allowed_uses"]) for ref in parents]
            allowed = set.intersection(*parent_uses)
            states = {str(source_records[ref]["authority_state"]) for ref in parents}
            state = "RESOLVED" if states == {"RESOLVED"} else "UNRESOLVED"
        else:
            allowed = set()
            state = "UNRESOLVED"
        reasons: list[str] = []
        if missing:
            reasons.append("claim_parent_authority_missing:" + ",".join(sorted(missing)))
        if not parents:
            reasons.append("claim_parent_refs_missing")
        claim_records[claim_ref] = {
            "claim_ref": claim_ref,
            "ticker": ticker,
            "parent_source_refs": parents,
            "authority_state": state,
            "authority_basis": "intersection_of_bound_parent_source_permissions",
            "authority_origin": TRUSTED_AUTHORITY_ORIGIN,
            "allowed_uses": sorted(allowed),
            "prohibited_uses": sorted({item.value for item in SourceUse} - allowed),
            "denial_reasons": reasons,
            "polarity": (
                row.get("claim", {}).get("polarity")
                if isinstance(row.get("claim"), Mapping)
                else None
            ),
            "compound_parent_count": len(parents),
        }
    return source_records, claim_records, sorted(set(errors))


def _permission_derivation_sha256(
    *,
    ticker: object,
    catalog_sha256: object,
    authority_manifest_sha256: object,
    source_records: object,
    claim_records: object,
) -> str:
    return canonical_sha256(
        {
            "contract": PERMISSION_DERIVATION_CONTRACT,
            "ticker": ticker,
            "catalog_sha256": catalog_sha256,
            "authority_manifest_sha256": authority_manifest_sha256,
            "source_records": source_records,
            "claim_records": claim_records,
        }
    )


def projection_permission_derivation_sha256(projection: Mapping[str, object]) -> str:
    """Recompute the semantic permission identity from received projection content."""
    return _permission_derivation_sha256(
        ticker=projection.get("ticker"),
        catalog_sha256=projection.get("catalog_sha256"),
        authority_manifest_sha256=projection.get("authority_manifest_sha256"),
        source_records=projection.get("source_records"),
        claim_records=projection.get("claim_records"),
    )


def freeze_source_use_input_expectation(
    *,
    ticker: str,
    source_generation_id: str,
    execution_generation_id: str,
    catalog: Mapping[str, object],
    source_metadata: Sequence[Mapping[str, object]],
    authority_manifest: Mapping[str, object],
) -> dict[str, object]:
    """Freeze caller-owned current input identities before any source-use consumption."""
    if not ticker or ticker != str(catalog.get("ticker") or ""):
        raise ValueError("source_input_expectation_subject_catalog_mismatch")
    if not source_generation_id:
        raise ValueError("source_input_expectation_source_generation_missing")
    if not execution_generation_id:
        raise ValueError("source_input_expectation_execution_generation_missing")
    if authority_manifest.get("contract") != SOURCE_AUTHORITY_CONTRACT:
        raise ValueError("source_input_expectation_authority_contract_mismatch")
    if authority_manifest.get("status") != "PASS":
        raise ValueError("source_input_expectation_authority_status_not_pass")
    if not _valid_self_hash(authority_manifest, "authority_manifest_sha256"):
        raise ValueError("source_input_expectation_authority_hash_invalid")
    if authority_manifest.get("ticker") != ticker:
        raise ValueError("source_input_expectation_authority_subject_mismatch")
    if authority_manifest.get("source_generation_id") != source_generation_id:
        raise ValueError("source_input_expectation_authority_generation_mismatch")
    if authority_manifest.get("catalog_sha256") != canonical_sha256(catalog):
        raise ValueError("source_input_expectation_authority_catalog_mismatch")
    metadata_sha = canonical_source_metadata_sha256(source_metadata)
    if authority_manifest.get("source_metadata_sha256") != metadata_sha:
        raise ValueError("source_input_expectation_authority_metadata_mismatch")
    source_records, claim_records, derivation_errors = _derive_source_use_permission_records(
        ticker=ticker,
        source_generation_id=source_generation_id,
        catalog=catalog,
        authority_manifest=authority_manifest,
    )
    if derivation_errors:
        raise ValueError("source_input_expectation_permission_derivation_invalid")
    permission_derivation_sha = _permission_derivation_sha256(
        ticker=ticker,
        catalog_sha256=canonical_sha256(catalog),
        authority_manifest_sha256=authority_manifest.get("authority_manifest_sha256"),
        source_records=source_records,
        claim_records=claim_records,
    )
    expectation: dict[str, object] = {
        "contract": SOURCE_INPUT_EXPECTATION_CONTRACT,
        "contract_version": 2,
        "expectation_origin": TRUSTED_INPUT_EXPECTATION_ORIGIN,
        "ticker": ticker,
        "source_generation_id": source_generation_id,
        "execution_generation_id": execution_generation_id,
        "catalog_sha256": canonical_sha256(catalog),
        "source_metadata_sha256": metadata_sha,
        "authority_manifest_sha256": authority_manifest.get("authority_manifest_sha256"),
        "permission_derivation_sha256": permission_derivation_sha,
    }
    expectation["expectation_sha256"] = canonical_sha256(expectation)
    return expectation


def validate_source_use_current_input(
    projection: Mapping[str, object] | None,
    binding: Mapping[str, object] | None,
    expectation: Mapping[str, object] | None,
    *,
    ticker: str,
    source_generation_id: str,
    execution_generation_id: str,
    catalog: Mapping[str, object],
    source_metadata: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Validate a pair against caller-owned current values, not values echoed by the pair."""
    errors = list(validate_source_use_projection_binding(projection, binding)["errors"])
    projection = projection if isinstance(projection, Mapping) else {}
    binding = binding if isinstance(binding, Mapping) else {}
    expectation = expectation if isinstance(expectation, Mapping) else {}
    if expectation.get("contract") != SOURCE_INPUT_EXPECTATION_CONTRACT:
        errors.append("source_input_expectation_contract_mismatch")
    if expectation.get("expectation_origin") != TRUSTED_INPUT_EXPECTATION_ORIGIN:
        errors.append("source_input_expectation_origin_untrusted")
    if expectation and not _valid_self_hash(expectation, "expectation_sha256"):
        errors.append("source_input_expectation_hash_invalid")
    expected_permission_derivation = expectation.get("permission_derivation_sha256")
    if not expected_permission_derivation:
        errors.append("source_input_expectation_permission_derivation_missing")
    actual = {
        "ticker": ticker,
        "source_generation_id": source_generation_id,
        "execution_generation_id": execution_generation_id,
        "catalog_sha256": canonical_sha256(catalog),
        "source_metadata_sha256": canonical_source_metadata_sha256(source_metadata),
    }
    for field, actual_value in actual.items():
        if expectation.get(field) != actual_value:
            errors.append(f"source_input_expectation_actual_mismatch:{field}")
        if projection.get(field) != actual_value:
            errors.append(f"source_use_projection_current_input_mismatch:{field}")
        if binding.get(field) != actual_value:
            errors.append(f"source_use_binding_current_input_mismatch:{field}")
    expectation_sha = expectation.get("expectation_sha256")
    if projection.get("authority_manifest_sha256") != expectation.get("authority_manifest_sha256"):
        errors.append("source_use_projection_expected_authority_mismatch")
    if binding.get("authority_manifest_sha256") != expectation.get("authority_manifest_sha256"):
        errors.append("source_use_binding_expected_authority_mismatch")
    actual_permission_derivation = projection_permission_derivation_sha256(projection)
    if projection.get("permission_derivation_sha256") != actual_permission_derivation:
        errors.append("source_use_projection_permission_derivation_hash_invalid")
    if projection.get("permission_derivation_sha256") != expected_permission_derivation:
        errors.append("source_use_projection_expected_permission_derivation_mismatch")
    if binding.get("permission_derivation_sha256") != expected_permission_derivation:
        errors.append("source_use_binding_expected_permission_derivation_mismatch")
    if projection.get("current_input_expectation_sha256") != expectation_sha:
        errors.append("source_use_projection_current_expectation_mismatch")
    if binding.get("current_input_expectation_sha256") != expectation_sha:
        errors.append("source_use_binding_current_expectation_mismatch")
    unique_errors = sorted(set(errors))
    return {
        "contract": "m12da-r3-current-input-and-permission-binding-validation-v2",
        "ticker": ticker,
        "errors": unique_errors,
        "error_count": len(unique_errors),
        "status": "PASS" if not unique_errors else "FAIL",
    }


def _build_bound_source_use_projection(
    *,
    ticker: str,
    source_generation_id: str,
    execution_generation_id: str,
    catalog: Mapping[str, object],
    authority_manifest: Mapping[str, object],
    current_input_expectation: Mapping[str, object],
) -> dict[str, object]:
    source_records, claim_records, errors = _derive_source_use_permission_records(
        ticker=ticker,
        source_generation_id=source_generation_id,
        catalog=catalog,
        authority_manifest=authority_manifest,
    )
    if current_input_expectation.get("contract") != SOURCE_INPUT_EXPECTATION_CONTRACT:
        errors.append("current_input_expectation_contract_mismatch")
    if current_input_expectation.get("expectation_origin") != TRUSTED_INPUT_EXPECTATION_ORIGIN:
        errors.append("current_input_expectation_origin_untrusted")
    if not _valid_self_hash(current_input_expectation, "expectation_sha256"):
        errors.append("current_input_expectation_hash_invalid")
    expected_input = {
        "ticker": ticker,
        "source_generation_id": source_generation_id,
        "execution_generation_id": execution_generation_id,
        "catalog_sha256": canonical_sha256(catalog),
        "source_metadata_sha256": authority_manifest.get("source_metadata_sha256"),
        "authority_manifest_sha256": authority_manifest.get("authority_manifest_sha256"),
    }
    for field, expected in expected_input.items():
        if current_input_expectation.get(field) != expected:
            errors.append(f"current_input_expectation_identity_mismatch:{field}")
    permission_derivation_sha = _permission_derivation_sha256(
        ticker=ticker,
        catalog_sha256=canonical_sha256(catalog),
        authority_manifest_sha256=authority_manifest.get("authority_manifest_sha256"),
        source_records=source_records,
        claim_records=claim_records,
    )
    if current_input_expectation.get("permission_derivation_sha256") != permission_derivation_sha:
        errors.append("current_input_expectation_permission_derivation_mismatch")

    projection: dict[str, object] = {
        "contract": SOURCE_USE_CONTRACT,
        "contract_version": 4,
        "ticker": ticker,
        "source_generation_id": source_generation_id,
        "execution_generation_id": execution_generation_id,
        "catalog_sha256": canonical_sha256(catalog),
        "source_metadata_sha256": authority_manifest.get("source_metadata_sha256"),
        "authority_contract": authority_manifest.get("contract"),
        "authority_manifest_sha256": authority_manifest.get("authority_manifest_sha256"),
        "current_input_expectation_sha256": current_input_expectation.get("expectation_sha256"),
        "permission_derivation_sha256": permission_derivation_sha,
        "source_records": source_records,
        "claim_records": claim_records,
        "projection_errors": sorted(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }
    projection["projection_sha256"] = canonical_sha256(projection)
    return projection


def build_source_use_projection(
    *,
    ticker: str,
    input_generation_id: str,
    catalog: Mapping[str, object],
    source_authorities: Sequence[Mapping[str, object]] = (),
    claim_authorities: Sequence[Mapping[str, object]] = (),
    authority_manifest: Mapping[str, object] | None = None,
    current_input_expectation: Mapping[str, object] | None = None,
    execution_generation_id: str | None = None,
) -> dict[str, object]:
    """Build either an explicitly legacy view or a caller-bound projection.

    The legacy branch exists only for frozen comparison fixtures. New-contract PASS requires a
    trusted metadata manifest and never inherits permissive baseline rights for missing records.
    """
    if authority_manifest is None:
        return _build_legacy_source_use_projection(
            ticker=ticker,
            input_generation_id=input_generation_id,
            catalog=catalog,
            source_authorities=source_authorities,
            claim_authorities=claim_authorities,
        )
    if source_authorities or claim_authorities:
        raise ValueError("bound_projection_rejects_ad_hoc_authority_rows")
    if not execution_generation_id:
        raise ValueError("source_use_execution_generation_missing")
    if current_input_expectation is None:
        raise ValueError("source_use_current_input_expectation_missing")
    return _build_bound_source_use_projection(
        ticker=ticker,
        source_generation_id=input_generation_id,
        execution_generation_id=execution_generation_id,
        catalog=catalog,
        authority_manifest=authority_manifest,
        current_input_expectation=current_input_expectation,
    )


def _record_for_ref(projection: Mapping[str, object], ref_id: str) -> Mapping[str, object] | None:
    for key in ("claim_records", "source_records"):
        records = projection.get(key)
        if isinstance(records, Mapping):
            record = records.get(ref_id)
            if isinstance(record, Mapping):
                return record
    return None


def freeze_source_use_binding(
    *,
    projection: Mapping[str, object],
    authority_manifest: Mapping[str, object],
    current_input_expectation: Mapping[str, object],
) -> dict[str, object]:
    """Freeze caller-held expected identities separately from the consumer projection."""
    if projection.get("contract") != SOURCE_USE_CONTRACT or projection.get("status") != "PASS":
        raise ValueError("source_use_binding_requires_pass_bound_projection")
    if authority_manifest.get("contract") != SOURCE_AUTHORITY_CONTRACT:
        raise ValueError("source_use_binding_authority_contract_mismatch")
    if not _valid_self_hash(projection, "projection_sha256"):
        raise ValueError("source_use_binding_projection_hash_invalid")
    if not _valid_self_hash(authority_manifest, "authority_manifest_sha256"):
        raise ValueError("source_use_binding_authority_hash_invalid")
    if current_input_expectation.get("contract") != SOURCE_INPUT_EXPECTATION_CONTRACT:
        raise ValueError("source_use_binding_expectation_contract_mismatch")
    if not _valid_self_hash(current_input_expectation, "expectation_sha256"):
        raise ValueError("source_use_binding_expectation_hash_invalid")
    if projection.get("authority_manifest_sha256") != authority_manifest.get(
        "authority_manifest_sha256"
    ):
        raise ValueError("source_use_binding_authority_identity_mismatch")
    if projection.get("current_input_expectation_sha256") != current_input_expectation.get(
        "expectation_sha256"
    ):
        raise ValueError("source_use_binding_expectation_identity_mismatch")
    actual_permission_derivation = projection_permission_derivation_sha256(projection)
    expected_permission_derivation = current_input_expectation.get("permission_derivation_sha256")
    if projection.get("permission_derivation_sha256") != actual_permission_derivation:
        raise ValueError("source_use_binding_projection_permission_derivation_invalid")
    if projection.get("permission_derivation_sha256") != expected_permission_derivation:
        raise ValueError("source_use_binding_permission_derivation_mismatch")
    binding: dict[str, object] = {
        "contract": SOURCE_USE_BINDING_CONTRACT,
        "contract_version": 3,
        "binding_origin": "CALLER_FROZEN_EXPECTATION",
        "ticker": projection.get("ticker"),
        "source_generation_id": projection.get("source_generation_id"),
        "execution_generation_id": projection.get("execution_generation_id"),
        "catalog_sha256": projection.get("catalog_sha256"),
        "source_metadata_sha256": projection.get("source_metadata_sha256"),
        "authority_manifest_sha256": projection.get("authority_manifest_sha256"),
        "current_input_expectation_sha256": projection.get("current_input_expectation_sha256"),
        "permission_derivation_sha256": projection.get("permission_derivation_sha256"),
        "projection_sha256": projection.get("projection_sha256"),
    }
    binding["binding_sha256"] = canonical_sha256(binding)
    return binding


def validate_source_use_projection_binding(
    projection: Mapping[str, object] | None,
    binding: Mapping[str, object] | None,
) -> dict[str, object]:
    errors: list[str] = []
    if not isinstance(projection, Mapping):
        errors.append("source_use_projection_missing")
        projection = {}
    if not isinstance(binding, Mapping):
        errors.append("source_use_binding_missing")
        binding = {}
    if projection.get("contract") != SOURCE_USE_CONTRACT:
        errors.append("source_use_projection_contract_mismatch")
    if projection.get("status") != "PASS":
        errors.append("source_use_projection_status_not_pass")
    if projection.get("projection_errors"):
        errors.append("source_use_projection_contains_errors")
    if projection and not _valid_self_hash(projection, "projection_sha256"):
        errors.append("source_use_projection_hash_invalid")
    if projection and projection.get(
        "permission_derivation_sha256"
    ) != projection_permission_derivation_sha256(projection):
        errors.append("source_use_projection_permission_derivation_hash_invalid")
    if binding.get("contract") != SOURCE_USE_BINDING_CONTRACT:
        errors.append("source_use_binding_contract_mismatch")
    if binding.get("binding_origin") != "CALLER_FROZEN_EXPECTATION":
        errors.append("source_use_binding_origin_untrusted")
    if binding and not _valid_self_hash(binding, "binding_sha256"):
        errors.append("source_use_binding_hash_invalid")
    identity_fields = (
        "ticker",
        "source_generation_id",
        "execution_generation_id",
        "catalog_sha256",
        "source_metadata_sha256",
        "authority_manifest_sha256",
        "current_input_expectation_sha256",
        "permission_derivation_sha256",
        "projection_sha256",
    )
    for field in identity_fields:
        if projection.get(field) != binding.get(field):
            errors.append(f"source_use_binding_identity_mismatch:{field}")
    return {
        "contract": "m12da-r1-source-use-binding-validation-v1",
        "ticker": projection.get("ticker"),
        "errors": sorted(set(errors)),
        "error_count": len(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }


def _projection_is_consumable(
    projection: Mapping[str, object] | None,
    binding: Mapping[str, object] | None,
) -> bool:
    if not isinstance(projection, Mapping):
        return False
    if projection.get("contract") == LEGACY_SOURCE_USE_CONTRACT:
        return binding is None
    return validate_source_use_projection_binding(projection, binding)["status"] == "PASS"


def is_use_allowed(
    projection: Mapping[str, object] | None,
    *,
    ref_id: str,
    use: SourceUse | str,
    binding: Mapping[str, object] | None = None,
) -> bool:
    if not _projection_is_consumable(projection, binding):
        return False
    assert isinstance(projection, Mapping)
    record = _record_for_ref(projection, ref_id)
    return bool(record and str(use) in set(record.get("allowed_uses") or ()))


def eligible_refs_for_use(
    projection: Mapping[str, object] | None,
    *,
    refs: Sequence[object],
    use: SourceUse | str,
    binding: Mapping[str, object] | None = None,
) -> list[str]:
    return [
        ref_id
        for ref_id in _ordered_unique(refs)
        if is_use_allowed(projection, ref_id=ref_id, use=use, binding=binding)
    ]


def validate_selected_refs(
    projection: Mapping[str, object] | None,
    *,
    refs: Sequence[object],
    use: SourceUse | str,
    require_any: bool,
    binding: Mapping[str, object] | None = None,
) -> dict[str, object]:
    selected = _ordered_unique(refs)
    errors: list[dict[str, object]] = []
    valid_contracts = {SOURCE_USE_CONTRACT, LEGACY_SOURCE_USE_CONTRACT}
    if not isinstance(projection, Mapping) or projection.get("contract") not in valid_contracts:
        errors.append(
            {
                "code": "SOURCE_USE_PROJECTION_MISSING",
                "ref_id": None,
                "use": str(use),
                "cause": "missing_or_wrong_contract",
            }
        )
    else:
        if projection.get("contract") == SOURCE_USE_CONTRACT:
            binding_validation = validate_source_use_projection_binding(projection, binding)
            for cause in binding_validation["errors"]:
                errors.append(
                    {
                        "code": "SOURCE_USE_BINDING_INVALID",
                        "ref_id": None,
                        "use": str(use),
                        "cause": cause,
                    }
                )
        elif binding is not None:
            errors.append(
                {
                    "code": "SOURCE_USE_LEGACY_BINDING_FORBIDDEN",
                    "ref_id": None,
                    "use": str(use),
                    "cause": "legacy_projection_cannot_claim_v2_binding",
                }
            )
        expected_ticker = str(projection.get("ticker") or "")
        if not expected_ticker:
            errors.append(
                {
                    "code": "SOURCE_USE_SUBJECT_MISSING",
                    "ref_id": None,
                    "use": str(use),
                    "cause": "projection_ticker_missing",
                }
            )
        for ref_id in selected:
            record = _record_for_ref(projection, ref_id)
            if record is None:
                errors.append(
                    {
                        "code": "SOURCE_USE_REF_UNKNOWN",
                        "ref_id": ref_id,
                        "use": str(use),
                        "cause": "ref_not_in_subject_projection",
                    }
                )
                continue
            if str(record.get("ticker") or "") != expected_ticker:
                errors.append(
                    {
                        "code": "SOURCE_USE_CROSS_SUBJECT_REF",
                        "ref_id": ref_id,
                        "use": str(use),
                        "cause": "record_subject_mismatch",
                    }
                )
                continue
            if str(use) not in set(record.get("allowed_uses") or ()):
                errors.append(
                    {
                        "code": "SOURCE_USE_REF_FORBIDDEN",
                        "ref_id": ref_id,
                        "use": str(use),
                        "cause": list(record.get("denial_reasons") or ()) or ["use_not_authorized"],
                    }
                )
    if require_any and not selected:
        errors.append(
            {
                "code": "SOURCE_USE_REQUIRED_REF_MISSING",
                "ref_id": None,
                "use": str(use),
                "cause": "selected_ref_set_empty",
            }
        )
    return {
        "contract": "m12da-selected-source-use-validation-v1",
        "use": str(use),
        "selected_refs": selected,
        "errors": errors,
        "error_count": len(errors),
        "status": "PASS" if not errors else "FAIL",
    }


def model_source_use_projection(
    projection: Mapping[str, object],
    *,
    binding: Mapping[str, object] | None = None,
    uses: Sequence[SourceUse | str] | None = None,
    claim_refs: Sequence[object] | None = None,
    source_refs: Sequence[object] | None = None,
) -> dict[str, object]:
    """Expose only decision-relevant permissions, without parser/source noise."""
    if projection.get("contract") == SOURCE_USE_CONTRACT:
        validation = validate_source_use_projection_binding(projection, binding)
        if validation["status"] != "PASS":
            raise ValueError("source_use_projection_binding_invalid")
    elif projection.get("contract") != LEGACY_SOURCE_USE_CONTRACT:
        raise ValueError("source_use_projection_contract_invalid")
    claims = projection.get("claim_records")
    claims = claims if isinstance(claims, Mapping) else {}
    sources = projection.get("source_records")
    sources = sources if isinstance(sources, Mapping) else {}
    scoped_uses = tuple(sorted({str(use) for use in uses or ()}))
    requested_claims = set(_ordered_unique(claim_refs or claims))
    requested_sources = set(_ordered_unique(source_refs or sources))
    if scoped_uses:
        scoped_claims = {
            str(ref_id): row
            for ref_id, row in claims.items()
            if isinstance(row, Mapping)
            and str(ref_id) in requested_claims
            and bool(set(row.get("allowed_uses") or ()) & set(scoped_uses))
        }
        requested_sources.update(
            str(parent_ref)
            for row in scoped_claims.values()
            for parent_ref in row.get("parent_source_refs") or ()
        )
        scoped_sources = {
            str(ref_id): row
            for ref_id, row in sources.items()
            if isinstance(row, Mapping)
            and str(ref_id) in requested_sources
            and bool(set(row.get("allowed_uses") or ()) & set(scoped_uses))
        }
    else:
        scoped_claims = {
            str(ref_id): row for ref_id, row in claims.items() if isinstance(row, Mapping)
        }
        scoped_sources = {
            str(ref_id): row for ref_id, row in sources.items() if isinstance(row, Mapping)
        }
    result = {
        "contract": projection.get("contract"),
        "ticker": projection.get("ticker"),
        "input_generation_id": projection.get("input_generation_id"),
        "source_generation_id": projection.get("source_generation_id"),
        "execution_generation_id": projection.get("execution_generation_id"),
        "authority_manifest_sha256": projection.get("authority_manifest_sha256"),
        "current_input_expectation_sha256": projection.get("current_input_expectation_sha256"),
        "permission_derivation_sha256": projection.get("permission_derivation_sha256"),
        "binding_sha256": binding.get("binding_sha256") if binding is not None else None,
        "projection_sha256": projection.get("projection_sha256"),
        "claim_permissions": [
            {
                "claim_ref": ref_id,
                "allowed_uses": [
                    use
                    for use in row.get("allowed_uses") or ()
                    if not scoped_uses or use in scoped_uses
                ],
                "denial_reasons": list(row.get("denial_reasons") or ()),
                **(
                    {"parent_source_refs": list(row.get("parent_source_refs") or ())}
                    if scoped_uses
                    else {}
                ),
            }
            for ref_id, row in sorted(scoped_claims.items())
        ],
        "source_permissions": [
            {
                "ref_id": ref_id,
                "allowed_uses": [
                    use
                    for use in row.get("allowed_uses") or ()
                    if not scoped_uses or use in scoped_uses
                ],
                "denial_reasons": list(row.get("denial_reasons") or ()),
            }
            for ref_id, row in sorted(scoped_sources.items())
        ],
    }
    if scoped_uses:
        result.update(
            {
                "model_view_contract": "m12db-stage-scoped-source-use-model-view-v1",
                "model_view_uses": list(scoped_uses),
                "model_claim_refs": sorted(scoped_claims),
                "model_source_refs": sorted(scoped_sources),
            }
        )
        result["model_permission_view_sha256"] = canonical_sha256(result)
    return result


def _iso_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _decimal(value: object) -> Decimal | None:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def resolve_archived_sec_security_identity(
    *,
    ticker: str,
    security_type: str,
    submissions_bytes: bytes,
    exhibit_bytes: bytes,
    expected_submissions_sha256: str,
    expected_exhibit_sha256: str,
) -> dict[str, object]:
    """Resolve issuer/ticker/venue from already archived official SEC bytes."""
    submissions_sha = hashlib.sha256(submissions_bytes).hexdigest()
    exhibit_sha = hashlib.sha256(exhibit_bytes).hexdigest()
    errors: list[str] = []
    if submissions_sha != expected_submissions_sha256:
        errors.append("sec_submissions_sha256_mismatch")
    if exhibit_sha != expected_exhibit_sha256:
        errors.append("sec_exhibit_sha256_mismatch")
    try:
        submissions = json.loads(submissions_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        submissions = {}
        errors.append("sec_submissions_json_invalid")
    if not isinstance(submissions, Mapping):
        submissions = {}
        errors.append("sec_submissions_shape_invalid")
    cik = str(submissions.get("cik") or "")
    issuer_name = str(submissions.get("name") or "")
    tickers = submissions.get("tickers") or ()
    exchanges = submissions.get("exchanges") or ()
    if not isinstance(tickers, Sequence) or isinstance(tickers, (str, bytes)):
        tickers = ()
        errors.append("sec_submissions_tickers_invalid")
    if not isinstance(exchanges, Sequence) or isinstance(exchanges, (str, bytes)):
        exchanges = ()
        errors.append("sec_submissions_exchanges_invalid")
    if len(tickers) != len(exchanges):
        errors.append("sec_submissions_ticker_exchange_alignment_invalid")
    matches = [
        (index, str(exchange))
        for index, (candidate, exchange) in enumerate(zip(tickers, exchanges, strict=False))
        if str(candidate).upper() == ticker.upper() and str(exchange)
    ]
    if len(matches) != 1:
        errors.append("sec_submissions_ticker_mapping_not_unique")
        ticker_index = None
        venue = ""
    else:
        ticker_index, venue = matches[0]
    if not cik.isdigit() or not issuer_name:
        errors.append("sec_submissions_issuer_identity_missing")

    try:
        exhibit_html = exhibit_bytes.decode("utf-8")
    except UnicodeDecodeError:
        exhibit_html = ""
        errors.append("sec_exhibit_utf8_invalid")
    exhibit_text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", exhibit_html)))
    issuer_occurrences: list[tuple[str, str]] = []
    if issuer_name:
        pattern = re.compile(
            re.escape(issuer_name) + r"\s*\(\s*([A-Za-z.]+)\s*:\s*([A-Za-z0-9.-]+)\s*\)",
            re.IGNORECASE,
        )
        issuer_occurrences = [
            (match.group(1).upper(), match.group(2).upper())
            for match in pattern.finditer(exhibit_text)
        ]
    expected_occurrence = (venue.upper(), ticker.upper()) if venue else None
    if expected_occurrence is None or issuer_occurrences.count(expected_occurrence) != 1:
        errors.append("sec_exhibit_issuer_identity_not_uniquely_confirmed")

    resolved: dict[str, object] = {
        "contract": "m12da-r2-archived-sec-security-identity-resolution-v1",
        "ticker": ticker.upper(),
        "issuer_id": f"sec:{cik}" if cik else None,
        "issuer_name": issuer_name or None,
        "venue": venue.lower() if venue else None,
        "security_type": security_type,
        "security_id": (f"{venue.lower()}:{ticker.upper()}:{security_type}" if venue else None),
        "ticker_exchange_index": ticker_index,
        "submissions_sha256": submissions_sha,
        "exhibit_sha256": exhibit_sha,
        "exhibit_issuer_occurrences": [list(item) for item in issuer_occurrences],
        "errors": sorted(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }
    resolved["resolution_sha256"] = canonical_sha256(resolved)
    return resolved


def freeze_security_identity_binding(
    *,
    ticker: str,
    issuer_id: str,
    venue: str,
    security_type: str,
    official_sources: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    normalized_venue = venue.lower()
    identity: dict[str, object] = {
        "contract": SECURITY_IDENTITY_CONTRACT,
        "contract_version": 1,
        "namespace": "venue:ticker:security_type",
        "ticker": ticker,
        "issuer_id": issuer_id,
        "venue": venue.upper(),
        "security_type": security_type,
        "security_id": f"{normalized_venue}:{ticker}:{security_type}",
        "official_sources": [dict(row) for row in official_sources],
    }
    identity["identity_sha256"] = canonical_sha256(identity)
    return identity


def validate_security_identity_binding(
    identity: Mapping[str, object],
    *,
    expected: Mapping[str, object] | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    if identity.get("contract") != SECURITY_IDENTITY_CONTRACT:
        errors.append("security_identity_contract_mismatch")
    if identity.get("namespace") != "venue:ticker:security_type":
        errors.append("security_identity_namespace_mismatch")
    for field in ("ticker", "issuer_id", "venue", "security_type", "security_id"):
        if identity.get(field) in (None, ""):
            errors.append(f"security_identity_required_field_missing:{field}")
    expected_id = ":".join(
        (
            str(identity.get("venue") or "").lower(),
            str(identity.get("ticker") or ""),
            str(identity.get("security_type") or ""),
        )
    )
    if identity.get("security_id") != expected_id:
        errors.append("security_identity_id_components_mismatch")
    if not _valid_self_hash(identity, "identity_sha256"):
        errors.append("security_identity_hash_invalid")
    sources = identity.get("official_sources")
    if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes)) or not sources:
        errors.append("security_identity_official_sources_missing")
        sources = []
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            errors.append(f"security_identity_source_invalid:{index}")
            continue
        for field in ("provider", "document_sha256", "locator", "assertion"):
            if source.get(field) in (None, ""):
                errors.append(f"security_identity_source_field_missing:{index}:{field}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(source.get("document_sha256") or "")):
            errors.append(f"security_identity_source_sha_invalid:{index}")
    for field, expected_value in (expected or {}).items():
        if identity.get(field) != expected_value:
            errors.append(f"security_identity_expected_mismatch:{field}")
    return {
        "contract": "m12da-r1-security-identity-validation-v1",
        "security_id": identity.get("security_id"),
        "errors": sorted(set(errors)),
        "error_count": len(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }


def validate_metric_definition_binding(
    binding: Mapping[str, object],
    *,
    expected: Mapping[str, object] | None = None,
    expected_security_identity: Mapping[str, object] | None = None,
    replay_cutoff: str | None = None,
    historical_use: bool = False,
) -> dict[str, object]:
    errors: list[str] = []
    required = (
        "contract",
        "binding_id",
        "ticker",
        "issuer_id",
        "security_id",
        "security_identity",
        "metric_id",
        "definition_id",
        "formula",
        "period_start",
        "period_end",
        "duration_days",
        "comparison_basis",
        "currency",
        "unit",
        "consolidation_scope",
        "value_type",
        "value",
        "component_refs",
        "source",
        "historical_packet_carried_evidence",
        "claim_scope",
    )
    for field in required:
        if field not in binding or binding.get(field) in (None, ""):
            errors.append(f"definition_binding_required_field_missing:{field}")
    if binding.get("contract") != DEFINITION_BINDING_CONTRACT:
        errors.append("definition_binding_contract_mismatch")
    security_identity = binding.get("security_identity")
    if isinstance(security_identity, Mapping):
        if expected_security_identity is None:
            errors.append("definition_binding_expected_security_identity_missing")
        identity_validation = validate_security_identity_binding(
            security_identity,
            expected={
                "ticker": binding.get("ticker"),
                "issuer_id": binding.get("issuer_id"),
                "security_id": binding.get("security_id"),
                **dict(expected_security_identity or {}),
            },
        )
        errors.extend(identity_validation["errors"])
    else:
        errors.append("definition_binding_security_identity_missing")
    if binding.get("claim_scope") != "EXACT_METRIC_ONLY":
        errors.append("partial_paragraph_laundering_blocked")
    start = _iso_date(binding.get("period_start"))
    end = _iso_date(binding.get("period_end"))
    if start is None or end is None or start > end:
        errors.append("definition_binding_period_invalid")
    try:
        duration = int(binding.get("duration_days"))
    except (TypeError, ValueError):
        duration = 0
    if duration <= 0:
        errors.append("definition_binding_duration_invalid")
    if _decimal(binding.get("value")) is None:
        errors.append("definition_binding_value_invalid")
    source = binding.get("source")
    if not isinstance(source, Mapping):
        errors.append("definition_binding_source_missing")
        source = {}
    for field in (
        "provider",
        "accession",
        "document_type",
        "exhibit",
        "row_locator",
        "document_sha256",
        "publication_date",
        "retrieval_date",
    ):
        if source.get(field) in (None, ""):
            errors.append(f"definition_binding_source_field_missing:{field}")
    document_sha = str(source.get("document_sha256") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", document_sha):
        errors.append("definition_binding_document_sha_invalid")
    publication = _iso_date(source.get("publication_date"))
    retrieval = _iso_date(source.get("retrieval_date"))
    if publication is None or retrieval is None or publication > retrieval:
        errors.append("definition_binding_source_dates_invalid")
    cutoff = _iso_date(replay_cutoff) if replay_cutoff is not None else None
    if replay_cutoff is not None and cutoff is None:
        errors.append("definition_binding_cutoff_invalid")
    elif cutoff is not None and publication is not None and publication > cutoff:
        errors.append("definition_binding_post_cutoff_source")
    components = binding.get("component_refs")
    if not isinstance(components, Sequence) or isinstance(components, (str, bytes)):
        errors.append("definition_binding_component_refs_invalid")
        components = []
    if str(binding.get("value_type") or "").startswith("DERIVED") and not components:
        errors.append("definition_binding_derived_components_missing")
    if historical_use and binding.get("historical_packet_carried_evidence") is not True:
        errors.append("historical_packet_did_not_carry_source_binding")
    for field, expected_value in (expected or {}).items():
        actual = binding.get(field)
        if actual != expected_value:
            errors.append(f"definition_binding_expected_mismatch:{field}")
    return {
        "contract": "m12da-r1-metric-definition-validation-v2",
        "binding_id": binding.get("binding_id"),
        "errors": sorted(set(errors)),
        "error_count": len(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }


def frozen_source_authority(
    *,
    ticker: str,
    ref_id: str,
    source_type: str,
    source_scope: str,
    allowed_uses: Sequence[SourceUse | str],
    prohibited_uses: Sequence[SourceUse | str] = (),
    denial_reasons: Sequence[str] = (),
    source_period: str | None = None,
    fact_kind: str = "fact",
    authority_basis: str,
    independence_group: str | None = None,
    definition_binding_ref: str | None = None,
) -> dict[str, object]:
    return {
        "ticker": ticker,
        "ref_id": ref_id,
        "authority_origin": TRUSTED_AUTHORITY_ORIGIN,
        "source_type": source_type,
        "source_scope": source_scope,
        "source_period": source_period,
        "fact_kind": fact_kind,
        "authority_state": "RESOLVED",
        "authority_basis": authority_basis,
        "allowed_uses": _ordered_unique(allowed_uses),
        "prohibited_uses": _ordered_unique(prohibited_uses),
        "denial_reasons": _ordered_unique(denial_reasons),
        "independence_group": independence_group or ref_id,
        "definition_binding_ref": definition_binding_ref,
    }
