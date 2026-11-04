"""Offline projection mechanics, not real issuer economic/source qualification."""
import json
import subprocess
import sys

import pytest

from app.services.direction_timing_ownership_service import OwnedEvidencePacket
from app.services.legacy_context_authority import _seal_built_context
from app.services.owned_evidence_derivative import (
    restrict_owned_evidence, revoke_owned_derivative,
)
from tests.test_legacy_consumer_boundaries_r22r1 import _fixture
from tests.test_core_input_source_isolation_r21 import _isolated_data as _isolated_data


@pytest.mark.parametrize("ticker", ("UNSEEN_US_SUBSET", "UNSEEN_KR_SUBSET", "UNSEEN_ADS_SUBSET"))
def test_subset_exact_rows_preserve_ownership_and_same_parent_lookup(ticker):
    _, _, parent, _ = _fixture(ticker)
    ref = sorted(parent.core_refs)[0]
    child = restrict_owned_evidence(parent, retained_refs=(ref,), purpose="REQUEST_REF_RESTRICTION")
    assert child.core_refs == {ref}
    assert child.timing_refs == parent.timing_refs & {ref}
    assert child.evidence == tuple(row for row in parent.evidence if row.ref.ref_id == ref)
    assert child.source_packet.evidence == tuple(row for row in parent.source_packet.evidence if row.ref_id == ref)
    for restored in (child.model_copy(deep=True), OwnedEvidencePacket.model_validate_json(child.model_dump_json())):
        assert restored.core_refs == child.core_refs
        assert restored.core_refs == child.core_refs


def test_empty_subset_stays_empty_and_cannot_expand():
    _, _, parent, _ = _fixture()
    empty = restrict_owned_evidence(parent, retained_refs=(), purpose="DENIED_USE_FILTER")
    assert not empty.core_refs and not empty.timing_refs and not empty.source_packet.evidence
    with pytest.raises(ValueError, match="membership_expansion"):
        restrict_owned_evidence(empty, retained_refs=tuple(parent.core_refs), purpose="DENIED_USE_FILTER")


@pytest.mark.parametrize("change", ("security", "market", "period", "statement", "time", "domain", "receipt", "unissued"))
def test_derivative_mutation_fails_before_consumer(change):
    _, _, parent, _ = _fixture()
    child = restrict_owned_evidence(parent, retained_refs=tuple(parent.core_refs), purpose="DENIED_USE_FILTER")
    raw = child.model_dump(mode="json")
    if change in {"security", "market", "period"}:
        field = {"security": "ticker", "market": "market", "period": "assessment_date"}[change]
        raw["source_packet"][field] = {"security": "NOT_ISSUED", "market": "kr", "period": "2020-01-01"}[change]
    elif change in {"statement", "time"}:
        raw["evidence"][0]["ref"]["statement" if change == "statement" else "as_of"] = "unadmitted"
    elif change == "domain":
        raw["evidence"][0]["domain"] = "MARKET_EXPECTATIONS"
    else:
        raw["backend_seal"]["payload_sha256" if change == "receipt" else "receipt_id"] = "0" * 64
    with pytest.raises(ValueError):
        OwnedEvidencePacket.model_validate(raw).core_refs


def test_parent_revoke_invalidates_descendants_not_original_source():
    _, _, original, _ = _fixture()
    parent = restrict_owned_evidence(original, retained_refs=tuple(original.core_refs), purpose="DENIED_USE_FILTER")
    child = restrict_owned_evidence(parent, retained_refs=tuple(parent.core_refs), purpose="DENIED_USE_FILTER")
    revoke_owned_derivative(parent)
    for value in (parent, child):
        with pytest.raises(ValueError, match="unissued"):
            value.core_refs
    assert original.core_refs


