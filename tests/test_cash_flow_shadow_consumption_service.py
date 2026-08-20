from __future__ import annotations

import re
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from app.services.cash_flow_capital_efficiency_service import (
    CapexScope,
    FactType,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
)
from app.services.cash_flow_shadow_consumption_service import (
    EarningsAlignmentState,
    FreshnessState,
    RelationType,
    ShadowNumericClaim,
    ShadowReasoning,
    UsageMode,
    build_cash_flow_reasoning_context,
    classify_relation,
    format_financial_amount,
    point_in_time_facts,
    render_shadow_reasoning,
    resolve_cash_flow_unknowns,
    select_prior_comparable,
    validate_shadow_reasoning,
)


CUTOFF = date(2026, 8, 20)


def _fact(
    fact_id: str,
    metric: Metric,
    value: str,
    *,
    start: date = date(2026, 1, 1),
    end: date = date(2026, 6, 30),
    period_type: PeriodType = PeriodType.YTD,
    fiscal_year: int = 2026,
    fiscal_quarter: int | None = 2,
    filing_date: date = date(2026, 7, 20),
    input_fact_ids: tuple[str, ...] = (),
    currency: str = "USD",
    fact_type: FactType = FactType.REPORTED,
) -> FinancialFact:
    return FinancialFact(
        fact_id=fact_id,
        issuer_id="issuer-1",
        metric=metric,
        value=Decimal(value),
        currency=currency,
        unit=currency,
        period=PeriodIdentity(
            start=start,
            end=end,
            period_type=period_type,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter,
        ),
        entity_scope="consolidated",
        statement_basis="CFS",
        reported_or_derived=(
            "derived_metric" if fact_type == FactType.DERIVED_METRIC else "reported"
        ),
        source_provider="sec_companyfacts",
        source_document_id=f"doc-{fiscal_year}",
        filing_date=filing_date,
        source_occurrence_id=f"occ-{fact_id}",
        raw_payload_sha256="a" * 64,
        semantic_mapping=(
            "OCF_MINUS_PPE_CAPEX_CASH_OUTFLOW"
            if metric == Metric.FCF
            else metric.value
        ),
        fact_type=fact_type,
        source_semantic=metric.value,
        source_reported_value=Decimal(value),
        source_reported_unit=currency,
        source_sign=(
            "positive_payment_magnitude" if metric == Metric.CAPEX else "economic_signed"
        ),
        capex_scope=CapexScope.PPE_ONLY if metric == Metric.CAPEX else None,
        derivation_formula=(
            "OCF_MINUS_PPE_CAPEX_CASH_OUTFLOW"
            if metric == Metric.FCF
            else None
        ),
        derivation_version=(
            "cash-flow-capital-efficiency-v1"
            if metric == Metric.FCF
            else None
        ),
        input_fact_ids=input_fact_ids,
    )


def _full_facts() -> tuple[FinancialFact, ...]:
    prior_ocf = _fact(
        "ocf-2025",
        Metric.OCF,
        "80",
        start=date(2025, 1, 1),
        end=date(2025, 6, 30),
        fiscal_year=2025,
        filing_date=date(2025, 7, 20),
    )
    prior_capex = _fact(
        "capex-2025",
        Metric.CAPEX,
        "50",
        start=date(2025, 1, 1),
        end=date(2025, 6, 30),
        fiscal_year=2025,
        filing_date=date(2025, 7, 20),
    )
    prior_fcf = _fact(
        "fcf-2025",
        Metric.FCF,
        "30",
        start=date(2025, 1, 1),
        end=date(2025, 6, 30),
        fiscal_year=2025,
        filing_date=date(2025, 7, 20),
        input_fact_ids=(prior_ocf.fact_id, prior_capex.fact_id),
        fact_type=FactType.DERIVED_METRIC,
    )
    ocf = _fact("ocf-2026", Metric.OCF, "100")
    capex = _fact("capex-2026", Metric.CAPEX, "40")
    fcf = _fact(
        "fcf-2026",
        Metric.FCF,
        "60",
        input_fact_ids=(ocf.fact_id, capex.fact_id),
        fact_type=FactType.DERIVED_METRIC,
    )
    return prior_ocf, prior_capex, prior_fcf, ocf, capex, fcf


