from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.industry_reasoning_service import (
    INDUSTRY_REASONING_CONTRACT,
    INDUSTRY_REASONING_REFERENCE_FIELD,
    build_industry_reasoning_plan,
    industry_reasoning_guardrail_flags,
    industry_reasoning_reference_errors,
)


def _stock(
    industry_key: str,
    *,
    industry: str | None = None,
    fact_fields: dict[str, object] | None = None,
) -> dict[str, object]:
    facts = []
    if fact_fields is not None:
        facts.append(
            {
                "fact_id": "fact:verified",
                "fact_type": "fundamental",
                "fields": fact_fields,
                "interpretation_eligible": True,
            }
        )
    return {
        "industry": industry,
        "company_profile": {"quality": "verified"},
        "knowledge_routing": {
            "industry_key": industry_key,
            "industry_routing": {
                "confidence": "high" if industry_key != "general" else "low",
                "source": "normalized_profile_taxonomy",
                "evidence": [f"company.profile.taxonomy_key={industry_key}"],
                "secondary_frameworks": [],
            },
        },
        "fact_catalog": facts,
        "industry_reasoning_contract": INDUSTRY_REASONING_CONTRACT,
    }


def _review(text: str, *, facts_used: list[str] | None = None) -> SimpleNamespace:
    section = SimpleNamespace(text=text)
    price = SimpleNamespace(
        text="",
        new_observer_view="신규 관찰자는 진입 손익비를 확인합니다.",
        holder_view="보유자는 지지 유지와 논리 훼손을 확인합니다.",
    )
    return SimpleNamespace(
        facts_used=facts_used or [],
        core_judgment=section,
        business_earnings=SimpleNamespace(text=""),
        price_positioning=price,
        supply_analysis=SimpleNamespace(text=""),
        valuation_analysis=SimpleNamespace(text=""),
        unknowns=["업종 핵심 지표가 확인되지 않았습니다."],
        priority_watch=[],
        next_checks=[],
    )


@pytest.mark.parametrize(
    ("industry_key", "expected"),
    [
        ("memory", "memory"),
        ("semiconductor_foundry", "semiconductor_foundry"),
        ("insurance", "insurance"),
        ("shipping", "transport_logistics"),
        ("steel_materials", "steel_materials"),
        ("automotive", "automotive"),
        ("biotech", "biotech"),
        ("hpc_crypto_infrastructure", "hpc_crypto_infrastructure"),
        ("epc", "epc_construction"),
        ("saas", "saas"),
        ("holding_company", "holding_company"),
        ("general", "general"),
    ],
)
def test_structured_framework_routing(industry_key: str, expected: str) -> None:
    plan = build_industry_reasoning_plan(_stock(industry_key))

    assert plan.primary_framework == expected


def test_verified_steel_industry_recovers_specialized_route() -> None:
    plan = build_industry_reasoning_plan(
        _stock("general", industry="Steel Manufacturing")
    )

    assert plan.primary_framework == "steel_materials"
    assert plan.source == "verified_company_industry"
    assert plan.confidence == "high"


def test_thesis_or_theme_does_not_change_primary_framework() -> None:
    stock = _stock("general", industry="Financial Services")
    routing = stock["knowledge_routing"]["industry_routing"]
    routing["secondary_frameworks"] = ["hyperscaler_capex_transmission"]
    stock["thesis"] = {"core_thesis": "HPC capacity and power conversion"}

    plan = build_industry_reasoning_plan(stock)

    assert plan.primary_framework == "general"
    assert plan.secondary_contexts == ("hyperscaler_capex_transmission",)


def test_supported_causal_reference_passes() -> None:
    text = "확인된 매출과 이익률은 같은 방향으로 움직였습니다."
    stock = _stock(
        "general",
        fact_fields={"revenue": 100.0, "operating_margin": 10.0},
    )
    review = {
        "facts_used": ["fact:verified"],
        "core_judgment": {"text": text, "fact_ids": ["fact:verified"]},
        INDUSTRY_REASONING_REFERENCE_FIELD: [
            {
                "ref_id": "causal",
                "text_ref": "core_judgment.text",
                "exact_text_span": text,
                "claim_type": "verified_causal_interpretation",
                "primary_framework": "general",
                "supporting_fact_ids": ["fact:verified"],
                "required_fact_families": ["revenue", "operating_margin"],
            }
        ],
    }

    errors, accepted = industry_reasoning_reference_errors(
        review,
        stock,
        prefix="TEST",
    )

    assert errors == []
    assert len(accepted) == 1


