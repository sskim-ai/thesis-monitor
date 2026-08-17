from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.semantic_decision_service import (
    SEMANTIC_CLAIM_REFERENCE_FIELD,
    SEMANTIC_SCOPE_CONTRACT,
    VALUATION_CONTEXT_CONTRACT,
    VALUATION_CONTEXT_REFERENCE_FIELD,
    assign_listed_security_valuation_scope,
    financial_cross_field_coherence_report,
    historical_valuation_selection,
    observer_holder_semantic_error,
    select_decision_material_delta,
    select_valuation_context,
    semantic_claim_reference_errors,
    typed_valuation_scope_error,
    valuation_context_reference_errors,
)


def _valuation_fact(scope: str = "listed_security") -> dict[str, object]:
    return {
        "fact_id": "valuation:book",
        "fact_type": "valuation_interpretation",
        "valuation_scope": scope,
        "interpretation_eligible": True,
        "fields": {"price_to_book": 1.0},
    }


def _semantic_review(text: str, refs: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "facts_used": ["financial_quality:test"],
        "core_judgment": {
            "text": text,
            "fact_ids": ["financial_quality:test"],
        },
        SEMANTIC_CLAIM_REFERENCE_FIELD: refs or [],
    }


def _denied_stock(*families: str) -> dict[str, object]:
    return {
        "semantic_scope_contract": SEMANTIC_SCOPE_CONTRACT,
        "denied_semantic_families": list(families),
        "fact_catalog": [
            {
                "fact_id": "financial_quality:test",
                "fact_type": "financial_quality",
                "fields": {"state": "denied"},
            }
        ],
    }


def _historical_stock(
    *,
    percentile: float = 92.0,
    comparability: str = "normal",
    history_end: str = "2026-08-10",
) -> dict[str, object]:
    statistics = {
        "current_percentile": percentile,
        "deduplicated_observation_count": 200,
        "history_quality": "high",
        "history_coverage_ratio": 0.95,
        "history_start_date": "2022-01-01",
        "history_end_date": history_end,
    }
    return {
        "fact_catalog": [
            {
                "fact_id": "valuation:current",
                "fact_type": "valuation",
                "fields": {"historical_comparability": comparability},
            },
            {
                "fact_id": "valuation:historical_pe",
                "fact_type": "valuation_interpretation",
                "as_of_date": "2026-08-14",
                "interpretation_eligible": True,
                "fields": {"historical_pe_statistics": statistics},
            },
        ]
    }


def test_company_valuation_scope_accepts_company_wording() -> None:
    fact = _valuation_fact()
    item = {"economic_scope": "listed_security"}

    assert typed_valuation_scope_error(item, fact, "회사 전체 PBR은 현재 PBR 1배입니다.") is None


def test_company_valuation_scope_rejects_segment_wording() -> None:
    fact = _valuation_fact()
    item = {"economic_scope": "listed_security"}

    assert typed_valuation_scope_error(item, fact, "운송 사업의 PBR은 1배입니다.") == (
        "company_multiple_presented_as_segment"
    )


def test_true_segment_multiple_accepts_segment_wording() -> None:
    fact = _valuation_fact("segment")
    item = {"economic_scope": "segment"}

    assert typed_valuation_scope_error(item, fact, "메모리 사업의 PER은 8배입니다.") is None


def test_pure_play_multiple_remains_listed_security_scope() -> None:
    facts = [_valuation_fact("")]

    assign_listed_security_valuation_scope(facts)

    assert facts[0]["valuation_scope"] == "listed_security"


def test_denied_revenue_qualitative_echo_is_rejected() -> None:
    review = _semantic_review("외형 성장이 강해졌습니다.")

    errors, accepted = semantic_claim_reference_errors(
        review,
        _denied_stock("revenue"),
        prefix="TEST",
    )

    assert accepted == []
    assert any("denied_fact_qualitative_echo" in error for error in errors)


def test_denied_margin_and_pe_echoes_are_rejected() -> None:
    review = _semantic_review("수익성이 크게 개선됐고 낮은 이익 배수입니다.")

    errors, _accepted = semantic_claim_reference_errors(
        review,
        _denied_stock("margin", "pe"),
        prefix="TEST",
    )

    assert sum("denied_fact_qualitative_echo" in error for error in errors) == 2


