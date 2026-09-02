from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.numeric_provenance_service import (
    TYPED_VALUATION_CONTRACT,
    _directional_valuation_occurrences,
    _typed_valuation_reference_errors,
)


def _review(text: str, fact_id: str = "valuation:current") -> dict[str, object]:
    return {
        "facts_used": [fact_id],
        "core_judgment": {"text": "판단을 유지합니다.", "fact_ids": []},
        "business_earnings": {"text": "실적을 확인합니다.", "fact_ids": []},
        "price_positioning": {
            "text": "가격 구조를 확인합니다.",
            "new_observer_view": "신규 관찰 조건입니다.",
            "holder_view": "보유 조건입니다.",
            "fact_ids": [],
        },
        "supply_analysis": {"text": "거래량을 확인합니다.", "fact_ids": []},
        "valuation_analysis": {"text": text, "fact_ids": [fact_id]},
        "priority_watch": [],
        "next_checks": [],
        "unknowns": [],
    }


def _stock(fact_id: str, **fact: object) -> dict[str, object]:
    return {
        "typed_valuation_interpretation_contract": TYPED_VALUATION_CONTRACT,
        "fact_catalog": [
            {
                "fact_id": fact_id,
                "fact_type": "valuation",
                "interpretation_eligible": True,
                **fact,
            }
        ],
    }


def _binding(ref_id: str, semantic_type: str, usage: str) -> dict[str, object]:
    return {
        "ref_id": ref_id,
        "semantic_type": semantic_type,
        "text_ref": "valuation_analysis.text",
        "usage": usage,
    }


def _typed(
    *,
    interpretation_type: str,
    metric: str,
    fact_id: str,
    numeric_refs: list[str],
    exact_span: str,
) -> dict[str, object]:
    return {
        "ref_id": "interpretation_one",
        "interpretation_type": interpretation_type,
        "metric": metric,
        "fact_id": fact_id,
        "text_ref": "valuation_analysis.text",
        "exact_text_span": exact_span,
        "comparison_numeric_ref_ids": numeric_refs,
        "basis_status": "verified",
        "source_type": "canonical",
        "direction": "neutral",
    }


def test_neutral_absolute_multiple_with_typed_reference_passes() -> None:
    review = _review("현재 PBR 0.67배를 중립적으로 확인합니다.")
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="absolute",
            metric="pbr",
            fact_id="valuation:current",
            numeric_refs=["pbr_now"],
            exact_span="현재 PBR 0.67배를 중립적으로 확인합니다.",
        )
    ]

    errors, accepted = _typed_valuation_reference_errors(
        review,
        _stock("valuation:current"),
        [_binding("pbr_now", "price_to_book", "PBR 0.67배")],
        prefix="TEST",
    )

    assert errors == []
    assert len(accepted) == 1


@pytest.mark.parametrize(
    "text",
    [
        "PBR 0.67배 수준의 낮은 자산 배수입니다.",
        "역사 비교상 한쪽으로 치우친 신호는 아닙니다.",
        "PER와 PBR 모두 기대 부담이 큽니다.",
        "peer 대비 프리미엄입니다.",
        "시장 기대가 높습니다.",
    ],
)
def test_directional_valuation_without_typed_evidence_is_rejected(text: str) -> None:
    review = _review(text)

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        _stock("valuation:current"),
        [],
        prefix="TEST",
    )

    assert any("occurrence_uncovered" in error for error in errors)


def test_historical_interpretation_requires_visible_same_metric_percentile() -> None:
    fact_id = "valuation:historical_pe"
    review = _review("PER 역사적 백분위 80%로 과거보다 높습니다.", fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="historical",
            metric="pe",
            fact_id=fact_id,
            numeric_refs=["pe_percentile"],
            exact_span="PER 역사적 백분위 80%로 과거보다 높습니다.",
        )
    ]

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        _stock(fact_id, fact_type="valuation_interpretation"),
        [
            _binding(
                "pe_percentile",
                "historical_pb_percentile",
                "PER 역사적 백분위 80%",
            )
        ],
        prefix="TEST",
    )

    assert any("metric_evidence_mismatch" in error for error in errors)


