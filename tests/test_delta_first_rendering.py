from __future__ import annotations

from copy import deepcopy

from app.schemas.ai_review import AIStockReview
from app.services.ai_assisted_delivery_service import _render_ai_stock_message
from app.services.ai_reasoning_quality_service import _final_rendered_language_report
from app.services.ai_review_service import _validate_stock_review
from app.services.delta_first_rendering_service import (
    build_delta_first_render_plan,
    build_delta_first_stock_draft,
    financial_recovery_fact,
    prepare_delta_first_packet,
)
from app.services.numeric_provenance_service import (
    TYPED_VALUATION_CONTRACT,
    bind_numeric_fact_references,
)


def _lineage(account: str) -> dict[str, object]:
    return {
        "account_id": account,
        "account_name": account,
        "amount_period_type": "single_quarter",
        "amount_period_start": "2026-04-01",
        "amount_period_end": "2026-06-30",
        "currency": "KRW",
        "source_filing": "20260814000001",
        "source_row_identity": f"row:{account}",
        "statement_basis": "consolidated",
        "statement_basis_state": "verified_consolidated",
    }


def _recovery() -> dict[str, object]:
    return {
        "fields": {
            "revenue": {
                "status": "verified_usable",
                "value": 1_000_000_000_000.0,
                "lineage": _lineage("revenue"),
                "yoy": {"status": "verified_usable", "value": 12.0},
            },
            "operating_income": {
                "status": "verified_usable",
                "value": 100_000_000_000.0,
                "lineage": _lineage("operating_income"),
                "yoy": {"status": "verified_usable", "value": 8.0},
            },
            "net_income": {
                "status": "unknown",
                "value": None,
                "lineage": None,
                "yoy": {"status": "unknown", "value": None},
            },
            "operating_margin": {"status": "verified_usable", "value": 10.0},
        }
    }


def _source_packet() -> dict[str, object]:
    facts = [
        {
            "fact_id": "price:current",
            "fact_type": "price",
            "fields": {"current_price": 100_000.0, "currency": "KRW"},
        },
        {
            "fact_id": "chart:structure:nearest_supports:1",
            "fact_type": "chart_support_zone",
            "fields": {"zone_low": 90_000.0, "zone_high": 95_000.0, "currency": "KRW"},
        },
        {
            "fact_id": "chart:structure:nearest_resistance:1",
            "fact_type": "chart_resistance_zone",
            "fields": {"zone_low": 105_000.0, "zone_high": 110_000.0, "currency": "KRW"},
        },
        {
            "fact_id": "chart:structure:risk_reward:current_price",
            "fact_type": "chart_risk_reward",
            "fields": {"ratio": 0.5, "rr_basis": "current_price"},
        },
        {
            "fact_id": "positioning:2026-08-14",
            "fact_type": "positioning",
            "fields": {
                "foreign_net_buy_qty": 100.0,
                "institution_net_buy_qty": -50.0,
                "foreign_net_buy_qty_5": 200.0,
                "institution_net_buy_qty_5": -100.0,
                "foreign_net_buy_qty_20": 300.0,
                "institution_net_buy_qty_20": 150.0,
            },
        },
        {
            "fact_id": "valuation:current",
            "fact_type": "valuation",
            "interpretation_eligible": True,
            "fields": {"trailing_pe": 10.0, "price_to_book": 1.0},
        },
        {
            "fact_id": "valuation:trailing_earnings",
            "fact_type": "valuation_interpretation",
            "interpretation_eligible": True,
            "fields": {"trailing_pe": 10.0},
        },
        {
            "fact_id": "valuation:book",
            "fact_type": "valuation_interpretation",
            "interpretation_eligible": True,
            "fields": {"price_to_book": 1.0},
        },
    ]
    return {
        "packet_id": "source",
        "stocks": [
            {
                "ticker": "TEST",
                "company_name": "테스트",
                "fact_catalog": facts,
                "monitoring_state": {
                    "delta": {
                        "chart_state_change": "WAIT_to_WAIT",
                        "supply_transition": "short_term_divergence",
                    }
                },
                "deterministic_assessment": {"daily_change_severity": "none"},
                "knowledge_routing": {
                    "required_frameworks": ["earnings_quality"],
                    "industry_routing": {"confidence": "low", "primary_framework": ""},
                },
                "state_grounding_requirements": {
                    "price": [
                        {"fact_id": "price:current", "field_paths": ["fields.current_price"]},
                        {
                            "fact_id": "chart:structure:nearest_supports:1",
                            "field_paths": ["fields.zone_low", "fields.zone_high"],
                        },
                        {
                            "fact_id": "chart:structure:nearest_resistance:1",
                            "field_paths": ["fields.zone_low", "fields.zone_high"],
                        },
                        {
                            "fact_id": "chart:structure:risk_reward:current_price",
                            "field_paths": ["fields.ratio"],
                        },
                    ],
                    "valuation": [],
                },
            }
        ],
    }


def _original_review() -> dict[str, object]:
    return {
        "ticker": "TEST",
        "thesis_version": 1,
        "ai_thesis_assessment": "no_material_change",
        "earnings_estimate_view": "unchanged",
        "valuation_view": "neutral",
        "frameworks_used": ["earnings_quality"],
        "priority_watch": ["이익률과 현금흐름"],
        "confidence": 0.8,
    }