def _context(**overrides: object):
    values = {
        "ticker": "TEST",
        "industry": "memory_semiconductor",
        "financial_type": "non_financial",
        "core_status": "ELIGIBLE",
        "facts": _full_facts(),
        "cutoff": CUTOFF,
        "latest_formal_period": date(2026, 6, 30),
        "latest_provisional_period": None,
        "latest_operating_earnings_period": date(2026, 6, 30),
        "preferred_fcf_fact_id": "fcf-2026",
        "existing_unknowns": ("OCF·CAPEX·FCF가 미확인입니다.",),
        "materiality_signals": (),
    }
    values.update(overrides)
    return build_cash_flow_reasoning_context(**values)


def test_point_in_time_rejects_future_fact_and_all_derived_dependants() -> None:
    ocf = _fact("ocf", Metric.OCF, "100")
    future_capex = _fact(
        "capex", Metric.CAPEX, "40", filing_date=date(2026, 8, 21)
    )
    fcf = _fact(
        "fcf",
        Metric.FCF,
        "60",
        filing_date=date(2026, 8, 21),
        input_fact_ids=(ocf.fact_id, future_capex.fact_id),
        fact_type=FactType.DERIVED_METRIC,
    )

    safe, excluded = point_in_time_facts((ocf, future_capex, fcf), cutoff=CUTOFF)

    assert {item.fact_id for item in safe} == {"ocf"}
    reasons = {item["fact_id"]: item["reason"] for item in excluded}
    assert reasons["capex"] == "future_filing_after_replay_cutoff"
    assert reasons["fcf"] == "future_filing_after_replay_cutoff"


def test_point_in_time_requires_complete_derived_lineage() -> None:
    fcf = _fact(
        "fcf",
        Metric.FCF,
        "60",
        input_fact_ids=("missing-ocf", "missing-capex"),
        fact_type=FactType.DERIVED_METRIC,
    )

    safe, excluded = point_in_time_facts((fcf,), cutoff=CUTOFF)

    assert safe == ()
    assert excluded[0]["reason"] == "derived_input_fact_missing"


def test_current_formal_full_fcf_context_selects_exact_primary_and_comparables() -> None:
    context = _context()

    assert context.status == "READY"
    assert context.usage_mode == UsageMode.FULL_FCF_CONTEXT
    assert context.freshness_state == FreshnessState.CURRENT_FORMAL
    assert context.earnings_alignment_state == EarningsAlignmentState.ALIGNED
    assert context.shadow_used is True
    assert context.fcf_fact_id == "fcf-2026"
    assert set(context.prior_comparable_refs) == {
        "ocf-2025",
        "capex-2025",
        "fcf-2025",
    }
    relation = next(
        item for item in context.deterministic_relations if item.metric == Metric.FCF
    )
    assert relation.relation == RelationType.POSITIVE_HIGHER


def test_later_provisional_makes_formal_cash_flow_context_only() -> None:
    context = _context(latest_provisional_period=date(2026, 9, 30))

    assert context.freshness_state == FreshnessState.FORMAL_LAGGING_PROVISIONAL
    assert context.usage_mode == UsageMode.LATEST_FORMAL_CONTEXT_ONLY
    assert context.consumption_eligible is True
    assert context.shadow_used is False


def test_newer_formal_period_blocks_old_cash_flow_as_current_substitute() -> None:
    context = _context(latest_formal_period=date(2026, 9, 30))

    assert context.freshness_state == FreshnessState.STALE_FORMAL
    assert context.usage_mode == UsageMode.SUPPRESSED
    assert context.consumption_eligible is False
    assert context.shadow_used is False


def test_ocf_only_context_does_not_infer_fcf() -> None:
    facts = tuple(item for item in _full_facts() if item.metric == Metric.OCF)
    context = _context(
        facts=facts,
        preferred_fcf_fact_id=None,
        core_status="PARTIAL",
    )

    assert context.usage_mode == UsageMode.OCF_ONLY_CONTEXT
    assert context.ocf_fact_id == "ocf-2026"
    assert context.capex_fact_id is None
    assert context.fcf_fact_id is None
    assert context.shadow_used is True


