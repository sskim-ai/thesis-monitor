"""Process-local TEST_ONLY authority for one reviewed expectation fixture recipe."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import hmac
import json
import os
import secrets
from typing import Literal

from pydantic import BaseModel, ConfigDict


CONSUMER = "MARKET_EXPECTATION_SEMANTICS"
RECIPE = "market-expectation-new8-fixture-v1"
VIEW_CONTRACT = "test-only-market-expectation-evidence-view-v1"
ALIAS_CONTRACT = "test-only-market-expectation-alias-v1"
SCHEMA_CONTRACT = "test-only-market-expectation-schema-v1"
_REFS = frozenset({"fixture:expectation", "fixture:dependency", "fixture:operating"})
_PID = os.getpid()
_LIFETIME = secrets.token_hex(24)
_KEY = secrets.token_bytes(32)
_ISSUED: dict[str, str] = {}


class TestOnlyFixtureSeal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract: Literal["test-only-expectation-fixture-seal-v1"] = "test-only-expectation-fixture-seal-v1"
    provenance: Literal["TEST_ONLY"] = "TEST_ONLY"
    recipe: Literal["market-expectation-new8-fixture-v1"] = RECIPE
    consumer: Literal["MARKET_EXPECTATION_SEMANTICS"] = CONSUMER
    basis_kind: Literal["conditional", "independent", "unknown"]
    owner_pid: int
    owner_lifetime: str
    receipt_id: str
    payload_sha256: str
    signature: str


def _process() -> None:
    if os.getpid() != _PID:
        raise ValueError("fixture_context_owner_process_mismatch")


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _payload(context) -> str:
    return _digest(context.model_dump(mode="json", exclude={"backend_seal"}))


def contains_fixture_provenance(value) -> bool:
    """Reserve this recipe's refs even if a caller strips the receipt/marker."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return (value.get("contract") in (VIEW_CONTRACT, ALIAS_CONTRACT, SCHEMA_CONTRACT,
                                         "test-only-expectation-fixture-seal-v1")
                or value.get("provenance") == "TEST_ONLY"
                or value.get("validation_scope") == "TEST_ONLY_MARKET_EXPECTATION_SEMANTICS"
                or any(contains_fixture_provenance(item) for item in value.values()))
    if isinstance(value, (tuple, list)):
        return any(contains_fixture_provenance(item) for item in value)
    return isinstance(value, str) and value in _REFS


def _unique_prompt_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("production_frozen_context_duplicate_key")
        result[key] = value
    return result


def _invalid_prompt_constant(value):
    raise ValueError("production_frozen_context_json_invalid")


