from __future__ import annotations

import argparse
import json

from scripts.preconfirmation_asymmetry_decision_engine_v2 import (
    _historical_diagnostic,
    _prompt,
    _received_quality,
    _strict_json_schema,
)


def test_v2_prompt_is_label_blind_and_forbids_fixed_rules() -> None:
    prompt = _prompt(({"ticker": "TEST", "evidence": []},))
    assert "v1 labels are intentionally absent" in prompt
    assert "fixed score" in prompt
    assert "Full confirmation is not required for BUY" in prompt
    assert "CANONICAL_EVIDENCE_PACKETS" in prompt
    assert '"v1_decision"' not in prompt


def test_strict_schema_closes_objects_and_requires_every_field() -> None:
    schema = _strict_json_schema(
        {"type": "object", "properties": {"value": {"type": "string", "default": "x"}}}
    )
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["value"]
    assert "default" not in schema["properties"]["value"]


def test_historical_diagnostic_fails_closed_without_forward_outcomes(tmp_path) -> None:
    source = tmp_path / "temporal.json"
    output = tmp_path / "diagnostic.json"
    source.write_text(
        json.dumps(
            {
                "contract": "temporal-v1",
                "subject_count": 20,
                "checkpoint_count": 200,
                "historical_replay_lookahead_leak": 0,
                "outcome_diagnostics": "SUPPRESSED_SOURCE_NOT_ARCHIVED",
            }
        )
    )
    _historical_diagnostic(argparse.Namespace(temporal=source, output=output))
    result = json.loads(output.read_text())
    assert result["status"] == "PARTIAL_SAFE"
    assert result["confirmation_delay_price_change"] == "NOT_AVAILABLE"
    assert result["presented_as_validated_alpha"] == 0


def test_test_sink_payload_quality_is_specific_and_compact() -> None:
    message = """🧪 SHADOW V2 · 비대칭/증거성숙도 검증
🧠 AI 종합 판단: HOLD
증거 성숙도: 부분 확인 | 가격 비대칭: 균형
🎯 판단
• 사업 근거와 기대 부담을 함께 봅니다.
🔄 판단 변경 조건
• 상향 조건과 하향 조건을 분리합니다."""
    assert _received_quality(message)["status"] == "PASS"
    assert _received_quality(message + "\n목표가를 제시합니다.")["status"] == "FAIL"
