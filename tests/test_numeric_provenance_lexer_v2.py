from __future__ import annotations

import pytest

from app.services.ai_review_service import (
    _numeric_correction_context,
    _prose_number_diagnostics,
    _prose_number_occurrences,
)


@pytest.mark.parametrize(
    "label",
    ("Russell 2000은", "S&P500은", "KOSPI 200은", "KOSDAQ 150은"),
)
def test_structural_index_label_before_korean_particle_is_not_numeric_claim(
    label: str,
) -> None:
    assert _prose_number_occurrences(f"{label} 하락했습니다.") == []


def test_run49_normalized_visible_sentence_has_no_phantom_2000() -> None:
    text = (
        "미국 10년물 실질금리와 명목금리가 상승했습니다. "
        "현재 세션에서 상승은 Nasdaq·반도체, 하락은 S&P500·Russell 2000이었습니다. "
        "동일가중 S&P500은 하락했습니다."
    )

    assert _prose_number_occurrences(text) == []


@pytest.mark.parametrize(
    ("text", "token"),
    (
        ("근거 없는 2000을 사용했습니다.", "2000"),
        ("근거 없는 $2000을 사용했습니다.", "2000"),
        ("근거 없는 2,000을 사용했습니다.", "2000"),
        ("근거 없는 2000%를 사용했습니다.", "2000"),
    ),
)
def test_real_unsupported_2000_remains_visible_to_provenance(
    text: str,
    token: str,
) -> None:
    assert [row[2] for row in _prose_number_occurrences(text)] == [token]


def test_unproven_number_diagnostic_records_exact_visible_span_and_rule() -> None:
    text = "근거 없는 2000을 사용했습니다."
    diagnostic = _prose_number_diagnostics(text, field_path="market_context.text")

    assert diagnostic == [
        {
            "raw_matched_text": "2000",
            "normalized_token": "2000",
            "parsed_numeric_value": 2000.0,
            "character_span": {"start": 6, "end": 10},
            "field_path": "market_context.text",
            "matching_rule": "visible_numeric_literal_v2",
        }
    ]


def test_correction_context_uses_validated_visible_text_for_diagnostics() -> None:
    candidate = {"market_review": {"market_context": {"text": "근거 없는 2000을 사용했습니다."}}}
    contexts = _numeric_correction_context(
        {"market_context": {"numeric_registry": []}},
        candidate,
        ["market_review:numbers_without_provenance:market_context.text:2000"],
    )

    assert contexts[0]["rendered_phrase"] == "근거 없는 2000을 사용했습니다."
    assert contexts[0]["numeric_diagnostics"][0]["character_span"] == {
        "start": 6,
        "end": 10,
    }
    assert contexts[0]["numeric_diagnostics"][0]["candidate_fact_binding_attempt"] == []
