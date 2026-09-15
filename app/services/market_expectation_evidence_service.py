"""Canonical market-expectation roles for directional evidence use."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from enum import StrEnum
import hashlib
import json

from pydantic import Field, model_validator

from app.services.cross_market_decision_engine_service import (
    EvidenceCategory,
    FrozenModel,
)
from app.services.direction_timing_ownership_service import (
    EvidenceDomain,
    OwnedEvidencePacket,
)
from app.services.structured_autonomy_alias_service import EvidenceAliasCatalog


CONTRACT_VERSION = "market-expectation-evidence-view-v1"
POST_MODEL_VALIDATOR_CONTRACT = "post-model-market-expectation-validator-v1"


class MarketExpectationEvidenceRole(StrEnum):
    INDEPENDENT_DIRECTIONAL_SUPPORT = "INDEPENDENT_DIRECTIONAL_SUPPORT"
    CONDITIONAL_CONTEXT_ONLY = "CONDITIONAL_CONTEXT_ONLY"
    ALREADY_REFLECTED_OR_COUNTERWEIGHT = "ALREADY_REFLECTED_OR_COUNTERWEIGHT"
    INDEPENDENCE_UNKNOWN = "INDEPENDENCE_UNKNOWN"
    NOT_MARKET_EXPECTATION = "NOT_MARKET_EXPECTATION"


class MarketExpectationStructuredBasis(FrozenModel):
    """Structured provenance supplied before the model sees an expectation ref."""

    expectation_ref: str
    independently_observed: bool = False
    independence_basis_refs: tuple[str, ...] = ()
    dependency_refs: tuple[str, ...] = ()
    already_reflected_or_counterweight: bool = False

    @model_validator(mode="after")
    def validate_basis(self) -> MarketExpectationStructuredBasis:
        if self.independently_observed and not self.independence_basis_refs:
            raise ValueError("market_expectation_independence_basis_required")
        if self.independence_basis_refs and not self.independently_observed:
            raise ValueError("market_expectation_independent_observation_required")
        if self.independently_observed and self.dependency_refs:
            raise ValueError("market_expectation_independence_dependency_conflict")
        if self.independently_observed and self.already_reflected_or_counterweight:
            raise ValueError("market_expectation_independence_counterweight_conflict")
        if len(set(self.independence_basis_refs)) != len(self.independence_basis_refs):
            raise ValueError("duplicate_market_expectation_independence_basis_ref")
        if len(set(self.dependency_refs)) != len(self.dependency_refs):
            raise ValueError("duplicate_market_expectation_dependency_ref")
        return self


class MarketExpectationEvidenceItem(FrozenModel):
    alias: str
    canonical_ref: str
    source_ref: str
    role: MarketExpectationEvidenceRole
    reason: str
    material_anchor_eligible: bool
    dominant_evidence_eligible: bool
    independence_basis_refs: tuple[str, ...] = ()
    independence_basis_aliases: tuple[str, ...] = ()
    dependency_refs: tuple[str, ...] = ()
    dependency_aliases: tuple[str, ...] = ()


class MarketExpectationEvidenceView(FrozenModel):
    contract: str = CONTRACT_VERSION
    ticker: str
    items: tuple[MarketExpectationEvidenceItem, ...] = Field(min_length=1)

    @property
    def expectation_items(self) -> tuple[MarketExpectationEvidenceItem, ...]:
        return tuple(
            item
            for item in self.items
            if item.role != MarketExpectationEvidenceRole.NOT_MARKET_EXPECTATION
        )

    @property
    def material_anchor_eligible_aliases(self) -> tuple[str, ...]:
        return tuple(item.alias for item in self.items if item.material_anchor_eligible)

    @property
    def dominant_evidence_eligible_aliases(self) -> tuple[str, ...]:
        return tuple(item.alias for item in self.items if item.dominant_evidence_eligible)

    @property
    def restricted_expectation_refs(self) -> frozenset[str]:
        return frozenset(
            item.canonical_ref
            for item in self.expectation_items
            if not item.material_anchor_eligible
            or not item.dominant_evidence_eligible
        )

    def model_context(self) -> dict[str, object]:
        return {
            "contract": CONTRACT_VERSION,
            "expectations": [
                {
                    "ref": item.alias,
                    "role": item.role.value,
                    "material_anchor_eligible": item.material_anchor_eligible,
                    "dominant_evidence_eligible": item.dominant_evidence_eligible,
                    "reason": item.reason,
                    "independence_basis_refs": list(
                        item.independence_basis_aliases
                    ),
                    "dependency_refs": list(item.dependency_aliases),
                }
                for item in self.expectation_items
            ],
        }


def market_expectation_evidence_view_sha256(
    view: MarketExpectationEvidenceView,
) -> str:
    payload = json.dumps(
        view.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _expectation_role(
    basis: MarketExpectationStructuredBasis | None,
) -> tuple[MarketExpectationEvidenceRole, str]:
    if basis is None:
        return (
            MarketExpectationEvidenceRole.INDEPENDENCE_UNKNOWN,
            "STRUCTURED_INDEPENDENCE_BASIS_UNAVAILABLE",
        )
    if basis.already_reflected_or_counterweight:
        return (
            MarketExpectationEvidenceRole.ALREADY_REFLECTED_OR_COUNTERWEIGHT,
            "STRUCTURED_ALREADY_REFLECTED_OR_COUNTERWEIGHT",
        )
    if basis.dependency_refs:
        return (
            MarketExpectationEvidenceRole.CONDITIONAL_CONTEXT_ONLY,
            "STRUCTURED_DEPENDENCY_ON_UNRESOLVED_CONDITION",
        )
    if basis.independently_observed:
        return (
            MarketExpectationEvidenceRole.INDEPENDENT_DIRECTIONAL_SUPPORT,
            "STRUCTURED_INDEPENDENT_CURRENT_EXPECTATION_BASIS",
        )
    return (
        MarketExpectationEvidenceRole.INDEPENDENCE_UNKNOWN,
        "STRUCTURED_INDEPENDENCE_BASIS_UNAVAILABLE",
    )


def build_market_expectation_evidence_view(
    owned: OwnedEvidencePacket,
    catalog: EvidenceAliasCatalog,
    *,
    structured_bases: Sequence[MarketExpectationStructuredBasis] = (),
) -> MarketExpectationEvidenceView:
    packet = owned.source_packet
    if (
        catalog.ticker != packet.ticker
        or catalog.market != packet.market
        or catalog.generation != packet.packet_id
    ):
        raise ValueError("market_expectation_catalog_owner_mismatch")
    by_ref = {row.ref.ref_id: row for row in owned.evidence}
    aliases_by_ref = catalog.by_ref
    if set(aliases_by_ref) - set(by_ref):
        raise ValueError("market_expectation_catalog_ref_missing_from_owned_packet")
    bases = {basis.expectation_ref: basis for basis in structured_bases}
    if len(bases) != len(structured_bases):
        raise ValueError("duplicate_market_expectation_structured_basis")
    unknown_basis_refs = sorted(set(bases) - set(aliases_by_ref))
    if unknown_basis_refs:
        raise ValueError(
            f"market_expectation_basis_ref_missing:{unknown_basis_refs}"
        )
    all_refs = set(aliases_by_ref)
    for basis in bases.values():
        linked = set(basis.independence_basis_refs) | set(basis.dependency_refs)
        missing = sorted(linked - all_refs)
        if missing:
            raise ValueError(f"market_expectation_linked_ref_missing:{missing}")
        if basis.expectation_ref in linked:
            raise ValueError("market_expectation_self_dependency_forbidden")

    items: list[MarketExpectationEvidenceItem] = []
    for entry in catalog.entries:
        owned_ref = by_ref[entry.canonical_ref]
        is_expectation = (
            owned_ref.ref.category == EvidenceCategory.EXPECTATIONS
            or owned_ref.domain == EvidenceDomain.MARKET_EXPECTATIONS
        )
        if is_expectation and not (
            owned_ref.ref.category == EvidenceCategory.EXPECTATIONS
            and owned_ref.domain == EvidenceDomain.MARKET_EXPECTATIONS
        ):
            raise ValueError("market_expectation_category_domain_mismatch")
        basis = bases.get(entry.canonical_ref)
        if not is_expectation:
            if basis is not None:
                raise ValueError("market_expectation_basis_attached_to_non_expectation")
            role = MarketExpectationEvidenceRole.NOT_MARKET_EXPECTATION
            reason = "NOT_MARKET_EXPECTATION"
            eligible = True
            independence_refs: tuple[str, ...] = ()
            dependency_refs: tuple[str, ...] = ()
        else:
            role, reason = _expectation_role(basis)
            eligible = role == MarketExpectationEvidenceRole.INDEPENDENT_DIRECTIONAL_SUPPORT
            independence_refs = basis.independence_basis_refs if basis else ()
            dependency_refs = basis.dependency_refs if basis else ()
        items.append(
            MarketExpectationEvidenceItem(
                alias=entry.alias,
                canonical_ref=entry.canonical_ref,
                source_ref=owned_ref.ref.source_ref,
                role=role,
                reason=reason,
                material_anchor_eligible=eligible,
                dominant_evidence_eligible=eligible,
                independence_basis_refs=independence_refs,
                independence_basis_aliases=tuple(
                    aliases_by_ref[ref].alias for ref in independence_refs
                ),
                dependency_refs=dependency_refs,
                dependency_aliases=tuple(
                    aliases_by_ref[ref].alias for ref in dependency_refs
                ),
            )
        )
    return MarketExpectationEvidenceView(ticker=packet.ticker, items=tuple(items))


def attach_market_expectation_evidence_view(
    context: Mapping[str, object],
    view: MarketExpectationEvidenceView,
) -> dict[str, object]:
    if str(context.get("ticker") or "") != view.ticker:
        raise ValueError("market_expectation_view_context_ticker_mismatch")
    return {**context, "market_expectation_evidence_view": view.model_context()}


def audit_market_expectation_view_projection(
    view: MarketExpectationEvidenceView,
) -> dict[str, object]:
    mismatches: list[str] = []
    for item in view.expectation_items:
        independent = (
            item.role == MarketExpectationEvidenceRole.INDEPENDENT_DIRECTIONAL_SUPPORT
        )
        if item.material_anchor_eligible != independent:
            mismatches.append(f"{item.alias}:material_anchor")
        if item.dominant_evidence_eligible != independent:
            mismatches.append(f"{item.alias}:dominant_evidence")
        if item.role == MarketExpectationEvidenceRole.CONDITIONAL_CONTEXT_ONLY:
            if not item.dependency_refs:
                mismatches.append(f"{item.alias}:dependency_refs")
        if item.role == MarketExpectationEvidenceRole.INDEPENDENT_DIRECTIONAL_SUPPORT:
            if not item.independence_basis_refs:
                mismatches.append(f"{item.alias}:independence_basis_refs")
    return {
        "contract": CONTRACT_VERSION,
        "ticker": view.ticker,
        "expectation_ref_count": len(view.expectation_items),
        "expectation_view_projection_mismatches": sorted(set(mismatches)),
        "expectation_view_projection_mismatch_count": len(set(mismatches)),
        "status": "PASS" if not mismatches else "FAIL",
    }


def _batch_choices(schema: Mapping[str, object]) -> list[dict[str, object]]:
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        raise ValueError("expectation_batch_schema_properties_missing")
    candidates = properties.get("candidates")
    if not isinstance(candidates, Mapping):
        raise ValueError("expectation_batch_candidates_schema_missing")
    items = candidates.get("items")
    if not isinstance(items, Mapping) or not isinstance(items.get("anyOf"), list):
        raise ValueError("expectation_batch_choices_schema_missing")
    return items["anyOf"]


def constrain_market_expectation_batch_schema(
    schema: Mapping[str, object],
    *,
    views: Mapping[str, MarketExpectationEvidenceView],
) -> dict[str, object]:
    """Constrain only anchor and dominant fields; all context fields keep full aliases."""

    result = copy.deepcopy(dict(schema))
    definitions = result.get("$defs")
    if not isinstance(definitions, dict):
        raise ValueError("expectation_batch_schema_definitions_missing")
    choices = _batch_choices(result)
    if len(choices) != len(views):
        raise ValueError("expectation_batch_choice_count_mismatch")
    seen: set[str] = set()
    for choice in choices:
        properties = choice.get("properties")
        if not isinstance(properties, dict):
            raise ValueError("expectation_candidate_properties_missing")
        ticker_schema = properties.get("ticker")
        if not isinstance(ticker_schema, Mapping):
            raise ValueError("expectation_candidate_ticker_schema_missing")
        ticker = str(ticker_schema.get("const") or "")
        if ticker not in views or ticker in seen:
            raise ValueError("expectation_candidate_ticker_scope_mismatch")
        seen.add(ticker)
        view = views[ticker]

        anchor = properties.get("material_directional_anchor_basis")
        dominant = properties.get("dominant_evidence")
        if not isinstance(anchor, dict) or not isinstance(dominant, dict):
            raise ValueError("expectation_directional_fields_missing")
        anchor_items = anchor.get("items")
        if not isinstance(anchor_items, Mapping):
            raise ValueError("expectation_anchor_items_schema_missing")
        alias_ref = str(anchor_items.get("$ref") or "")
        if not alias_ref.startswith("#/$defs/"):
            raise ValueError("expectation_anchor_alias_definition_missing")
        existing_anchor_definition = definitions.get(
            alias_ref.removeprefix("#/$defs/")
        )
        if not isinstance(existing_anchor_definition, Mapping) or not isinstance(
            existing_anchor_definition.get("enum"), list
        ):
            raise ValueError("expectation_anchor_alias_choices_missing")
        existing_anchor_aliases = set(existing_anchor_definition["enum"])
        prefix = alias_ref.removeprefix("#/$defs/").removesuffix("EvidenceAlias")
        anchor_alias_name = f"{prefix}MaterialAnchorAlias"
        dominant_alias_name = f"{prefix}DominantEvidenceAlias"
        dominant_claim_name = f"{prefix}DominantEvidenceClaim"
        definitions[anchor_alias_name] = {
            "enum": [
                alias
                for alias in view.material_anchor_eligible_aliases
                if alias in existing_anchor_aliases
            ],
            "type": "string",
        }
        anchor["items"] = {"$ref": f"#/$defs/{anchor_alias_name}"}

        dominant_ref = str(dominant.get("$ref") or "")
        if not dominant_ref.startswith("#/$defs/"):
            raise ValueError("expectation_dominant_claim_definition_missing")
        source_name = dominant_ref.removeprefix("#/$defs/")
        source_claim = definitions.get(source_name)
        if not isinstance(source_claim, Mapping):
            raise ValueError("expectation_dominant_claim_source_missing")
        constrained_claim = copy.deepcopy(dict(source_claim))
        claim_properties = constrained_claim.get("properties")
        if not isinstance(claim_properties, dict):
            raise ValueError("expectation_dominant_claim_properties_missing")
        evidence_refs = claim_properties.get("evidence_refs")
        if not isinstance(evidence_refs, dict):
            raise ValueError("expectation_dominant_evidence_refs_missing")
        dominant_items = evidence_refs.get("items")
        if not isinstance(dominant_items, Mapping):
            raise ValueError("expectation_dominant_alias_items_missing")
        existing_dominant_ref = str(dominant_items.get("$ref") or "")
        if not existing_dominant_ref.startswith("#/$defs/"):
            raise ValueError("expectation_dominant_alias_definition_missing")
        existing_dominant_definition = definitions.get(
            existing_dominant_ref.removeprefix("#/$defs/")
        )
        if not isinstance(existing_dominant_definition, Mapping) or not isinstance(
            existing_dominant_definition.get("enum"), list
        ):
            raise ValueError("expectation_dominant_alias_choices_missing")
        existing_dominant_aliases = set(existing_dominant_definition["enum"])
        definitions[dominant_alias_name] = {
            "enum": [
                alias
                for alias in view.dominant_evidence_eligible_aliases
                if alias in existing_dominant_aliases
            ],
            "type": "string",
        }
        evidence_refs["items"] = {"$ref": f"#/$defs/{dominant_alias_name}"}
        definitions[dominant_claim_name] = constrained_claim
        dominant["$ref"] = f"#/$defs/{dominant_claim_name}"
    if seen != set(views):
        raise ValueError("expectation_batch_view_scope_mismatch")
    return result


def _candidate_mapping(candidate: object) -> Mapping[str, object]:
    if isinstance(candidate, Mapping):
        return candidate
    model_dump = getattr(candidate, "model_dump", None)
    if callable(model_dump):
        value = model_dump(mode="json")
        if isinstance(value, Mapping):
            return value
    raise TypeError("market_expectation_candidate_mapping_required")


def _selected_paths(value: object, *, path: str = "") -> dict[str, list[str]]:
    selected: dict[str, list[str]] = {}
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key == "material_directional_anchor_basis" and isinstance(
                child, Sequence
            ) and not isinstance(child, (str, bytes)):
                for ref in child:
                    selected.setdefault(str(ref), []).append(child_path)
            elif key == "evidence_refs" and isinstance(child, Sequence) and not isinstance(
                child, (str, bytes)
            ):
                for ref in child:
                    selected.setdefault(str(ref), []).append(child_path)
            else:
                nested = _selected_paths(child, path=child_path)
                for ref, paths in nested.items():
                    selected.setdefault(ref, []).extend(paths)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            nested = _selected_paths(child, path=f"{path}[{index}]")
            for ref, paths in nested.items():
                selected.setdefault(ref, []).extend(paths)
    return selected


def validate_market_expectation_candidate(
    candidate: object,
    view: MarketExpectationEvidenceView,
    *,
    pre_model_view_sha256: str | None = None,
) -> dict[str, object]:
    value = _candidate_mapping(candidate)
    errors: list[str] = []
    if str(value.get("ticker") or "") != view.ticker:
        errors.append("market_expectation_candidate_ticker_mismatch")
    current_sha = market_expectation_evidence_view_sha256(view)
    expected_sha = pre_model_view_sha256 or current_sha
    if current_sha != expected_sha:
        errors.append("market_expectation_view_identity_mismatch")
    projection = audit_market_expectation_view_projection(view)
    if projection["status"] != "PASS":
        errors.append("market_expectation_view_projection_mismatch")

    anchors = {
        str(ref) for ref in value.get("material_directional_anchor_basis", ())
    }
    dominant_value = value.get("dominant_evidence")
    dominant = (
        {str(ref) for ref in dominant_value.get("evidence_refs", ())}
        if isinstance(dominant_value, Mapping)
        else set()
    )
    restricted = {
        item.canonical_ref: item
        for item in view.expectation_items
        if not item.material_anchor_eligible
        or not item.dominant_evidence_eligible
    }
    anchor_violations = sorted(set(restricted) & anchors)
    dominant_violations = sorted(set(restricted) & dominant)
    errors.extend(
        f"context_only_market_expectation_used_as_material_anchor:{ref}"
        for ref in anchor_violations
    )
    errors.extend(
        f"context_only_market_expectation_used_as_dominant_evidence:{ref}"
        for ref in dominant_violations
    )

    driver_violations: list[str] = []
    sell_drivers = value.get("sell_drivers", ())
    if isinstance(sell_drivers, Sequence) and not isinstance(
        sell_drivers, (str, bytes)
    ):
        for index, driver in enumerate(sell_drivers):
            if not isinstance(driver, Mapping):
                continue
            refs = {str(ref) for ref in driver.get("evidence_refs", ())}
            if refs.intersection(restricted) and driver.get("classification") != "OTHER_EVIDENCE":
                driver_violations.append(
                    f"context_only_market_expectation_sell_driver_not_other_evidence:{index}"
                )
    errors.extend(driver_violations)

    selected = _selected_paths(value)
    linked = [
        {
            "alias": item.alias,
            "canonical_ref": item.canonical_ref,
            "role": item.role.value,
            "material_anchor_eligible": item.material_anchor_eligible,
            "dominant_evidence_eligible": item.dominant_evidence_eligible,
            "independence_basis_refs": list(item.independence_basis_refs),
            "dependency_refs": list(item.dependency_refs),
            "selected_fields": sorted(set(selected.get(item.canonical_ref, ()))),
        }
        for item in view.expectation_items
    ]
    deduplicated = list(dict.fromkeys(errors))
    return {
        "contract": POST_MODEL_VALIDATOR_CONTRACT,
        "ticker": view.ticker,
        "pre_model_expectation_view_sha256": expected_sha,
        "post_model_validator_expectation_view_sha256": current_sha,
        "pre_post_expectation_view_identity_mismatch_count": int(
            expected_sha != current_sha
        ),
        "expectation_view_projection_mismatch_count": int(
            projection["expectation_view_projection_mismatch_count"]
        ),
        "context_only_expectation_material_anchor_violation_count": len(
            anchor_violations
        ),
        "context_only_expectation_dominant_evidence_violation_count": len(
            dominant_violations
        ),
        "context_only_expectation_driver_classification_violation_count": len(
            driver_violations
        ),
        "linked_evidence": linked,
        "errors": deduplicated,
        "status": "PASS" if not deduplicated else "FAIL",
    }
