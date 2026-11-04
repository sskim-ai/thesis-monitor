"""Actual stage-session boundary for synthetic reviewed risk fixtures."""

from threading import Event, Thread

import pytest

from app.services.native_accepted_ownership import BackendOwnershipRegistry
from app.services.reported_economic_claim_consumer import (
    ReportedEconomicClaimOwnership,
    ReportedRiskClaimOwnership,
)
from tests.test_native_owner_session import composition, session
from tests.test_reviewed_economic_property import issue, reviewed_fixture
from tests.test_reviewed_narrative_risk import invocation_fixture


def test_risk_actual_session_recreation_retry_revoke_cancel(tmp_path):
    owner, inv, candidate = invocation_fixture()
    parent, scope, body = composition(inv)
    key = inv.request.invocation.invocation_id
    first = session(tmp_path / "first", parent, scope, body)
    recreated = session(tmp_path / "recreated", parent, scope, body)
    try:
        handle, receipt, packet = issue(parent, inv, candidate)
        assert type(receipt) is ReportedRiskClaimOwnership
        assert first.native_reported_economic_claim(key, receipt, packet) == packet
        assert recreated.native_reported_economic_claim(key, receipt, packet) == packet
        assert recreated.native_reported_economic_claim(key, receipt, packet) == packet
        assert parent.complete(handle, candidate.model_dump_json().encode()) == receipt
        assert len(packet.narrative_context) == len(owner.admission.review.spans)
        assert any("contracts" in s.text for s in packet.narrative_context)
        assert not parent._registry._accepted
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
    with pytest.raises(ValueError):
        first.native_reported_economic_claim(key, receipt, packet)


@pytest.mark.parametrize(
    "field,value",
    [
        ("output_id", "unissued"),
        ("packet_sha256", "a" * 64),
        ("request_sha256", "a" * 64),
        ("invocation_sha256", "a" * 64),
        ("property_admission_sha256", "a" * 64),
        ("claim_eligibility_sha256", "a" * 64),
        ("role", "BUY_DRIVER"),
        ("consumer", "HOLDER"),
        ("use_axis", "HOLDER_DIRECTION"),
        ("security_id", "wrong"),
        ("generation_id", "wrong"),
        ("source_generation_id", "wrong"),
        ("contract", "backend-reported-economic-claim-ownership-fact-v2"),
    ],
)
def test_forged_receipt_rejected_at_actual_consumer(tmp_path, field, value):
    _, inv, candidate = invocation_fixture()
    parent, scope, body = composition(inv)
    native = session(tmp_path / "consumer", parent, scope, body)
    try:
        _, receipt, packet = issue(parent, inv, candidate)
        with pytest.raises(ValueError):
            native.native_reported_economic_claim(
                inv.request.invocation.invocation_id,
                receipt.model_copy(update={field: value}),
                packet,
            )
        assert not parent._registry._accepted
        assert (
            native.native_reported_economic_claim(
                inv.request.invocation.invocation_id, receipt, packet
            )
            == packet
        )
    finally:
        parent.close()


@pytest.mark.parametrize(
    "change", ["span", "context", "source", "review", "claim", "facts", "provenance", "role"]
)
def test_changed_packet_rejected_at_actual_consumer(tmp_path, change):
    _, inv, candidate = invocation_fixture()
    parent, scope, body = composition(inv)
    native = session(tmp_path / "consumer", parent, scope, body)
    try:
        _, receipt, packet = issue(parent, inv, candidate)
        changes = {
            "span": {"narrative_span_sha256": ("a" * 64,)},
            "context": {"narrative_context": packet.narrative_context[:-1]},
            "source": {"narrative_source_sha256": "a" * 64},
            "review": {"review_sha256": "a" * 64},
            "claim": {
                "claim": packet.claim.model_copy(update={"text": "Current downturn proves SELL"})
            },
            "facts": {"facts": packet.facts[:-1]},
            "provenance": {"source_kind": "REAL_SEALED_SOURCE"},
            "role": {"role": "HOLDER_REASON"},
        }
        with pytest.raises(ValueError):
            native.native_reported_economic_claim(
                inv.request.invocation.invocation_id,
                receipt,
                packet.model_copy(update=changes[change]),
            )
        assert not parent._registry._accepted
    finally:
        parent.close()


def test_cross_parent_wrong_request_and_genuine_downgrade_are_rejected(tmp_path):
    _, inv, candidate = invocation_fixture()
    parent, scope, body = composition(inv)
    native = session(tmp_path / "consumer", parent, scope, body)
    _, other_inv, _ = invocation_fixture(identity="UNSEEN_OTHER")
    other, other_scope, other_body = composition(other_inv)
    other_native = session(tmp_path / "other", other, other_scope, other_body)
    try:
        handle, receipt, packet = issue(parent, inv, candidate)
        with pytest.raises(ValueError):
            other_native.native_reported_economic_claim(
                other_inv.request.invocation.invocation_id, receipt, packet
            )
        with pytest.raises(ValueError):
            native.native_reported_economic_claim("wrong-invocation", receipt, packet)
        with pytest.raises(ValueError, match="RESPONSE_CONFLICT"):
            parent.complete(handle, candidate.model_dump_json().encode() + b" ")
        stranger = BackendOwnershipRegistry(offline_reproof=True)
        for begin in (stranger.begin, stranger.begin_claims):
            with pytest.raises(ValueError, match="ROUTE"):
                begin(inv, model="fixture", effort="fixture")
        with pytest.raises(ValueError):
            stranger.consume_reported_claim(receipt, invocation=inv, packet=packet)
        assert not stranger._accepted and not stranger._reported_claim_issued
    finally:
        parent.close()
        other.close()


