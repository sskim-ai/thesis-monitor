from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from scripts.kr_final_preenable_test_delivery import deliver_test_messages


def test_test_delivery_is_exact_and_redacts_recipients(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": {"message_id": len(requests), "text": body["text"]},
            },
        )

    receipt_path = tmp_path / "receipt.json"
    messages = [
        {
            "ticker": "__DAILY_DIGEST_KR__",
            "route": "AI",
            "logical_identity": "test:market",
            "text": "market",
        },
        {
            "ticker": "005930",
            "route": "AI",
            "logical_identity": "test:stock:005930",
            "text": "stock",
        },
    ]
    receipt = asyncio.run(
        deliver_test_messages(
            messages,
            token="test-token",
            test_chat_id="test-chat",
            production_chat_id="production-chat",
            test_sink_alias="test:alias",
            production_sink_alias="production:alias",
            receipt_path=receipt_path,
            transport=httpx.MockTransport(handler),
        )
    )

    assert receipt["status"] == "sent"
    assert receipt["sent_message_count"] == 2
    assert receipt["exact_payload_match"] is True
    assert len(requests) == 2
    persisted = receipt_path.read_text(encoding="utf-8")
    assert "test-chat" not in persisted
    assert "production-chat" not in persisted
    assert "test-token" not in persisted


def test_test_delivery_blocks_production_collision(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="matches production"):
        asyncio.run(
            deliver_test_messages(
                [],
                token="test-token",
                test_chat_id="same-chat",
                production_chat_id="same-chat",
                test_sink_alias="test:alias",
                production_sink_alias="production:alias",
                receipt_path=tmp_path / "receipt.json",
            )
        )


def test_existing_receipt_blocks_duplicate_send(tmp_path: Path) -> None:
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing duplicate"):
        asyncio.run(
            deliver_test_messages(
                [],
                token="test-token",
                test_chat_id="test-chat",
                production_chat_id="production-chat",
                test_sink_alias="test:alias",
                production_sink_alias="production:alias",
                receipt_path=receipt_path,
            )
        )