def test_denial_explanation_is_allowed_with_denied_fact() -> None:
    text = "공식 손익 수치는 품질 충돌 때문에 이번 판단에 사용하지 않습니다."
    review = _semantic_review(
        text,
        [
            {
                "ref_id": "denial",
                "text_ref": "core_judgment.text",
                "exact_text_span": text,
                "claim_type": "denial_explanation",
                "economic_scope": "company",
                "supporting_fact_ids": ["financial_quality:test"],
                "semantic_families": ["earnings"],
            }
        ],
    )

    errors, accepted = semantic_claim_reference_errors(
        review,
        _denied_stock("earnings"),
        prefix="TEST",
    )

    assert errors == []
    assert len(accepted) == 1


def test_material_earnings_delta_beats_mild_supply_delta() -> None:
    stock = {
        "deterministic_assessment": {"daily_change_severity": "material"},
        "monitoring_state": {"delta": {"supply_transition": "short_term_divergence"}},
        "fact_catalog": [],
    }

    result = select_decision_material_delta(stock, financial_available=True)

    assert result.selected_primary == "earnings_or_thesis"
    assert result.selected_secondary == "supply"


def test_mild_supply_is_secondary_to_verified_current_earnings_context() -> None:
    stock = {
        "deterministic_assessment": {"daily_change_severity": "none"},
        "monitoring_state": {"delta": {"supply_transition": "short_term_divergence"}},
        "fact_catalog": [],
    }

    result = select_decision_material_delta(stock, financial_available=True)

    assert result.selected_primary == "none"
    assert result.selected_secondary == "supply"
    assert result.decision_context == "earnings_and_valuation"


def test_price_transition_is_primary_without_safe_earnings() -> None:
    stock = {
        "deterministic_assessment": {"daily_change_severity": "none"},
        "monitoring_state": {"delta": {"chart_state_change": "WAIT_to_CONFIRMED"}},
        "fact_catalog": [],
    }

    result = select_decision_material_delta(stock, financial_available=False)

    assert result.selected_primary == "price_structure"


def test_no_material_delta_is_explicit() -> None:
    result = select_decision_material_delta(
        {"deterministic_assessment": {}, "monitoring_state": {"delta": {}}, "fact_catalog": []},
        financial_available=False,
    )

    assert result.selected_primary == "none"
    assert result.reason == "no_verified_material_delta"


def test_safe_elevated_history_is_retained_when_peer_context_is_absent() -> None:
    result = historical_valuation_selection(_historical_stock(), denied_earnings=False)

    assert result["selected"]["metric"] == "pe"
    assert result["safe_context_lost"] is False


def test_failed_comparability_suppresses_history() -> None:
    result = historical_valuation_selection(
        _historical_stock(comparability="low"),
        denied_earnings=False,
    )

    assert result["selected"] is None
    assert result["candidates"][0]["reason"] == "historical_comparability_failed"


def test_stale_history_is_suppressed() -> None:
    result = historical_valuation_selection(
        _historical_stock(history_end="2026-07-01"),
        denied_earnings=False,
    )

    assert result["selected"] is None
    assert result["candidates"][0]["reason"] == "historical_context_stale"


def test_actual_samsung_recovery_is_cross_field_coherent() -> None:
    path = Path("docs/reports/20260817-phase8-1-1-authoritative-financial-recovery-audit.json")
    recovery = json.loads(path.read_text(encoding="utf-8"))["results"]["005930"]

    report = financial_cross_field_coherence_report(recovery)

    assert report["classification"] == "VALID_AND_COHERENT"
    assert report["operating_margin"]["formula_match"] is True
    assert report["yoy"]["revenue"]["lineage_comparable"] is True
    assert report["yoy"]["operating_income"]["formula_match"] is True


def test_observer_holder_label_only_duplication_is_rejected() -> None:
    error = observer_holder_semantic_error(
        "신규 관찰자는 지지 유지를 확인합니다.",
        "보유자는 지지 유지를 확인합니다.",
    )

    assert error == "observer_holder_label_only_duplication"


def test_observer_holder_distinct_decision_variables_pass() -> None:
    error = observer_holder_semantic_error(
        "신규 관찰자는 현재 손익비와 가까운 저항을 봅니다.",
        "보유자는 지지 유지와 영업이익 악화를 봅니다.",
    )

    assert error is None