def reject_test_only_production(value) -> None:
    """Reject structured fixture carriers, not arbitrary prose or reconstructed inputs."""
    from app.services.reviewed_fixture_authority import contains_reviewed_fixture

    if contains_fixture_provenance(value) or contains_reviewed_fixture(value):
        raise ValueError("production_test_only_fixture_forbidden")
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "prompt" and isinstance(item, str):
                for delimiter in ("\nFROZEN_CONTEXT:\n", "\nFUNDAMENTAL_CORE_CONTEXT:\n", "\nPRODUCTION_V2_CONTEXT:\n", "\nDIRECTIONAL_CORE_CONTEXT:\n", "\nPRICE_TIMING_CONTEXT:\n", "\nFUNDAMENTAL_STANCE_CONTEXT:\n"):
                    parts = item.split(delimiter)
                    if len(parts) > 2:
                        raise ValueError("production_frozen_context_duplicate")
                    if len(parts) == 2:
                        try:
                            embedded = json.loads(parts[1], object_pairs_hook=_unique_prompt_object,
                                                  parse_constant=_invalid_prompt_constant)
                        except json.JSONDecodeError as exc:
                            raise ValueError("production_frozen_context_json_invalid") from exc
                        reject_test_only_production(embedded)
            elif isinstance(item, (Mapping, list, tuple, BaseModel)):
                reject_test_only_production(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            reject_test_only_production(item)


def _recipe(basis_kind):
    from app.services.cross_market_decision_engine_service import (
        DecisionEvidencePacket, DecisionEvidenceRef, EvidenceCategory,
    )
    from app.services.direction_timing_ownership_service import (
        EvidenceDomain, OwnedEvidencePacket, OwnedEvidenceRef,
    )
    from app.services.market_expectation_evidence_service import MarketExpectationStructuredBasis
    from app.services.structured_autonomy_alias_service import build_evidence_alias_catalog

    if basis_kind not in {"conditional", "independent", "unknown"}:
        raise ValueError("fixture_context_unapproved_recipe")
    rows = (
        ("expectation", EvidenceCategory.EXPECTATIONS, "market-expectation", EvidenceDomain.MARKET_EXPECTATIONS),
        ("dependency", EvidenceCategory.UNKNOWN, "unresolved-condition", EvidenceDomain.DATA_QUALITY_LIMIT),
        ("operating", EvidenceCategory.EARNINGS, "operating-evidence", EvidenceDomain.EARNINGS_FINANCIAL_CURRENT),
    )
    refs = tuple(DecisionEvidenceRef(ref_id="fixture:" + name, category=category, label=label,
        statement=f"Structured fixture evidence for {label}.", as_of="2026-09-12",
        source_ref="fixture." + label) for name, category, label, _ in rows)
    packet = DecisionEvidencePacket(packet_id="fixture:market-expectation", ticker="EXP-FIXTURE",
        company_name="Expectation Fixture", market="us", assessment_date="2026-09-12",
        horizon="12m", evidence=refs, prohibited_claims=(), evidence_sha256="fixture-market-expectation-sha")
    owned = OwnedEvidencePacket(source_packet=packet, evidence=tuple(
        OwnedEvidenceRef(ref=ref, domain=row[3]) for ref, row in zip(refs, rows, strict=True)))
    bases = ()
    if basis_kind == "conditional":
        bases = (MarketExpectationStructuredBasis(expectation_ref=refs[0].ref_id,
                                                  dependency_refs=(refs[1].ref_id,)),)
    elif basis_kind == "independent":
        bases = (MarketExpectationStructuredBasis(expectation_ref=refs[0].ref_id,
            independently_observed=True, independence_basis_refs=(refs[2].ref_id,)),)
    return owned, build_evidence_alias_catalog(packet), bases


def _signature(fields) -> str:
    return hmac.new(_KEY, _digest(fields).encode(), hashlib.sha256).hexdigest()


def issue_market_expectation_fixture(owned, *, basis_kind):
    """Approve only the exact deterministic recipe; never sign caller-selected facts."""
    _process()
    expected, _, _ = _recipe(basis_kind)
    if type(owned) is not type(expected) or owned.model_dump(mode="json") != expected.model_dump(mode="json"):
        raise ValueError("fixture_context_unapproved_payload")
    fields = dict(contract="test-only-expectation-fixture-seal-v1", provenance="TEST_ONLY",
        recipe=RECIPE, consumer=CONSUMER, basis_kind=basis_kind, owner_pid=_PID,
        owner_lifetime=_LIFETIME, receipt_id=secrets.token_hex(32), payload_sha256=_payload(owned))
    seal = TestOnlyFixtureSeal(**fields, signature=_signature(fields))
    _ISSUED[seal.receipt_id] = seal.model_dump_json()
    return owned.model_copy(update={"backend_seal": seal})


def _verify_seal(seal, *, consumer):
    _process()
    if consumer != CONSUMER:
        raise ValueError("fixture_context_consumer_forbidden")
    if not isinstance(seal, TestOnlyFixtureSeal):
        raise ValueError("fixture_context_provenance_required")
    fields = seal.model_dump(mode="json", exclude={"signature"})
    if (seal.owner_pid != _PID or seal.owner_lifetime != _LIFETIME
            or _ISSUED.get(seal.receipt_id) != seal.model_dump_json()
            or not hmac.compare_digest(seal.signature, _signature(fields))):
        raise ValueError("fixture_context_unissued_revoked_or_changed")
    return seal


def verify_market_expectation_fixture(owned, catalog, structured_bases, *, consumer=CONSUMER):
    seal = _verify_seal(owned.backend_seal, consumer=consumer)
    expected, expected_catalog, expected_bases = _recipe(seal.basis_kind)
    if (_payload(owned) != seal.payload_sha256 or _payload(owned) != _payload(expected)
            or catalog != expected_catalog or tuple(structured_bases) != expected_bases):
        raise ValueError("fixture_context_recipe_binding_mismatch")
    return seal


def verify_market_expectation_fixture_view(view):
    """A semantic projection stays exact, live and TEST_ONLY after JSON transport."""
    seal = getattr(view, "test_only_provenance", None)
    from app.services.reviewed_fixture_authority import ReviewedFixtureSeal, verify_reviewed_view
    if isinstance(seal, ReviewedFixtureSeal) or str(view.contract).startswith("test-only-reviewed-"):
        return verify_reviewed_view(view)
    if seal is None:
        verify_reviewed_view(view)
        if contains_fixture_provenance(view.model_dump(mode="json")):
            raise ValueError("fixture_context_provenance_required")
        return None
    seal = _verify_seal(seal, consumer=CONSUMER)
    owned, catalog, bases = _recipe(seal.basis_kind)
    from app.services.market_expectation_evidence_service import (
        MarketExpectationEvidenceItem, MarketExpectationEvidenceRole, _expectation_role,
    )

    aliases = catalog.by_ref
    basis = bases[0] if bases else None
    items = []
    for entry in catalog.entries:
        is_expectation = entry.canonical_ref == "fixture:expectation"
        role, reason = (_expectation_role(basis) if is_expectation else
                        (MarketExpectationEvidenceRole.NOT_MARKET_EXPECTATION, "NOT_MARKET_EXPECTATION"))
        independent = basis.independence_basis_refs if is_expectation and basis else ()
        dependent = basis.dependency_refs if is_expectation and basis else ()
        eligible = not is_expectation or role == MarketExpectationEvidenceRole.INDEPENDENT_DIRECTIONAL_SUPPORT
        items.append(MarketExpectationEvidenceItem(alias=entry.alias, canonical_ref=entry.canonical_ref,
            source_ref=entry.source_ref, role=role, reason=reason, material_anchor_eligible=eligible,
            dominant_evidence_eligible=eligible, independence_basis_refs=independent,
            independence_basis_aliases=tuple(aliases[ref].alias for ref in independent),
            dependency_refs=dependent, dependency_aliases=tuple(aliases[ref].alias for ref in dependent)))
    expected = dict(contract=VIEW_CONTRACT, ticker=owned.source_packet.ticker,
                    items=[item.model_dump(mode="json") for item in items])
    if view.model_dump(mode="json", exclude={"test_only_provenance"}) != expected:
        raise ValueError("fixture_context_semantic_projection_mismatch")
    return seal


def fixture_semantic_metadata(view) -> dict[str, object]:
    seal = verify_market_expectation_fixture_view(view)
    if seal is None:
        return {}
    return dict(test_only_provenance=seal.model_dump(mode="json"),
                validation_scope="TEST_ONLY_MARKET_EXPECTATION_SEMANTICS",
                accepted_model_judgment=False, production_eligible=False)


def fixture_alias_metadata(packet, catalog, view) -> dict[str, object]:
    """Only the issued recipe can enter the explicit fixture alias projection."""
    seal = verify_market_expectation_fixture_view(view)
    from app.services.reviewed_fixture_authority import ReviewedFixtureSeal
    if isinstance(seal, ReviewedFixtureSeal):
        raise ValueError("reviewed_fixture_alias_parent_required")
    if seal is None:
        raise ValueError("fixture_context_provenance_required")
    owned, expected_catalog, _ = _recipe(seal.basis_kind)
    if packet != owned.source_packet or catalog != expected_catalog:
        raise ValueError("fixture_context_alias_projection_mismatch")
    return {**fixture_semantic_metadata(view), "contract": ALIAS_CONTRACT}


def fixture_schema_metadata(views) -> dict[str, object]:
    parents = []
    for view in views:
        seal = verify_market_expectation_fixture_view(view)
        if seal is not None:
            parents.append(seal.model_dump(mode="json"))
    if not parents:
        return {}
    return {"x-test-only-provenance": dict(contract=SCHEMA_CONTRACT,
        provenance="TEST_ONLY", consumer=CONSUMER, parents=parents,
        accepted_model_judgment=False, production_eligible=False)}


def revoke_market_expectation_fixture(owned) -> None:
    seal = _verify_seal(owned.backend_seal, consumer=CONSUMER)
    _ISSUED.pop(seal.receipt_id)
