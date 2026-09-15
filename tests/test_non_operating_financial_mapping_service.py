from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.services.cash_flow_capital_efficiency_service import FactType, Metric
from app.services.cross_market_decision_engine_service import (
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.financial_context_adapter_service import (
    adapt_fact_catalog_financial_context,
)
from app.services.financial_lineage_projection_service import (
    project_financial_fact_catalog,
)
from app.services.non_operating_financial_mapping_service import (
    CONTRACT_VERSION,
    DENIAL_REASON_TAXONOMY,
    NET_FINANCIAL_EFFECT_FORMULA,
    NO_NORMALIZED_EARNINGS_POLICY,
    NO_UNIVERSAL_NON_OPERATING_TOTAL_POLICY,
    SectorRoute,
    build_non_operating_mapping_batch,
    build_sec_non_operating_mapping_batch,
    canonicalize_non_operating_occurrences,
    promote_opendart_non_operating_facts,
    registry_audit,
    sector_route,
)
from app.services.opendart_financial_recovery_service import Filing
from app.services.opendart_xbrl_service import XbrlContext, XbrlFact
from app.services.working_capital_evidence_service import OfficialFinancialOccurrence


RAW_SHA = "a" * 64
AS_OF = date(2026, 9, 9)


def _occurrence(
    tag: str = "FinanceIncome",
    value: str = "100",
    *,
    namespace: str = "ifrs-full",
    start: date = date(2026, 4, 1),
    end: date = date(2026, 6, 30),
    fiscal_year: int = 2026,
    fiscal_period: str = "Q2",
    currency: str | None = "USD",
    unit: str | None = "USD",
    entity_scope: str | None = "issuer_level",
    statement_basis: str | None = "consolidated",
    document: str = "0001-26-000001",
    filed: date = date(2026, 8, 1),
    frame: str | None = "CY2026Q2",
    source_provider: str = "sec_edgar_companyfacts",
    source_column: str = "val",
) -> OfficialFinancialOccurrence:
    return OfficialFinancialOccurrence(
        issuer_id="sec:0000000001",
        value=Decimal(value),
        currency=currency,
        unit=unit,
        period_start=start,
        period_end=end,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        source_provider=source_provider,
        source_document_id=document,
        source_document_type="10-K" if fiscal_period == "FY" else "10-Q",
        filing_date=filed,
        namespace=namespace,
        tag=tag,
        raw_payload_sha256=RAW_SHA,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
        frame=frame,
        source_column=source_column,
    )


def _batch(*occurrences: OfficialFinancialOccurrence, framework: str = "manufacturing"):
    return build_non_operating_mapping_batch(
        occurrences,
        as_of_date=AS_OF,
        analysis_framework=framework,
    )


def _context(fact, all_facts):
    rows = project_financial_fact_catalog(all_facts, context_id="m11-test")
    row = next(item for item in rows if item["fact_id"] == fact.fact_id)
    return adapt_fact_catalog_financial_context(row, rows)


def test_contract_registry_and_denial_taxonomy_are_explicit_and_ticker_neutral() -> None:
    rows = registry_audit()

    assert CONTRACT_VERSION == "non-operating-financial-income-effects-v1"
    assert NET_FINANCIAL_EFFECT_FORMULA == "financial_income_minus_financial_cost"
    assert NO_UNIVERSAL_NON_OPERATING_TOTAL_POLICY == (
        "NO_UNIVERSAL_NON_OPERATING_TOTAL"
    )
    assert NO_NORMALIZED_EARNINGS_POLICY == "NO_ADJUSTED_OR_NORMALIZED_EARNINGS"
    assert len({row["source_semantic"] for row in rows}) == len(rows)
    assert all("ticker" not in row for row in rows)
    assert {
        "sector_not_applicable",
        "aggregate_child_overlap",
        "period_mismatch",
        "currency_mismatch",
        "entity_scope_mismatch",
        "statement_basis_mismatch",
        "attribution_basis_mismatch",
        "continuing_discontinued_mismatch",
        "broad_context_not_specific",
        "sign_semantics_unresolved",
        "source_conflict",
        "exact_context_unresolved",
        "component_scope_incomplete",
    }.issubset(DENIAL_REASON_TAXONOMY)


def test_financial_sector_routes_out_with_zero_generic_emissions() -> None:
    for framework in ("bank", "insurance", "reinsurance", "financial_institution"):
        batch = _batch(_occurrence(), framework=framework)

        assert sector_route(framework) == SectorRoute.SECTOR_FRAMEWORK_REQUIRED
        assert batch.sector_route == SectorRoute.SECTOR_FRAMEWORK_REQUIRED
        assert not batch.facts
        assert {item["reason"] for item in batch.denials} == {
            "sector_not_applicable"
        }


def test_holding_and_biotech_are_context_only_without_quality_labels() -> None:
    for framework in ("holding_company", "biotech"):
        batch = _batch(_occurrence(), framework=framework)
        assert batch.sector_route == SectorRoute.CONTEXT_ONLY
        assert "sector_context_only" in batch.direct_facts[0].cautions
        assert not {
            "non_core",
            "one_off",
            "low_quality",
        }.intersection(batch.direct_facts[0].cautions)


def test_direct_component_taxonomy_stays_typed_and_separate() -> None:
    occurrences = (
        _occurrence("FinanceIncome", "100"),
        _occurrence("FinanceCosts", "40"),
        _occurrence("InterestIncomeFinanceIncome", "20", namespace="dart"),
        _occurrence("InterestExpenseFinanceExpense", "15", namespace="dart"),
        _occurrence("NetForeignExchangeGain", "7"),
        _occurrence("NetForeignExchangeLoss", "3"),
        _occurrence("OtherGains", "9", namespace="dart"),
        _occurrence("OtherLosses", "8", namespace="dart"),
        _occurrence("GainsOnDisposalsOfPropertyPlantAndEquipment", "4"),
        _occurrence("LossesOnDisposalsOfPropertyPlantAndEquipment", "2"),
        _occurrence(
            "GainsOnValuationOfFairValueFinancialAsset", "6", namespace="dart"
        ),
        _occurrence(
            "LossesOnValuationOfFairValueFinancialAsset", "1", namespace="dart"
        ),
        _occurrence(
            "ShareOfProfitLossOfAssociatesAndJointVenturesAccountedForUsingEquityMethod",
            "5",
        ),
        _occurrence("IncomeTaxExpenseContinuingOperations", "25"),
        _occurrence("ProfitLossFromContinuingOperations", "75"),
        _occurrence("ProfitLossFromDiscontinuedOperations", "10"),
    )
    batch = _batch(*occurrences)

    assert {fact.metric for fact in batch.direct_facts} == {
        Metric.FINANCIAL_INCOME,
        Metric.FINANCIAL_COST,
        Metric.INTEREST_INCOME,
        Metric.INTEREST_EXPENSE,
        Metric.FOREIGN_EXCHANGE_GAIN,
        Metric.FOREIGN_EXCHANGE_LOSS,
        Metric.OTHER_INCOME_CONTEXT,
        Metric.OTHER_EXPENSE_CONTEXT,
        Metric.ASSET_DISPOSAL_GAIN,
        Metric.ASSET_DISPOSAL_LOSS,
        Metric.FAIR_VALUE_GAIN,
        Metric.FAIR_VALUE_LOSS,
        Metric.EQUITY_METHOD_RESULT_CONTEXT,
        Metric.INCOME_TAX_EXPENSE,
        Metric.CONTINUING_OPERATIONS_INCOME,
        Metric.DISCONTINUED_OPERATIONS_RESULT,
    }
    assert len(batch.derived_facts) == 1


def test_other_income_and_expense_remain_broad_context() -> None:
    batch = _batch(
        _occurrence("OtherGains", "9", namespace="dart"),
        _occurrence("OtherLosses", "8", namespace="dart"),
    )

    assert {fact.presentation_type for fact in batch.direct_facts} == {
        "BROAD_CONTEXT"
    }
    assert all("broad_context_not_specific" in fact.cautions for fact in batch.facts)
    assert not batch.derived_facts


def test_equity_method_result_is_not_financial_income() -> None:
    batch = _batch(
        _occurrence(
            "ShareOfProfitLossOfAssociatesAndJointVenturesAccountedForUsingEquityMethod",
            "12",
        )
    )

    fact = batch.direct_facts[0]
    assert fact.metric == Metric.EQUITY_METHOD_RESULT_CONTEXT
    assert fact.economic_role == "INVESTMENT_RESULT"
    assert "equity_method_separate_investment_result" in fact.cautions


def test_tax_is_separate_and_does_not_derive_effective_rate() -> None:
    batch = _batch(_occurrence("IncomeTaxExpenseContinuingOperations", "25"))

    fact = batch.direct_facts[0]
    assert fact.metric == Metric.INCOME_TAX_EXPENSE
    assert fact.continuity_scope == "continuing_operations"
    assert "tax_not_operating_performance" in fact.cautions
    assert "effective_tax_rate_not_derived" in fact.cautions
    assert not batch.derived_facts


def test_continuing_and_discontinued_results_remain_distinct() -> None:
    batch = _batch(
        _occurrence("ProfitLossFromContinuingOperations", "75"),
        _occurrence("ProfitLossFromDiscontinuedOperations", "10"),
    )

    by_metric = {fact.metric: fact for fact in batch.direct_facts}
    assert by_metric[Metric.CONTINUING_OPERATIONS_INCOME].continuity_scope == (
        "continuing_operations"
    )
    assert by_metric[Metric.DISCONTINUED_OPERATIONS_RESULT].continuity_scope == (
        "discontinued_operations"
    )


def test_safe_aggregate_net_effect_is_exact_and_lineaged() -> None:
    batch = _batch(
        _occurrence("FinanceIncome", "100"),
        _occurrence("FinanceCosts", "40"),
    )

    net = batch.derived_facts[0]
    assert net.metric == Metric.NET_FINANCIAL_INCOME_EFFECT
    assert net.value == Decimal(60)
    assert net.fact_type == FactType.DERIVED_METRIC
    assert net.derivation_formula == NET_FINANCIAL_EFFECT_FORMULA
    by_metric = {fact.metric: fact.fact_id for fact in batch.direct_facts}
    assert net.input_fact_ids == (
        by_metric[Metric.FINANCIAL_INCOME],
        by_metric[Metric.FINANCIAL_COST],
    )
    adapted = _context(net, batch.facts)
    assert adapted.denial_reasons == ()
    assert adapted.context is not None
    assert adapted.context["evidence_status"] == "DERIVED_SAFE"
    assert adapted.context["derivation"]["formula"] == (
        NET_FINANCIAL_EFFECT_FORMULA
    )


def test_negative_net_effect_is_valid_when_cost_exceeds_income() -> None:
    batch = _batch(
        _occurrence("FinanceIncome", "40"),
        _occurrence("FinanceCosts", "100"),
    )
    assert batch.derived_facts[0].value == Decimal(-60)


def test_direct_official_net_takes_precedence_over_derived() -> None:
    batch = _batch(
        _occurrence("FinanceIncome", "100"),
        _occurrence("FinanceCosts", "40"),
        _occurrence("FinanceIncomeCost", "60"),
    )

    direct_net = [
        fact
        for fact in batch.direct_facts
        if fact.metric == Metric.NET_FINANCIAL_INCOME_EFFECT
    ]
    assert len(direct_net) == 1
    assert not batch.derived_facts
    assert "official_direct_net_precedence" in {
        item["reason"] for item in batch.denials
    }


def test_incomplete_components_do_not_synthesize_total() -> None:
    for occurrence in (
        _occurrence("FinanceIncome", "100"),
        _occurrence("FinanceCosts", "40"),
        _occurrence("InterestIncomeFinanceIncome", "20", namespace="dart"),
    ):
        batch = _batch(occurrence)
        assert not batch.derived_facts
        if occurrence.tag in {"FinanceIncome", "FinanceCosts"}:
            assert "component_scope_incomplete" in {
                item["reason"] for item in batch.denials
            }


def test_negative_aggregate_sign_blocks_arithmetic_but_preserves_direct_fact() -> None:
    batch = _batch(
        _occurrence("FinanceIncome", "100"),
        _occurrence("FinanceCosts", "-40"),
    )

    assert len(batch.direct_facts) == 2
    assert not batch.derived_facts
    assert batch.sign_semantics_unresolved_count == 1
    assert "sign_semantics_unresolved" in {item["reason"] for item in batch.denials}


def test_period_currency_entity_and_basis_mismatches_cannot_net() -> None:
    mismatch_costs = (
        _occurrence(
            "FinanceCosts",
            "40",
            start=date(2026, 1, 1),
            frame="CY2026Q2YTD",
        ),
        _occurrence("FinanceCosts", "40", currency="EUR", unit="EUR"),
        _occurrence("FinanceCosts", "40", entity_scope="subsidiary_level"),
        _occurrence("FinanceCosts", "40", statement_basis="separate"),
    )
    for cost in mismatch_costs:
        batch = _batch(_occurrence("FinanceIncome", "100"), cost)
        assert not batch.derived_facts


def test_parent_and_child_are_preserved_but_marked_no_summation() -> None:
    batch = _batch(
        _occurrence("FinanceIncome", "100"),
        _occurrence("InterestIncomeFinanceIncome", "20", namespace="dart"),
        _occurrence("NetForeignExchangeGain", "7"),
    )

    assert len(batch.direct_facts) == 3
    assert batch.aggregate_child_overlap_conflict_count == 1
    assert batch.aggregate_precedence_count == 2
    assert batch.child_detail_preserved_count == 2
    assert batch.overlap_events[0]["reason"] == "aggregate_child_overlap"
    parent = next(fact for fact in batch.facts if fact.metric == Metric.FINANCIAL_INCOME)
    assert "children_present_no_double_count" in parent.cautions
    assert all(
        "aggregate_parent_present_no_summation" in fact.cautions
        for fact in batch.facts
        if fact.metric in {Metric.INTEREST_INCOME, Metric.FOREIGN_EXCHANGE_GAIN}
    )


def test_unsupported_fuzzy_and_wrong_statement_semantics_are_blocked() -> None:
    batch = canonicalize_non_operating_occurrences(
        (
            _occurrence("IssuerSpecificFinanceIncome"),
            _occurrence("OperatingIncomeLoss", namespace="us-gaap"),
            _occurrence(
                "OtherComprehensiveIncomeNetOfTaxExchangeDifferencesOnTranslation"
            ),
            _occurrence("EffectOfExchangeRateChangesOnCashAndCashEquivalents"),
        ),
        as_of_date=AS_OF,
        analysis_framework="manufacturing",
    )

    assert not batch.facts
    assert {item["reason"] for item in batch.denials} == {
        "unsupported_semantic",
        "operating_metric_not_non_operating",
        "oci_translation_not_profit_or_loss_fx",
        "cash_flow_fx_not_income_statement_fx",
    }


def test_missing_currency_unit_entity_basis_or_period_fails_closed() -> None:
    cases = (
        _occurrence(currency=None, unit=None),
        _occurrence(entity_scope=None),
        _occurrence(statement_basis=None),
        replace(_occurrence(), period_start=None),
    )
    for occurrence in cases:
        assert not _batch(occurrence).facts


def test_exact_duplicate_is_idempotent_and_conflict_is_blocked() -> None:
    occurrence = _occurrence()
    duplicate = _batch(occurrence, occurrence)
    conflict = _batch(occurrence, replace(occurrence, value=Decimal(101)))

    assert len(duplicate.direct_facts) == 1
    assert duplicate.exact_duplicates_suppressed == 1
    assert _batch(occurrence) == _batch(occurrence)
    assert not conflict.direct_facts
    assert conflict.source_conflicts == 1


def test_sec_exact_qtd_and_ytd_source_rows_are_classified_without_fuzzy_mapping() -> None:
    payload = {
        "cik": 1,
        "facts": {
            "ifrs-full": {
                "FinanceIncome": {
                    "units": {
                        "USD": [
                            {
                                "val": 30,
                                "start": "2026-04-01",
                                "end": "2026-06-30",
                                "fy": 2026,
                                "fp": "Q2",
                                "form": "10-Q",
                                "filed": "2026-08-01",
                                "accn": "0001-26-000001",
                                "frame": "CY2026Q2",
                            },
                            {
                                "val": 50,
                                "start": "2026-01-01",
                                "end": "2026-06-30",
                                "fy": 2026,
                                "fp": "Q2",
                                "form": "10-Q",
                                "filed": "2026-08-01",
                                "accn": "0001-26-000001",
                                "frame": "CY2026Q2YTD",
                            },
                        ]
                    }
                },
                "IssuerSpecificFinanceIncome": {
                    "units": {"USD": []}
                },
            }
        },
    }
    batch = build_sec_non_operating_mapping_batch(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
        analysis_framework="manufacturing",
    )

    assert {fact.period.period_type.value for fact in batch.facts} == {"QTD", "YTD"}
    assert {fact.value for fact in batch.facts} == {Decimal(30), Decimal(50)}


def _xbrl_fact(
    tag: str,
    value: str,
    *,
    context_id: str,
    start: date,
) -> XbrlFact:
    return XbrlFact(
        taxonomy_element=f"{{https://xbrl.ifrs.org}}{tag}",
        context_ref=context_id,
        unit_ref="KRW",
        value=value,
        context=XbrlContext(
            context_id=context_id,
            entity_identifier="00126380",
            period_type="duration",
            period_start=start,
            period_end=date(2026, 6, 30),
            dimensions=(),
            statement_basis="consolidated",
        ),
    )


def _dart_row(tag: str, qtd: str, ytd: str) -> dict[str, object]:
    return {
        "account_id": f"ifrs-full_{tag}",
        "bsns_year": "2026",
        "corp_code": "00126380",
        "currency": "KRW",
        "fs_div": "CFS",
        "rcept_no": "20260814000001",
        "reprt_code": "11012",
        "sj_div": "CIS",
        "thstrm_amount": qtd,
        "thstrm_add_amount": ytd,
    }


def test_opendart_exact_context_promotes_qtd_ytd_and_safe_net() -> None:
    filing = Filing(
        ticker="005930",
        corp_code="00126380",
        company_name="fixture",
        receipt_no="20260814000001",
        report_name="fixture",
        receipt_date=date(2026, 8, 14),
        business_year=2026,
        report_code="11012",
        correction=False,
    )
    rows = (
        _dart_row("FinanceIncome", "30", "50"),
        _dart_row("FinanceCosts", "10", "20"),
    )
    xbrl = (
        _xbrl_fact(
            "FinanceIncome",
            "30",
            context_id="income-qtd",
            start=date(2026, 4, 1),
        ),
        _xbrl_fact(
            "FinanceIncome",
            "50",
            context_id="income-ytd",
            start=date(2026, 1, 1),
        ),
        _xbrl_fact(
            "FinanceCosts",
            "10",
            context_id="cost-qtd",
            start=date(2026, 4, 1),
        ),
        _xbrl_fact(
            "FinanceCosts",
            "20",
            context_id="cost-ytd",
            start=date(2026, 1, 1),
        ),
    )
    batch = promote_opendart_non_operating_facts(
        filing,
        {"CFS": list(rows), "OFS": []},
        xbrl,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
        analysis_framework="manufacturing",
    )

    assert len(batch.direct_facts) == 4
    assert len(batch.derived_facts) == 2
    assert {fact.period.period_type.value for fact in batch.derived_facts} == {
        "QTD",
        "YTD",
    }
    assert {fact.value for fact in batch.derived_facts} == {Decimal(20), Decimal(30)}


def test_opendart_fuzzy_name_and_nonunique_context_do_not_promote() -> None:
    filing = Filing(
        ticker="005930",
        corp_code="00126380",
        company_name="fixture",
        receipt_no="20260814000001",
        report_name="fixture",
        receipt_date=date(2026, 8, 14),
        business_year=2026,
        report_code="11012",
        correction=False,
    )
    fuzzy = _dart_row("IssuerFinanceIncome", "30", "50")
    exact = _dart_row("FinanceIncome", "30", "50")
    duplicate_contexts = (
        _xbrl_fact(
            "FinanceIncome",
            "30",
            context_id="one",
            start=date(2026, 4, 1),
        ),
        _xbrl_fact(
            "FinanceIncome",
            "30",
            context_id="two",
            start=date(2026, 4, 1),
        ),
    )
    batch = promote_opendart_non_operating_facts(
        filing,
        {"CFS": [fuzzy, exact], "OFS": []},
        duplicate_contexts,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
        analysis_framework="manufacturing",
    )

    assert not batch.facts
    assert batch.source_candidates == 2
    assert {item["reason"] for item in batch.denials} == {
        "exact_context_unresolved"
    }


def test_direct_adapter_preserves_metric_period_and_limitations() -> None:
    fact = _batch(_occurrence("OtherGains", "9", namespace="dart")).facts[0]
    result = _context(fact, (fact,))

    assert result.denial_reasons == ()
    assert result.context is not None
    assert result.context["metric"] == "other_income_context"
    assert result.context["period"]["type"] == "QTD"
    assert "broad_other_context_not_specific" in result.context["limitations"]
    assert "not_normalized_earnings" in result.context["limitations"]


def test_adapter_rejects_tampered_net_arithmetic_and_scope() -> None:
    batch = _batch(
        _occurrence("FinanceIncome", "100"),
        _occurrence("FinanceCosts", "40"),
    )
    rows = project_financial_fact_catalog(batch.facts, context_id="m11-tamper")
    net_row = next(
        row
        for row in rows
        if row["fact_type"] == "income_statement_net_financial_income_effect"
    )
    tampered_value = dict(net_row)
    tampered_value["fields"] = {**net_row["fields"], "value": 61}
    tampered_scope = dict(net_row)
    tampered_scope["fields"] = {
        **net_row["fields"],
        "financial_effect_scope": "child_components_incomplete",
    }
    tampered_role = dict(net_row)
    tampered_role["fields"] = {
        **net_row["fields"],
        "economic_role": "INCOME",
    }
    tampered_presentation = dict(net_row)
    tampered_presentation["fields"] = {
        **net_row["fields"],
        "presentation_type": "DIRECT_AGGREGATE",
    }
    tampered_continuity = dict(net_row)
    tampered_continuity["fields"] = {
        **net_row["fields"],
        "continuity_scope": "continuing_operations",
    }

    value_result = adapt_fact_catalog_financial_context(tampered_value, rows)
    scope_result = adapt_fact_catalog_financial_context(tampered_scope, rows)
    role_result = adapt_fact_catalog_financial_context(tampered_role, rows)
    presentation_result = adapt_fact_catalog_financial_context(
        tampered_presentation,
        rows,
    )
    continuity_result = adapt_fact_catalog_financial_context(
        tampered_continuity,
        rows,
    )
    assert value_result.context is None
    assert any("mismatch" in reason for reason in value_result.denial_reasons)
    assert scope_result.context is None
    assert any("mismatch" in reason for reason in scope_result.denial_reasons)
    assert role_result.context is None
    assert any("economic_role" in reason for reason in role_result.denial_reasons)
    assert presentation_result.context is None
    assert any(
        "presentation_type" in reason
        for reason in presentation_result.denial_reasons
    )
    assert continuity_result.context is None
    assert any(
        "continuity_scope" in reason
        for reason in continuity_result.denial_reasons
    )


def test_safe_prior_year_comparison_requires_matching_period_and_semantic() -> None:
    current = _occurrence("FinanceIncome", "100")
    prior = _occurrence(
        "FinanceIncome",
        "80",
        start=date(2025, 4, 1),
        end=date(2025, 6, 30),
        fiscal_year=2025,
        document="0001-25-000001",
        filed=date(2025, 8, 1),
        frame="CY2025Q2",
    )
    facts = _batch(current, prior).facts
    current_fact = max(facts, key=lambda fact: fact.period.end)
    result = _context(current_fact, facts)

    assert result.context is not None
    assert result.context["comparison"]["kind"] == "prior_year_comparable"

    ytd_prior = replace(prior, period_start=date(2025, 1, 1), frame="CY2025Q2YTD")
    mixed = _batch(current, ytd_prior).facts
    mixed_result = _context(max(mixed, key=lambda fact: fact.period.end), mixed)
    assert mixed_result.context is not None
    assert mixed_result.context["comparison"] is None


def test_financial_context_extension_does_not_change_compact_ai_context() -> None:
    batch = _batch(
        _occurrence("FinanceIncome", "100"),
        _occurrence("FinanceCosts", "40"),
    )
    rows = project_financial_fact_catalog(batch.facts, context_id="m11-non-leak")
    enriched = build_decision_evidence_packet(
        packet={
            "packet_id": "m11-non-leak",
            "market": "us",
            "assessment_date": "2026-09-09",
        },
        stock={"ticker": "M11", "fact_catalog": rows},
    )
    legacy = enriched.model_copy(
        update={
            "evidence": tuple(
                ref.model_copy(update={"financial_context": None})
                for ref in enriched.evidence
            )
        }
    )

    assert compact_ai_context(enriched) == compact_ai_context(legacy)


def test_no_forbidden_derived_metrics_are_created() -> None:
    batch = _batch(
        _occurrence("FinanceIncome", "100"),
        _occurrence("FinanceCosts", "40"),
        _occurrence("OtherGains", "9", namespace="dart"),
        _occurrence("OtherLosses", "8", namespace="dart"),
        _occurrence("IncomeTaxExpenseContinuingOperations", "25"),
    )

    assert {fact.derivation_formula for fact in batch.derived_facts} == {
        NET_FINANCIAL_EFFECT_FORMULA
    }
    assert not {
        "net_non_operating_effect",
        "normalized_net_income",
        "adjusted_net_income",
        "normalized_eps",
        "effective_tax_rate",
        "reconstructed_operating_profit",
        "recurring_earnings_score",
    }.intersection({fact.metric.value for fact in batch.facts})
