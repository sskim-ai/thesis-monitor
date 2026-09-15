from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.services.cash_flow_capital_efficiency_service import Metric
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
from app.services.opendart_financial_recovery_service import Filing
from app.services.opendart_xbrl_service import XbrlContext, XbrlFact
from app.services.working_capital_evidence_service import OfficialFinancialOccurrence
from app.services.working_capital_financial_mapping_service import (
    BALANCE_DELTA_FORMULA,
    CONTRACT_ASSET_POLICY,
    CONTRACT_LIABILITY_POLICY,
    CONTRACT_VERSION,
    NO_WORKING_CAPITAL_FORMULA_POLICY,
    ComparisonKind,
    SectorRoute,
    build_sec_working_capital_mapping_batch,
    build_working_capital_mapping_batch,
    canonicalize_working_capital_occurrences,
    comparison_compatibility_reasons,
    derive_balance_absolute_delta,
    derive_safe_balance_deltas,
    promote_opendart_working_capital_facts,
    registry_audit,
    sector_route,
)


RAW_SHA = "a" * 64


def _occurrence(
    *,
    namespace: str = "us-gaap",
    tag: str = "InventoryNet",
    value: str = "100",
    end: date = date(2026, 6, 30),
    fiscal_year: int = 2026,
    fiscal_period: str = "Q2",
    currency: str | None = "USD",
    unit: str | None = "USD",
    entity_scope: str | None = "issuer_level",
    statement_basis: str | None = "consolidated",
    accession: str = "0001-26-000001",
    filed: date = date(2026, 8, 1),
    frame: str | None = "CY2026Q2I",
    source_column: str = "val",
) -> OfficialFinancialOccurrence:
    return OfficialFinancialOccurrence(
        issuer_id="sec:0000000001",
        value=Decimal(value),
        currency=currency,
        unit=unit,
        period_start=None,
        period_end=end,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        source_provider="sec_edgar_companyfacts",
        source_document_id=accession,
        source_document_type="10-Q" if fiscal_period != "FY" else "10-K",
        filing_date=filed,
        namespace=namespace,
        tag=tag,
        raw_payload_sha256=RAW_SHA,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
        frame=frame,
        source_column=source_column,
    )


def _facts(*occurrences: OfficialFinancialOccurrence):
    facts = canonicalize_working_capital_occurrences(
        occurrences,
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    ).direct_facts
    return tuple(sorted(facts, key=lambda fact: fact.period.end, reverse=True))


def _context_for_fact(fact, all_facts):
    rows = project_financial_fact_catalog(
        all_facts,
        context_id="m10-test",
    )
    row = next(item for item in rows if item["fact_id"] == fact.fact_id)
    return adapt_fact_catalog_financial_context(row, rows)


def test_contract_and_registry_are_exact_and_ticker_neutral() -> None:
    rows = registry_audit()

    assert CONTRACT_VERSION == "inventory-receivables-working-capital-v1"
    assert CONTRACT_ASSET_POLICY == "SEPARATE_WORKING_CAPITAL_CONTEXT"
    assert CONTRACT_LIABILITY_POLICY == "SEPARATE_WORKING_CAPITAL_CONTEXT"
    assert NO_WORKING_CAPITAL_FORMULA_POLICY == (
        "NO_UNIVERSAL_OPERATING_WORKING_CAPITAL"
    )
    assert rows
    assert len({row["source_semantic"] for row in rows}) == len(rows)
    assert all("ticker" not in row for row in rows)


def test_inventory_aggregate_takes_precedence_over_components() -> None:
    batch = build_working_capital_mapping_batch(
        (
            _occurrence(tag="InventoryNet", value="120"),
            _occurrence(tag="InventoryRawMaterials", value="40"),
            _occurrence(tag="InventoryWorkInProcess", value="30"),
            _occurrence(tag="InventoryFinishedGoods", value="50"),
        ),
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )

    assert [(fact.metric, fact.value) for fact in batch.direct_facts] == [
        (Metric.INVENTORY, Decimal(120))
    ]
    assert batch.aggregate_precedence_count == 3
    assert batch.overlap_conflict_count == 1
    assert batch.overlap_blocked_count == 3
    assert sum(
        denial["reason"] == "aggregate_child_overlap" for denial in batch.denials
    ) == 3