def test_insurance_is_not_applicable_and_never_consumed() -> None:
    context = _context(
        industry="insurance_reinsurance",
        financial_type="financial",
        core_status="NOT_APPLICABLE",
        facts=(),
    )

    assert context.freshness_state == FreshnessState.NOT_APPLICABLE
    assert context.usage_mode == UsageMode.NOT_APPLICABLE
    assert context.shadow_used is False


def test_comparison_rejects_mixed_period_and_duration() -> None:
    current = _fact("current", Metric.FCF, "60")
    prior_fy = _fact(
        "prior-fy",
        Metric.FCF,
        "30",
        start=date(2025, 1, 1),
        end=date(2025, 12, 31),
        period_type=PeriodType.FY,
        fiscal_year=2025,
        fiscal_quarter=None,
    )
    prior_short = _fact(
        "prior-short",
        Metric.FCF,
        "30",
        start=date(2025, 1, 1),
        end=date(2025, 6, 29),
        fiscal_year=2025,
    )

    assert select_prior_comparable(current, (prior_fy, prior_short)) is None


@pytest.mark.parametrize(
    ("period_type", "current_start", "prior_start", "fiscal_quarter"),
    [
        (PeriodType.QTD, date(2026, 4, 1), date(2025, 4, 1), 2),
        (PeriodType.TTM, date(2025, 7, 1), date(2024, 7, 1), None),
    ],
)
def test_comparison_accepts_safe_qtd_and_ttm_pairs(
    period_type: PeriodType,
    current_start: date,
    prior_start: date,
    fiscal_quarter: int | None,
) -> None:
    current = _fact(
        "current",
        Metric.FCF,
        "60",
        start=current_start,
        end=date(2026, 6, 30),
        period_type=period_type,
        fiscal_quarter=fiscal_quarter,
    )
    prior = _fact(
        "prior",
        Metric.FCF,
        "30",
        start=prior_start,
        end=date(2025, 6, 30),
        period_type=period_type,
        fiscal_year=2025,
        fiscal_quarter=fiscal_quarter,
        filing_date=date(2025, 7, 20),
    )

    assert select_prior_comparable(current, (prior,)) == prior


@pytest.mark.parametrize(
    ("prior", "current", "expected"),
    [
        ("1", "2", RelationType.POSITIVE_HIGHER),
        ("2", "1", RelationType.POSITIVE_LOWER),
        ("-2", "-1", RelationType.NEGATIVE_LESS_NEGATIVE),
        ("-1", "-2", RelationType.NEGATIVE_MORE_NEGATIVE),
        ("-1", "1", RelationType.NEGATIVE_TO_POSITIVE),
        ("1", "-1", RelationType.POSITIVE_TO_NEGATIVE),
        ("0", "1", RelationType.ZERO_TO_POSITIVE),
        ("0", "-1", RelationType.ZERO_TO_NEGATIVE),
        ("1", "0", RelationType.POSITIVE_TO_ZERO),
        ("-1", "0", RelationType.NEGATIVE_TO_ZERO),
        ("1", "1", RelationType.UNCHANGED),
    ],
)
def test_relation_types_are_numeric_not_investment_verdicts(
    prior: str, current: str, expected: RelationType
) -> None:
    assert classify_relation(Decimal(prior), Decimal(current)) == expected


def test_renderer_uses_canonical_fact_and_industry_specific_memory_language() -> None:
    context = _context()
    facts = {item.fact_id: item for item in _full_facts()}

    reasoning = render_shadow_reasoning(
        context,
        facts,
        industry="memory_semiconductor",
        source_text="HBM ASP와 재고를 확인합니다.",
    )

    assert reasoning is not None
    assert "HBM" in reasoning.text
    assert "누계" in reasoning.text
    assert reasoning.numeric_claims[0].fact_id == "fcf-2026"
    assert validate_shadow_reasoning(context, facts, reasoning) == ()


