from __future__ import annotations

import copy

import pytest

from app.schemas.ai_review import AIStockReview
from app.services.ai_assisted_delivery_service import (
    _cash_flow_delivery_metadata,
    _cash_flow_run_metadata,
)
from app.services.ai_review_service import _cash_flow_user_visible_errors


FCF_ID = "cashflow:fcf"
OCF_ID = "cashflow:ocf"
CAPEX_ID = "cashflow:capex"
CONTEXT_ID = "cf-visible-fixture"


def _context() -> dict[str, object]:
    return {
        "contract": "cash-flow-user-visible-v1",
        "rollout_mode": "SELECTIVE_CURRENT_FORMAL_FULL_FCF",
        "selection_state": "SELECTED",
        "cash_flow_user_visible_context_id": CONTEXT_ID,
        "primary_fact_ref": FCF_ID,
        "ocf_fact_ref": OCF_ID,
        "ppe_capex_fact_ref": CAPEX_ID,
        "fcf_fact_ref": FCF_ID,
        "primary_period": {
            "period_start": "2026-01-01",
            "period_end": "2026-06-30",
            "period_type": "YTD",
            "fiscal_year": 2026,
            "fiscal_quarter": 2,
        },
        "period_identity_contract": "cash-flow-period-identity-v1",
        "required_period_label": "2026 회계연도 상반기 누계",
        "duration_basis": "fiscal_year_to_date_cumulative",
        "is_ytd": True,
        "is_fy": False,
        "allowed_period_claims": {
            "fiscal_year": 2026,
            "fiscal_quarter": 2,
            "period_type": "YTD",
            "period_end": "2026-06-30",
            "canonical_label": "2026 회계연도 상반기 누계",
        },
        "forbidden_period_claims": [
            "annualized",
            "calendar_period_inference",
            "standalone_quarter",
        ],
        "fcf_scope": "OCF - PPE CAPEX",
        "financial_currency": "USD",
        "freshness_state": "CURRENT_FORMAL",
        "suppressed_baseline_claim_ids": ["claim-1"],
        "user_visible_enabled": True,
    }


def _stock() -> dict[str, object]:
    return {
        "cash_flow_user_visible": _context(),
        "fact_catalog": [
            {"fact_id": OCF_ID, "fact_type": "cash_flow_ocf"},
            {"fact_id": CAPEX_ID, "fact_type": "cash_flow_ppe_capex"},
            {"fact_id": FCF_ID, "fact_type": "cash_flow_fcf_ppe"},
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
            "facts_used": [OCF_ID, CAPEX_ID, FCF_ID],
            "frameworks_used": [],
            "core_judgment": {"text": "사업 논리는 유지됩니다.", "fact_ids": []},
            "business_earnings": {
                "text": (
                    "2026 회계연도 상반기 누계 PPE 투자 후 잉여현금흐름은 "
                    "$600M입니다. Cloud 성장과 마진을 함께 봅니다."
                ),
                "fact_ids": [OCF_ID, CAPEX_ID, FCF_ID],
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
                    "fact_id": FCF_ID,
                    "field_path": "fields.value",
                    "value": 600_000_000,
                    "unit": "USD",
                    "semantic_type": "free_cash_flow_ppe",
                    "text_ref": "business_earnings.text",
                    "usage": "PPE 투자 후 잉여현금흐름은 $600M",
                }
            ],
            "unknowns": ["Cloud 성장과 마진 지속성은 미확인입니다."],
            "priority_watch": [],
            "next_checks": [],
            "confidence": 0.8,
        }
    )


def test_ai_cash_flow_owner_period_scope_and_unknown_contract_passes() -> None:
    assert _cash_flow_user_visible_errors(_review(), _stock()) == []


def test_ai_cash_flow_requires_exact_fiscal_ytd_label() -> None:
    review = _review()
    review.business_earnings.text = (
        "2026년 2분기 PPE 투자 후 잉여현금흐름은 $600M입니다."
    )

    errors = _cash_flow_user_visible_errors(review, _stock())

    assert "TEST:cash_flow_required_period_label_missing" in errors
    assert "TEST:cash_flow_ytd_label_missing" in errors


def test_ai_cash_flow_fy_cannot_be_shortened_to_quarter() -> None:
    stock = _stock()
    stock["cash_flow_user_visible"] = {
        **_context(),
        "primary_period": {
            "period_start": "2025-06-28",
            "period_end": "2026-07-03",
            "period_type": "FY",
            "fiscal_year": 2026,
            "fiscal_quarter": 4,
        },
        "required_period_label": "2026 회계연도 연간",
        "duration_basis": "full_fiscal_year",
        "is_ytd": False,
        "is_fy": True,
    }
    review = _review()
    review.business_earnings.text = (
        "2026 회계연도 4분기 PPE 투자 후 잉여현금흐름은 $600M입니다."
    )

    errors = _cash_flow_user_visible_errors(review, stock)

    assert "TEST:cash_flow_required_period_label_missing" in errors
    assert "TEST:cash_flow_fy_label_missing" in errors