def test_peer_interpretation_requires_metric_and_sample_count() -> None:
    fact_id = "valuation:peer"
    review = _review("비교군 PBR보다 높습니다.", fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="peer",
            metric="pbr",
            fact_id=fact_id,
            numeric_refs=["peer_pbr"],
            exact_span="비교군 PBR보다 높습니다.",
        )
    ]

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        _stock(fact_id, fact_type="peer_valuation"),
        [_binding("peer_pbr", "peer_pb_multiple", "비교군 PBR")],
        prefix="TEST",
    )

    assert any("evidence_invalid" in error for error in errors)


def test_trailing_forward_relation_requires_comparable_backend_fact() -> None:
    fact_id = "valuation:multiple_relation"
    review = _review("현재 PER보다 시장 예상 fPER가 높습니다.", fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="trailing_forward_relation",
            metric="earnings",
            fact_id=fact_id,
            numeric_refs=["trailing", "forward"],
            exact_span="현재 PER보다 시장 예상 fPER가 높습니다.",
        )
    ]
    stock = _stock(
        fact_id,
        fact_type="valuation_multiple_relation",
        fields={"basis_comparable": False, "forward_period_status": "exact"},
    )

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        stock,
        [
            _binding("trailing", "trailing_pe", "현재 PER"),
            _binding("forward", "forward_pe", "시장 예상 fPER"),
        ],
        prefix="TEST",
    )

    assert any("evidence_invalid" in error for error in errors)


def test_trailing_forward_relation_passes_only_with_comparable_backend_fact() -> None:
    fact_id = "valuation:multiple_relation"
    review = _review("현재 PER보다 시장 예상 fPER가 낮습니다.", fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="trailing_forward_relation",
            metric="earnings",
            fact_id=fact_id,
            numeric_refs=["trailing", "forward"],
            exact_span="현재 PER보다 시장 예상 fPER가 낮습니다.",
        )
    ]
    stock = _stock(
        fact_id,
        fact_type="valuation_multiple_relation",
        fields={"basis_comparable": True, "forward_period_status": "exact"},
    )

    errors, accepted = _typed_valuation_reference_errors(
        review,
        stock,
        [
            _binding("trailing", "trailing_pe", "현재 PER"),
            _binding("forward", "forward_pe", "시장 예상 fPER"),
        ],
        prefix="TEST",
    )

    assert errors == []
    assert accepted[0]["interpretation_type"] == "trailing_forward_relation"


def test_aggregate_fact_cannot_ground_negative_book_claim() -> None:
    review = _review("주당순자산이 음수여서 PBR 해석을 보류합니다.")
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="quality_unknown",
            metric="book",
            fact_id="valuation:current",
            numeric_refs=[],
            exact_span="주당순자산이 음수여서 PBR 해석을 보류합니다.",
        )
    ]

    errors, _accepted = _typed_valuation_reference_errors(
        deepcopy(review),
        _stock("valuation:current"),
        [],
        prefix="TEST",
    )

    assert any("evidence_invalid" in error for error in errors)


def test_earnings_based_valuation_unknown_phrase_matches_typed_metric() -> None:
    fact_id = "financial_quality:2026-06-30"
    text = "재무 품질을 확인하지 못해 현재 실적 기반 가치평가는 보류합니다."
    review = _review(text, fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="quality_unknown",
            metric="earnings",
            fact_id=fact_id,
            numeric_refs=[],
            exact_span=text,
        )
    ]

    errors, accepted = _typed_valuation_reference_errors(
        review,
        _stock(fact_id, fact_type="financial_quality"),
        [],
        prefix="CORZ",
    )

    assert errors == []
    assert accepted[0]["metric"] == "earnings"


def test_financial_quality_gate_failure_is_valid_unknown_evidence() -> None:
    fact_id = "financial_quality:2026-06-30"
    text = (
        "최신 재무 이익 계열이 품질 기준을 통과하지 못해 "
        "이익 배수는 제시하지 않습니다."
    )
    review = _review(text, fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="quality_unknown",
            metric="earnings",
            fact_id=fact_id,
            numeric_refs=[],
            exact_span=text,
        )
    ]

    errors, accepted = _typed_valuation_reference_errors(
        review,
        _stock(fact_id, fact_type="financial_quality"),
        [],
        prefix="TEST",
    )

    assert errors == []
    assert accepted[0]["interpretation_type"] == "quality_unknown"


