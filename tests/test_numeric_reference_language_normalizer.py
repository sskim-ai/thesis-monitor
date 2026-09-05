from __future__ import annotations

from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.numeric_reference_language_normalizer_service import (
    normalize_numeric_reference_language,
)


def _packet() -> dict[str, object]:
    source = {
        "fact_id": "price:current",
        "field_path": "fields.current_price",
        "value": 17.89,
        "unit": "USD",
        "semantic_type": "share_price",
        "canonical_label": "현재가",
        "approved_labels": ["현재가"],
        "canonical_display_value": "$17.89",
        "registered": True,
        "prose_allowed": True,
        "scope": "stock",
    }
    return {
        "stocks": [
            {
                "ticker": "GENERIC",
                "numeric_registry": [source],
                "fact_catalog": [
                    {
                        "fact_id": "price:current",
                        "fact_type": "price",
                        "fields": {"current_price": 17.89, "currency": "USD"},
                    }
                ],
            }
        ]
    }


def _output(text: str) -> dict[str, object]:
    return {
        "stock_reviews": [
            {
                "ticker": "GENERIC",
                "facts_used": ["price:current"],
                "core_judgment": {"text": text},
                "numeric_fact_refs": [
                    {
                        "ref_id": "price",
                        "fact_id": "price:current",
                        "field_path": "fields.current_price",
                        "text_ref": "core_judgment.text",
                    }
                ],
            }
        ]
    }


def test_one_pass_removes_redundant_label_and_preserves_safe_copula() -> None:
    packet = _packet()
    normalized, report = normalize_numeric_reference_language(
        packet,
        _output("현재가는 {{numeric:price}}이며 확인선을 유지합니다."),
    )
    bound = bind_numeric_fact_references(packet, normalized)

    assert report["attempt_count"] == 1
    assert report["rewrite_count"] == 1
    assert report["invariant_errors"] == []
    assert bound.errors == ()
    assert (
        bound.output["stock_reviews"][0]["core_judgment"]["text"]
        == "현재가 $17.89이며 확인선을 유지합니다."
    )


def test_one_pass_moves_raw_particle_to_structured_reference() -> None:
    packet = _packet()
    normalized, report = normalize_numeric_reference_language(
        packet,
        _output("{{numeric:price}}는 확인된 종가입니다."),
    )
    bound = bind_numeric_fact_references(packet, normalized)

    assert report["rewrite_count"] == 1
    assert bound.errors == ()
    assert "현재가 $17.89는" in bound.output["stock_reviews"][0]["core_judgment"]["text"]


def test_one_pass_restores_exact_structured_interpretation_span() -> None:
    packet = _packet()
    output = _output("현재가 {{numeric:price}}. 이 값은 이는 비교 구간입니다.")
    review = output["stock_reviews"][0]
    review["valuation_analysis"] = review.pop("core_judgment")
    review["numeric_fact_refs"][0]["text_ref"] = "valuation_analysis.text"
    review["valuation_interpretation_refs"] = [
        {
            "ref_id": "valuation_price",
            "interpretation_type": "absolute",
            "metric": "pbr",
            "fact_id": "price:current",
            "text_ref": "valuation_analysis.text",
            "exact_text_span": (
                "현재가 {{numeric:price}}이며, 이는 비교 구간입니다."
            ),
            "comparison_numeric_ref_ids": ["price"],
        }
    ]

    normalized, report = normalize_numeric_reference_language(packet, output)

    assert report["rewrite_count"] == 2
    assert report["invariant_errors"] == []
    assert (
        normalized["stock_reviews"][0]["valuation_analysis"]["text"]
        == "{{numeric:price}}이며, 이는 비교 구간입니다."
    )
    assert (
        normalized["stock_reviews"][0]["valuation_interpretation_refs"][0][
            "exact_text_span"
        ]
        == "현재가 {{numeric:price}}이며, 이는 비교 구간입니다."
    )


def test_structured_span_repair_is_fail_closed_when_ambiguous() -> None:
    packet = _packet()
    malformed = "현재가 {{numeric:price}}. 이 값은 이는 비교 구간입니다."
    output = _output(f"{malformed} {malformed}")
    review = output["stock_reviews"][0]
    review["valuation_interpretation_refs"] = [
        {
            "ref_id": "valuation_price",
            "text_ref": "core_judgment.text",
            "exact_text_span": "현재가 {{numeric:price}}이며, 이는 비교 구간입니다.",
        }
    ]

    normalized, report = normalize_numeric_reference_language(packet, output)

    assert report["rewrite_count"] == 0
    assert normalized == output