def test_financial_recovery_keeps_safe_amount_and_omits_unknown_dependency() -> None:
    fact = financial_recovery_fact("TEST", _recovery())

    assert fact is not None
    fields = fact["fields"]
    assert fields["revenue"]["value"] == 1_000_000_000_000.0
    assert fields["operating_income_yoy_pct"] == 8.0
    assert "net_income" not in fields
    assert fields["field_period_labels"]["latest_revenue"].startswith(
        "2026년 2분기 연결 기준"
    )


def test_prepare_packet_normalizes_rr_basis_and_typed_valuation_contract() -> None:
    packet = prepare_delta_first_packet(
        _source_packet(), {"TEST": _recovery()}, ["TEST"], packet_id="retrospective"
    )
    stock = packet["stocks"][0]
    rr = next(
        item
        for item in stock["numeric_registry"]
        if item["fact_id"] == "chart:structure:risk_reward:current_price"
        and item["field_path"] == "fields.ratio"
    )

    assert packet["packet_id"] == "retrospective"
    assert rr["semantic_type"] == "current_price_risk_reward_ratio"
    assert stock["typed_valuation_interpretation_contract"] == TYPED_VALUATION_CONTRACT


def test_integrated_draft_binds_and_passes_stock_validator() -> None:
    packet = prepare_delta_first_packet(
        _source_packet(), {"TEST": _recovery()}, ["TEST"], packet_id="retrospective"
    )
    stock = packet["stocks"][0]
    draft, audit = build_delta_first_stock_draft(stock, _original_review(), _recovery())
    binding = bind_numeric_fact_references(packet, {"stock_reviews": [draft]})

    assert binding.errors == ()
    assert binding.report["manual_legacy"] == 0
    assert binding.report["typed_valuation_interpretations"]["accepted"] == 2
    assert binding.report["typed_valuation_interpretations"]["errors"] == []
    review = AIStockReview.model_validate(binding.output["stock_reviews"][0])
    assert _validate_stock_review(review, stock, "kr") == []
    assert audit["financial_available"] is True
    assert audit["suppressed_sections"] == ["business", "priority_watch"]
    assert review.price_positioning.new_observer_view != review.price_positioning.holder_view


def test_adaptive_renderer_suppresses_static_sections_without_rewriting_text() -> None:
    packet = prepare_delta_first_packet(
        _source_packet(), {"TEST": _recovery()}, ["TEST"], packet_id="retrospective"
    )
    stock = packet["stocks"][0]
    draft, _audit = build_delta_first_stock_draft(stock, _original_review(), _recovery())
    binding = bind_numeric_fact_references(packet, {"stock_reviews": [draft]})
    review = AIStockReview.model_validate(binding.output["stock_reviews"][0])
    deterministic = (
        "🏢 테스트(TEST)\n\n투자 논리: 유지\n\n구조적 위험: 보통\n\n"
        "시장 기대: 균형\n\n⚠️ 기존 경고\n• 변화 없음"
    )
    standard = _render_ai_stock_message(
        deterministic,
        review,
        market="kr",
        pilot_day=3,
        target_days=5,
    )
    adaptive = _render_ai_stock_message(
        deterministic,
        review,
        market="kr",
        pilot_day=3,
        target_days=5,
        render_plan=build_delta_first_render_plan(stock, financial_available=True),
    )

    assert "📈 사업·실적" in standard
    assert "👁 핵심 감시" in standard
    assert "📈 사업·실적" not in adaptive
    assert "👁 핵심 감시" not in adaptive
    assert "🎯 핵심 판단" in adaptive
    assert "💰 가격·포지셔닝" in adaptive
    assert "📊 수급" in adaptive
    assert "📐 Valuation" in adaptive
    assert "• 신규 관찰자:" in adaptive
    assert "• 보유자:" in adaptive
    assert "📌 다음 확인" in adaptive
    assert "⚠️ 미확인" in adaptive
    assert _final_rendered_language_report([adaptive])["hard_checks_passed"] is True


def test_supply_delta_places_grounded_supply_before_static_context() -> None:
    stock = _source_packet()["stocks"][0]
    stock["monitoring_state"] = {
        "delta": {
            "supply_transition": "short_term_divergence",
            "chart_state_change": "WAIT_to_WAIT",
        }
    }

    plan = build_delta_first_render_plan(stock, financial_available=True)

    assert plan.material_delta == "supply"
    assert plan.section_order.index("supply") < plan.section_order.index("core")


def test_denied_recovery_does_not_restore_earnings_or_pe() -> None:
    recovery = deepcopy(_recovery())
    for field in ("revenue", "operating_income", "net_income"):
        recovery["fields"][field]["status"] = "denied"
    packet = prepare_delta_first_packet(
        _source_packet(), {"TEST": recovery}, ["TEST"], packet_id="retrospective"
    )
    draft, audit = build_delta_first_stock_draft(
        packet["stocks"][0], _original_review(), recovery
    )
    binding = bind_numeric_fact_references(packet, {"stock_reviews": [draft]})
    review = AIStockReview.model_validate(binding.output["stock_reviews"][0])
    rendered = "\n".join(
        [
            review.core_judgment.text,
            review.business_earnings.text,
            review.valuation_analysis.text,
        ]
    )

    assert audit["financial_available"] is False
    assert "영업이익 1,000억원" not in rendered
    assert "현재 PER" not in rendered
    assert "현재 PBR 1배" in rendered