def test_valid_historical_pbr_span_cannot_cover_denied_per_occurrence() -> None:
    fact_id = "valuation:historical_pb"
    text = (
        "PBR 역사적 백분위 87%는 높은 위치입니다. "
        "피크 이익의 낮은 배수를 저평가 근거로 보지 않습니다."
    )
    review = _review(text, fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="historical",
            metric="pbr",
            fact_id=fact_id,
            numeric_refs=["pb_percentile"],
            exact_span="PBR 역사적 백분위 87%는 높은 위치입니다.",
        )
    ]

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        _stock(fact_id, fact_type="valuation_interpretation"),
        [
            _binding(
                "pb_percentile",
                "historical_pb_percentile",
                "PBR 역사적 백분위 87%",
            )
        ],
        prefix="TEST",
    )

    assert any("occurrence_uncovered" in error for error in errors)


def test_same_sentence_requires_each_valuation_occurrence_to_be_typed() -> None:
    fact_id = "valuation:historical_pb"
    text = "PBR 역사적 백분위 87%는 높지만 이익 배수는 낮습니다."
    review = _review(text, fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="historical",
            metric="pbr",
            fact_id=fact_id,
            numeric_refs=["pb_percentile"],
            exact_span="PBR 역사적 백분위 87%는 높지만",
        )
    ]

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        _stock(fact_id, fact_type="valuation_interpretation"),
        [
            _binding(
                "pb_percentile",
                "historical_pb_percentile",
                "PBR 역사적 백분위 87%",
            )
        ],
        prefix="TEST",
    )

    assert any("occurrence_uncovered" in error for error in errors)


def test_wrong_metric_reference_is_rejected_at_exact_span() -> None:
    fact_id = "valuation:historical_pb"
    text = "PER 역사적 백분위 80%로 과거보다 높습니다."
    review = _review(text, fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="historical",
            metric="pbr",
            fact_id=fact_id,
            numeric_refs=["pe_percentile"],
            exact_span=text,
        )
    ]

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        _stock(fact_id, fact_type="valuation_interpretation"),
        [
            _binding(
                "pe_percentile",
                "historical_pe_percentile",
                "PER 역사적 백분위 80%",
            )
        ],
        prefix="TEST",
    )

    assert any("metric_evidence_mismatch" in error for error in errors)


def test_wrong_span_hash_and_duplicate_span_are_rejected() -> None:
    fact_id = "valuation:historical_pb"
    phrase = "PBR 역사적 백분위 87%로 높습니다."
    review = _review(f"{phrase} {phrase}", fact_id)
    reference = _typed(
        interpretation_type="historical",
        metric="pbr",
        fact_id=fact_id,
        numeric_refs=["pb_percentile"],
        exact_span=phrase,
    )
    reference["normalized_span_sha256"] = "0" * 64
    review["valuation_interpretation_refs"] = [reference]

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        _stock(fact_id, fact_type="valuation_interpretation"),
        [
            _binding(
                "pb_percentile",
                "historical_pb_percentile",
                "PBR 역사적 백분위 87%",
            )
        ],
        prefix="TEST",
    )

    assert any("span_not_unique" in error for error in errors)


def test_relation_caution_must_match_forward_period_status() -> None:
    fact_id = "valuation:multiple_relation"
    review = _review(
        "현재 PER보다 시장 예상 fPER가 낮습니다. fPER 산출 기간은 불명확합니다.",
        fact_id,
    )
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="trailing_forward_relation",
            metric="earnings",
            fact_id=fact_id,
            numeric_refs=["trailing", "forward"],
            exact_span="현재 PER보다 시장 예상 fPER가 낮습니다.",
        )
    ]
    stock = _stock(
        fact_id,
        fact_type="valuation_multiple_relation",
        fields={"basis_comparable": True, "forward_period_status": "exact"},
    )

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        stock,
        [
            _binding("trailing", "trailing_pe", "현재 PER"),
            _binding("forward", "forward_pe", "시장 예상 fPER"),
        ],
        prefix="TEST",
    )

    assert any("relation_caution_contradiction" in error for error in errors)


def test_decimal_points_do_not_split_directional_valuation_occurrence() -> None:
    text = (
        "현재 PER 12.4배와 시장 예상 fPER 19.29배의 관계는 같은 기준에서 "
        "선행 이익 분모가 현재 이익 분모보다 낮은 방향임을 보여줍니다."
    )

    assert len(_directional_valuation_occurrences(text)) == 1