def test_biotech_negative_fcf_is_cash_burn_without_runway_inference() -> None:
    facts = list(_full_facts())
    facts[-1] = replace(facts[-1], value=Decimal("-60"))
    context = _context(facts=tuple(facts))
    by_id = {item.fact_id: item for item in facts}

    reasoning = render_shadow_reasoning(
        context,
        by_id,
        industry="biotech",
        source_text="현금소진과 임상 milestone을 봅니다.",
    )

    assert reasoning is not None
    assert "현금소진" in reasoning.text
    assert "runway를 계산하지" in reasoning.text
    assert not re.search(r"\d+\s*개월", reasoning.text)
    assert validate_shadow_reasoning(context, by_id, reasoning) == ()


def test_resolved_unknown_moves_to_industry_specific_remaining_question() -> None:
    context = _context()

    unknowns, audit = resolve_cash_flow_unknowns(
        ("OCF·CAPEX·FCF가 없어 판단할 수 없습니다.",),
        context,
        industry="memory_semiconductor",
        source_text="HBM과 재고를 확인합니다.",
    )

    assert audit["resolved"] == 1
    assert "FCF가 없어" not in unknowns[0]
    assert "ASP·HBM" in unknowns[0]


def test_ocf_only_unknown_names_missing_capex_basis_instead_of_all_cash_flow() -> None:
    facts = tuple(item for item in _full_facts() if item.metric == Metric.OCF)
    context = _context(
        facts=facts,
        preferred_fcf_fact_id=None,
        core_status="PARTIAL",
    )

    unknowns, audit = resolve_cash_flow_unknowns(
        ("현금흐름이 없어 판단할 수 없습니다.",),
        context,
        industry="hpc_data_center",
        source_text="프로젝트 NOI를 확인합니다.",
    )

    assert audit["still_valid"] == 1
    assert "영업현금흐름은 확인" in unknowns[0]
    assert "PPE" in unknowns[0]


def test_validator_rejects_numeric_mismatch_resolved_unknown_and_valuation_change() -> None:
    context = _context()
    facts = {item.fact_id: item for item in _full_facts()}
    claim = ShadowNumericClaim(
        fact_id="fcf-2026",
        semantic_type=Metric.FCF.value,
        value="999",
        display=format_financial_amount(facts["fcf-2026"]),
        currency="USD",
        unit="USD",
    )
    reasoning = ShadowReasoning(
        text=f"2026 회계연도 상반기 누계 잉여현금흐름은 {claim.display}입니다.",
        fact_ids=("fcf-2026",),
        numeric_claims=(claim,),
    )

    errors = validate_shadow_reasoning(
        context,
        facts,
        reasoning,
        unknowns=("FCF가 미확인입니다.",),
        valuation_changed=True,
    )

    assert "numeric_value_mismatch" in errors
    assert "resolved_unknown_claimed_missing" in errors
    assert "cashflow_based_valuation_change" in errors


def test_validator_rejects_unsupported_metrics_and_management_fcf_label() -> None:
    context = _context()
    facts = {item.fact_id: item for item in _full_facts()}
    claim = ShadowNumericClaim(
        fact_id="fcf-2026",
        semantic_type=Metric.FCF.value,
        value="60",
        display=format_financial_amount(facts["fcf-2026"]),
        currency="USD",
        unit="USD",
    )
    reasoning = ShadowReasoning(
        text=(
            f"회사 보고 FCF는 {claim.display}이며 FCF yield와 ROIC도 개선됐습니다."
        ),
        fact_ids=("fcf-2026",),
        numeric_claims=(claim,),
    )

    errors = validate_shadow_reasoning(context, facts, reasoning)

    assert "management_fcf_mislabel" in errors
    assert "unsupported_cash_flow_metric" in errors


def test_currency_formatter_never_converts_foreign_issuer_amount() -> None:
    twd = _fact("twd", Metric.FCF, "870170600000", currency="TWD")

    assert format_financial_amount(twd) == "NT$870.17B"
