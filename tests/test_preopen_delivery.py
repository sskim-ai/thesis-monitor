import asyncio
import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from app.services.notification_service import TelegramNotifier
from app.services.preopen_delivery import (
    deliver_preopen,
    existing_preopen_preview,
    render_preopen_messages,
)
from app.services.production_delivery import destination_fingerprint
from app.services.unified_snapshot_contract import digest


OPENING = date(2026, 11, 30)
SYNTHETIC_DESTINATION = digest("synthetic")


def messages(text):
    return [{"message_id": "summary", "text": text}]


def delivery(root, text, *, fingerprint=SYNTHETIC_DESTINATION, **overrides):
    arguments = {
        "root": root, "market": "kr", "opening_session": OPENING,
        "recipient_fingerprint": fingerprint, "messages": messages(text),
    }
    return deliver_preopen(**(arguments | overrides))


def mock_notifier(handler):
    notifier = TelegramNotifier(transport=httpx.MockTransport(handler))
    notifier.settings = notifier.settings.model_copy(update={
        "notification_dry_run": False,
        "telegram_bot_token": "synthetic-token",
        "telegram_chat_id": "synthetic-destination",
        "telegram_retry_attempts": 4,
    })
    fingerprint = destination_fingerprint(
        recipient=notifier.settings.telegram_chat_id, token=notifier.settings.telegram_bot_token,
    )
    return notifier, fingerprint


def test_preserves_text_order_hash_and_utf16_part_limit():
    text = "  한글 🧪\n\n " + ("시장 🏢 가격  \n" * 900) + "\n "
    row, = render_preopen_messages(messages(text))
    parts = row["telegram_parts"]
    assert len(parts) > 1
    assert row["text"] == text and row["message_sha256"] == digest(text)
    assert "".join(part["text"].split("\n", 1)[1] for part in parts) == text
    for index, part in enumerate(parts, 1):
        assert part["message_id"] == f"summary:part:{index}"
        assert part["text"].startswith(f"[{index}/{len(parts)}]\n")
        assert len(part["text"].encode("utf-16-le")) // 2 <= 4096
        assert part["content_sha256"] == digest(part["text"])


def test_no_send_preview_is_frozen_per_market_date_and_destination(tmp_path):
    earlier = dict(
        root=tmp_path, market="kr", opening_session=OPENING,
        recipient_fingerprint=SYNTHETIC_DESTINATION,
    )
    assert existing_preopen_preview(**earlier) is None
    first = asyncio.run(delivery(tmp_path, "first", metadata={"base_session": "2026-11-27"}))
    assert first["mode"] == "NO_SEND"
    assert first["status"] == "COMPLETE" and not first["normal_messages_sent"]
    assert first["receipts"][0]["status"] == "DRY_RUN_NOT_SENT"
    second = asyncio.run(delivery(tmp_path, "new text", metadata={"source": "new attempt"}))
    assert second == existing_preopen_preview(**earlier)
    assert second["duplicate"] and second["preview_path"] == first["preview_path"]
    preview = json.loads(Path(first["preview_path"]).read_text())
    assert preview["messages"][0]["text"] == "first"
    assert preview["metadata"]["base_session"] == "2026-11-27"
    assert preview.pop('messages_sha256') == digest(preview['messages'])
    Path(first['preview_path']).write_text(json.dumps(preview))
    assert existing_preopen_preview(**earlier) == second
    for change in (
        {"market": "us"}, {"opening_session": date(2026, 12, 1)},
        {"fingerprint": digest("other")},
    ):
        distinct = asyncio.run(delivery(tmp_path, "new", **change))
        assert distinct["session_sha256"] != first["session_sha256"]
        assert not distinct["duplicate"]