def test_inventory_components_remain_separate_without_aggregate() -> None:
    facts = _facts(
        _occurrence(tag="InventoryRawMaterials", value="40"),
        _occurrence(tag="InventoryWorkInProcess", value="30"),
        _occurrence(tag="InventoryFinishedGoods", value="50"),
    )

    assert {fact.balance_scope for fact in facts} == {
        "inventory_raw_materials",
        "inventory_work_in_process",
        "inventory_finished_goods",
    }
    assert {fact.metric for fact in facts} == {Metric.INVENTORY_COMPONENT}


def test_trade_broad_current_and_contract_balances_stay_distinct() -> None:
    facts = _facts(
        _occurrence(tag="AccountsReceivableTradeCurrent", value="80"),
        _occurrence(tag="AccountsReceivableNetCurrent", value="90"),
        _occurrence(tag="AccountsPayableTradeCurrent", value="40"),
        _occurrence(tag="AccountsPayableCurrent", value="60"),
        _occurrence(tag="AssetsCurrent", value="400"),
        _occurrence(tag="LiabilitiesCurrent", value="250"),
        _occurrence(tag="ContractWithCustomerAssetNetCurrent", value="20"),
        _occurrence(tag="ContractWithCustomerLiabilityCurrent", value="25"),
    )

    assert {fact.metric for fact in facts} == {
        Metric.TRADE_AR,
        Metric.BROAD_AR,
        Metric.TRADE_AP,
        Metric.BROAD_AP,
        Metric.CURRENT_ASSETS,
        Metric.CURRENT_LIABILITIES,
        Metric.CONTRACT_ASSETS,
        Metric.CONTRACT_LIABILITIES,
    }
    assert next(fact for fact in facts if fact.metric == Metric.BROAD_AR).cautions == (
        "broad_receivable_context",
        "broad_balance_not_trade_only",
    )
    assert "separate_working_capital_context_only" in next(
        fact for fact in facts if fact.metric == Metric.CONTRACT_ASSETS
    ).cautions


def test_net_receivables_precede_same_scope_gross_receivables() -> None:
    batch = canonicalize_working_capital_occurrences(
        (
            _occurrence(tag="AccountsReceivableNetCurrent", value="80"),
            _occurrence(tag="AccountsReceivableGrossCurrent", value="90"),
        ),
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )

    assert len(batch.direct_facts) == 1
    assert batch.direct_facts[0].net_gross_scope == "net"
    assert batch.gross_net_precedence_count == 1
    assert batch.overlap_blocked_count == 1
    assert batch.denials[-1]["reason"] == "gross_net_basis_mismatch"


def test_unsupported_and_nontrade_semantics_are_not_fuzzily_promoted() -> None:
    batch = canonicalize_working_capital_occurrences(
        (
            _occurrence(tag="EntitySpecificInventory", value="1"),
            _occurrence(
                namespace="ifrs-full", tag="OtherCurrentReceivables", value="2"
            ),
            _occurrence(namespace="ifrs-full", tag="LoansReceivable", value="3"),
            _occurrence(namespace="ifrs-full", tag="Assets", value="4"),
            _occurrence(namespace="ifrs-full", tag="Liabilities", value="5"),
        ),
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )

    assert not batch.direct_facts
    assert {denial["reason"] for denial in batch.denials} == {
        "unsupported_semantic",
        "broad_receivable_not_trade",
        "loan_receivable_not_trade",
        "total_assets_not_inventory",
        "total_liabilities_not_trade_payables",
    }


