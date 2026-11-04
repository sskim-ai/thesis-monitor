"""Synthetic SQLite capabilities; no provider/model or production fixture reads.

These are boundary negatives, not a fabricated full-source readiness proof.
Main's guarded harness must supply any real whole-source positive integration.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import time

import pytest

from app.services import prospective_class_c_owner as prospective
from app.services.manual_shadow_source_session import ManualShadowSourceSession, code_fingerprints
from app.services.minimal_class_c_export import capture_authorized_class_c
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_stock_acquisition import UNIVERSE
from test_minimal_class_c_export import POLICY, database


def case(tmp_path, *, expires_seconds=900):
    subjects = [(t, m) for m, tickers in UNIVERSE.items() for t in tickers]
    permission = database(tmp_path, subjects)
    now = datetime.now(timezone.utc)
    approval = prospective.record_backend_approval(prospective.ApprovalDecision(
        event_id="SYNTHETIC_MANUAL_SESSION_ONLY", approved=True,
        user_message_sha256=digest("synthetic consent, never a live read permission"),
        effective_at=now - timedelta(seconds=1), expires_at=now + timedelta(seconds=expires_seconds),
        subjects=tuple(t for t, _ in subjects)))
    capture = capture_authorized_class_c(permission)
    root = tmp_path / "captured-source"
    (root / "class-c").mkdir(parents=True)
    owners, pins = {}, {}
    generation = "synthetic-ng09-manual-session"
    for market in UNIVERSE:
        owner, document = prospective.issue_prospective_owner(approval=approval, capture=capture,
            market=market, source_generation_id="synthetic-export", generation_id=generation, policy=POLICY)
        owners[market] = owner
        name = "class-c/local-" + market + ".json"
        raw = encoded(document)
        (root / name).write_bytes(raw)
        pins[name] = sha256(raw).hexdigest()
    frozen = dict(generation_id=generation, execution_purpose=prospective.SCOPE,
                  protected_input_hashes=deepcopy(pins))
    kwargs = dict(output_root=tmp_path / "unsent-only", frozen=frozen, outcome={}, policy=POLICY,
        prospective_owners=owners, source_file_sha256=pins, expected_code_fingerprints=code_fingerprints(),
        enabled=True)
    return root, kwargs, approval, now + timedelta(seconds=expires_seconds)


@pytest.mark.parametrize("enabled", [False, None, 1, "true"])
def test_default_off_before_path_or_capability_access(enabled):
    with pytest.raises(ValueError, match="manual_shadow_disabled"):
        ManualShadowSourceSession(object(), output_root=object(), frozen=None, outcome=None, policy=None,
            prospective_owners=None, source_file_sha256=None, expected_code_fingerprints=None, enabled=enabled)


def test_original_live_handles_retained_without_copy_or_issuance(tmp_path):
    root, kwargs, _, _ = case(tmp_path)
    session = ManualShadowSourceSession(root, **kwargs)
    for market, owner in kwargs["prospective_owners"].items():
        assert session._owners[market] is owner
        prospective.require_generation(owner, kwargs["frozen"]["generation_id"])
    session._guard()
    session._guard()
    assert not kwargs["output_root"].exists()
    # Caller mutation does not rewrite the adapter's frozen source inputs.
    kwargs["frozen"]["untrusted_later_field"] = True
    session._guard()


def test_missing_original_stock_plan_blocks_without_fake_ready(tmp_path):
    root, kwargs, _, _ = case(tmp_path)
    session = ManualShadowSourceSession(root, **kwargs)
    with pytest.raises(KeyError, match="stock_plan"):
        session.prepare()
    assert session._state == "BLOCKED" and not session._sessions
    assert not kwargs["output_root"].exists()
    with pytest.raises(ValueError, match="session_terminal"):
        session.prepare()


def test_same_live_run_cannot_be_retried_in_new_session_after_failure(tmp_path):
    root, kwargs, _, _ = case(tmp_path)
    first = ManualShadowSourceSession(root, **kwargs)
    second = ManualShadowSourceSession(root, **{**kwargs, "output_root": tmp_path / "other-output"})
    with pytest.raises(KeyError, match="stock_plan"):
        first.prepare()
    with pytest.raises(ValueError, match="owner_run_already_claimed"):
        second.prepare()


@pytest.mark.parametrize("method", ["prepare", "build", "accept"])
@pytest.mark.parametrize("revoke", ["owner", "approval"])
def test_live_capability_rechecked_at_every_boundary(tmp_path, method, revoke):
    root, kwargs, approval, _ = case(tmp_path)
    session = ManualShadowSourceSession(root, **kwargs)
    if revoke == "owner":
        prospective.revoke_prospective_owner(kwargs["prospective_owners"]["us"])
    else:
        prospective.revoke_approval(approval)
    args = () if method == "prepare" else ("MARKET", "us") if method == "build" else ("MARKET", "us", {}, {})
    with pytest.raises(ValueError, match="prospective_live_"):
        getattr(session, method)(*args)
    assert not kwargs["output_root"].exists()


def test_real_expiry_without_replacing_production_clock(tmp_path):
    root, kwargs, _, expiry = case(tmp_path, expires_seconds=10)
    session = ManualShadowSourceSession(root, **kwargs)
    time.sleep(max(0, (expiry - datetime.now(timezone.utc)).total_seconds()) + 0.02)
    for method, args in (("prepare", ()), ("build", ("MARKET", "us")),
                         ("accept", ("MARKET", "us", {}, {}))):
        with pytest.raises(ValueError, match="prospective_approval_expired"):
            getattr(session, method)(*args)


def test_wrong_generation_and_unissued_owner_fail_closed(tmp_path):
    root, kwargs, _, _ = case(tmp_path)
    changed = {**kwargs, "frozen": {**kwargs["frozen"], "generation_id": "other-generation"}}
    with pytest.raises(ValueError, match="prospective_generation_or_purpose_mismatch"):
        ManualShadowSourceSession(root, **changed)
    changed = {**kwargs, "prospective_owners": {**kwargs["prospective_owners"], "us": prospective.ProspectiveOwner()}}
    with pytest.raises(ValueError, match="prospective_live_backend_owner_required"):
        ManualShadowSourceSession(root, **changed)


def test_parent_pid_must_match_without_spawning_child(tmp_path):
    root, kwargs, _, _ = case(tmp_path)
    session = ManualShadowSourceSession(root, **kwargs)
    session._pid -= 1
    with pytest.raises(ValueError, match="parent_pid_changed"):
        session.build("MARKET", "us")


@pytest.mark.parametrize("change", ["bytes", "inventory", "symlink", "internal_pin"])
def test_source_or_pin_drift_blocks_before_original_replay(tmp_path, change):
    root, kwargs, _, _ = case(tmp_path)
    session = ManualShadowSourceSession(root, **kwargs)
    local = root / "class-c/local-us.json"
    if change == "bytes":
        local.write_bytes(local.read_bytes() + b"\n")
    elif change == "inventory":
        (root / "unplanned.json").write_text("{}")
    elif change == "symlink":
        (root / "linked.json").symlink_to(local)
    else:
        session._source_pins["class-c/local-us.json"] = "0" * 64
    with pytest.raises(ValueError, match="source_bytes_drift|source_inventory_drift|symlink_denied|frozen_input_drift"):
        session.prepare()
    assert not kwargs["output_root"].exists()


def test_code_pin_cannot_omit_owner_or_be_changed_to_current_after_construction(tmp_path):
    root, kwargs, _, _ = case(tmp_path)
    changed = deepcopy(kwargs["expected_code_fingerprints"])
    changed.pop("scripts/r9_rev11_replay.py")
    with pytest.raises(ValueError, match="code_policy_schema_drift"):
        ManualShadowSourceSession(root, **{**kwargs, "expected_code_fingerprints": changed})
    session = ManualShadowSourceSession(root, **kwargs)
    session._code["scripts/r9_rev11_replay.py"] = "0" * 64
    with pytest.raises(ValueError, match="frozen_input_drift"):
        session.prepare()


@pytest.mark.parametrize("stage", ["MARKET", "CORE", "A", "B", "B2", "PRODUCTION"])
def test_no_model_stage_or_output_before_genuine_prepare(tmp_path, stage):
    root, kwargs, _, _ = case(tmp_path)
    session = ManualShadowSourceSession(root, **kwargs)
    with pytest.raises(ValueError, match="source_not_prepared"):
        session.build(stage, "us")
    with pytest.raises(ValueError, match="source_not_prepared"):
        session.accept(stage, "us", {"batch": 1}, {"status": "PASS"})
    assert not kwargs["output_root"].exists()


def test_b2_blocked_without_actual_coverage_and_census_owners(tmp_path):
    root, kwargs, _, _ = case(tmp_path)
    session = ManualShadowSourceSession(root, **kwargs)
    with pytest.raises(ValueError, match="b2_coverage_census_owners_required"):
        session.b2_request("SKHY")
    assert not kwargs["output_root"].exists()


@pytest.mark.parametrize("kind", ["existing", "inside_source", "contains_source"])
def test_output_must_be_new_and_disjoint(tmp_path, kind):
    root, kwargs, _, _ = case(tmp_path)
    output = tmp_path if kind == "contains_source" else root / "output" if kind == "inside_source" else tmp_path / "existing"
    if kind == "existing":
        output.mkdir()
    with pytest.raises(ValueError, match="new_disjoint_output_required"):
        ManualShadowSourceSession(root, **{**kwargs, "output_root": output})


def test_class_c_pin_and_full_manual_scope_required(tmp_path):
    root, kwargs, _, _ = case(tmp_path)
    for field, value, error in (("scope", "US14_ONLY", "full_manual_scope_required"),
                                ("execution_purpose", "PRODUCTION_MONITORING", "full_manual_scope_required"),
                                ("protected_input_hashes", {}, "class_c_independent_pin_required")):
        with pytest.raises(ValueError, match=error):
            ManualShadowSourceSession(root, **{**kwargs, "frozen": {**kwargs["frozen"], field: value}})
