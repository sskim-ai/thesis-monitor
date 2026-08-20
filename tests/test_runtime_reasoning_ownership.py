from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.runtime_reasoning_ownership_service import (
    apply_candidate_ownership_contracts,
)


def _packet() -> dict[str, object]:
    facts = [
        {
            "fact_id": "chart:structure:risk_reward:current_price",
            "fact_type": "chart_risk_reward_current_price",
            "fields": {"ratio": 2.08, "currency": "KRW"},
        }
    ]
    return {
        "stocks": [
            {
                "ticker": "GENERIC",
                "numeric_registry": build_numeric_registry(facts),
            }
        ]
    }


def _candidate(core_text: str) -> dict[str, object]:
    fact_id = "chart:structure:risk_reward:current_price"
    return {
        "stock_reviews": [
            {
                "ticker": "GENERIC",
                "core_judgment": {"text": core_text, "fact_ids": [fact_id]},
                "price_positioning": {
                    "text": "{{numeric:price_rr}}입니다.",
                    "fact_ids": [fact_id],
                },
                "numeric_fact_refs": [
                    {
                        "ref_id": "core_rr",
                        "fact_id": fact_id,
                        "field_path": "fields.ratio",
                        "text_ref": "core_judgment.text",
                    },
                    {
                        "ref_id": "price_rr",
                        "fact_id": fact_id,
                        "field_path": "fields.ratio",
                        "text_ref": "price_positioning.text",
                    },
                ],
            }
        ]
    }


def test_candidate_owner_normalizer_suppresses_standalone_secondary_rr() -> None:
    output, report = apply_candidate_ownership_contracts(
        _packet(), _candidate("{{numeric:core_rr}}입니다. 고유 판단입니다.")
    )
    review = output["stock_reviews"][0]

    assert review["core_judgment"]["text"] == "고유 판단입니다."
    assert [item["ref_id"] for item in review["numeric_fact_refs"]] == ["price_rr"]
    assert report["status"] == "passed"
    assert report["suppressions"][0]["reason"] == (
        "current_rr_secondary_exact_occurrence"
    )


def test_candidate_owner_normalizer_leaves_embedded_secondary_for_rejection() -> None:
    output, report = apply_candidate_ownership_contracts(
        _packet(), _candidate("{{numeric:core_rr}}가 개선돼 고유 판단을 바꿉니다.")
    )
    review = output["stock_reviews"][0]

    assert len(review["numeric_fact_refs"]) == 2
    assert report["status"] == "unresolved"
    assert report["unresolved"][0]["reason"] == (
        "current_rr_secondary_not_safely_removable"
    )


def test_candidate_owner_normalizer_removes_rr_from_numeric_list_tail() -> None:
    output, report = apply_candidate_ownership_contracts(
        _packet(),
        _candidate(
            "고유 판단 숫자는 {{numeric:first}}; {{numeric:second}}; "
            "{{numeric:core_rr}}입니다."
        ),
    )
    review = output["stock_reviews"][0]

    assert review["core_judgment"]["text"] == (
        "고유 판단 숫자는 {{numeric:first}}; {{numeric:second}}입니다."
    )
    assert [item["ref_id"] for item in review["numeric_fact_refs"]] == ["price_rr"]
    assert report["status"] == "passed"


def test_candidate_owner_normalizer_requires_one_primary_price_occurrence() -> None:
    candidate = _candidate("{{numeric:core_rr}}입니다.")
    review = candidate["stock_reviews"][0]
    review["numeric_fact_refs"] = review["numeric_fact_refs"][:1]

    output, report = apply_candidate_ownership_contracts(_packet(), candidate)

    assert len(output["stock_reviews"][0]["numeric_fact_refs"]) == 1
    assert report["status"] == "unresolved"
    assert report["unresolved"][0]["reason"] == (
        "current_rr_primary_owner_missing_or_ambiguous"
    )