def test_sector_routing_blocks_financials_and_preserves_context_only() -> None:
    financial = canonicalize_working_capital_occurrences(
        (_occurrence(),),
        as_of_date=date(2026, 9, 9),
        analysis_framework="insurance",
    )
    context = canonicalize_working_capital_occurrences(
        (_occurrence(tag="AccountsReceivableTradeCurrent"),),
        as_of_date=date(2026, 9, 9),
        analysis_framework="saas",
    )

    assert sector_route("bank") == SectorRoute.SECTOR_FRAMEWORK_REQUIRED
    assert financial.sector_route == SectorRoute.SECTOR_FRAMEWORK_REQUIRED
    assert not financial.direct_facts
    assert {item["reason"] for item in financial.denials} == {
        "sector_not_applicable"
    }
    assert context.sector_route == SectorRoute.CONTEXT_ONLY
    assert "sector_context_only" in context.direct_facts[0].cautions


def test_missing_point_currency_entity_or_basis_fails_closed() -> None:
    cases = (
        replace(_occurrence(), period_end=None),
        _occurrence(currency=None, unit=None),
        _occurrence(entity_scope=None),
        _occurrence(statement_basis=None),
    )

    for occurrence in cases:
        batch = canonicalize_working_capital_occurrences(
            (occurrence,),
            as_of_date=date(2026, 9, 9),
            analysis_framework="manufacturing",
        )
        assert not batch.direct_facts


def test_prior_year_comparable_delta_is_exact_and_adapter_lineaged() -> None:
    current, prior = _facts(
        _occurrence(value="130"),
        _occurrence(
            value="100",
            end=date(2025, 6, 30),
            fiscal_year=2025,
            accession="0001-25-000001",
            filed=date(2025, 8, 1),
            frame="CY2025Q2I",
        ),
    )
    delta, reasons = derive_balance_absolute_delta(
        current,
        prior,
        comparison_kind=ComparisonKind.PRIOR_YEAR_COMPARABLE,
        as_of_date=date(2026, 9, 9),
    )

    assert not reasons
    assert delta is not None
    assert delta.value == Decimal(30)
    assert delta.derivation_formula == BALANCE_DELTA_FORMULA
    assert delta.input_fact_ids == (current.fact_id, prior.fact_id)
    assert delta.comparison_kind == "prior_year_comparable"
    adapted = _context_for_fact(delta, (current, prior, delta))
    assert adapted.denial_reasons == ()
    assert adapted.context is not None
    assert adapted.context["comparison"]["kind"] == "prior_year_comparable"
    assert adapted.context["derivation"]["input_source_refs"] == [
        f"stock.fact_catalog.{current.fact_id}",
        f"stock.fact_catalog.{prior.fact_id}",
    ]


def test_prior_year_end_delta_is_not_labeled_yoy() -> None:
    current, prior = _facts(
        _occurrence(value="130"),
        _occurrence(
            value="110",
            end=date(2025, 12, 31),
            fiscal_year=2025,
            fiscal_period="FY",
            accession="0001-25-000010",
            filed=date(2026, 2, 1),
            frame="CY2025I",
        ),
    )
    delta, reasons = derive_balance_absolute_delta(
        current,
        prior,
        comparison_kind=ComparisonKind.PRIOR_YEAR_END,
        as_of_date=date(2026, 9, 9),
    )

    assert not reasons
    assert delta is not None
    assert delta.comparison_kind == "prior_year_end"
    adapted = _context_for_fact(delta, (current, prior, delta))
    assert adapted.context is not None
    assert adapted.context["comparison"]["kind"] == "prior_year_end"


def test_year_end_to_interim_cannot_be_prior_year_comparable() -> None:
    current, prior = _facts(
        _occurrence(),
        _occurrence(
            end=date(2025, 12, 31),
            fiscal_year=2025,
            fiscal_period="FY",
            accession="0001-25-000010",
            filed=date(2026, 2, 1),
            frame="CY2025I",
        ),
    )

    reasons = comparison_compatibility_reasons(
        current,
        prior,
        ComparisonKind.PRIOR_YEAR_COMPARABLE,
    )

    assert "fiscal_quarter_mismatch" in reasons
    assert "point_in_time_mismatch" in reasons


