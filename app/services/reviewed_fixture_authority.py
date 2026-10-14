"""Finite historical semantic fixtures, never production source authority.

The registry admits only backend-held recipe bytes. It cannot sign caller facts,
and its process-local receipts permit named offline semantic consumers only.
"""
from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import secrets
from typing import Literal

from pydantic import BaseModel, ConfigDict
from app.services.reviewed_fixture_parameters import CANARY_PARAMETERS, DEFAULT_DELTA_KINDS, FINANCIAL_GENERATIONS


CONTRACT = "reviewed-test-only-semantic-recipes-v1"
OWNED_CONTRACT = "test-only-reviewed-owned-evidence-v1"
RECIPE_SHA256 = "38e3bf787a36885358466e433a0bd69cb0e1cac1a8fa0f3491b3f39257045a38"
PACKET_RECIPE_SHA256 = "e833d6fcb421f4e9f6d318179138eae6fac903cd9675310d53a777d6920a6592"
MATURITY_RECIPE_SHA256 = "a4286002e0ebc1e0a7797d2758f860ecf36d00ece9ade4985c1eeb45c347de82"
_PID = os.getpid()
_LIFETIME = secrets.token_hex(24)
_ISSUED = {}
_ACTIVE_PAYLOADS = {}
_RESERVED_REFS: set[str] = set()
_MAX_ISSUED = 4096
_CONSUMERS = {
    "FROZEN_FINANCIAL_SEMANTICS": frozenset({"REF_CATALOG", "FINANCIAL_CONTEXT", "BUSINESS_DELTA", "MARKET_EXPECTATION", "CORE_TIMING_SEMANTICS", "OWNED_CONTEXT"}),
    "FROZEN_CORE_TIMING_SEMANTICS": frozenset({"REF_CATALOG", "FINANCIAL_CONTEXT", "BUSINESS_DELTA", "MARKET_EXPECTATION", "CORE_TIMING_SEMANTICS", "OWNED_CONTEXT"}),
    "FROZEN_DELTA_SEMANTICS": frozenset({"REF_CATALOG", "BUSINESS_DELTA", "ALIAS_CONTEXT"}),
    "FROZEN_CORE_SCHEMA_SEMANTICS": frozenset({"CORE_SCHEMA", "STAGE2_SCHEMA", "CORE_PROMPT", "STAGE2_PROMPT"}),
    "FROZEN_STAGE2_MATURITY": frozenset({"STAGE2_SCHEMA", "STAGE2_MATERIALIZATION"}),
}


class ReviewedFixtureSeal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract: Literal["reviewed-test-only-fixture-seal-v1"] = "reviewed-test-only-fixture-seal-v1"
    provenance: Literal["TEST_ONLY"] = "TEST_ONLY"
    scope: Literal["OWNED_EVIDENCE", "CORE_CONTEXT"] = "OWNED_EVIDENCE"
    recipe_id: str
    recipe_sha256: str
    purpose: str
    parameters: tuple[tuple[str, str], ...]
    owner_pid: int
    owner_lifetime: str
    receipt_id: str
    payload_sha256: str


class TestOnlyModelProjection(dict):
    """Legacy public fields only; this in-process carrier is never an authority."""


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _payload(value):
    return value.model_dump(mode="json", exclude={"backend_seal"})


def _process():
    if os.getpid() != _PID:
        raise ValueError("reviewed_fixture_owner_process_mismatch")


def _recipe_identity(recipe_id):
    return MATURITY_RECIPE_SHA256 if recipe_id.startswith("stage2-maturity:") else RECIPE_SHA256


def _issue_seal(value, recipe_id, recipe, parameters):
    """Repeated issuance is idempotent only while the exact live capability exists."""
    parameters = tuple(sorted(parameters.items()))
    payload_sha = _digest(_payload(value))
    key = (recipe["scope"], recipe_id, parameters, payload_sha)
    existing = _ISSUED.get(_ACTIVE_PAYLOADS.get(key))
    if existing is not None:
        return ReviewedFixtureSeal.model_validate_json(existing)
    if len(_ISSUED) >= _MAX_ISSUED:
        raise ValueError("reviewed_fixture_registry_capacity")
    seal = ReviewedFixtureSeal(scope=recipe["scope"], recipe_id=recipe_id,
        recipe_sha256=_recipe_identity(recipe_id), purpose=recipe["purpose"], parameters=parameters,
        owner_pid=_PID, owner_lifetime=_LIFETIME, receipt_id=secrets.token_hex(32),
        payload_sha256=payload_sha)
    _ISSUED[seal.receipt_id] = seal.model_dump_json()
    _ACTIVE_PAYLOADS[key] = seal.receipt_id
    return seal


