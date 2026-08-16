from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.numeric_provenance_service import (
    TYPED_VALUATION_CONTRACT,
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


def _binding(ref_id: str, semantic_type: str) -> dict[str, object]:
    return {
        "ref_id": ref_id,
        "semantic_type": semantic_type,
        "text_ref": "valuation_analysis.text",
    }


def _typed(
    *,
    interpretation_type: str,
    metric: str,
    fact_id: str,
    numeric_refs: list[str],
) -> dict[str, object]:
    return {
        "ref_id": "interpretation_one",
        "interpretation_type": interpretation_type,
        "metric": metric,
        "fact_id": fact_id,
        "text_ref": "valuation_analysis.text",
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
        )
    ]

    errors, accepted = _typed_valuation_reference_errors(
        review,
        _stock("valuation:current"),
        [_binding("pbr_now", "price_to_book")],
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

    assert any("typed_reference_missing" in error for error in errors)


def test_historical_interpretation_requires_visible_same_metric_percentile() -> None:
    fact_id = "valuation:historical_pe"
    review = _review("PER 역사적 백분위 80%로 과거보다 높습니다.", fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="historical",
            metric="pe",
            fact_id=fact_id,
            numeric_refs=["pe_percentile"],
        )
    ]

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        _stock(fact_id, fact_type="valuation_interpretation"),
        [_binding("pe_percentile", "historical_pb_percentile")],
        prefix="TEST",
    )

    assert any("metric_evidence_mismatch" in error for error in errors)


def test_peer_interpretation_requires_metric_and_sample_count() -> None:
    fact_id = "valuation:peer"
    review = _review("비교군 PBR보다 높은 프리미엄입니다.", fact_id)
    review["valuation_interpretation_refs"] = [
        _typed(
            interpretation_type="peer",
            metric="pbr",
            fact_id=fact_id,
            numeric_refs=["peer_pbr"],
        )
    ]

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        _stock(fact_id, fact_type="peer_valuation"),
        [_binding("peer_pbr", "peer_pb_multiple")],
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
        )
    ]
    stock = _stock(
        fact_id,
        fact_type="valuation_multiple_relation",
        fields={"basis_comparable": False},
    )

    errors, _accepted = _typed_valuation_reference_errors(
        review,
        stock,
        [
            _binding("trailing", "trailing_pe"),
            _binding("forward", "forward_pe"),
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
        )
    ]
    stock = _stock(
        fact_id,
        fact_type="valuation_multiple_relation",
        fields={"basis_comparable": True},
    )

    errors, accepted = _typed_valuation_reference_errors(
        review,
        stock,
        [
            _binding("trailing", "trailing_pe"),
            _binding("forward", "forward_pe"),
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
        )
    ]

    errors, _accepted = _typed_valuation_reference_errors(
        deepcopy(review),
        _stock("valuation:current"),
        [],
        prefix="TEST",
    )

    assert any("evidence_invalid" in error for error in errors)