def test_ai_cash_flow_rejects_ytd_as_standalone_or_annualized() -> None:
    review = _review()
    review.business_earnings.text = (
        "2026 회계연도 상반기 누계 분기 단독 PPE 투자 후 잉여현금흐름은 "
        "$600M이며 연율화합니다."
    )

    errors = _cash_flow_user_visible_errors(review, _stock())

    assert "TEST:cash_flow_period_type_mislabel" in errors
    assert "TEST:cash_flow_period_annualization_forbidden" in errors


def test_ai_cash_flow_wrong_owner_and_resolved_unknown_are_rejected() -> None:
    review = _review()
    review.numeric_claims[0].text_ref = "valuation_analysis.text"
    review.valuation_analysis.text = "FCF 수익률을 valuation에 반영합니다."
    review.unknowns = ["FCF가 없어 확인할 수 없습니다."]

    errors = _cash_flow_user_visible_errors(review, _stock())

    assert "TEST:cash_flow_numeric_owner_invalid" in errors
    assert "TEST:unsupported_cash_flow_metric" in errors
    assert "TEST:resolved_cash_flow_unknown_retained" in errors
    assert "TEST:cash_flow_valuation_owner_misuse" in errors


def test_suppressed_context_rejects_cash_flow_fact_use() -> None:
    stock = _stock()
    stock["cash_flow_user_visible"] = {
        **_context(),
        "selection_state": "SUPPRESSED",
        "user_visible_enabled": False,
    }

    assert "TEST:suppressed_cash_flow_fact_used" in _cash_flow_user_visible_errors(
        _review(), stock
    )


def test_suppressed_context_does_not_reclassify_unrelated_legacy_roic_text() -> None:
    stock = _stock()
    stock["cash_flow_user_visible"] = {
        **_context(),
        "selection_state": "SUPPRESSED",
        "user_visible_enabled": False,
    }
    review = _review()
    review.facts_used = []
    review.business_earnings.fact_ids = []
    review.numeric_claims = []
    review.business_earnings.text = "ROIC 확인은 기존 사업 품질 점검 항목입니다."

    assert _cash_flow_user_visible_errors(review, stock) == []


def test_ai_and_fallback_share_context_identity_and_lineage() -> None:
    packet = {"stocks": [{"ticker": "TEST", "cash_flow_user_visible": _context()}]}
    deterministic = {
        "analysis_context": {"cash_flow_user_visible": _context()}
    }

    metadata = _cash_flow_delivery_metadata(packet, "TEST", deterministic)

    assert metadata["cash_flow_user_visible_context_id"] == CONTEXT_ID
    assert metadata["cash_flow_fact_ids"] == [OCF_ID, CAPEX_ID, FCF_ID]
    run_metadata = _cash_flow_run_metadata(packet)
    assert run_metadata["cash_flow_selected_count"] == 1
    assert run_metadata["cash_flow_selected_tickers"] == ["TEST"]


def test_ai_fallback_period_or_context_mismatch_is_hard_failure() -> None:
    packet = {"stocks": [{"ticker": "TEST", "cash_flow_user_visible": _context()}]}
    fallback_context = copy.deepcopy(_context())
    fallback_context["primary_period"]["period_end"] = "2026-03-31"
    deterministic = {
        "analysis_context": {"cash_flow_user_visible": fallback_context}
    }

    with pytest.raises(ValueError, match="cash_flow_ai_fallback_context_mismatch"):
        _cash_flow_delivery_metadata(packet, "TEST", deterministic)


def test_ai_fallback_suppression_identity_mismatch_is_hard_failure() -> None:
    suppressed = {
        **_context(),
        "cash_flow_user_visible_context_id": None,
        "selection_state": "SUPPRESSED",
        "selection_reason": "unchanged_visible_cash_flow_context",
        "display_reason": "SUPPRESSED_NO_DELTA",
        "user_visible_enabled": False,
    }
    packet = {"stocks": [{"ticker": "TEST", "cash_flow_user_visible": suppressed}]}
    fallback_context = copy.deepcopy(suppressed)
    fallback_context["suppressed_baseline_claim_ids"] = ["different-claim"]

    with pytest.raises(ValueError, match="cash_flow_ai_fallback_context_mismatch"):
        _cash_flow_delivery_metadata(
            packet,
            "TEST",
            {"analysis_context": {"cash_flow_user_visible": fallback_context}},
        )
