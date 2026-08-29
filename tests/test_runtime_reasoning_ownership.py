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


def test_candidate_owner_normalizer_hands_off_selected_inventory_relation() -> None:
    relation_id = "working-capital-relation:inventory"
    packet = {
        "stocks": [
            {
                "ticker": "GENERIC",
                "fact_catalog": [
                    {
                        "fact_id": relation_id,
                        "fact_type": "working_capital_inventory_relation",
                        "interpretation_eligible": True,
                    }
                ],
                "working_capital_user_visible": {
                    "user_visible_enabled": True,
                    "relation_id": relation_id,
                    "relation_family": "inventory_vs_revenue",
                    "direction": "LOWER",
                },
            }
        ]
    }
    candidate = {
        "stock_reviews": [
            {
                "ticker": "GENERIC",
                "facts_used": [],
                "business_earnings": {
                    "text": "사업 실적을 확인합니다.",
                    "fact_ids": [],
                },
            }
        ]
    }

    output, report = apply_candidate_ownership_contracts(packet, candidate)
    review = output["stock_reviews"][0]

    assert review["facts_used"] == [relation_id]
    assert review["business_earnings"]["fact_ids"] == [relation_id]
    assert review["business_earnings"]["text"].startswith(
        "재고 증가율은 매출 증가율을 {{numeric:owned_inventory_relation}} "
        "밑돌았습니다."
    )
    assert review["numeric_fact_refs"] == [
        {
            "ref_id": "owned_inventory_relation",
            "fact_id": relation_id,
            "field_path": "fields.gap_percentage_points_signed",
            "text_ref": "business_earnings.text",
        }
    ]
    assert report["status"] == "passed"


def test_candidate_owner_normalizer_leaves_ambiguous_inventory_for_rejection() -> None:
    relation_id = "working-capital-relation:inventory"
    packet = {
        "stocks": [
            {
                "ticker": "GENERIC",
                "fact_catalog": [
                    {
                        "fact_id": relation_id,
                        "fact_type": "working_capital_inventory_relation",
                        "interpretation_eligible": True,
                    }
                ],
                "working_capital_user_visible": {
                    "user_visible_enabled": True,
                    "relation_id": relation_id,
                    "relation_family": "inventory_vs_revenue",
                    "direction": "LOWER",
                },
            }
        ]
    }
    candidate = {
        "stock_reviews": [
            {
                "ticker": "GENERIC",
                "facts_used": [],
                "business_earnings": {
                    "text": "재고가 부담입니다.",
                    "fact_ids": [],
                },
            }
        ]
    }

    output, report = apply_candidate_ownership_contracts(packet, candidate)

    assert "numeric_fact_refs" not in output["stock_reviews"][0]
    assert report["status"] == "unresolved"
    assert report["unresolved"][0]["reason"] == (
        "inventory_prose_present_without_unambiguous_numeric_owner"
    )


def test_candidate_owner_normalizer_adds_narrow_valuation_owners() -> None:
    packet = {
        "stocks": [
            {
                "ticker": "GENERIC",
                "fact_catalog": [
                    {
                        "fact_id": "valuation:current",
                        "interpretation_eligible": False,
                    },
                    {
                        "fact_id": "valuation:current_pbr",
                        "interpretation_eligible": True,
                    },
                    {
                        "fact_id": "valuation:consensus_forward_earnings",
                        "interpretation_eligible": True,
                    },
                ],
            }
        ]
    }
    candidate = {
        "stock_reviews": [
            {
                "ticker": "GENERIC",
                "facts_used": ["valuation:current"],
                "valuation_analysis": {
                    "text": "{{numeric:pbr}}. {{numeric:fpe}}.",
                    "fact_ids": ["valuation:current"],
                },
                "numeric_fact_refs": [
                    {
                        "ref_id": "pbr",
                        "fact_id": "valuation:current",
                        "field_path": "fields.price_to_book",
                        "text_ref": "valuation_analysis.text",
                    },
                    {
                        "ref_id": "fpe",
                        "fact_id": "valuation:current",
                        "field_path": "fields.forward_pe",
                        "text_ref": "valuation_analysis.text",
                    },
                ],
            }
        ]
    }

    output, report = apply_candidate_ownership_contracts(packet, candidate)
    review = output["stock_reviews"][0]

    assert review["valuation_analysis"]["fact_ids"] == [
        "valuation:current_pbr",
        "valuation:consensus_forward_earnings",
    ]
    assert [item["fact_id"] for item in review["valuation_interpretation_refs"]] == [
        "valuation:current_pbr",
        "valuation:consensus_forward_earnings",
    ]
    assert report["status"] == "passed"


def test_candidate_owner_normalizer_consumes_canonical_market_plan() -> None:
    packet = {
        "market_context": {
            "us_market_digest_plan": {
                "contract": "us-market-digest-plan-v1",
                "items": [
                    {
                        "slot": "CURRENT_MARKET",
                        "required_consumption": True,
                        "claim_text": "현재 세션에서 S&P500이 하락했습니다.",
                        "evidence_refs": ["market:index:SPY"],
                    }
                ],
            }
        },
        "stocks": [],
    }
    candidate = {
        "market_review": {
            "facts_used": [],
            "frameworks_used": [
                "macro_transmission",
                "hyperscaler_capex_transmission",
                "arbitrary_unknown_framework",
            ],
            "market_context": {"text": "시장 맥락입니다.", "fact_ids": []},
        },
        "stock_reviews": [],
    }

    output, report = apply_candidate_ownership_contracts(packet, candidate)
    market = output["market_review"]

    assert market["facts_used"] == ["market:index:SPY"]
    assert market["market_context"]["fact_ids"] == ["market:index:SPY"]
    assert market["market_context"]["text"].endswith(
        "현재 세션에서 S&P500이 하락했습니다."
    )
    assert market["frameworks_used"] == [
        "macro_transmission",
        "arbitrary_unknown_framework",
    ]
    assert report["status"] == "passed"


def test_candidate_owner_normalizer_only_removes_known_stale_rr_declaration() -> None:
    packet = {
        "stocks": [
            {
                "ticker": "GENERIC",
                "fact_catalog": [],
            }
        ]
    }
    candidate = {
        "stock_reviews": [
            {
                "ticker": "GENERIC",
                "facts_used": [
                    "monitoring:risk_reward_transition",
                    "arbitrary:unknown",
                ],
                "price_positioning": {
                    "text": "현재 손익비를 확인합니다.",
                    "fact_ids": [
                        "monitoring:risk_reward_transition",
                        "arbitrary:unknown",
                    ],
                },
            }
        ]
    }

    output, report = apply_candidate_ownership_contracts(packet, candidate)
    review = output["stock_reviews"][0]

    assert review["facts_used"] == ["arbitrary:unknown"]
    assert review["price_positioning"]["fact_ids"] == ["arbitrary:unknown"]
    assert report["suppressions"][0]["reason"] == (
        "unavailable_rr_transition_declaration_without_claim"
    )