def test_gross_to_net_currency_entity_and_basis_comparisons_fail() -> None:
    current, prior = _facts(
        _occurrence(tag="AccountsReceivableNetCurrent", value="100"),
        _occurrence(
            tag="AccountsReceivableNetCurrent",
            value="80",
            end=date(2025, 6, 30),
            fiscal_year=2025,
            accession="0001-25-000001",
            filed=date(2025, 8, 1),
            frame="CY2025Q2I",
        ),
    )
    mutations = (
        replace(prior, net_gross_scope="gross"),
        replace(prior, currency="EUR", unit="EUR"),
        replace(prior, entity_scope="parent_only"),
        replace(prior, statement_basis="separate"),
    )

    for mutation in mutations:
        delta, reasons = derive_balance_absolute_delta(
            current,
            mutation,
            comparison_kind=ComparisonKind.PRIOR_YEAR_COMPARABLE,
            as_of_date=date(2026, 9, 9),
        )
        assert delta is None
        assert reasons


def test_safe_selector_prefers_prior_year_comparable_over_year_end() -> None:
    facts = _facts(
        _occurrence(value="130"),
        _occurrence(
            value="100",
            end=date(2025, 6, 30),
            fiscal_year=2025,
            accession="0001-25-000001",
            filed=date(2025, 8, 1),
            frame="CY2025Q2I",
        ),
        _occurrence(
            value="110",
            end=date(2025, 12, 31),
            fiscal_year=2025,
            fiscal_period="FY",
            accession="0001-25-000010",
            filed=date(2026, 2, 1),
            frame="CY2025I",
        ),
    )

    derived, denials = derive_safe_balance_deltas(
        facts,
        as_of_date=date(2026, 9, 9),
    )

    assert not denials
    assert len(derived) == 1
    assert derived[0].comparison_kind == "prior_year_comparable"
    assert derived[0].value == Decimal(30)


def test_direct_adapter_uses_year_end_kind_when_comparable_is_absent() -> None:
    current, prior = _facts(
        _occurrence(value="130"),
        _occurrence(
            value="110",
            end=date(2025, 12, 31),
            fiscal_year=2025,
            fiscal_period="FY",
            accession="0001-25-000010",
            filed=date(2026, 2, 1),
            frame="CY2025I",
        ),
    )

    adapted = _context_for_fact(current, (current, prior))

    assert adapted.context is not None
    assert adapted.context["comparison"]["kind"] == "prior_year_end"


def test_tampered_delta_arithmetic_fails_adapter() -> None:
    current, prior = _facts(
        _occurrence(value="130"),
        _occurrence(
            value="100",
            end=date(2025, 6, 30),
            fiscal_year=2025,
            accession="0001-25-000001",
            filed=date(2025, 8, 1),
            frame="CY2025Q2I",
        ),
    )
    delta, _ = derive_balance_absolute_delta(
        current,
        prior,
        comparison_kind=ComparisonKind.PRIOR_YEAR_COMPARABLE,
        as_of_date=date(2026, 9, 9),
    )
    assert delta is not None
    tampered = replace(delta, value=Decimal(31))

    adapted = _context_for_fact(tampered, (current, prior, tampered))

    assert adapted.context is None
    assert "working_capital_delta_arithmetic_mismatch" in adapted.denial_reasons