@pytest.mark.parametrize('damage,legacy', [
    ('logical_text', True), ('physical_text', True), ('removed_message', False), ('empty_messages', True),
])
def test_frozen_preview_rejects_changed_content(tmp_path, damage, legacy):
    original = messages('first') + [{"message_id": "detail", "text": "original detail"}]
    first = asyncio.run(delivery(tmp_path, 'unused', messages=original))
    path = Path(first['preview_path'])
    preview = json.loads(path.read_text())
    if legacy:
        preview.pop('messages_sha256')
    if damage == 'logical_text':
        preview['messages'][0]['text'] = 'changed briefing'
    elif damage == 'physical_text':
        preview['messages'][0]['telegram_parts'][0]['text'] = 'changed part'
    elif damage == 'removed_message':
        preview['messages'].pop()
    else:
        preview['messages'].clear()
    path.write_text(json.dumps(preview))

    with pytest.raises(ValueError, match='preopen_prior_manifest_content_mismatch'):
        existing_preopen_preview(root=tmp_path, market='kr', opening_session=OPENING,
                                 recipient_fingerprint=SYNTHETIC_DESTINATION)
    with pytest.raises(ValueError, match='preopen_prior_manifest_content_mismatch'):
        asyncio.run(delivery(tmp_path, 'replacement'))
    assert json.loads(path.read_text()) == preview


def test_live_reuses_exact_physical_parts_and_no_send_keeps_separate_receipts(tmp_path):
    calls = []

    def handler(request):
        calls.append(json.loads(request.content)["text"])
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    notifier, fingerprint = mock_notifier(handler)
    text = " " + "x" * 8010 + " "
    dry = asyncio.run(delivery(tmp_path, text, fingerprint=fingerprint, notifier=notifier))
    assert not calls
    with pytest.raises(ValueError, match="not_authorized"):
        asyncio.run(delivery(tmp_path, text, fingerprint=fingerprint, dry_run=False, notifier=notifier))

    receipt = asyncio.run(delivery(
        tmp_path, text, fingerprint=fingerprint, dry_run=False, live_authorized=True,
        notifier=notifier,
    ))
    expected = render_preopen_messages(messages(text))[0]["telegram_parts"]
    assert calls == [part["text"] for part in expected]
    assert receipt["normal_messages_sent"] and receipt["status"] == "COMPLETE"
    assert receipt["session_sha256"] == dry["session_sha256"]
    assert receipt["manifest_path"] != dry["manifest_path"]
    assert notifier.settings.telegram_retry_attempts == 4


def test_uncertain_partial_delivery_never_resends_or_attempts_later_parts(tmp_path):
    calls = []

    def handler(request):
        calls.append(json.loads(request.content)["text"])
        if len(calls) == 2:
            return httpx.Response(503, json={"ok": False})
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    notifier, fingerprint = mock_notifier(handler)
    options = dict(
        fingerprint=fingerprint, dry_run=False, live_authorized=True, notifier=notifier,
    )
    first = asyncio.run(delivery(tmp_path, "x" * 9200, **options))
    assert first["status"] == "PARTIAL" and first["failure_type"] == "TelegramDeliveryError"
    expected = ["SENT", "OUTCOME_UNCERTAIN", "NOT_ATTEMPTED"]
    assert [part["status"] for part in first["receipts"]] == expected
    duplicate = asyncio.run(delivery(tmp_path, "replacement", **options))
    assert len(calls) == 2 and duplicate["duplicate"]
    assert [part["status"] for part in duplicate["receipts"]] == expected


def test_concurrent_replacement_does_not_send_frozen_part(tmp_path):
    async def concurrent():
        started, release = asyncio.Event(), asyncio.Event()
        requests = []

        async def handler(request):
            requests.append(json.loads(request.content)["text"])
            started.set()
            await release.wait()
            return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

        notifier, fingerprint = mock_notifier(handler)
        options = dict(
            fingerprint=fingerprint, dry_run=False, live_authorized=True, notifier=notifier,
        )
        initial = asyncio.create_task(delivery(tmp_path, "initial", **options))
        await started.wait()
        try:
            duplicate = await delivery(tmp_path, "replacement", **options)
            assert duplicate["duplicate"] and requests == ["initial"]
        finally:
            release.set()
            receipt = await initial
        assert receipt["status"] == "COMPLETE"

    asyncio.run(concurrent())