def test_r17_positive_and_new_risk_cannot_exchange_receipt_types(tmp_path):
    _, buy, buy_candidate = reviewed_fixture()
    buy_parent, buy_scope, buy_body = composition(buy)
    buy_native = session(tmp_path / "buy", buy_parent, buy_scope, buy_body)
    _, risk, risk_candidate = invocation_fixture()
    risk_parent, risk_scope, risk_body = composition(risk)
    risk_native = session(tmp_path / "risk", risk_parent, risk_scope, risk_body)
    try:
        _, buy_receipt, buy_packet = issue(buy_parent, buy, buy_candidate)
        _, risk_receipt, risk_packet = issue(risk_parent, risk, risk_candidate)
        assert (
            buy_native.native_reported_economic_claim(
                buy.request.invocation.invocation_id, buy_receipt, buy_packet
            )
            == buy_packet
        )
        assert (
            risk_native.native_reported_economic_claim(
                risk.request.invocation.invocation_id, risk_receipt, risk_packet
            )
            == risk_packet
        )
        for native, inv, receipt, packet in (
            (buy_native, buy, risk_receipt, risk_packet),
            (risk_native, risk, buy_receipt, buy_packet),
        ):
            with pytest.raises(ValueError):
                native.native_reported_economic_claim(
                    inv.request.invocation.invocation_id, receipt, packet
                )
    finally:
        buy_parent.close()
        risk_parent.close()


def test_identical_serialized_receipt_with_wrong_python_contract_type(tmp_path):
    _, inv, candidate = invocation_fixture()
    parent, scope, body = composition(inv)
    native = session(tmp_path / "consumer", parent, scope, body)
    try:
        _, receipt, packet = issue(parent, inv, candidate)
        wrong_type = ReportedEconomicClaimOwnership.model_construct(**receipt.model_dump())
        assert wrong_type.model_dump_json() == receipt.model_dump_json()
        with pytest.raises(ValueError, match="^REPORTED_ECONOMIC_FACT_V2_RECEIPT_REQUIRED$"):
            native.native_reported_economic_claim(
                inv.request.invocation.invocation_id, wrong_type, packet
            )
        assert (
            native.native_reported_economic_claim(
                inv.request.invocation.invocation_id, receipt, packet
            )
            == packet
        )
        assert not parent._registry._accepted
    finally:
        parent.close()


def test_parent_close_serializes_with_inflight_native_role_consumption(tmp_path, monkeypatch):
    _, inv, candidate = invocation_fixture()
    parent, scope, body = composition(inv)
    native = session(tmp_path / "consumer", parent, scope, body)
    _, receipt, packet = issue(parent, inv, candidate)
    key = inv.request.invocation.invocation_id
    looked_up, release, close_entered, closed = Event(), Event(), Event(), Event()
    result, errors, order = [], [], []
    original_lookup = parent.invocation
    original_consume = parent._registry.consume_reported_claim

    def lookup(value):
        capability = original_lookup(value)
        looked_up.set()
        if not release.wait(5):
            raise AssertionError("TEST_LOOKUP_BARRIER_TIMEOUT")
        return capability

    def registry_consume(*args, **kwargs):
        value = original_consume(*args, **kwargs)
        order.append("consumed")
        return value

    def consume():
        try:
            result.append(native.native_reported_economic_claim(key, receipt, packet))
        except Exception as error:
            errors.append(error)

    def close():
        close_entered.set()
        parent.close()
        order.append("closed")
        closed.set()

    monkeypatch.setattr(parent, "invocation", lookup)
    monkeypatch.setattr(parent._registry, "consume_reported_claim", registry_consume)
    consumer = Thread(target=consume)
    closer = Thread(target=close)
    consumer.start()
    try:
        assert looked_up.wait(5)
        closer.start()
        assert close_entered.wait(5)
        assert not closed.wait(0.2), "PARENT_CLOSED_WHILE_CONSUMER_HELD_LIVE_CAPABILITY"
    finally:
        release.set()
        consumer.join(5)
        if closer.ident is not None:
            closer.join(5)
        parent.close()
    assert not consumer.is_alive() and not closer.is_alive()
    assert not errors and result == [packet] and order == ["consumed", "closed"]
    with pytest.raises(ValueError):
        native.native_reported_economic_claim(key, receipt, packet)
