"""Live registration-bound plan authorization, not captured source or Native use.

Only the trusted orchestration boundary may issue this capability. Public JSON
is an audit receipt, never an ownership credential. No provider is called here.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from threading import RLock
from typing import Literal
from weakref import WeakKeyDictionary, ref

from pydantic import AwareDatetime, Field

from app.services import prospective_class_c_owner as registration
from app.services.scoped_source_plan import (
    OWNER_FILES as WIRE_OWNER_FILES, ScopedConfig, compile_scoped_wire_contract,
)
from app.services.sealed_fresh_dispatch import FreshRequestDescriptor, RequestPlan
from app.services.unified_local_seed_bridge import admit_pinned_local_seed
from app.services.unified_snapshot_contract import ContractModel, digest, encoded
from app.services.unified_source_policy import UnifiedSourcePolicy

CONTRACT = "current-scoped-source-parent-v1"
PURPOSE = "SCOPED_SOURCE_ONLY"
ROOT = Path(__file__).resolve().parents[2]
OWNER_FILES = tuple(sorted(set(WIRE_OWNER_FILES) | {
    "app/services/current_scoped_source_owner.py",
    "app/services/current_scoped_source_results.py",
    "app/services/current_scoped_source_dispatch.py",
    "app/services/scoped_external_code_manifest.py",
    "app/services/kiwoom_account_pacing.py",
    "app/services/short_history_reference.py",
    "app/services/kiwoom_completed_close_owner.py",
    "app/services/current_scoped_worker_bridge.py",
    "app/services/scoped_worker_launch.py",
    "app/services/kiwoom_participant_session.py",
    "app/services/completed_session_projection.py",
    "app/services/projected_technical_input.py",
    "app/services/packet_owned_technical_context_service.py",
    "app/services/technical_feature_dependency_service.py",
    "app/services/current_effective_technical.py",
    "app/services/ohlcv_feature_engine_service.py",
    "app/services/ohlcv_completed_bar_finality_service.py",
    "app/services/ohlcv_provider_integrity_service.py",
    "scripts/current_scoped_source_worker.py",
    "scripts/unified_stock_source_worker.py",
    "app/services/minimal_class_c_export.py",
    "app/services/prospective_class_c_owner.py",
    "app/services/unified_local_seed_bridge.py",
    "app/services/unified_persisted_projection.py",
    "app/services/onboarding_readiness_service.py",
    "app/services/security_identity_service.py",
    "app/services/unified_cycle_owner.py",
    "app/services/unified_source_policy.py",
    "app/services/unified_snapshot_contract.py",
    "app/services/sealed_fresh_dispatch.py",
    "app/services/sealed_response_binding.py",
    "app/services/sealed_chart_slots.py",
    "app/services/bounded_financial_acquisition.py",
    "app/services/sec_current_financial_candidates.py",
    "app/services/fpi_filing_document_graph.py",
    "app/services/sec_logical_cell_reference.py",
    "app/services/sec_financial_snapshot_service.py",
    "app/services/opendart_financial_recovery_service.py",
    "app/models/security.py",
    "app/models/watchlist.py",
    "app/models/company.py",
    "app/models/thesis.py",
}))
_PID = os.getpid()
_LOCK = RLock()
_PARENTS = WeakKeyDictionary()
_RUNS = WeakKeyDictionary()


class ScopedSourceSpec(ContractModel):
    contract: Literal["current-scoped-source-parent-v1"] = CONTRACT
    purpose: Literal["SCOPED_SOURCE_ONLY"] = PURPOSE
    config: ScopedConfig
    generation_id: str = Field(pattern=r"^[A-Za-z0-9_.:-]+$")
    cutoff: AwareDatetime
    code_sha: str = Field(pattern=r"^[a-f0-9]{40}$")
    provider_config_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    retries: int = Field(default=0, ge=0, le=2, strict=True)
    # Explicit task-authorized finite bound, not an inherited revision ceiling.
    maximum_attempts: int = Field(ge=1, strict=True)


class CurrentScopedSourceParent:
    __slots__ = ("__weakref__",)


@dataclass(frozen=True)
class _State:
    owners: tuple
    documents: tuple
    policy: UnifiedSourcePolicy
    spec_json: str
    plan_json: str
    pins: tuple
    fingerprint: str
    receipt_json: str
    pid: int


def _now():
    return datetime.now(timezone.utc)


def current_code_pins():
    """Finite local code-only manifest; never discover paths from caller input."""
    result = {}
    for name in OWNER_FILES:
        path = ROOT / name
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("scoped_parent_code_symlink")
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _model(cls, value):
    raw = value.model_dump_json() if isinstance(value, cls) else encoded(value)
    return cls.model_validate_json(raw)


def _registration(owners, documents, spec, policy, *, replay):
    markets = {s.market for s in spec.config.subjects}
    if set(owners) != markets or set(documents) != markets:
        raise ValueError("scoped_parent_exact_market_owners_required")
    identities, receipts = {}, {}
    for market in sorted(markets):
        owner = owners[market]
        registration.require_generation(owner, spec.generation_id)
        original, receipt = registration._state(owner)
        authenticated = registration.apply_prospective_owner(original, original=original, owner=owner)
        if encoded(authenticated) != encoded(documents[market]):
            raise ValueError("scoped_parent_authenticated_projection_required")
        expected = {s.ticker for s in spec.config.subjects if s.market == market}
        if (receipt["market"] != market
                or datetime.fromisoformat(receipt["cutoff"]) != spec.cutoff
                or set(receipt["bindings"]) != expected
                or set(authenticated["universe"]["eligible_subjects"]) != expected
                or receipt["identity_policy_sha256"] != digest(sorted(policy.allowed_providers))):
            raise ValueError("scoped_parent_registration_scope_mismatch")
        if replay:
            raw = encoded(authenticated)
            admit_pinned_local_seed(raw, expected_sha256=digest(authenticated),
                market=market, session_key=authenticated["session"], cutoff=spec.cutoff,
                subjects=sorted(expected), policy=policy, prospective_owner=owner)
        for row in authenticated["roles"]["security_identity"]["records"]:
            security = row["record"]
            ticker = security["ticker"]
            if row["table"] != "securitymaster" or ticker in identities or ticker not in expected:
                raise ValueError("scoped_parent_registration_identity_coverage")
            identities[ticker] = security
        receipts[market] = receipt
    # A single capture and consent must own the whole selected configuration.
    for key in ("capture_receipt_sha256", "source_export_sha256", "approval_sha256", "source_generation_id"):
        if len({r[key] for r in receipts.values()}) != 1:
            raise ValueError("scoped_parent_single_capture_required")
    if set(identities) != {s.ticker for s in spec.config.subjects}:
        raise ValueError("scoped_parent_registration_identity_coverage")
    for subject in spec.config.subjects:
        security = identities[subject.ticker]
        actual = (security["canonical_security_id"],
            security.get("corp_code" if subject.market == "kr" else "cik"),
            security["exchange"], "KRW" if subject.market == "kr" else "USD")
        if actual != (subject.security_id, subject.issuer_id, subject.venue, subject.currency):
            raise ValueError("scoped_parent_registered_identity_mismatch")
    return identities, receipts


def _plan(spec, identities, candidate):
    plan = _model(RequestPlan, candidate)
    rebuilt = compile_scoped_wire_contract(config=spec.config, identities=identities,
        generation_id=spec.generation_id, at=spec.cutoff, code_sha=spec.code_sha,
        provider_config_sha256=spec.provider_config_sha256, retries=spec.retries)["request_plan"]
    if plan != rebuilt:
        raise ValueError("scoped_parent_original_wire_plan_required")
    attempts = sum(d.max_transport_attempts for d in plan.descriptors)
    if (not plan.descriptors or plan.unresolved_roles
            or any(d.provider != "kiwoom" for d in plan.descriptors)
            or attempts > spec.maximum_attempts):
        raise ValueError("scoped_parent_descriptor_budget_or_provider_denied")
    return plan, attempts


def issue_parent(*, registration_owners, admitted_projections, spec, plan, policy,
                 code_pins, enabled=False):
    """Trusted composition root only; supplied projections are independently replayed.

    A parent authorizes only exact frozen descriptors. It is not a dispatcher
    admission receipt, consumed HTTP budget, source success, or Native grant.
    """
    if enabled is not True:
        raise ValueError("scoped_parent_feature_off")
    if os.getpid() != _PID:
        raise ValueError("scoped_parent_process_changed")
    spec = _model(ScopedSourceSpec, spec)
    plan = _model(RequestPlan, plan)
    if (not plan.descriptors or plan.unresolved_roles
            or any(d.provider != "kiwoom" for d in plan.descriptors)
            or sum(d.max_transport_attempts for d in plan.descriptors) > spec.maximum_attempts):
        raise ValueError("scoped_parent_descriptor_budget_or_provider_denied")
    if type(policy) is not UnifiedSourcePolicy:
        raise ValueError("scoped_parent_original_policy_required")
    policy = UnifiedSourcePolicy(frozenset(policy.allowed_providers))
    policy.require("kiwoom")
    code_pins = dict(code_pins)
    if code_pins != current_code_pins():
        raise ValueError("scoped_parent_code_identity_mismatch")
    owners = dict(registration_owners)
    documents = json.loads(encoded(admitted_projections))
    with _LOCK:
        identities, receipts = _registration(owners, documents, spec, policy, replay=True)
        plan, attempts = _plan(spec, identities, plan)
        # Detect an in-flight source edit before minting a capability.
        if dict(code_pins) != current_code_pins():
            raise ValueError("scoped_parent_code_identity_mismatch")
        expiry = min(datetime.fromisoformat(r["expires_at"]) for r in receipts.values())
        if not spec.cutoff <= _now() < expiry:
            raise ValueError("scoped_parent_expired_or_future")
        fingerprint = digest(dict(spec=spec.model_dump(mode="json"), plan=plan.model_dump(mode="json"),
            registration={m: digest(d) for m, d in documents.items()}, pins=dict(code_pins),
            providers=sorted(policy.allowed_providers)))
        owner_items = tuple(sorted(owners.items()))
        anchor = owner_items[0][1]
        runs = _RUNS.setdefault(anchor, {})
        if spec.generation_id in runs:
            old_fingerprint, old_ref = runs[spec.generation_id]
            previous = old_ref()
            if (old_fingerprint != fingerprint or previous not in _PARENTS
                    or _PARENTS[previous].owners != owner_items):
                raise ValueError("scoped_parent_run_already_issued_or_revoked")
            resolve_parent(previous, plan=plan)
            return previous
        receipt = dict(contract=CONTRACT, scope=PURPOSE, generation_id=spec.generation_id,
            cutoff=spec.cutoff.isoformat(), expires_at=expiry.isoformat(), issued_at=_now().isoformat(),
            plan_sha256=plan.plan_sha256, spec_sha256=digest(spec.model_dump(mode="json")),
            code_pins_sha256=digest(dict(code_pins)), registration_sha256=digest(receipts),
            descriptor_count=len(plan.descriptors), maximum_attempts=spec.maximum_attempts,
            planned_attempts=attempts, status="CURRENT_REGISTRATION_AND_PLAN_BOUND_ONLY",
            current_source_evidence="NOT_ISSUED", source_result_integration="BOUND_PER_ROLE_SOURCE_ONLY_V1",
            full22_native=False, D01_D02=False, financial_use=False, model_use=False)
        parent = CurrentScopedSourceParent()
        _PARENTS[parent] = _State(owner_items, tuple((m, encoded(d).decode()) for m, d in sorted(documents.items())),
            policy, spec.model_dump_json(), plan.model_dump_json(), tuple(sorted(dict(code_pins).items())),
            fingerprint, encoded(receipt).decode(), os.getpid())
        runs[spec.generation_id] = (fingerprint, ref(parent))
        return parent


def _live(parent):
    if type(parent) is not CurrentScopedSourceParent or parent not in _PARENTS:
        raise ValueError("scoped_parent_live_capability_required")
    state = _PARENTS[parent]
    if os.getpid() != _PID or state.pid != _PID:
        raise ValueError("scoped_parent_process_changed")
    if dict(state.pins) != current_code_pins():
        raise ValueError("scoped_parent_code_identity_mismatch")
    receipt = json.loads(state.receipt_json)
    if not datetime.fromisoformat(receipt["cutoff"]) <= _now() < datetime.fromisoformat(receipt["expires_at"]):
        raise ValueError("scoped_parent_expired_or_future")
    spec = ScopedSourceSpec.model_validate_json(state.spec_json)
    _registration(dict(state.owners), {m: json.loads(d) for m, d in state.documents},
        spec, state.policy, replay=False)
    return state, receipt


def resolve_parent(parent, *, plan=None):
    """Idempotent same-parent lookup; returned JSON cannot restore authority."""
    with _LOCK:
        state, receipt = _live(parent)
        if plan is not None and _model(RequestPlan, plan).plan_sha256 != receipt["plan_sha256"]:
            raise ValueError("scoped_parent_plan_mismatch")
        return receipt


def authorize_descriptor(parent, descriptor, *, plan):
    """Authorize only a frozen template, not a caller-resolved wire request.

    The original dispatcher still owns ResponseBinding resolution, raw custody,
    retries, actual wire accounting and capture validation. This does not spend
    or replenish its budget and is not sufficient to issue a source result.
    """
    with _LOCK:
        state, receipt = _live(parent)
        candidate = _model(RequestPlan, plan)
        if candidate.plan_sha256 != receipt["plan_sha256"]:
            raise ValueError("scoped_parent_plan_mismatch")
        descriptor = _model(FreshRequestDescriptor, descriptor)
        original = RequestPlan.model_validate_json(state.plan_json)
        if descriptor not in original.descriptors:
            raise ValueError("scoped_parent_descriptor_not_authorized")
        return dict(contract=CONTRACT, scope=PURPOSE, generation_id=receipt["generation_id"],
            plan_sha256=receipt["plan_sha256"], descriptor_sha256=descriptor.descriptor_sha256,
            status="DESCRIPTOR_AUTHORIZED_SOURCE_RESULT_NOT_ISSUED")


def revoke_parent(parent):
    """Permit cleanup even after expiry/code drift; never reactivate a run."""
    with _LOCK:
        if type(parent) is not CurrentScopedSourceParent or parent not in _PARENTS:
            raise ValueError("scoped_parent_live_capability_required")
        if os.getpid() != _PID or _PARENTS[parent].pid != _PID:
            raise ValueError("scoped_parent_process_changed")
        del _PARENTS[parent]


def issue_source_result(parent, *, plan, dispatcher=None, entry_id=None):
    resolve_parent(parent, plan=plan)
    if dispatcher is None or entry_id is None:
        raise ValueError("scoped_original_dispatcher_capture_required")
    from app.services.current_scoped_source_results import issue_source_result as issue
    return issue(parent, dispatcher=dispatcher, entry_id=entry_id)


def consume_source_result(parent, capability, *, plan, dispatcher, entry_id, consumer=PURPOSE):
    resolve_parent(parent, plan=plan)
    from app.services.current_scoped_source_results import consume_source_result as consume
    return consume(parent, capability, dispatcher=dispatcher, entry_id=entry_id, consumer=consumer)


def revoke_source_result(capability):
    from app.services.current_scoped_source_results import revoke_source_result as revoke
    revoke(capability)


def read_source_rows(parent, capability, *, plan, dispatcher, entry_id, consumer=PURPOSE):
    resolve_parent(parent, plan=plan)
    from app.services.current_scoped_source_results import read_source_rows as read
    return read(parent, capability, dispatcher=dispatcher, entry_id=entry_id, consumer=consumer)