def test_sec_source_class_mapping_is_exact_and_idempotent() -> None:
    payload = {
        "cik": 1,
        "facts": {
            "us-gaap": {
                "InventoryNet": {
                    "units": {
                        "USD": [
                            {
                                "val": 120,
                                "end": "2026-06-30",
                                "filed": "2026-08-01",
                                "accn": "0001-26-000001",
                                "form": "10-Q",
                                "fy": 2026,
                                "fp": "Q2",
                                "frame": "CY2026Q2I",
                            },
                            {
                                "val": 100,
                                "end": "2025-06-30",
                                "filed": "2025-08-01",
                                "accn": "0001-25-000001",
                                "form": "10-Q",
                                "fy": 2025,
                                "fp": "Q2",
                                "frame": "CY2025Q2I",
                            },
                        ]
                    }
                },
                "EntitySpecificInventory": {
                    "units": {
                        "USD": [
                            {
                                "val": 999,
                                "end": "2026-06-30",
                                "filed": "2026-08-01",
                                "accn": "0001-26-000001",
                                "form": "10-Q",
                                "fy": 2026,
                                "fp": "Q2",
                            }
                        ]
                    }
                },
            }
        },
    }

    first = build_sec_working_capital_mapping_batch(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )
    second = build_sec_working_capital_mapping_batch(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )

    assert [fact.fact_id for fact in first.facts] == [
        fact.fact_id for fact in second.facts
    ]
    assert len(first.direct_facts) == 2
    assert len(first.derived_facts) == 1
    assert first.derived_facts[0].comparison_kind == "prior_year_comparable"
    assert all("EntitySpecificInventory" not in fact.semantic_mapping for fact in first.facts)


def _xbrl_fact(
    *,
    taxonomy_element: str,
    context_id: str,
    value: str,
    end: date,
    corp_code: str,
) -> XbrlFact:
    context = XbrlContext(
        context_id=context_id,
        entity_identifier=corp_code,
        period_type="instant",
        period_start=end,
        period_end=end,
        dimensions=(("StatementBasisAxis", "ConsolidatedMember"),),
        statement_basis="consolidated",
    )
    return XbrlFact(
        taxonomy_element=taxonomy_element,
        context_ref=context_id,
        unit_ref="KRW",
        value=value,
        context=context,
    )


def test_opendart_exact_current_and_prior_year_end_contexts_are_promoted() -> None:
    corp_code = "00126380"
    receipt = "20260814003699"
    filing = Filing(
        ticker="005930",
        corp_code=corp_code,
        company_name="Samsung Electronics",
        receipt_no=receipt,
        report_name="semiannual report",
        receipt_date=date(2026, 8, 14),
        business_year=2026,
        report_code="11012",
        correction=False,
    )
    rows = [
        {
            "account_id": "ifrs-full_Inventories",
            "account_nm": "inventories",
            "sj_div": "BS",
            "fs_div": "CFS",
            "rcept_no": receipt,
            "reprt_code": "11012",
            "bsns_year": "2026",
            "corp_code": corp_code,
            "currency": "KRW",
            "thstrm_amount": "130",
            "frmtrm_amount": "110",
        },
        {
            "account_id": "ifrs-full_CurrentTradeReceivables",
            "account_nm": "trade receivables",
            "sj_div": "BS",
            "fs_div": "CFS",
            "rcept_no": receipt,
            "reprt_code": "11012",
            "bsns_year": "2026",
            "corp_code": corp_code,
            "currency": "KRW",
            "thstrm_amount": "80",
            "frmtrm_amount": "70",
        },
    ]
    xbrl_facts = (
        _xbrl_fact(
            taxonomy_element="Inventories",
            context_id="current",
            value="130",
            end=date(2026, 6, 30),
            corp_code=corp_code,
        ),
        _xbrl_fact(
            taxonomy_element="CurrentTradeReceivables",
            context_id="current-trade-ar",
            value="80",
            end=date(2026, 6, 30),
            corp_code=corp_code,
        ),
        _xbrl_fact(
            taxonomy_element="CurrentTradeReceivables",
            context_id="prior-year-end-trade-ar",
            value="70",
            end=date(2025, 12, 31),
            corp_code=corp_code,
        ),
        _xbrl_fact(
            taxonomy_element="Inventories",
            context_id="prior-year-end",
            value="110",
            end=date(2025, 12, 31),
            corp_code=corp_code,
        ),
    )

    batch = promote_opendart_working_capital_facts(
        filing,
        {"CFS": rows, "OFS": []},
        xbrl_facts,
        raw_payload_sha256=RAW_SHA,
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )

    assert len(batch.direct_facts) == 4
    assert {fact.period.end for fact in batch.direct_facts} == {
        date(2026, 6, 30),
        date(2025, 12, 31),
    }
    assert {fact.metric for fact in batch.direct_facts} == {
        Metric.INVENTORY,
        Metric.TRADE_AR,
    }
    assert len(batch.derived_facts) == 2
    assert {fact.comparison_kind for fact in batch.derived_facts} == {
        "prior_year_end"
    }
    assert {fact.value for fact in batch.derived_facts} == {
        Decimal(10),
        Decimal(20),
    }


