import asyncio
import json

import pytest

from app.services.production_delivery import ProductionDelivery, destination_fingerprint
from app.services.unified_snapshot_contract import digest


class Notifier:
    def __init__(self, outcome="sent"):
        self.calls = []
        self.outcome = outcome

    async def send(self, payload):
        self.calls.append(payload)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def run(delivery, generation="current", text="Offline fixture"):
    return asyncio.run(delivery.deliver(run_id="market-date", generation_id=generation,
        messages=[dict(message_id="stock", generation_id=generation, text=text)]))


def test_dry_run_no_send_and_dedup(tmp_path):
    notifier = Notifier()
    delivery = ProductionDelivery(root=tmp_path, fingerprint=digest("synthetic"), dry_run=True,
                                  live_authorized=False, notifier=notifier)
    first = run(delivery)
    assert first == run(delivery)
    assert first["receipts"][0]["status"] == "DRY_RUN_NOT_SENT"
    assert first["normal_messages_sent"] is False and notifier.calls == []


def test_live_authorization_and_different_generation_does_not_suppress(tmp_path):
    notifier = Notifier()
    delivery = ProductionDelivery(root=tmp_path, fingerprint=digest("synthetic"), dry_run=False,
                                  live_authorized=True, notifier=notifier)
    run(delivery)
    run(delivery)
    run(delivery, generation="next")
    run(delivery, generation="next", text="changed")
    assert len(notifier.calls) == 3


def test_uncertain_send_is_not_repeated(tmp_path):
    notifier = Notifier(TimeoutError())
    delivery = ProductionDelivery(root=tmp_path, fingerprint=digest("synthetic"), dry_run=False,
                                  live_authorized=True, notifier=notifier)
    with pytest.raises(TimeoutError):
        run(delivery)
    with pytest.raises(RuntimeError, match="uncertain"):
        run(delivery)
    assert len(notifier.calls) == 1


def test_prior_dry_run_cannot_masquerade_as_live(tmp_path):
    notifier = Notifier()
    run(ProductionDelivery(root=tmp_path, fingerprint="same", dry_run=True, live_authorized=False, notifier=notifier))
    with pytest.raises(ValueError, match="receipt"):
        run(ProductionDelivery(root=tmp_path, fingerprint="same", dry_run=False, live_authorized=True, notifier=notifier))
    assert not notifier.calls


def test_fingerprint_does_not_export_recipient_or_token(tmp_path):
    fingerprint = destination_fingerprint(recipient="synthetic-destination", token="synthetic-token")
    delivery = ProductionDelivery(root=tmp_path, fingerprint=fingerprint, dry_run=True, live_authorized=False, notifier=Notifier())
    result = run(delivery)
    assert "synthetic-destination" not in json.dumps(result)
    assert "synthetic-token" not in json.dumps(result)
    assert fingerprint != destination_fingerprint(recipient="different", token="synthetic-token")
