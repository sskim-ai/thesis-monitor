"""Synthetic original Class-C captures; no real registration or provider proof.

Parent audit matrix, written before implementation or execution:
  registration: exact configured coverage, original private replay, no forged owner
  identity: security/issuer/venue binding, unseen US/KR/ADS properties
  scope: distinct source-only parent, no offline-v1 or Full22 promotion
  plan: exact generation/cutoff, finite Kiwoom-only descriptors and code pins
  lifetime: same-process lookup, expiry, revocation, idempotency, no resurrection
  custody: copied inputs/outputs cannot mutate stored authority
  result: no current source evidence can be issued before original capture integration

These are implementation tests, not execution receipts. No tests have been run
as part of writing this matrix.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import sqlite3

import pytest

from app.services import current_scoped_source_owner as owner
from app.services import prospective_class_c_owner as registration
from app.services.minimal_class_c_export import capture_authorized_class_c
from app.services.scoped_routing_identity import ScopedSubject
from app.services.scoped_source_plan import (
    HistoryCounts, ScopedConfig, compile_scoped_wire_contract,
)
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from test_minimal_class_c_export import database


POLICY = UnifiedSourcePolicy(frozenset({"canonical_local", "sec_edgar", "dart", "kiwoom"}))
# Latest task planning inputs, not shortened history to fit an old ceiling.
COUNTS = dict(adjusted_daily=1000, adjusted_weekly=700,
              adjusted_monthly=300, unadjusted_weekly_valuation=300)


def setup_parent(tmp_path, *, depositary=False, three_types=False, names=None):
    subjects = names or [("NEWUS", "us"), ("888888", "kr")]
    if three_types:
        subjects = [("NEWUS", "us"), ("NEWADS", "us"), ("888888", "kr")]
    permission = database(tmp_path, subjects)
    with sqlite3.connect(permission.database) as db:
        for ordinal, (ticker, market) in enumerate(subjects, 1):
            if market == "us":
                db.execute("UPDATE securitymaster SET cik=? WHERE ticker=?", (str(1000 + ordinal), ticker))
        if depositary or three_types:
            ticker = "NEWADS" if three_types else subjects[0][0]
            db.execute("UPDATE securitymaster SET security_type='ads', "
                       "issuer_type='foreign_private_issuer', country='TW' WHERE ticker=?", (ticker,))
    now = datetime.now(timezone.utc)
    decision = registration.ApprovalDecision(event_id="SYNTHETIC_NG44_SOURCE_ONLY",
        user_message_sha256=digest("SYNTHETIC_SOURCE_ONLY_AUTHORIZATION"), approved=True,
        effective_at=now - timedelta(seconds=5), expires_at=now + timedelta(minutes=30),
        subjects=tuple(t for t, _ in subjects))
    approval = registration.record_backend_approval(decision)
    capture = capture_authorized_class_c(permission)
    owners, documents = {}, {}
    for market in sorted({m for _, m in subjects}):
        owners[market], documents[market] = registration.issue_prospective_owner(
            approval=approval, capture=capture, market=market, policy=POLICY,
            source_generation_id="synthetic-ng44-capture", generation_id="synthetic-ng44")
    identities = {row["record"]["ticker"]: row["record"] for doc in documents.values()
                  for row in doc["roles"]["security_identity"]["records"]}
    configured = tuple(ScopedSubject(ticker=t, market=m,
        security_id=identities[t]["canonical_security_id"],
        issuer_id=identities[t]["cik" if m == "us" else "corp_code"],
        venue=identities[t]["exchange"], currency="USD" if m == "us" else "KRW") for t, m in subjects)
    config = ScopedConfig(subjects=configured, kr_history=HistoryCounts(**COUNTS),
        us_history=HistoryCounts(**COUNTS), kr_max_pages=7)
    cutoff = datetime.fromisoformat(next(iter(documents.values()))["cutoff"])
    spec = owner.ScopedSourceSpec(config=config, generation_id="synthetic-ng44", cutoff=cutoff,
        code_sha="a" * 40, provider_config_sha256=digest("SYNTHETIC_PUBLIC_CONFIG"),
        retries=0, maximum_attempts=152)
    plan = wire(spec, identities)
    args = dict(registration_owners=owners, admitted_projections=documents, spec=spec,
        plan=plan, policy=POLICY, code_pins=owner.current_code_pins(), enabled=True)
    return args, approval, identities


def wire(spec, identities):
    return compile_scoped_wire_contract(config=spec.config, identities=identities,
        generation_id=spec.generation_id, at=spec.cutoff, code_sha=spec.code_sha,
        provider_config_sha256=spec.provider_config_sha256, retries=spec.retries)["request_plan"]


@pytest.mark.parametrize("depositary,names", [
    (False, [("NEWUS", "us"), ("888888", "kr")]),
    (True, [("UNSEENADS", "us"), ("777777", "kr")]),
])
def test_original_private_admission_generic_parent_only(tmp_path, depositary, names):
    args, _, _ = setup_parent(tmp_path, depositary=depositary, names=names)
    parent = owner.issue_parent(**args)
    assert owner.issue_parent(**args) is parent
    receipt = owner.resolve_parent(parent, plan=args["plan"])
    assert receipt["status"] == "CURRENT_REGISTRATION_AND_PLAN_BOUND_ONLY"
    assert receipt["current_source_evidence"] == "NOT_ISSUED"
    assert receipt["source_result_integration"] == "BOUND_PER_ROLE_SOURCE_ONLY_V1"
    assert not any(receipt[k] for k in ("full22_native", "D01_D02", "financial_use", "model_use"))
    assert receipt["planned_attempts"] == sum(d.max_transport_attempts for d in args["plan"].descriptors)
    for descriptor in args["plan"].descriptors:
        checked = owner.authorize_descriptor(parent, descriptor, plan=args["plan"])
        assert checked["descriptor_sha256"] == descriptor.descriptor_sha256
    assert owner.resolve_parent(parent) == receipt
    assert "selected private" not in json.dumps(receipt)
    assert "canonical_security_id" not in json.dumps(receipt)


def test_current_three_type_wire_explicit_finite_ceiling_not_old_120(tmp_path):
    args, _, _ = setup_parent(tmp_path, three_types=True)
    assert sum(d.max_transport_attempts for d in args["plan"].descriptors) == 152
    old_bound = args["spec"].model_copy(update={"maximum_attempts": 120})
    with pytest.raises(ValueError, match="budget_or_provider"):
        owner.issue_parent(**{**args, "spec": old_bound})
    parent = owner.issue_parent(**args)
    assert owner.resolve_parent(parent)["planned_attempts"] == 152
    with pytest.raises(ValueError, match="original_dispatcher_capture"):
        owner.issue_source_result(parent, plan=args["plan"])


@pytest.mark.parametrize("case", ["disabled", "bare_owner", "missing_market", "extra_market", "forged_projection"])
def test_unissued_or_wrong_registration_boundary(tmp_path, case):
    args, _, _ = setup_parent(tmp_path)
    if case == "disabled":
        args["enabled"] = False
    elif case == "forged_projection":
        args["admitted_projections"] = deepcopy(args["admitted_projections"])
        args["admitted_projections"]["us"]["prospective_owner_receipt"]["scope"] = "FULL22"
    else:
        args["registration_owners"] = dict(args["registration_owners"])
        if case == "bare_owner":
            args["registration_owners"]["us"] = registration.ProspectiveOwner()
        elif case == "missing_market":
            args["registration_owners"].pop("us")
        else:
            args["registration_owners"]["global"] = args["registration_owners"]["us"]
    with pytest.raises(ValueError):
        owner.issue_parent(**args)


@pytest.mark.parametrize("field,value", [
    ("security_id", "security:WRONG"), ("issuer_id", "999999"),
    ("venue", "NYSE"), ("currency", "KRW"),
])
def test_config_cannot_replace_registered_identity(tmp_path, field, value):
    args, _, _ = setup_parent(tmp_path)
    spec = args["spec"]
    configured = list(spec.config.subjects)
    configured[0] = configured[0].model_copy(update={field: value})
    args["spec"] = spec.model_copy(update={"config": spec.config.model_copy(update={"subjects": tuple(configured)})})
    with pytest.raises(ValueError, match="registered_identity_mismatch"):
        owner.issue_parent(**args)


def test_configured_subject_omission_does_not_pass_as_full_selection(tmp_path):
    args, _, _ = setup_parent(tmp_path, three_types=True)
    spec = args["spec"]
    reduced = (spec.config.subjects[0], spec.config.subjects[2])
    args["spec"] = spec.model_copy(update={"config": spec.config.model_copy(update={"subjects": reduced})})
    with pytest.raises(ValueError, match="registration_scope_mismatch"):
        owner.issue_parent(**args)


@pytest.mark.parametrize("case", ["generation", "cutoff", "policy", "code_pins", "schema_bypass"])
def test_exact_current_scope_and_frozen_code_required(tmp_path, case):
    args, _, _ = setup_parent(tmp_path)
    if case == "generation":
        args["spec"] = args["spec"].model_copy(update={"generation_id": "other-run"})
    elif case == "cutoff":
        args["spec"] = args["spec"].model_copy(update={"cutoff": args["spec"].cutoff + timedelta(seconds=1)})
    elif case == "policy":
        args["policy"] = UnifiedSourcePolicy(POLICY.allowed_providers | {"sec_official_identity"})
    elif case == "code_pins":
        args["code_pins"] = {**args["code_pins"], "arbitrary/private/path": "a" * 64}
    else:
        args["spec"] = args["spec"].model_copy(update={"purpose": "FULL22_NATIVE"})
    with pytest.raises(ValueError):
        owner.issue_parent(**args)


@pytest.mark.parametrize("case", ["missing_descriptor", "changed_wire", "role_elevation", "source_date", "retry", "plan_code"])
def test_only_original_rebuilt_wire_plan_can_be_issued(tmp_path, case):
    args, _, _ = setup_parent(tmp_path)
    value = args["plan"].model_dump(mode="json")
    descriptor = next(d for d in value["descriptors"] if d["role_id"].startswith("stock:"))
    if case == "missing_descriptor":
        value["descriptors"].pop()
    elif case == "changed_wire":
        request = json.loads(descriptor["request_json"])
        body = json.loads(request["body"])
        body["stk_cd"] = "OTHER"
        from app.services.unified_snapshot_contract import encoded
        request["body"] = encoded(body).decode()
        descriptor["request_json"] = encoded(request).decode()
    elif case == "role_elevation":
        descriptor["consumer_role"] = "CORE_DIRECTION"
    elif case == "source_date":
        descriptor["target_period"] = "1900-01-01"
    elif case == "retry":
        descriptor["transient_retry_max"] = 1
    else:
        value["code_sha"] = "b" * 40
    with pytest.raises(ValueError):
        owner.issue_parent(**{**args, "plan": value})


def test_known_overbudget_rejected_before_original_private_admission(tmp_path, monkeypatch):
    args, _, _ = setup_parent(tmp_path)
    args["spec"] = args["spec"].model_copy(update={"maximum_attempts": 1})
    def forbidden(*unused, **kwargs):
        raise AssertionError("registration consulted before obvious budget denial")
    monkeypatch.setattr(registration, "require_generation", forbidden)
    with pytest.raises(ValueError, match="budget_or_provider"):
        owner.issue_parent(**args)


def test_inputs_outputs_and_same_invocation_lookup_do_not_mutate_authority(tmp_path):
    args, _, _ = setup_parent(tmp_path)
    parent = owner.issue_parent(**args)
    plan = args["plan"]
    baseline = owner.resolve_parent(parent)
    returned = owner.resolve_parent(parent)
    returned["current_source_evidence"] = "PASS"
    args["admitted_projections"]["us"]["prospective_owner_receipt"]["generation_id"] = "forged"
    args["registration_owners"].clear()
    args["code_pins"].clear()
    assert owner.resolve_parent(parent, plan=plan) == baseline
    with pytest.raises(ValueError, match="live_capability"):
        owner.resolve_parent(returned)
    with pytest.raises(ValueError, match="live_capability"):
        owner.resolve_parent(owner.CurrentScopedSourceParent())


@pytest.mark.parametrize("case", ["parent", "registration", "approval", "expiry", "clock_rollback", "pid", "code_drift"])
def test_live_parent_lifetime_enforced_for_lookup_and_descriptor(tmp_path, monkeypatch, case):
    args, approval, _ = setup_parent(tmp_path)
    parent = owner.issue_parent(**args)
    if case == "parent":
        owner.revoke_parent(parent)
    elif case == "registration":
        registration.revoke_prospective_owner(args["registration_owners"]["us"])
    elif case == "approval":
        registration.revoke_approval(approval)
    elif case == "expiry":
        expiry = datetime.fromisoformat(owner.resolve_parent(parent)["expires_at"])
        monkeypatch.setattr(owner, "_now", lambda: expiry)
    elif case == "clock_rollback":
        monkeypatch.setattr(owner, "_now", lambda: args["spec"].cutoff - timedelta(seconds=1))
    elif case == "pid":
        monkeypatch.setattr(owner, "_PID", owner._PID + 1)
    else:
        monkeypatch.setattr(owner, "current_code_pins", lambda: {})
    with pytest.raises(ValueError):
        owner.resolve_parent(parent, plan=args["plan"])
    with pytest.raises(ValueError):
        owner.authorize_descriptor(parent, args["plan"].descriptors[0], plan=args["plan"])


def test_revoked_run_cannot_resurrect(tmp_path):
    args, _, _ = setup_parent(tmp_path)
    parent = owner.issue_parent(**args)
    owner.revoke_parent(parent)
    with pytest.raises(ValueError, match="already_issued_or_revoked"):
        owner.issue_parent(**args)
    # A new real invocation needs new original registration authority, not a
    # changed generation label over the old prospective handle.
    with pytest.raises(ValueError):
        owner.issue_parent(**{**args, "spec": args["spec"].model_copy(update={"generation_id": "retry"})})


def test_expired_parent_can_be_revoked_without_revalidating_registration(tmp_path, monkeypatch):
    args, _, _ = setup_parent(tmp_path)
    parent = owner.issue_parent(**args)
    expiry = datetime.fromisoformat(owner.resolve_parent(parent)["expires_at"])
    monkeypatch.setattr(owner, "_now", lambda: expiry)
    owner.revoke_parent(parent)
    with pytest.raises(ValueError, match="live_capability"):
        owner.resolve_parent(parent)


def test_cross_parent_plan_and_changed_descriptor_rejected(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    a, _, _ = setup_parent(first)
    b, _, _ = setup_parent(second, names=[("OTHERUS", "us"), ("666666", "kr")])
    left, right = owner.issue_parent(**a), owner.issue_parent(**b)
    with pytest.raises(ValueError, match="plan_mismatch"):
        owner.resolve_parent(left, plan=b["plan"])
    changed = a["plan"].descriptors[0].model_copy(update={"consumer_role": "CORE_DIRECTION"})
    with pytest.raises(ValueError, match="descriptor_not_authorized"):
        owner.authorize_descriptor(left, changed, plan=a["plan"])
    owner.revoke_parent(left)
    assert owner.resolve_parent(right, plan=b["plan"])["current_source_evidence"] == "NOT_ISSUED"


def test_result_flags_cannot_issue_current_evidence(tmp_path):
    args, _, _ = setup_parent(tmp_path)
    parent = owner.issue_parent(**args)
    with pytest.raises(ValueError, match="original_dispatcher_capture"):
        owner.issue_source_result(parent, plan=args["plan"])
    with pytest.raises(TypeError):
        owner.issue_source_result(parent, plan=args["plan"], source_qualified=True)