def test_opendart_account_name_does_not_create_fuzzy_mapping() -> None:
    filing = Filing(
        ticker="005930",
        corp_code="00126380",
        company_name="Samsung Electronics",
        receipt_no="20260814003699",
        report_name="semiannual report",
        receipt_date=date(2026, 8, 14),
        business_year=2026,
        report_code="11012",
        correction=False,
    )
    rows = [
        {
            "account_id": "entity_CustomBalance",
            "account_nm": "inventories and receivables",
            "sj_div": "BS",
            "fs_div": "CFS",
            "rcept_no": filing.receipt_no,
            "reprt_code": filing.report_code,
            "bsns_year": "2026",
            "corp_code": "00126380",
            "currency": "KRW",
            "thstrm_amount": "130",
        }
    ]

    batch = promote_opendart_working_capital_facts(
        filing,
        {"CFS": rows, "OFS": []},
        (),
        raw_payload_sha256=RAW_SHA,
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )

    assert batch.source_candidates == 0
    assert not batch.facts


def test_no_nwc_or_efficiency_ratio_is_derived() -> None:
    batch = build_working_capital_mapping_batch(
        (
            _occurrence(tag="AssetsCurrent", value="400"),
            _occurrence(tag="LiabilitiesCurrent", value="250"),
            _occurrence(tag="AccountsReceivableTradeCurrent", value="80"),
            _occurrence(tag="InventoryNet", value="120"),
            _occurrence(tag="AccountsPayableTradeCurrent", value="40"),
        ),
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )

    forbidden = {
        Metric.DSO,
        Metric.INVENTORY_DAYS,
        Metric.DPO,
        Metric.CCC,
    }
    assert not forbidden.intersection({fact.metric for fact in batch.facts})
    assert all(fact.metric != Metric.BALANCE_DELTA for fact in batch.facts)
    assert all(
        fact.derivation_formula not in {"net_working_capital", "operating_working_capital"}
        for fact in batch.facts
    )


def test_financial_context_does_not_leak_into_compact_ai_context() -> None:
    current, prior = _facts(
        _occurrence(value="130"),
        _occurrence(
            value="100",
            end=date(2025, 6, 30),
            fiscal_year=2025,
            accession="0001-25-000001",
            filed=date(2025, 8, 1),
            frame="CY2025Q2I",
        ),
    )
    delta, _ = derive_balance_absolute_delta(
        current,
        prior,
        comparison_kind=ComparisonKind.PRIOR_YEAR_COMPARABLE,
        as_of_date=date(2026, 9, 9),
    )
    assert delta is not None
    rows = project_financial_fact_catalog(
        (current, prior, delta),
        context_id="m10-compact-non-leak",
    )
    enriched = build_decision_evidence_packet(
        packet={
            "packet_id": "m10-compact-non-leak",
            "market": "us",
            "assessment_date": "2026-09-09",
        },
        stock={"ticker": "M10FIXTURE", "fact_catalog": rows},
    )
    legacy = enriched.model_copy(
        update={
            "evidence": tuple(
                ref.model_copy(update={"financial_context": None})
                for ref in enriched.evidence
            )
        }
    )

    assert any(ref.financial_context is not None for ref in enriched.evidence)
    assert compact_ai_context(enriched) == compact_ai_context(legacy)
