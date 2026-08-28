from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx

from app.services.us_market_message_quality_service import (
    quality_result_matches_received_payload,
    validate_us_market_message_payload,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages


FIXTURE = Path(__file__).parent / "fixtures" / "us_run43_bad_market_payload.txt"
GOOD_PAYLOAD = """🇺🇸 미국시장 마감

📈 주요 지수
• SPY +0.66%
• QQQ +1.37%
• IWM +0.29%
• SOXX +1.95%
• RSP -0.30%

🔎 시장 내부
• 업종 강세: 정보기술 +3.16%
• 업종 약세: 필수소비재 -1.38%

📌 다음 확인
• 다음 완료 세션의 참여 폭을 확인합니다."""


def test_run43_exact_bad_payload_fails_new_quality_gate() -> None:
    result = validate_us_market_message_payload(FIXTURE.read_text().rstrip("\n"))

    assert result.status == "FAIL"
    assert result.malformed_zero_change_korean == 1
    assert result.generic_no_change_macro_section_visible == 1
    assert "malformed_zero_change_korean" in result.errors


def test_macro_omitted_payload_passes() -> None:
    result = validate_us_market_message_payload(GOOD_PAYLOAD)

    assert result.status == "PASS"
    assert result.malformed_zero_change_korean == 0
    assert result.generic_no_change_macro_section_visible == 0


def test_specific_neutral_macro_payload_passes() -> None:
    payload = GOOD_PAYLOAD.replace(
        "\n\n📌 다음 확인",
        "\n\n🌐 보조 시장환경\n"
        "• 공식 관측(2026-08-27) VIX는 큰 변화 없이 유지됐습니다."
        "\n\n📌 다음 확인",
    )

    result = validate_us_market_message_payload(payload)

    assert result.status == "PASS"


def test_quality_payload_hash_must_match_received_payload() -> None:
    result = validate_us_market_message_payload(GOOD_PAYLOAD)
    bad_result = validate_us_market_message_payload(
        FIXTURE.read_text().rstrip("\n")
    )

    assert quality_result_matches_received_payload(result, result.payload_sha256)
    assert not quality_result_matches_received_payload(
        result, bad_result.payload_sha256
    )


def test_delivery_quality_validator_receives_exact_telegram_payload(
    tmp_path: Path,
) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={"ok": True, "result": {"message_id": 1, "text": body["text"]}},
        )

    def validator(text: str) -> dict[str, object]:
        seen.append(text)
        return validate_us_market_message_payload(text).to_dict()

    receipt = asyncio.run(
        deliver_test_messages(
            [
                {
                    "ticker": "__DAILY_DIGEST__",
                    "route": "AI",
                    "logical_identity": "test:us:market",
                    "text": GOOD_PAYLOAD,
                }
            ],
            token="test-token",
            test_chat_id="test-chat",
            production_chat_id="production-chat",
            test_sink_alias="test:alias",
            production_sink_alias="production:alias",
            receipt_path=tmp_path / "receipt.json",
            transport=httpx.MockTransport(handler),
            received_payload_validator=validator,
        )
    )

    row = receipt["rows"][0]
    quality = row["received_payload_quality"]
    assert seen == [GOOD_PAYLOAD]
    assert quality["status"] == "PASS"
    assert quality["payload_sha256"] == row["received_sha256"]
