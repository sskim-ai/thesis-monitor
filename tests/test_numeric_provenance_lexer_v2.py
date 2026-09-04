from __future__ import annotations

import pytest

from app.services.ai_review_service import (
    _canonical_identifier_spans,
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


def test_valuation_correction_context_offers_grounded_quality_unknown() -> None:
    candidate = {
        "stock_reviews": [
            {
                "ticker": "ADR",
                "valuation_analysis": {
                    "text": "현재 상장 증권의 검증 가능한 배수 근거가 부족합니다.",
                    "fact_ids": [],
                },
            }
        ]
    }
    packet = {
        "stocks": [
            {
                "ticker": "ADR",
                "numeric_registry": [],
                "fact_catalog": [
                    {
                        "fact_id": "security_basis:current",
                        "fact_type": "security_basis",
                        "valuation_scope": "listed_security",
                        "interpretation_eligible": True,
                    }
                ],
            }
        ]
    }

    contexts = _numeric_correction_context(
        packet,
        candidate,
        [
            "ADR:valuation_interpretation_occurrence_uncovered:"
            "valuation_analysis.text:7"
        ],
    )

    assert contexts[0]["text_ref"] == "valuation_analysis.text"
    assert contexts[0]["quality_candidates"] == [
        {
            "fact_id": "security_basis:current",
            "fact_type": "security_basis",
            "valuation_scope": "listed_security",
            "interpretation_eligible": True,
        }
    ]
    assert "add_typed_quality_unknown_reference" in contexts[0]["allowed_actions"]


@pytest.fixture
def canonical_identifier_context() -> dict[str, object]:
    return {
        "thesis": {
            "core_thesis": (
                "KF-21, FA-50, F-35, B-21, A320neo는 검증된 제품·모델 식별자입니다."
            )
        }
    }


def test_canonical_product_identifier_digits_are_not_numeric_claims(
    canonical_identifier_context: dict[str, object],
) -> None:
    text = "KF-21·FA-50과 F-35, B-21, A320neo를 확인합니다."

    assert _prose_number_occurrences(text, canonical_identifier_context) == []
    diagnostics = _canonical_identifier_spans(text, canonical_identifier_context)
    assert {str(item["full_span"]) for item in diagnostics} == {
        "KF-21",
        "FA-50",
        "F-35",
        "B-21",
        "A320neo",
    }
    assert all(item["canonical_source"] == "canonical_thesis" for item in diagnostics)
    assert all(item["fact_ref_id"] == "thesis:canonical" for item in diagnostics)


def test_product_identifier_mask_preserves_adjacent_real_numbers(
    canonical_identifier_context: dict[str, object],
) -> None:
    text = "KF-21 21대, FA-50 50대, KF-21 수출 5조원, FA-50 마진 12%"

    assert [
        token
        for _, _, token in _prose_number_occurrences(
            text,
            canonical_identifier_context,
        )
    ] == ["21", "50", "5", "12"]


def test_unproven_identifier_and_plain_hyphen_numbers_remain_numeric() -> None:
    text = "ZZ-999, -21%, 21-50, $-50"

    tokens = [token for _, _, token in _prose_number_occurrences(text, {})]

    assert "999" in tokens
    assert "-21" in tokens
    assert "21" in tokens
    assert "50" in tokens
    assert "-50" in tokens


def test_product_identifier_evidence_does_not_change_date_handling(
    canonical_identifier_context: dict[str, object],
) -> None:
    assert _prose_number_occurrences(
        "2026-09-01과 2023-06-05",
        canonical_identifier_context,
    ) == []


def test_run50_047810_fields_have_zero_product_identifier_phantom_numbers() -> None:
    context = {
        "thesis": {
            "core_thesis": (
                "KF-21 양산·인도·수출과 FA-50 해외 수주가 매출·이익·현금흐름으로 "
                "전환되는지가 핵심입니다."
            )
        }
    }
    fields = (
        "KF-21과 FA-50의 인도 확대가 수주잔고의 매출 전환으로 이어지는지 봅니다.",
        "이익 규모를 KF-21·FA-50 인도 확대와 연결하려면 현금 회수가 필요합니다.",
        "동적 지지 유지와 함께 KF-21·FA-50 인도를 확인합니다.",
        "수급 부담과 KF-21·FA-50 인도 여부는 별도 근거로 판단합니다.",
        "배수보다 KF-21·FA-50 인도가 마진과 현금으로 전환되는지 봅니다.",
        "KF-21·FA-50의 인도 일정과 신규 수주를 감시합니다.",
        "KF-21·FA-50 양산·인도 물량의 현금전환은 아직 확인되지 않았습니다.",
    )

    assert all(_prose_number_occurrences(text, context) == [] for text in fields)