@pytest.mark.parametrize(
    (
        "historical_status",
        "peer_status",
        "history_used",
        "peer_used",
        "expected_class",
    ),
    [
        ("available", "unavailable", True, False, "CURRENT_PLUS_HISTORY"),
        ("unavailable", "unavailable", False, False, "CURRENT_ONLY"),
        ("available", "available", True, True, "CURRENT_PLUS_HISTORY_PLUS_PEER"),
        ("unsafe", "unavailable", False, False, "CURRENT_ONLY"),
        ("unsafe", "available", False, True, "CURRENT_PLUS_PEER"),
    ],
)
def test_valuation_context_availability_matrix(
    historical_status: str,
    peer_status: str,
    history_used: bool,
    peer_used: bool,
    expected_class: str,
) -> None:
    result = select_valuation_context(
        current_status="available",
        historical_status=historical_status,
        peer_status=peer_status,
        forward_status="unavailable",
        current_used=True,
        history_used=history_used,
        peer_used=peer_used,
        forward_used=False,
    )

    assert result.valuation_context_class == expected_class


def test_valuation_context_rejects_history_with_current_only_wording() -> None:
    context_span = "같은 시점의 동종기업 비교값이 없어 현재 절대 배수만 표시합니다."
    review = {
        "valuation_analysis": {
            "text": (
                "회사 전체 PBR의 자체 역사 위치는 PBR 역사적 백분위 91.6%입니다. "
                + context_span
            ),
            "fact_ids": [],
        },
        VALUATION_CONTEXT_REFERENCE_FIELD: {
            "contract": VALUATION_CONTEXT_CONTRACT,
            "valuation_context_class": "CURRENT_PLUS_HISTORY",
            "current_status": "available",
            "historical_status": "available",
            "peer_status": "unavailable",
            "forward_status": "unavailable",
            "current_used": True,
            "history_used": True,
            "peer_used": False,
            "forward_used": False,
            "text_ref": "valuation_analysis.text",
            "exact_text_span": context_span,
        },
    }
    bindings = [
        {"text_ref": "valuation_analysis.text", "semantic_type": "price_to_book"},
        {
            "text_ref": "valuation_analysis.text",
            "semantic_type": "historical_pb_percentile",
        },
    ]

    errors, accepted = valuation_context_reference_errors(
        review,
        {"fact_catalog": []},
        bindings,
        prefix="TEST",
    )

    assert accepted is not None
    assert any("current_only_history_contradiction" in error for error in errors)


def test_valuation_context_accepts_current_plus_history_wording() -> None:
    context_span = (
        "같은 시점의 동종기업 비교값은 없어 이번 평가는 회사 전체 현재 배수와 "
        "자체 역사 위치를 중심으로 봅니다."
    )
    review = {
        "valuation_analysis": {"text": context_span, "fact_ids": []},
        VALUATION_CONTEXT_REFERENCE_FIELD: {
            "contract": VALUATION_CONTEXT_CONTRACT,
            "valuation_context_class": "CURRENT_PLUS_HISTORY",
            "current_status": "available",
            "historical_status": "available",
            "peer_status": "unavailable",
            "forward_status": "unavailable",
            "current_used": True,
            "history_used": True,
            "peer_used": False,
            "forward_used": False,
            "text_ref": "valuation_analysis.text",
            "exact_text_span": context_span,
        },
    }
    bindings = [
        {"text_ref": "valuation_analysis.text", "semantic_type": "price_to_book"},
        {
            "text_ref": "valuation_analysis.text",
            "semantic_type": "historical_pb_percentile",
        },
    ]

    errors, accepted = valuation_context_reference_errors(
        review,
        {"fact_catalog": []},
        bindings,
        prefix="TEST",
    )

    assert errors == []
    assert accepted is not None
    assert accepted["valuation_context_class"] == "CURRENT_PLUS_HISTORY"


def test_representative_valuation_context_classes_match_final_preview() -> None:
    path = Path(
        "docs/reports/20260817-phase8-4-1-1-valuation-context-audit.json"
    )
    artifact = json.loads(path.read_text(encoding="utf-8"))
    stocks = artifact["stocks"]
    expected = {
        "005930": "CURRENT_PLUS_HISTORY",
        "005490": "CURRENT_ONLY",
        "086280": "CURRENT_PLUS_HISTORY",
        "003690": "CURRENT_ONLY",
        "000660": "CURRENT_PLUS_HISTORY",
    }

    assert {
        ticker: value["valuation_context"]["valuation_context_class"]
        for ticker, value in stocks.items()
    } == expected
    rendered = {
        item["ticker"]: item["text"]
        for item in artifact["rendered_messages"]
        if item["ticker"] in expected
    }
    for ticker, value in stocks.items():
        context = value["valuation_context"]
        if context["history_used"]:
            assert "현재 절대 배수만" not in rendered[ticker]
            assert "자체 역사 위치" in rendered[ticker]