def test_missing_middle_fact_rejects_downstream_confirmation() -> None:
    text = "매출 증가가 현금흐름 개선으로 이어졌습니다."
    stock = _stock("general", fact_fields={"revenue": 100.0})
    review = {
        "facts_used": ["fact:verified"],
        "core_judgment": {"text": text, "fact_ids": ["fact:verified"]},
        INDUSTRY_REASONING_REFERENCE_FIELD: [
            {
                "ref_id": "leap",
                "text_ref": "core_judgment.text",
                "exact_text_span": text,
                "claim_type": "verified_causal_interpretation",
                "primary_framework": "general",
                "supporting_fact_ids": ["fact:verified"],
                "required_fact_families": ["revenue", "operating_cash_flow"],
            }
        ],
    }

    errors, accepted = industry_reasoning_reference_errors(
        review,
        stock,
        prefix="TEST",
    )

    assert accepted == []
    assert any("missing_middle_fact" in error for error in errors)


def test_missing_driver_unknown_passes_only_when_driver_is_absent() -> None:
    text = "합산비율이 확인되지 않았습니다."
    stock = _stock("insurance")
    review = {
        "facts_used": [],
        "unknowns": [text],
        INDUSTRY_REASONING_REFERENCE_FIELD: [
            {
                "ref_id": "unknown",
                "text_ref": "unknowns[0]",
                "exact_text_span": text,
                "claim_type": "missing_driver_unknown",
                "primary_framework": "insurance",
                "supporting_fact_ids": [],
                "required_fact_families": ["combined_ratio"],
            }
        ],
    }

    errors, accepted = industry_reasoning_reference_errors(
        review,
        stock,
        prefix="TEST",
    )

    assert errors == []
    assert len(accepted) == 1


def test_short_fact_markers_do_not_match_inside_unrelated_paths() -> None:
    stock = _stock(
        "steel_materials",
        fact_fields={
            "current_price": 100,
            "current_arrival_state": "confirmed",
            "scope": "listed_security",
        },
    )

    plan = build_industry_reasoning_plan(stock)

    assert "price" in plan.available_fact_families
    assert "arr" not in plan.available_fact_families
    assert "pe" not in plan.available_fact_families


def test_memory_low_trailing_pe_alone_cannot_mean_cheap() -> None:
    flags = industry_reasoning_guardrail_flags(
        _review("낮은 PER만으로 저평가라고 판단합니다."),
        _stock("memory", fact_fields={"trailing_pe": 5.0}),
    )

    assert "industry_reasoning:memory_low_trailing_pe_only" in flags


def test_insurance_low_pbr_without_roe_or_capital_cannot_mean_cheap() -> None:
    flags = industry_reasoning_guardrail_flags(
        _review("낮은 PBR이라 저평가입니다."),
        _stock("insurance", fact_fields={"price_to_book": 0.7}),
    )

    assert "industry_reasoning:insurance_low_pbr_without_returns_or_capital" in flags


def test_biotech_per_cheap_reasoning_is_rejected() -> None:
    flags = industry_reasoning_guardrail_flags(
        _review("PER가 낮아 저평가입니다."),
        _stock("biotech", fact_fields={"trailing_pe": 8.0}),
    )

    assert "industry_reasoning:biotech_per_cheap" in flags


def test_peer_discount_is_context_not_an_automatic_cheap_verdict() -> None:
    flags = industry_reasoning_guardrail_flags(
        _review("비교군 PER 할인만으로 저평가라고 판단합니다."),
        _stock("general", fact_fields={"peer_pe_relative_pct": -20.0}),
    )

    assert "industry_reasoning:peer_relative_multiple_used_as_verdict" in flags


def test_epc_order_to_margin_leap_requires_project_margin() -> None:
    flags = industry_reasoning_guardrail_flags(
        _review("수주 증가로 프로젝트 마진이 개선됐습니다."),
        _stock("epc", fact_fields={"orders": 100.0}),
    )

    assert "industry_reasoning:epc_order_to_margin_leap" in flags


def test_hyperscaler_theme_does_not_confirm_company_revenue() -> None:
    flags = industry_reasoning_guardrail_flags(
        _review("하이퍼스케일러 CAPEX가 회사 매출 증가를 확정했습니다."),
        _stock("general", fact_fields={"current_price": 10.0}),
    )

    assert "industry_reasoning:theme_promoted_to_company_revenue" in flags


def test_insurance_saas_metric_is_framework_mismatch() -> None:
    flags = industry_reasoning_guardrail_flags(
        _review("ARR과 NRR 개선이 보험 수익성을 지지합니다."),
        _stock("insurance"),
    )

    assert "industry_reasoning:insurance_saas_metric_mismatch" in flags
