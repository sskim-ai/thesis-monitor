"""Finite, process-local TEST_ONLY future conditions beside an unchanged parent.

This is not an OwnedEvidencePacket issuer or a production source-use grant.
Serialized children and caller-created recipes have no admission authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import secrets

from app.services.cross_market_decision_engine_service import DecisionEvidenceRef
from app.services.direction_timing_ownership_service import (
    OwnedEvidencePacket,
    stage_alias_catalogs,
)
from app.services.reviewed_fixture_authority import verify_reviewed_owned_fixture


CONTRACT = "reviewed-financial-configured-semantic-composition-v1"
RECIPE_SHA256 = "bb5b7de6b8e84397ef8e08af758039abdbde564ae5843643ddb3ac2dc3906e6b"
M12AU_CONSUMER = "M12AU_PROSPECTIVE_FINANCIAL_SEMANTICS_V1"
SCHEMA_CONSUMER = "M12AT_CONTEXT0_SCHEMA_V1"
MODEL_VIEW_CONSUMER = "M12AT_CONTEXT0_MODEL_VIEW_V1"
FUTURE_FIELDS = frozenset({
    "business_reevaluation_up", "business_reevaluation_down", "risk_context",
})
_PID = os.getpid()
_LIFETIME = secrets.token_hex(24)
_ISSUED: dict[str, tuple[object, str]] = {}
_ACTIVE: dict[tuple[str, str, str], str] = {}


def _digest(value, *, ascii=True):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=ascii, allow_nan=False).encode()).hexdigest()


def _process():
    if os.getpid() != _PID:
        raise ValueError("configured_composition_process_mismatch")


@lru_cache(maxsize=1)
def _recipe_bytes():
    raw = (Path(__file__).parents[1] /
        "fixtures/reviewed_configured_composition_recipes_v1.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != RECIPE_SHA256:
        raise ValueError("configured_composition_recipe_digest_mismatch")
    return raw


def _recipes():
    # Only immutable pinned bytes are cached; callers never receive live authority.
    value = json.loads(_recipe_bytes())
    if (value["contract"] != CONTRACT or value["provenance"] != "TEST_ONLY"
            or value["production_eligible"] is not False):
        raise ValueError("configured_composition_recipe_contract_mismatch")
    return {row["id"]: row for row in value["recipes"]}


@dataclass(frozen=True)
class ReviewedConfiguredComposition:
    parent: OwnedEvidencePacket
    configured_rows: tuple[DecisionEvidenceRef, ...]
    recipe_id: str
    consumer: str
    receipt_id: str
    parent_receipt_id: str
    owner_pid: int
    owner_lifetime: str
    contract: str = CONTRACT
    provenance: str = "TEST_ONLY"
    production_eligible: bool = False


def _binding(parent, rows, recipe_id, consumer):
    _process()
    seal = verify_reviewed_owned_fixture(parent, consumer="FINANCIAL_CONTEXT")
    recipe = _recipes().get(recipe_id)
    if recipe is None:
        raise ValueError("configured_composition_unregistered_recipe")
    if consumer not in recipe["consumers"]:
        raise ValueError("configured_composition_consumer_forbidden")
    packet = parent.source_packet
    if (seal.recipe_id != recipe["parent_recipe"]
            or seal.parameters != (("generation", recipe["generation"]),)
            or packet.ticker != recipe["subject"] or packet.market != recipe["market"]
            or _digest(parent.model_dump(mode="json", exclude={"backend_seal"}))
            != recipe["parent_payload_sha256"]):
        raise ValueError("configured_composition_parent_binding_mismatch")
    if (type(rows) is not tuple or any(type(row) is not DecisionEvidenceRef for row in rows)
            or [row.model_dump(mode="json") for row in rows] != recipe["configured_rows"]):
        raise ValueError("configured_composition_exact_occurrences_required")
    catalog, _ = stage_alias_catalogs(parent)
    if _digest(catalog.model_dump(mode="json"), ascii=False) != recipe["parent_catalog_sha256"]:
        raise ValueError("configured_composition_parent_catalog_mismatch")
    return seal, recipe


def _payload(child):
    return dict(recipe_id=child.recipe_id, consumer=child.consumer,
        parent_receipt_id=child.parent_receipt_id, owner_pid=child.owner_pid,
        owner_lifetime=child.owner_lifetime, contract=child.contract,
        provenance=child.provenance, production_eligible=child.production_eligible,
        parent=child.parent.model_dump(mode="json"),
        configured_rows=[row.model_dump(mode="json") for row in child.configured_rows])


def issue_reviewed_configured_composition(parent, *, rows, recipe_id, consumer):
    """The backend template is necessary in addition to a live finite parent."""
    seal, _ = _binding(parent, rows, recipe_id, consumer)
    key = (seal.receipt_id, recipe_id, consumer)
    prior = _ISSUED.get(_ACTIVE.get(key))
    if prior is not None:
        child = prior[0]
        verify_reviewed_configured_composition(child, consumer=consumer)
        return child
    if len(_ISSUED) >= 4096:
        raise ValueError("configured_composition_registry_capacity")
    child = ReviewedConfiguredComposition(parent, rows, recipe_id, consumer,
        secrets.token_hex(32), seal.receipt_id, _PID, _LIFETIME)
    _ISSUED[child.receipt_id] = (child, _digest(_payload(child)))
    _ACTIVE[key] = child.receipt_id
    return child


def build_reviewed_configured_composition(parent, *, recipe_id, consumer):
    recipe = _recipes().get(recipe_id)
    if recipe is None:
        raise ValueError("configured_composition_unregistered_recipe")
    rows = tuple(DecisionEvidenceRef.model_validate(row) for row in recipe["configured_rows"])
    return issue_reviewed_configured_composition(parent, rows=rows,
        recipe_id=recipe_id, consumer=consumer)


def verify_reviewed_configured_composition(child, *, consumer):
    _process()
    if type(child) is not ReviewedConfiguredComposition:
        raise ValueError("configured_composition_live_capability_required")
    if consumer != child.consumer:
        raise ValueError("configured_composition_consumer_forbidden")
    record = _ISSUED.get(child.receipt_id)
    if (record is None or record[0] is not child or child.owner_pid != _PID
            or child.owner_lifetime != _LIFETIME or record[1] != _digest(_payload(child))):
        raise ValueError("configured_composition_unissued_revoked_or_changed")
    seal, recipe = _binding(child.parent, child.configured_rows, child.recipe_id, consumer)
    if seal.receipt_id != child.parent_receipt_id:
        raise ValueError("configured_composition_parent_receipt_mismatch")
    return json.loads(json.dumps(recipe))


def revoke_reviewed_configured_composition(child):
    verify_reviewed_configured_composition(child, consumer=child.consumer)
    del _ISSUED[child.receipt_id]


def validate_composed_reference_use(child, candidate, *, consumer):
    """Request membership AND prospective field scope, before semantic validation."""
    recipe = verify_reviewed_configured_composition(child, consumer=consumer)
    if not isinstance(candidate, dict) or candidate.get("ticker") != recipe["subject"]:
        raise ValueError("configured_composition_candidate_identity_mismatch")
    catalog, _ = stage_alias_catalogs(child.parent)
    future = {row.ref_id for row in child.configured_rows}
    allowed = set(catalog.by_ref) | future
    from app.services.configured_signal_evidence_service import build_configured_signal_evidence_view

    roles = build_configured_signal_evidence_view(ticker=recipe["subject"],
        supplied_refs=child.configured_rows).by_ref

    def walk(value, field, depth=0):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "evidence_refs" or key == "material_directional_anchor_basis":
                    if not isinstance(item, (list, tuple)) or any(not isinstance(ref, str) for ref in item):
                        raise ValueError("configured_composition_reference_shape")
                    if any(ref not in allowed for ref in item):
                        raise ValueError("configured_composition_request_membership")
                    if future.intersection(item):
                        expected_depth = 0 if field == "risk_context" else 1
                        if field not in FUTURE_FIELDS or depth != expected_depth:
                            raise ValueError("configured_composition_prospective_only")
                        for ref in future.intersection(item):
                            eligible = (roles[ref].risk_context_eligible if field == "risk_context"
                                else roles[ref].future_reevaluation_eligible)
                            if not eligible:
                                raise ValueError("configured_composition_future_role_forbidden")
                else:
                    walk(item, field, depth + 1)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item, field, depth + 1)

    for field, value in candidate.items():
        walk({field: value} if field == "material_directional_anchor_basis" else value, field)
    return tuple(catalog.by_ref) + tuple(row.ref_id for row in child.configured_rows)
