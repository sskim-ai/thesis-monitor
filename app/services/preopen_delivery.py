"""Freeze one preopen briefing per session and destination before delivery."""

from __future__ import annotations

import fcntl
import re
from copy import copy
from datetime import date
from pathlib import Path

from app.services.analysis_report_service import telegram_render_parts
from app.services.production_delivery import ProductionDelivery, destination_fingerprint
from app.services.unified_run_artifacts import durable_json, load_json, sanitized
from app.services.unified_snapshot_contract import digest


def render_preopen_messages(messages):
    """Preserve the logical text and assign IDs to its Telegram parts in order."""
    rendered = []
    seen = set()
    for message in messages:
        message_id = message.get("message_id")
        text = message.get("text")
        if not isinstance(message_id, str) or not message_id.strip() or message_id in seen:
            raise ValueError("preopen_message_identity_invalid")
        if not isinstance(text, str) or not text:
            raise ValueError("preopen_message_text_missing")
        seen.add(message_id)
        parts = telegram_render_parts(text)
        rendered.append({
            **message,
            "message_sha256": digest(text),
            "telegram_parts": [
                {
                    "message_id": f"{message_id}:part:{index}",
                    "text": part,
                    "part_index": index,
                    "part_count": len(parts),
                    "content_sha256": digest(part),
                }
                for index, part in enumerate(parts, start=1)
            ],
        })
    if not rendered:
        raise ValueError("preopen_messages_missing")
    return rendered


def _session_path(root, market, opening_session, fingerprint, dry_run):
    market = market.lower()
    if (market not in {"kr", "us"} or type(opening_session) is not date
            or not isinstance(fingerprint, str) or not re.fullmatch("[0-9a-f]{64}", fingerprint)):
        raise ValueError("preopen_delivery_scope_invalid")
    scope = {
        "market": market,
        "opening_session": opening_session.isoformat(),
        "destination_fingerprint": fingerprint,
    }
    session_key = digest(scope)
    directory = Path(root) / ("no-send" if dry_run else "live") / session_key
    path = directory / ("preview.json" if dry_run else "manifest.json")
    return scope, session_key, path


def _delivery_status(path, scope, session_key, *, dry_run, duplicate, failure_type=None):
    manifest = load_json(path)
    mode = "NO_SEND" if dry_run else "LIVE_AUTHORIZED"
    if (manifest["scope"] != scope or manifest["session_sha256"] != session_key
            or manifest["mode"] != mode):
        raise ValueError("preopen_prior_manifest_mismatch")

    expected = "DRY_RUN_NOT_SENT" if dry_run else "SENT"
    parts = []
    for message in manifest["messages"]:
        for part in message["telegram_parts"]:
            identity = {
                "run_id": session_key,
                "generation_id": session_key,
                "message_id": part["message_id"],
                "destination_fingerprint": scope["destination_fingerprint"],
                "content_sha256": part["content_sha256"],
            }
            key = digest(identity)
            base = path.parent / "parts" / key
            try:
                receipt = load_json(base.with_suffix(".result.json"))
            except FileNotFoundError:
                if base.with_suffix(".intent.json").exists():
                    status = "DRY_RUN_INCOMPLETE" if dry_run else "OUTCOME_UNCERTAIN"
                else:
                    status = "NOT_ATTEMPTED"
            else:
                if receipt != {**identity, "dedup_sha256": key, "status": expected}:
                    raise ValueError("preopen_prior_part_receipt_mismatch")
                status = expected
            parts.append({**identity, "dedup_sha256": key, "status": status})

    completed = sum(part["status"] == expected for part in parts)
    uncertain = sum(part["status"] == "OUTCOME_UNCERTAIN" for part in parts)
    if completed == len(parts):
        status = "COMPLETE"
    elif completed:
        status = "PARTIAL"
    elif uncertain:
        status = "UNCERTAIN"
    else:
        status = "INCOMPLETE"
    return {
        "mode": mode,
        "status": status,
        "duplicate": duplicate,
        "session_sha256": session_key,
        "manifest_path": str(path),
        "preview_path": str(path) if dry_run else None,
        "normal_messages_sent": not dry_run and status == "COMPLETE",
        "logical_count": len(manifest["messages"]),
        "physical_count": len(parts),
        "completed_parts": completed,
        "uncertain_parts": uncertain,
        "receipts": parts,
        "failure_type": failure_type,
    }


def existing_preopen_preview(*, root, market, opening_session, recipient_fingerprint):
    """Reuse a frozen NO_SEND briefing before starting another source read."""
    scope, key, path = _session_path(root, market, opening_session, recipient_fingerprint, True)
    if path.is_file():
        return _delivery_status(path, scope, key, dry_run=True, duplicate=True)
    return None


class _TelegramPartTransport:
    def __init__(self, notifier, fingerprint):
        settings = notifier.settings
        if settings.notification_dry_run or fingerprint != destination_fingerprint(
            recipient=settings.telegram_chat_id, token=settings.telegram_bot_token
        ):
            raise ValueError("preopen_live_destination_mismatch")
        self.notifier = copy(notifier)
        self.notifier.settings = settings.model_copy(update={"telegram_retry_attempts": 1})

    async def send(self, payload):
        # TelegramNotifier.send() would split the already numbered part again.
        result = await self.notifier.send_chunk(payload["text"])
        return "sent" if result.message_id is not None else "uncertain"


async def deliver_preopen(
    *, root, market, opening_session, recipient_fingerprint, messages,
    dry_run=True, live_authorized=False, notifier=None, metadata=None,
):
    scope, key, path = _session_path(root, market, opening_session, recipient_fingerprint, dry_run)
    transport = None
    if not dry_run:
        if not live_authorized or notifier is None:
            raise ValueError("production_delivery_not_authorized")
        transport = _TelegramPartTransport(notifier, recipient_fingerprint)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.with_suffix(".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if path.is_file():
                return _delivery_status(path, scope, key, dry_run=dry_run, duplicate=True)
            return {"status": "ALREADY_RUNNING", "duplicate": True, "preview_path": None}
        if path.exists():
            return _delivery_status(path, scope, key, dry_run=dry_run, duplicate=True)
        rendered = render_preopen_messages(messages)
        durable_json(path, {
            "scope": scope,
            "session_sha256": key,
            "mode": "NO_SEND" if dry_run else "LIVE_AUTHORIZED",
            "metadata": sanitized(metadata or {}),
            "messages": rendered,
        }, exclusive=True)
        delivery = ProductionDelivery(
            root=path.parent / "parts", fingerprint=recipient_fingerprint,
            dry_run=dry_run, live_authorized=live_authorized, notifier=transport,
        )
        physical = [
            {**part, "generation_id": key}
            for message in rendered for part in message["telegram_parts"]
        ]
        failure_type = None
        try:
            await delivery.deliver(run_id=key, generation_id=key, messages=physical)
        except Exception as exc:
            failure_type = type(exc).__name__
        return _delivery_status(
            path, scope, key, dry_run=dry_run, duplicate=False, failure_type=failure_type,
        )
