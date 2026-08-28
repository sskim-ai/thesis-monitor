from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pytest

from app.services.us_market_message_quality_service import (
    validate_us_market_message_payload,
)
from scripts.us_macro_quality_reports import generate


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


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _inputs(tmp_path: Path) -> argparse.Namespace:
    payload_sha = _sha(GOOD_PAYLOAD)
    quality = validate_us_market_message_payload(GOOD_PAYLOAD).to_dict()
    market = {
        "selected_text": GOOD_PAYLOAD,
        "selected_sha256": payload_sha,
    }
    receipt = {
        "contract": "test",
        "namespace": "test",
        "status": "sent",
        "test_sink_alias": "test:alias",
        "production_sink_alias": "production:alias",
        "production_collision": False,
        "production_intent_created": False,
        "planned_message_count": 1,
        "sent_message_count": 1,
        "exact_payload_match": True,
        "duplicate_count": 0,
        "orphan_count": 0,
        "unowned_retry_count": 0,
        "production_recipient_send_count": 0,
        "rows": [
            {
                "sequence": 1,
                "ticker": "__DAILY_DIGEST__",
                "route": "AI",
                "logical_identity": "test:market",
                "character_count": len(GOOD_PAYLOAD),
                "rendered_sha256": payload_sha,
                "outbound_sha256": payload_sha,
                "received_sha256": payload_sha,
                "exact_payload_match": True,
                "remote_message_alias": "message:alias",
                "send_attempts": 1,
                "received_payload_quality": quality,
            }
        ],
    }
    market_path = tmp_path / "market.json"
    receipt_path = tmp_path / "receipt.json"
    market_path.write_text(json.dumps(market), encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    fixture = Path(__file__).parent / "fixtures" / "us_run43_bad_market_payload.txt"
    return argparse.Namespace(
        market_audit=market_path,
        receipt=receipt_path,
        bad_fixture=fixture,
        reports=tmp_path / "reports",
        instruction_path=tmp_path / "instruction.md",
        instruction_commit="instruction",
        implementation_commit="implementation",
        focused_tests="PASS",
        full_pytest="PASS",
        ruff="PASS",
        diff_check="PASS",
        knowledge_parity="PASS",
        public_action="0.4.5 PASS",
        operation_id="20/20 PASS",
        ci="PASS",
        api_health="PASS",
        operating_promotion="PASS",
    )


def test_report_generation_is_bound_to_exact_received_payload(tmp_path: Path) -> None:
    args = _inputs(tmp_path)

    generate(args)

    readiness = json.loads(
        (args.reports / "20260828-us-macro-quality-readiness.json").read_text()
    )
    safe_receipt = json.loads(
        (args.reports / "20260828-us-macro-quality-test-receipt.json").read_text()
    )
    received_sha = safe_receipt["rows"][0]["received_sha256"]
    assert readiness["quality_report_payload_sha256"] == received_sha
    assert readiness["quality_report_payload_hash_mismatch"] == 0
    assert readiness["run43_exact_bad_payload_new_quality_gate"] == "FAIL_AS_EXPECTED"


def test_report_generation_rejects_stale_quality_payload(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    receipt = json.loads(args.receipt.read_text())
    receipt["rows"][0]["received_payload_quality"]["payload_sha256"] = "stale"
    args.receipt.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(ValueError, match="payload SHA mismatch"):
        generate(args)