@lru_cache(maxsize=1)
def _recipes():
    raw = (Path(__file__).parents[1] / "fixtures/reviewed_semantic_recipes.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != RECIPE_SHA256:
        raise ValueError("reviewed_fixture_recipe_identity_mismatch")
    value = json.loads(raw)
    if value["contract"] != CONTRACT or value["provenance"] != "TEST_ONLY" or value["production_eligible"] is not False:
        raise ValueError("reviewed_fixture_recipe_contract_invalid")
    packet_raw = (Path(__file__).parents[1] / "fixtures/reviewed_packet_recipes.json").read_bytes()
    if hashlib.sha256(packet_raw).hexdigest() != PACKET_RECIPE_SHA256:
        raise ValueError("reviewed_fixture_packet_recipe_identity_mismatch")
    packet_value = json.loads(packet_raw)
    if packet_value["contract"] != CONTRACT or packet_value["provenance"] != "TEST_ONLY" or packet_value["production_eligible"] is not False:
        raise ValueError("reviewed_fixture_recipe_contract_invalid")
    value["recipes"].update(packet_value["recipes"])
    maturity_raw = (Path(__file__).parents[1] / "fixtures/reviewed_stage2_maturity_recipes.json").read_bytes()
    if hashlib.sha256(maturity_raw).hexdigest() != MATURITY_RECIPE_SHA256:
        raise ValueError("reviewed_fixture_maturity_recipe_identity_mismatch")
    maturity = json.loads(maturity_raw)
    if (maturity["contract"] != CONTRACT or maturity["provenance"] != "TEST_ONLY"
            or maturity["production_eligible"] is not False
            or any(not key.startswith("stage2-maturity:") for key in maturity["recipes"])
            or set(maturity["recipes"]) & set(value["recipes"])):
        raise ValueError("reviewed_fixture_maturity_recipe_contract_invalid")
    value["recipes"].update(maturity["recipes"])
    return value


def _substitute(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [_substitute(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: _substitute(item, old, new) for key, item in value.items()}
    return value


def _expected(recipe_id, parameters):
    from app.services.direction_timing_ownership_service import OwnedEvidencePacket
    from app.services.directional_financial_context_service import normalize_sector_framework

    recipe = _recipes()["recipes"].get(recipe_id)
    if recipe is None or set(parameters) != set(recipe["parameters"]):
        raise ValueError("reviewed_fixture_unapproved_recipe_or_parameters")
    if recipe["scope"] == "CORE_CONTEXT":
        if recipe.get("fixture_kind") == "STAGE2_MATURITY":
            from app.services.reviewed_stage2_maturity_fixture import frozen_maturity_context
            return frozen_maturity_context(recipe["arguments"]), recipe
        from app.services.reviewed_core_fixture import frozen_core_context
        return frozen_core_context(recipe["arguments"]), recipe
    payload = json.loads(json.dumps(recipe["payload"]))
    if "generation" in parameters:
        generation = parameters["generation"]
        if generation not in FINANCIAL_GENERATIONS:
            raise ValueError("reviewed_fixture_generation_invalid")
        payload["source_packet"]["packet_id"] = generation
    if "synthetic_identity" in parameters:
        identity = parameters["synthetic_identity"]
        padding = parameters["padding"]
        if (recipe_id.removeprefix("canary:"),identity,padding) not in CANARY_PARAMETERS:
            raise ValueError("reviewed_fixture_unapproved_canary_parameters")
        payload = _substitute(payload, "SYNTHETIC_TEMPLATE", identity)
        suffix = (" fictional operating evidence" * ((int(padding)+30)//31))[:int(padding)]
        for row in payload["evidence"]:
            if row["ref"]["ref_id"].endswith(":business"):
                row["ref"]["statement"] += suffix
        payload["source_packet"]["evidence"] = [row["ref"] for row in payload["evidence"]]
        payload["source_packet"]["evidence_sha256"] = hashlib.sha256(json.dumps(
            payload["source_packet"]["evidence"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode()).hexdigest()
    if "delta_identity" in parameters:
        identity = parameters["delta_identity"]
        # The frozen fixture manifest, not a caller's prefix, owns these identities.
        original = _recipes()["original_delta_fixture_rows"]
        rows = original if isinstance(original, list) else original["fixtures"]
        kind = recipe_id.removeprefix("delta:")
        allowed = {(str(row["kind"]),str(row["id"])) for row in rows}
        allowed.update((item,"DELTA-CAP") for item in DEFAULT_DELTA_KINDS)
        if (kind,identity) not in allowed:
            raise ValueError("reviewed_fixture_delta_identity_forbidden")
        payload = _substitute(payload, "DELTA-CAP", identity)
    payload["sector_framework"] = normalize_sector_framework(payload["sector_framework"])
    return OwnedEvidencePacket.model_validate(payload), recipe


def issue_reviewed_owned_fixture(owned, *, recipe_id, **parameters):
    """Compare to an independent finite template before issuing a test capability."""
    _process()
    normalized = {key: str(value) for key, value in parameters.items()}
    expected, recipe = _expected(recipe_id, normalized)
    if type(owned) is not type(expected) or _payload(owned) != _payload(expected) or owned.backend_seal is not None:
        raise ValueError("reviewed_fixture_unapproved_payload")
    owned = owned.model_copy(update={"contract": OWNED_CONTRACT})
    seal = _issue_seal(owned, recipe_id, recipe, normalized)
    _RESERVED_REFS.update(row.ref.ref_id for row in owned.evidence)
    return owned.model_copy(update={"backend_seal": seal})


def build_reviewed_packet_fixture(packet, *, stock):
    """Historical test producer: exact frozen packet AND stock, no default fallback."""
    for recipe_id, recipe in _recipes()["recipes"].items():
        if recipe_id.startswith("packet:") and recipe["stock"] == stock and recipe["payload"]["source_packet"] == packet.model_dump(mode="json"):
            return build_reviewed_owned_fixture(recipe_id)
    raise ValueError("reviewed_fixture_unapproved_packet_or_stock")


def build_reviewed_core_fixture(*, packet, claim_id, evidence_packets):
    _process()
    arguments = dict(packet=packet,claim_id=claim_id,evidence_packets=[p.model_dump(mode="json") for p in evidence_packets])
    for recipe_id, recipe in _recipes()["recipes"].items():
        if recipe["scope"] != "CORE_CONTEXT" or recipe["arguments"] != arguments:
            continue
        expected, _ = _expected(recipe_id,{})
        seal = _issue_seal(expected, recipe_id, recipe, {})
        _RESERVED_REFS.update(ref.ref_id for p in evidence_packets for ref in p.evidence)
        return expected.model_copy(update={"backend_seal":seal})
    raise ValueError("reviewed_fixture_unapproved_core_arguments")


def build_reviewed_owned_fixture(recipe_id, **parameters):
    expected, _ = _expected(recipe_id, {key: str(value) for key,value in parameters.items()})
    return issue_reviewed_owned_fixture(expected,recipe_id=recipe_id,**parameters)


def verify_reviewed_owned_fixture(owned, *, consumer):
    _process()
    seal = getattr(owned,"backend_seal",None)
    if not isinstance(seal, ReviewedFixtureSeal):
        raise ValueError("reviewed_fixture_receipt_required")
    if consumer not in _CONSUMERS.get(seal.purpose, ()):
        raise ValueError("reviewed_fixture_consumer_forbidden")
    if (seal.owner_pid != _PID or seal.owner_lifetime != _LIFETIME or
            _ISSUED.get(seal.receipt_id) != seal.model_dump_json() or
            seal.recipe_sha256 != _recipe_identity(seal.recipe_id) or _digest(_payload(owned)) != seal.payload_sha256):
        raise ValueError("reviewed_fixture_unissued_revoked_or_changed")
    expected, recipe = _expected(seal.recipe_id, dict(seal.parameters))
    if recipe["scope"] == "OWNED_EVIDENCE":
        expected = expected.model_copy(update={"contract":OWNED_CONTRACT})
    if seal.scope != recipe["scope"]:
        raise ValueError("reviewed_fixture_scope_mismatch")
    if _payload(owned) != _payload(expected) or seal.purpose != recipe["purpose"]:
        raise ValueError("reviewed_fixture_template_binding_mismatch")
    return seal


def fixture_metadata(owned, *, consumer, preserve_canary_wire=False):
    if not isinstance(getattr(owned,"backend_seal",None), ReviewedFixtureSeal):
        return {}
    seal=verify_reviewed_owned_fixture(owned,consumer=consumer)
    # Canonical canary contexts already retain a statically reserved identity.
    if preserve_canary_wire and consumer == "OWNED_CONTEXT" and seal.recipe_id in {"canary:us", "canary:kr"}:
        return {}
    # The frozen architecture fingerprint excludes live receipt IDs, not source facts.
    if (consumer == "OWNED_CONTEXT" and seal.scope == "OWNED_EVIDENCE"
            and seal.purpose == "FROZEN_FINANCIAL_SEMANTICS"
            and seal.parameters == (("generation", "m12ae-r2-architecture-proof"),)
            and seal.recipe_id in {"financial:FIC-FIN-01", "financial:FIC-FIN-02", "financial:FIC-FIN-03", "financial:FIC-FIN-04"}):
        return {}
    return dict(test_only_provenance={"provenance":"TEST_ONLY", "receipt_id":seal.receipt_id})


@lru_cache(maxsize=1)
def _fixture_identities():
    rows = _recipes()["original_delta_fixture_rows"]
    rows = rows if isinstance(rows, list) else rows["fixtures"]
    return frozenset({identity for _, identity, _ in CANARY_PARAMETERS} |
        {str(row["id"]) for row in rows} | {"DELTA-CAP"} |
        {recipe.removeprefix("financial:") for recipe in _recipes()["recipes"] if recipe.startswith("financial:")})


def is_reviewed_fixture_packet(packet):
    payload = packet.model_dump(mode="json")
    return packet.ticker in _fixture_identities() or any(
        recipe.get("payload", {}).get("source_packet") == payload
        for recipe in _recipes()["recipes"].values())


def _has_packet_fixture_lineage(value):
    """Deny only the frozen subject/ref/source combinations, not generic refs."""
    rows = [row for key in ("items", "evidence")
        if isinstance(value.get(key), (list, tuple)) for row in value[key]]
    actual = {(row[key], row["source_ref"])
        for row in rows if isinstance(row, Mapping) and isinstance(row.get("source_ref"), str)
        for key in ("canonical_ref", "ref_id") if isinstance(row.get(key), str)}
    for recipe_id, recipe in _recipes()["recipes"].items():
        if not recipe_id.startswith("packet:"):
            continue
        packet = recipe["payload"]["source_packet"]
        if value.get("ticker") == packet["ticker"] and actual.intersection(
                (ref["ref_id"], ref["source_ref"]) for ref in packet["evidence"]):
            return True
    return False


def verify_reviewed_view(view):
    """Re-derive permitted projections, never authorize caller-selected view labels."""
    seal = getattr(view, "test_only_provenance", None)
    if not isinstance(seal, ReviewedFixtureSeal):
        if str(view.contract).startswith("test-only-reviewed-") or view.ticker in _fixture_identities() or _has_packet_fixture_lineage(view.model_dump(mode="json")):
            raise ValueError("reviewed_fixture_view_parent_required")
        return None
    from app.services.business_delta_evidence_service import BusinessDeltaEvidenceView, build_business_delta_evidence_view
    from app.services.market_expectation_evidence_service import MarketExpectationEvidenceView, MarketExpectationStructuredBasis, build_market_expectation_evidence_view
    from app.services.direction_timing_ownership_service import stage_alias_catalogs
    from app.services.structured_autonomy_alias_service import build_evidence_alias_catalog, compact_alias_ai_context

    consumer = {BusinessDeltaEvidenceView: "BUSINESS_DELTA", MarketExpectationEvidenceView: "MARKET_EXPECTATION"}.get(type(view))
    if consumer is None or seal.scope != "OWNED_EVIDENCE":
        raise ValueError("reviewed_fixture_view_kind_forbidden")
    parent, _ = _expected(seal.recipe_id, dict(seal.parameters))
    parent = parent.model_copy(update={"contract": OWNED_CONTRACT, "backend_seal": seal})
    verify_reviewed_owned_fixture(parent, consumer=consumer)
    delta = seal.purpose == "FROZEN_DELTA_SEMANTICS"
    catalogs = (build_evidence_alias_catalog(parent.source_packet),) if delta else stage_alias_catalogs(parent)
    actual = view.model_dump(mode="json")
    for catalog in catalogs:
        if type(view) is BusinessDeltaEvidenceView:
            expected = build_business_delta_evidence_view(parent, catalog)
            if expected.model_dump(mode="json") == actual:
                return seal
            if delta:
                context = compact_alias_ai_context(parent.source_packet, catalog, reviewed_fixture=parent)
            else:
                from scripts.directional_core_price_timing_holdout import _owned_context
                context = _owned_context(parent, catalog)
            variants = (build_business_delta_evidence_view(parent, catalog, context=context),)
        else:
            if not catalog.entries:
                continue
            bases = [()]
            by_label = {entry.label: entry.canonical_ref for entry in catalog.entries}
            if seal.recipe_id == "financial:FIC-FIN-05" and {"market-expectation", "remaining-unknown"} <= set(by_label):
                bases.append((MarketExpectationStructuredBasis(expectation_ref=by_label["market-expectation"], dependency_refs=(by_label["remaining-unknown"],)),))
            variants = (build_market_expectation_evidence_view(parent, catalog, structured_bases=basis) for basis in bases)
        if any(expected.model_dump(mode="json") == actual for expected in variants):
            return seal
    raise ValueError("reviewed_fixture_view_projection_mismatch")


def reviewed_view_metadata(view):
    seal = verify_reviewed_view(view)
    return {} if seal is None else {"test_only_provenance": {"provenance": "TEST_ONLY", "receipt_id": seal.receipt_id}}


def reviewed_public_projection(view, payload):
    """Keep the live parent on the typed view, not in model-facing semantic fields."""
    seal = verify_reviewed_view(view)
    return payload if seal is None else TestOnlyModelProjection(payload)


def reviewed_schema_metadata(views):
    parents = [seal.model_dump(mode="json") for view in views if (seal := verify_reviewed_view(view)) is not None]
    return {} if not parents else {"x-test-only-provenance": {"provenance": "TEST_ONLY", "parents": parents, "production_eligible": False}}


def verify_reviewed_catalog(owned, catalog, *, consumer):
    if not isinstance(getattr(owned,"backend_seal",None),ReviewedFixtureSeal):
        return
    seal = verify_reviewed_owned_fixture(owned,consumer=consumer)
    if seal.purpose == "FROZEN_DELTA_SEMANTICS":
        from app.services.structured_autonomy_alias_service import build_evidence_alias_catalog
        expected = (build_evidence_alias_catalog(owned.source_packet),)
    else:
        from app.services.direction_timing_ownership_service import stage_alias_catalogs
        expected = stage_alias_catalogs(owned)
    if catalog not in expected:
        raise ValueError("reviewed_fixture_catalog_changed")


def verify_reviewed_projection(owned, catalog, context):
    if not isinstance(getattr(owned,"backend_seal",None),ReviewedFixtureSeal):
        return
    verify_reviewed_catalog(owned,catalog,consumer="BUSINESS_DELTA")
    if context is None:
        return
    if owned.backend_seal.purpose == "FROZEN_DELTA_SEMANTICS":
        from app.services.structured_autonomy_alias_service import compact_alias_ai_context
        expected = compact_alias_ai_context(owned.source_packet,catalog,reviewed_fixture=owned)
    else:
        from scripts.directional_core_price_timing_holdout import _owned_context
        expected = _owned_context(owned,catalog)
    # Attached derived views are not inputs to the recomputed business-delta view.
    actual = {key:value for key,value in context.items() if key not in {"business_delta_evidence_view","market_expectation_evidence_view"}}
    if actual != expected:
        raise ValueError("reviewed_fixture_context_changed")


def verify_reviewed_expectation_basis(owned, catalog, bases):
    if not isinstance(getattr(owned,"backend_seal",None),ReviewedFixtureSeal):
        return
    verify_reviewed_catalog(owned,catalog,consumer="MARKET_EXPECTATION")
    if not bases:
        return
    from app.services.market_expectation_evidence_service import MarketExpectationStructuredBasis
    by_label = {entry.label:entry.canonical_ref for entry in catalog.entries}
    if owned.backend_seal.recipe_id != "financial:FIC-FIN-05" or tuple(bases) != (MarketExpectationStructuredBasis(expectation_ref=by_label["market-expectation"],dependency_refs=(by_label["remaining-unknown"],)),):
        raise ValueError("reviewed_fixture_expectation_basis_changed")


def contains_reviewed_fixture(value):
    if isinstance(value, TestOnlyModelProjection):
        return True
    if isinstance(value, BaseModel):
        value=value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return str(value.get("contract", "")).startswith("test-only-reviewed-") or _has_packet_fixture_lineage(value) or any(contains_reviewed_fixture(item) for item in value.values())
    if isinstance(value,(list,tuple)):
        return any(contains_reviewed_fixture(item) for item in value)
    return isinstance(value,str) and (value in _fixture_identities() or value in _RESERVED_REFS or value.startswith(("synthetic_transport_fixture.","fictional:FIC-FIN-","canonical:fictional:FIC-FIN-")))


def revoke_reviewed_fixture(owned):
    consumer = "CORE_SCHEMA" if getattr(owned.backend_seal,"scope",None) == "CORE_CONTEXT" else "REF_CATALOG"
    if getattr(owned.backend_seal, "purpose", None) == "FROZEN_STAGE2_MATURITY":
        consumer = "STAGE2_MATERIALIZATION"
    seal=verify_reviewed_owned_fixture(owned,consumer=consumer)
    _ISSUED.pop(seal.receipt_id)
