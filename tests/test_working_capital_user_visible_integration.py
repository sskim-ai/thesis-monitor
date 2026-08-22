from __future__ import annotations

import copy

import pytest

from app.schemas.ai_review import AIStockReview
from app.services.ai_assisted_delivery_service import (
    _working_capital_delivery_metadata,
    _working_capital_run_metadata,
)
from app.services.ai_review_service import _working_capital_user_visible_errors
from app.services.numeric_semantic_registry import build_numeric_registry


RELATION_ID = "working-capital-relation:test-inventory"
FACT_IDS = [f"working-capital-fact:{index}" for index in range(6)]
CONTEXT_ID = "wc-visible-test-inventory"


def _context() -> dict[str, object]:
    return {
        "contract": "working-capital-user-visible-v1",
        "evidence_state": "NATURAL_PROOF_GATED_USER_VISIBLE",
        "working_capital_user_visible_context_id": CONTEXT_ID,
        "ticker": "TEST",
        "packet_id": "packet-test",
        "feature_mode": "SELECTIVE_INVENTORY",
        "metric_family": "inventory",
        "semantic_scope": "exact_total_inventory",
        "balance_date": "2026-05-28",
        "currentness": "CURRENT_FORMAL",
        "pit_state": "PASS",
        "relation_id": RELATION_ID,
        "relation_family": "inventory_vs_cogs",
        "direction": "LOWER",
        "display_value": "15.7%p",
        "selected_fact_ids": FACT_IDS,
        "resolved_unknowns": ["재고 추이는 확인되지 않았습니다."],
        "suppression_reasons": [],
        "user_visible_enabled": True,
    }


def _stock() -> dict[str, object]:
    return {
        "working_capital_user_visible": _context(),
        "fact_catalog": [
            {
                "fact_id": RELATION_ID,
                "fact_type": "working_capital_inventory_relation",
                "fields": {"gap_percentage_points_abs": 15.7339},
            },
            *(
                {
                    "fact_id": fact_id,
                    "fact_type": "working_capital_lineage_input",
                }
                for fact_id in FACT_IDS
            ),
        ],
    }


def _review() -> AIStockReview:
    return AIStockReview.model_validate(
        {
            "ticker": "TEST",
            "thesis_version": 1,
            "ai_thesis_assessment": "no_material_change",
            "earnings_estimate_view": "unchanged",
            "valuation_view": "neutral",
            "facts_used": [RELATION_ID, *FACT_IDS],
            "frameworks_used": [],
            "core_judgment": {"text": "사업 논리는 유지됩니다.", "fact_ids": []},
            "business_earnings": {
                "text": (
                    "재고 증가율은 매출원가 증가율보다 15.7%p 밑돌았습니다. "
                    "ASP와 제품 믹스를 함께 확인합니다."
                ),
                "fact_ids": [RELATION_ID, *FACT_IDS],
            },
            "price_positioning": {
                "text": "가격 구조는 별도입니다.",
                "new_observer_view": "지지 확인 전 관찰합니다.",
                "holder_view": "보유자는 무효화 기준을 봅니다.",
                "fact_ids": [],
            },
            "supply_analysis": {"text": "수급은 별도입니다.", "fact_ids": []},
            "valuation_analysis": {
                "text": "기존 valuation 기준을 유지합니다.",
                "fact_ids": [],
            },
            "numeric_claims": [
                {
                    "fact_id": RELATION_ID,
                    "field_path": "fields.gap_percentage_points_abs",
                    "value": 15.7339,
                    "unit": "pct_point",
                    "semantic_type": "inventory_growth_gap_pct_point",
                    "text_ref": "business_earnings.text",
                    "usage": "15.7%p",
                }
            ],
            "unknowns": ["ASP와 제품 믹스의 지속성은 미확인입니다."],
            "priority_watch": [],
            "next_checks": [],
            "confidence": 0.8,
        }
    )


def test_inventory_owner_scope_numeric_and_unknown_contract_passes() -> None:
    assert _working_capital_user_visible_errors(_review(), _stock()) == []


def test_inventory_rejects_trade_ar_mode_causal_overclaim_and_wrong_owner() -> None:
    stock = _stock()
    stock["working_capital_user_visible"] = {
        **_context(),
        "metric_family": "trade_accounts_receivable",
    }
    review = _review()
    review.business_earnings.text += " 수요 붕괴가 확정됐습니다."
    review.numeric_claims[0].text_ref = "valuation_analysis.text"

    errors = _working_capital_user_visible_errors(review, stock)

    assert "TEST:non_inventory_working_capital_leak" in errors
    assert "TEST:inventory_numeric_owner_invalid" in errors
    assert "TEST:working_capital_causal_or_ratio_overclaim" in errors


def test_suppressed_inventory_rejects_fact_use() -> None:
    stock = _stock()
    stock["working_capital_user_visible"] = {
        **_context(),
        "user_visible_enabled": False,
    }

    assert "TEST:suppressed_working_capital_fact_used" in (
        _working_capital_user_visible_errors(_review(), stock)
    )


def test_ai_fallback_share_exact_inventory_context_and_receipt_metadata() -> None:
    packet = {"stocks": [{"ticker": "TEST", "working_capital_user_visible": _context()}]}
    deterministic = {
        "analysis_context": {"working_capital_user_visible": _context()}
    }

    metadata = _working_capital_delivery_metadata(packet, "TEST", deterministic)
    run_metadata = _working_capital_run_metadata(packet)

    assert metadata["working_capital_user_visible_context_id"] == CONTEXT_ID
    assert metadata["working_capital_metric_family"] == "inventory"
    assert metadata["working_capital_fact_ids"] == FACT_IDS
    assert run_metadata["working_capital_selected_count"] == 1
    assert run_metadata["working_capital_metric_families"] == ["inventory"]


def test_ai_fallback_inventory_context_mismatch_is_hard_failure() -> None:
    packet = {"stocks": [{"ticker": "TEST", "working_capital_user_visible": _context()}]}
    fallback = copy.deepcopy(_context())
    fallback["balance_date"] = "2026-02-27"

    with pytest.raises(
        ValueError,
        match="working_capital_ai_fallback_context_mismatch",
    ):
        _working_capital_delivery_metadata(
            packet,
            "TEST",
            {"analysis_context": {"working_capital_user_visible": fallback}},
        )


def test_inventory_growth_gap_has_typed_numeric_registry_entry() -> None:
    registry = build_numeric_registry(_stock()["fact_catalog"])
    relation = next(item for item in registry if item["fact_id"] == RELATION_ID)

    assert relation["semantic_type"] == "inventory_growth_gap_pct_point"
    assert relation["unit"] == "pct_point"
    assert relation["canonical_display_value"] == "15.7%p"