def test_raw_parent_and_reseal_are_not_derivative_authority():
    _, _, original, _ = _fixture()
    with pytest.raises(ValueError, match="seal_required"):
        restrict_owned_evidence(original.model_copy(update={"backend_seal": None}), retained_refs=(), purpose="DENIED_USE_FILTER")
    child = restrict_owned_evidence(original, retained_refs=(), purpose="DENIED_USE_FILTER")
    with pytest.raises(ValueError, match="derivative_reseal_forbidden"):
        _seal_built_context(child, scope="OWNED_EVIDENCE")


@pytest.mark.parametrize("roundtrip", (False, True))
def test_stripped_derivative_cannot_use_generic_signer_after_revocation(roundtrip):
    _, _, parent, _ = _fixture()
    child = restrict_owned_evidence(parent, retained_refs=tuple(parent.core_refs), purpose="DENIED_USE_FILTER")
    revoke_owned_derivative(child)
    raw = child.model_dump(mode="json")
    raw["backend_seal"] = None
    stripped = (OwnedEvidencePacket.model_validate(raw) if roundtrip else
                child.model_copy(update={"backend_seal": None}))
    for permit in (None, object(), "OWNED_EVIDENCE"):
        with pytest.raises(ValueError, match="backend_builder_permit_required"):
            _seal_built_context(stripped, scope="OWNED_EVIDENCE", _permit=permit)


def test_builder_permits_are_scope_specific_not_public_wire_fields():
    from app.services import legacy_context_authority as owner
    _, view, owned, _ = _fixture()
    with pytest.raises(ValueError, match="backend_builder_permit_required"):
        _seal_built_context(owned, scope="OWNED_EVIDENCE", _permit=owner._CORE_BUILDER_PERMIT)
    with pytest.raises(ValueError, match="backend_builder_permit_required"):
        _seal_built_context(view.context, _permit=owner._OWNED_BUILDER_PERMIT)


def test_registry_depth_and_capacity_are_fail_closed(monkeypatch):
    from app.services import owned_evidence_derivative as owner
    _, _, root, _ = _fixture()
    child = root
    issued = []
    for _ in range(16):
        child = restrict_owned_evidence(child, retained_refs=(), purpose="DENIED_USE_FILTER")
        issued.append(child)
    with pytest.raises(ValueError, match="depth_limit"):
        restrict_owned_evidence(child, retained_refs=(), purpose="DENIED_USE_FILTER")
    monkeypatch.setattr(owner, "_MAX_ISSUED", len(owner._ISSUED))
    with pytest.raises(ValueError, match="registry_capacity"):
        restrict_owned_evidence(root, retained_refs=(), purpose="DENIED_USE_FILTER")
    for item in issued:
        revoke_owned_derivative(item)


def test_new_interpreter_has_no_derivative_registry(tmp_path):
    _, _, parent, _ = _fixture()
    child = restrict_owned_evidence(parent, retained_refs=tuple(parent.core_refs), purpose="DENIED_USE_FILTER")
    path = tmp_path / "child.json"
    path.write_text(child.model_dump_json())
    program = """import json,sys
from app.services.direction_timing_ownership_service import OwnedEvidencePacket
try:
    OwnedEvidencePacket.model_validate(json.load(open(sys.argv[1]))).core_refs
except ValueError as exc:
    print(str(exc))
else:
    raise SystemExit(2)
"""
    result = subprocess.run([sys.executable, "-B", "-c", program, str(path)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "owned_derivative_unissued_or_wrong_scope" in result.stdout
    assert json.loads(path.read_text())["backend_seal"]["receipt_id"] == child.backend_seal.receipt_id


def test_inherited_pid_cannot_issue_or_consume(monkeypatch):
    from app.services import owned_evidence_derivative as owner
    _, _, parent, _ = _fixture()
    child = restrict_owned_evidence(parent, retained_refs=(), purpose="DENIED_USE_FILTER")
    monkeypatch.setattr(owner, "_PID", -1)
    with pytest.raises(ValueError, match="owner_process_mismatch"):
        child.core_refs
    with pytest.raises(ValueError, match="owner_process_mismatch"):
        restrict_owned_evidence(parent, retained_refs=(), purpose="DENIED_USE_FILTER")
