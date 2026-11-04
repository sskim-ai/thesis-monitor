"""Durable intent before send; uncertain outcomes are never automatically resent."""
from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
from pathlib import Path

from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest


def destination_fingerprint(*, recipient, token):
    if not recipient or not token:
        raise ValueError("delivery_destination_binding_missing")
    # A keyed identity avoids exporting either chat IDs or enumerable plain hashes.
    return hmac.new(token.encode(), recipient.encode(), hashlib.sha256).hexdigest()


class ProductionDelivery:
    def __init__(self, *, root: Path, fingerprint: str, dry_run: bool, live_authorized: bool, notifier):
        if not fingerprint or not dry_run and not live_authorized:
            raise ValueError("production_delivery_not_authorized")
        self.root, self.fingerprint = root, fingerprint
        self.dry_run, self.notifier = dry_run, notifier

    async def deliver(self, *, run_id, generation_id, messages):
        receipts = []
        if not messages or len({m["message_id"] for m in messages}) != len(messages):
            raise ValueError("delivery_message_identity_invalid")
        for message in messages:
            if not message["text"] or message["generation_id"] != generation_id:
                raise ValueError("delivery_generation_or_content_mismatch")
            identity = dict(run_id=run_id, generation_id=generation_id, message_id=message["message_id"],
                destination_fingerprint=self.fingerprint, content_sha256=digest(message["text"]))
            key = digest(identity)
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            with (self.root / (key + ".lock")).open("a") as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise RuntimeError("delivery_already_running") from exc
                intent, result = self.root / (key + ".intent.json"), self.root / (key + ".result.json")
                if result.exists():
                    row = json.loads(result.read_bytes())
                    expected = "DRY_RUN_NOT_SENT" if self.dry_run else "SENT"
                    if any(row.get(k) != v for k, v in identity.items()) or row.get("status") != expected:
                        raise ValueError("delivery_prior_receipt_mismatch")
                    receipts.append(row)
                    continue
                if intent.exists():
                    raise RuntimeError("delivery_outcome_uncertain_no_automatic_resend")
                row = {**identity, "dedup_sha256": key, "status": "DELIVERY_ATTEMPT_STARTED"}
                durable_json(intent, row, exclusive=True)
                if self.dry_run:
                    row["status"] = "DRY_RUN_NOT_SENT"
                else:
                    outcome = await self.notifier.send({"text": message["text"], "use_llm": False})
                    if outcome != "sent":
                        raise RuntimeError("delivery_outcome_uncertain_no_automatic_resend")
                    row["status"] = "SENT"
                durable_json(result, row, exclusive=True)
                receipts.append(row)
        return {"mode": "DRY_RUN" if self.dry_run else "LIVE_AUTHORIZED",
                "normal_messages_sent": not self.dry_run, "receipts": receipts}
