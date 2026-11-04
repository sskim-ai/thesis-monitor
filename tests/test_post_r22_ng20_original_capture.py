"""Original membership-to-session boundary, not a full native positive.

The full capture worker requires a separately admitted owner bootstrap. These
tests do not manufacture its source receipts or claim that prepare completed.
"""

from copy import deepcopy
from hashlib import sha256

import pytest

from app.services import prospective_class_c_owner as prospective
from app.services.manual_shadow_source_session import ManualShadowSourceSession, code_fingerprints
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import ROLES, UNIVERSE, make_reads
from tests import test_post_r22_ng20_class_c as original_class_c

GENERATION, POLICY = original_class_c.GENERATION, original_class_c.POLICY
captured, clock = original_class_c.captured, original_class_c.clock


def session_inputs(tmp_path, captured):
    root = tmp_path / "original-captured-membership"
    (root / "class-c").mkdir(parents=True)
    pins = {}
    for market, raw in captured["projection_bytes"].items():
        name = "class-c/local-" + market + ".json"
        (root / name).write_bytes(raw)
        pins[name] = sha256(raw).hexdigest()
    return root, dict(
        output_root=tmp_path / "native-output-not-yet-issued",
        frozen=dict(generation_id=GENERATION, execution_purpose=prospective.SCOPE,
                    protected_input_hashes=deepcopy(pins)),
        outcome={}, policy=POLICY, prospective_owners=captured["owners"],
        source_file_sha256=pins, expected_code_fingerprints=code_fingerprints(),
        enabled=True, native_admission_enabled=True,
    )


def test_original_registered_capture_enters_exact_request_builder(captured, clock, record_property):
    universe = {m: captured["projections"][m]["universe"] for m in UNIVERSE}
    reads = make_reads(universe, captured["securities"], at=clock,
                       counts={m: {r: 300 for r in ROLES} for m in UNIVERSE})
    assert len(reads) == len({r.entry_id for r in reads}) == 88
    assert {r.subject for r in reads} == set(captured["securities"])
    assert all(r.canonical_security_id == captured["securities"][r.subject]["canonical_security_id"]
               and r.latest_completed_session == captured["sessions"][r.market] for r in reads)
    record_property("ng20_original_request_builder", dict(
        kind="TEST_ONLY_SYNTHETIC", original_builder="unified_stock_acquisition.make_reads",
        original_capture_sha256=digest(captured["capture_receipt"]),
        reads=88, subjects=22, reads_sha256=digest([r.model_dump(mode="json") for r in reads]),
        transport_calls=0, full_capture="NOT_RUN_OWNER_BOOTSTRAP_UNAVAILABLE",
        whole_source="NOT_ISSUED", native_manual_positive=0,
    ))


def test_original_manual_constructor_retains_real_test_issuer_handles(tmp_path, captured, record_property):
    root, kwargs = session_inputs(tmp_path, captured)
    session = ManualShadowSourceSession(root, **kwargs)
    for market, owner in captured["owners"].items():
        assert session._owners[market] is owner
        prospective.require_generation(owner, GENERATION)
    session._guard()
    assert not session._sessions and not kwargs["output_root"].exists()
    record_property("ng20_manual_constructor", dict(
        kind="TEST_ONLY_SYNTHETIC", constructor="PASS", owners=["kr", "us"],
        original_capture_sha256=digest(captured["capture_receipt"]),
        prepare="NOT_RUN_MISSING_ORIGINAL_FULL_SOURCE_CAPTURE",
        market="NOT_RUN", native_parent="NOT_ISSUED", native_manual_positive=0,
        N1="NOT_RUN_NO_AUTHENTIC_PARENT", N2="NOT_RUN_NO_AUTHENTIC_REQUEST",
    ))


@pytest.mark.parametrize("mutation", ["generation", "unissued", "disabled"])
def test_constructor_rejects_authority_substitution(tmp_path, captured, mutation):
    root, kwargs = session_inputs(tmp_path, captured)
    if mutation == "generation":
        kwargs["frozen"]["generation_id"] = "wrong-generation"
    elif mutation == "unissued":
        kwargs["prospective_owners"] = {"kr": prospective.ProspectiveOwner(), "us": captured["owners"]["us"]}
    else:
        kwargs["enabled"] = False
    with pytest.raises(ValueError):
        ManualShadowSourceSession(root, **kwargs)
    assert not kwargs["output_root"].exists()


def test_original_local_owner_rejects_cross_market_handle(captured, clock):
    from app.services.unified_local_seed_bridge import admit_pinned_local_seed

    with pytest.raises(ValueError):
        admit_pinned_local_seed(captured["projection_bytes"]["kr"],
            expected_sha256=captured["protected_input_hashes"]["class-c/local-kr.json"],
            market="kr", session_key=captured["sessions"]["kr"], cutoff=clock,
            subjects=UNIVERSE["kr"], policy=POLICY, prospective_owner=captured["owners"]["us"])


def test_original_session_rechecks_source_bytes_and_live_approval(tmp_path, captured):
    root, kwargs = session_inputs(tmp_path, captured)
    session = ManualShadowSourceSession(root, **kwargs)
    prospective.revoke_approval(captured["approval"])
    with pytest.raises(ValueError, match="prospective_live_operator_approval_required"):
        session._guard()
    assert not session._sessions and not kwargs["output_root"].exists()


def test_original_session_source_drift_denies_before_replay(tmp_path, captured):
    root, kwargs = session_inputs(tmp_path, captured)
    session = ManualShadowSourceSession(root, **kwargs)
    target = root / "class-c/local-kr.json"
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ValueError, match="source_bytes_drift"):
        session.prepare()
    assert not session._sessions and not kwargs["output_root"].exists()
