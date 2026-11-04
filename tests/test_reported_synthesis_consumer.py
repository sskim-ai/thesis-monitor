"""Synthetic mechanics: a bounded synthesis role is not complete Core or Holder."""

import pytest

from app.services.native_accepted_ownership import BackendOwnershipRegistry
from app.services.reported_economic_claim_consumer import ReportedSynthesisClaimOwnership
from tests.test_native_owner_session import composition, session
from tests.test_reviewed_economic_property import issue
from tests.test_reviewed_balanced_synthesis import synthesis_fixture


def test_synthesis_actual_session_lifetime_and_role_separation(tmp_path):
    _, inv, candidate = synthesis_fixture()
    parent, scope, body = composition(inv)
    first = session(tmp_path / "first", parent, scope, body)
    recreated = session(tmp_path / "recreated", parent, scope, body)
    key = inv.request.invocation.invocation_id
    try:
        handle, receipt, packet = issue(parent, inv, candidate)
        assert type(receipt) is ReportedSynthesisClaimOwnership
        assert packet.role == "DECISIVE_REASON"
        assert packet.claim.text == (
            "The admitted business anchor and risk require balanced synthesis. Uncertainty: limited."
        )
        assert packet.anchor_admission_sha256 != packet.risk_admission_sha256
        assert packet.anchor_execution_generation_id != packet.generation_id
        assert packet.risk_execution_generation_id != packet.generation_id
        assert first.native_reported_economic_claim(key, receipt, packet) == packet
        assert recreated.native_reported_economic_claim(key, receipt, packet) == packet
        assert recreated.native_reported_economic_claim(key, receipt, packet) == packet
        assert parent.complete(handle, candidate.model_dump_json().encode()) == receipt
        with pytest.raises(ValueError):
            first.native_economic_candidate(key, receipt, packet)
        retry = parent.begin(key)
        with pytest.raises(ValueError, match="SUPERSEDED"):
            first.native_reported_economic_claim(key, receipt, packet)
        current = parent.complete(retry, candidate.model_dump_json().encode())
        now = parent._registry.reported_claim_packet(current, invocation=inv)
        assert recreated.native_reported_economic_claim(key, current, now) == now
        parent.revoke(current)
        with pytest.raises(ValueError, match="REVOKED"):
            recreated.native_reported_economic_claim(key, current, now)
        pending = parent.begin(key)
        parent.cancel(pending)
        with pytest.raises(ValueError):
            parent.complete(pending, candidate.model_dump_json().encode())
        assert not parent._registry._accepted
    finally:
        parent.close()


@pytest.mark.parametrize("field,value", [
    ("output_id", "unissued"), ("security_id", "wrong"),
    ("generation_id", "wrong"), ("source_generation_id", "wrong"),
    ("request_sha256", "a" * 64), ("invocation_sha256", "a" * 64),
    ("packet_sha256", "a" * 64), ("property_admission_sha256", "a" * 64),
    ("role", "HOLDER_REASON"), ("role", "SELL_DRIVER"),
    ("consumer", "HOLDER"), ("consumer", "OVERALL"),
    ("consumer", "NEWBUYER"), ("use_axis", "CORE_VALUATION_CONTEXT"),
    ("contract", "backend-reported-risk-claim-ownership-fact-v2"),
])
def test_synthesis_receipt_tamper_preserves_valid_sibling(tmp_path, field, value):
    _, inv, candidate = synthesis_fixture()
    parent, scope, body = composition(inv)
    native = session(tmp_path / "consumer", parent, scope, body)
    key = inv.request.invocation.invocation_id
    try:
        _, receipt, packet = issue(parent, inv, candidate)
        with pytest.raises(ValueError):
            native.native_reported_economic_claim(key, receipt.model_copy(update={field: value}), packet)
        assert native.native_reported_economic_claim(key, receipt, packet) == packet
        assert not parent._registry._accepted
    finally:
        parent.close()


@pytest.mark.parametrize("change", ["anchor", "risk", "source", "span", "mitigation",
                                      "lineage", "role", "stance", "bucket", "facts"])
def test_synthesis_packet_content_not_caller_rehash_authority(tmp_path, change):
    _, inv, candidate = synthesis_fixture()
    parent, scope, body = composition(inv)
    native = session(tmp_path / "consumer", parent, scope, body)
    key = inv.request.invocation.invocation_id
    try:
        _, receipt, packet = issue(parent, inv, candidate)
        updates = {
            "anchor": {"anchor_admission_sha256": "a" * 64},
            "risk": {"risk_review_sha256": "a" * 64},
            "source": {"narrative_source_sha256": "a" * 64},
            "span": {"narrative_span_sha256": ("a" * 64,)},
            "mitigation": {"narrative_context": packet.narrative_context[:-1]},
            "lineage": {"original_owner_execution_generation_id": packet.generation_id},
            "role": {"role": "HOLDER_REASON"},
            "stance": {"claim": packet.claim.model_copy(update={"text": "The two roles require HOLD."})},
            "bucket": {"claim": packet.claim.model_copy(update={"text": "The opposite roles imply balance 5.0."})},
            "facts": {"facts": packet.facts[:-1]},
        }
        from app.services.unified_snapshot_contract import digest

        forged = packet.model_copy(update=updates[change])
        forged_receipt = receipt.model_copy(update={"packet_sha256": digest(forged.model_dump(mode="json"))})
        with pytest.raises(ValueError):
            native.native_reported_economic_claim(key, forged_receipt, forged)
        assert native.native_reported_economic_claim(key, receipt, packet) == packet
        assert not parent._registry._accepted
    finally:
        parent.close()


def test_synthesis_wrong_parent_registry_and_legacy_route(tmp_path):
    _, inv, candidate = synthesis_fixture()
    parent, scope, body = composition(inv)
    native = session(tmp_path / "consumer", parent, scope, body)
    _, other_inv, _ = synthesis_fixture(identity="UNSEEN_OTHER")
    other, other_scope, other_body = composition(other_inv)
    other_native = session(tmp_path / "other", other, other_scope, other_body)
    stranger = BackendOwnershipRegistry(offline_reproof=True)
    try:
        _, receipt, packet = issue(parent, inv, candidate)
        with pytest.raises(ValueError):
            other_native.native_reported_economic_claim(other_inv.request.invocation.invocation_id, receipt, packet)
        with pytest.raises(ValueError):
            native.native_reported_economic_claim("wrong-invocation", receipt, packet)
        with pytest.raises(ValueError):
            stranger.consume_reported_claim(receipt, invocation=inv, packet=packet)
        for begin in (stranger.begin, stranger.begin_claims):
            with pytest.raises(ValueError, match="ROUTE"):
                begin(inv, model="fixture", effort="fixture")
        assert not stranger._accepted and not stranger._reported_claim_issued
    finally:
        parent.close()
        other.close()


def test_synthesis_parent_close_serializes_with_consumer(tmp_path, monkeypatch):
    from tests import test_reported_risk_consumer as inherited

    monkeypatch.setattr(inherited, "invocation_fixture", synthesis_fixture)
    inherited.test_parent_close_serializes_with_inflight_native_role_consumption(tmp_path, monkeypatch)
