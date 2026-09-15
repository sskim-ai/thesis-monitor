from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FactType,
    Metric,
    PeriodType,
)
from app.services.cross_market_decision_engine_service import (
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.debt_liquidity_financial_mapping_service import (
    CONTRACT_VERSION,
    DEBT_SCOPE,
    LEASE_LIABILITY_POLICY,
    NET_DEBT_SCOPE,
    RESTRICTED_CASH_POLICY,
    DebtCompletenessAssessment,
    DebtCompletenessStatus,
    SectorRoute,
    assess_debt_completeness,
    build_debt_liquidity_batch,
    build_sec_debt_liquidity_batch,
    canonicalize_debt_liquidity_occurrences,
    derive_interest_bearing_debt_total,
    derive_net_debt,
    promote_opendart_debt_liquidity_facts,
)
from app.services.financial_context_adapter_service import (
    adapt_fact_catalog_financial_context,
)
from app.services.financial_lineage_projection_service import (
    project_financial_fact_catalog,
)
from app.services.opendart_financial_recovery_service import Filing
from app.services.opendart_xbrl_service import parse_xbrl_document
from app.services.working_capital_evidence_service import OfficialFinancialOccurrence


AS_OF = date(2026, 9, 8)
RAW_SHA = "a" * 64


def _occurrence(
    semantic: str,
    value: str,
    *,
    period_end: date = date(2026, 6, 30),
    currency: str | None = "USD",
    unit: str | None = "USD",
    entity_scope: str | None = "issuer_level",
    statement_basis: str | None = "issuer_reported_balance_sheet",
    document: str = "0000000000-26-000001",
    provider: str = "sec_edgar_companyfacts",
) -> OfficialFinancialOccurrence:
    namespace, tag = semantic.split(":", maxsplit=1)
    return OfficialFinancialOccurrence(
        issuer_id="sec:0000000001",
        value=Decimal(value),
        currency=currency,
        unit=unit,
        period_start=None,
        period_end=period_end,
        fiscal_year=2026,
        fiscal_period="Q2",
        source_provider=provider,
        source_document_id=document,
        source_document_type="10-Q",
        filing_date=date(2026, 8, 1),
        namespace=namespace,
        tag=tag,
        raw_payload_sha256=RAW_SHA,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
        frame="CY2026Q2I",
        source_column="val",
    )


def _positive_occurrences(*, cash: str = "600") -> tuple[OfficialFinancialOccurrence, ...]:
    return (
        _occurrence("us-gaap:CashAndCashEquivalentsAtCarryingValue", cash),
        _occurrence("us-gaap:ShortTermBorrowings", "100"),
        _occurrence("us-gaap:LongTermDebtNoncurrent", "400"),
    )


def _positive_batch(*, cash: str = "600"):
    return build_debt_liquidity_batch(
        _positive_occurrences(cash=cash),
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )


def test_complete_direct_components_derive_total_and_negative_net_debt() -> None:
    batch = _positive_batch()
    by_metric = {fact.metric: fact for fact in batch.facts}

    assert batch.completeness.status == DebtCompletenessStatus.COMPLETE
    assert batch.sector_route == SectorRoute.GENERIC_OPERATING_COMPANY
    assert by_metric[Metric.INTEREST_BEARING_DEBT_TOTAL].value == Decimal("500")
    assert by_metric[Metric.NET_DEBT].value == Decimal("-100")
    assert by_metric[Metric.INTEREST_BEARING_DEBT_TOTAL].balance_scope == DEBT_SCOPE
    assert by_metric[Metric.NET_DEBT].balance_scope == NET_DEBT_SCOPE
    assert by_metric[Metric.NET_DEBT].input_fact_ids == (
        by_metric[Metric.INTEREST_BEARING_DEBT_TOTAL].fact_id,
        by_metric[Metric.CASH_AND_CASH_EQUIVALENTS].fact_id,
    )
    assert all(fact.period.period_type == PeriodType.POINT_IN_TIME for fact in batch.facts)
    assert all(fact.period.start == fact.period.end for fact in batch.facts)
    assert LEASE_LIABILITY_POLICY == "SEPARATE_CONTEXT_ONLY"
    assert RESTRICTED_CASH_POLICY == "EXCLUDE_FROM_NET_DEBT_CASH_BASIS"


def test_unit_scale_is_normalized_before_derived_arithmetic() -> None:
    occurrences = tuple(
        replace(item, unit="thousand usd", currency="USD")
        for item in _positive_occurrences(cash="200")
    )

    batch = build_debt_liquidity_batch(
        occurrences,
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )
    by_metric = {fact.metric: fact for fact in batch.facts}

    assert by_metric[Metric.INTEREST_BEARING_DEBT_TOTAL].value == Decimal("500000")
    assert by_metric[Metric.NET_DEBT].value == Decimal("300000")
    assert {fact.unit for fact in batch.facts} == {"USD"}


@pytest.mark.parametrize(
    "semantic",
    (
        "us-gaap:Liabilities",
        "us-gaap:LiabilitiesCurrent",
        "ifrs-full:NoncurrentLiabilities",
    ),
)
def test_total_liabilities_never_become_interest_bearing_debt(semantic: str) -> None:
    batch = build_debt_liquidity_batch(
        (
            _occurrence(semantic, "900"),
            _occurrence("us-gaap:CashAndCashEquivalentsAtCarryingValue", "100"),
        ),
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )

    assert all(fact.metric not in {Metric.INTEREST_BEARING_DEBT_TOTAL, Metric.NET_DEBT} for fact in batch.facts)
    assert "total_liabilities_not_interest_bearing_debt" in {
        denial["reason"] for denial in batch.denials
    }
    assert batch.completeness.status == DebtCompletenessStatus.UNKNOWN


def test_incomplete_scope_and_basis_mismatch_fail_closed() -> None:
    direct = canonicalize_debt_liquidity_occurrences(
        _positive_occurrences(),
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
    )
    components = [fact for fact in direct.facts if fact.metric != Metric.CASH_AND_CASH_EQUIVALENTS]
    incomplete = assess_debt_completeness(
        components,
        analysis_framework="standard_operating_company",
        statement_inventory_complete=False,
    )
    mismatched = assess_debt_completeness(
        [components[0], replace(components[1], statement_basis="separate")],
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )

    assert incomplete.status == DebtCompletenessStatus.UNKNOWN
    assert derive_interest_bearing_debt_total(components, incomplete)[0] is None
    assert mismatched.status == DebtCompletenessStatus.PARTIAL
    assert "statement_basis_mismatch" in mismatched.reasons


def test_current_only_components_are_not_labeled_total_debt() -> None:
    batch = build_debt_liquidity_batch(
        (
            _occurrence("us-gaap:CashAndCashEquivalentsAtCarryingValue", "100"),
            _occurrence("us-gaap:ShortTermBorrowings", "80"),
            _occurrence("us-gaap:LongTermDebtCurrent", "20"),
        ),
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )

    assert batch.completeness.status == DebtCompletenessStatus.PARTIAL
    assert batch.completeness.reasons == ("debt_scope_incomplete",)
    assert all(
        fact.metric not in {Metric.INTEREST_BEARING_DEBT_TOTAL, Metric.NET_DEBT}
        for fact in batch.facts
    )


def test_current_debt_aggregate_takes_precedence_over_children_without_double_count() -> None:
    batch = build_debt_liquidity_batch(
        (
            _occurrence("us-gaap:CashAndCashEquivalentsAtCarryingValue", "100"),
            _occurrence("us-gaap:DebtCurrent", "150"),
            _occurrence("us-gaap:ShortTermBorrowings", "100"),
            _occurrence("us-gaap:LongTermDebtCurrent", "50"),
            _occurrence("us-gaap:LongTermDebtNoncurrent", "400"),
        ),
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )
    by_metric = {fact.metric: fact for fact in batch.facts}

    assert batch.completeness.aggregate_precedence_count == 2
    assert by_metric[Metric.INTEREST_BEARING_DEBT_TOTAL].value == Decimal("550")
    assert len(by_metric[Metric.INTEREST_BEARING_DEBT_TOTAL].input_fact_ids) == 2


@pytest.mark.parametrize("framework", ("bank", "insurance", "reinsurance"))
def test_financial_sector_is_routed_away_from_industrial_net_debt(framework: str) -> None:
    batch = build_debt_liquidity_batch(
        _positive_occurrences(),
        as_of_date=AS_OF,
        analysis_framework=framework,
        statement_inventory_complete=True,
    )

    assert batch.facts == ()
    assert batch.completeness.status == DebtCompletenessStatus.NOT_APPLICABLE
    assert {denial["reason"] for denial in batch.denials} == {
        "financial_sector_not_applicable"
    }


def test_restricted_or_combined_cash_cannot_be_netted() -> None:
    debt_only = _positive_occurrences()[1:]
    for semantic in (
        "us-gaap:RestrictedCashAndCashEquivalentsCurrent",
        "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ):
        batch = build_debt_liquidity_batch(
            (*debt_only, _occurrence(semantic, "100")),
            as_of_date=AS_OF,
            analysis_framework="standard_operating_company",
            statement_inventory_complete=True,
        )
        assert any(fact.metric == Metric.INTEREST_BEARING_DEBT_TOTAL for fact in batch.facts)
        assert all(fact.metric != Metric.NET_DEBT for fact in batch.facts)
        assert any(denial["reason"] == "missing_cash" for denial in batch.denials)


def test_lease_liabilities_are_preserved_but_excluded_from_debt_total() -> None:
    batch = build_debt_liquidity_batch(
        (
            *_positive_occurrences(cash="100"),
            _occurrence("us-gaap:FinanceLeaseLiabilityCurrent", "25"),
            _occurrence("us-gaap:FinanceLeaseLiabilityNoncurrent", "75"),
        ),
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )
    by_metric = {fact.metric: fact for fact in batch.facts}

    assert by_metric[Metric.INTEREST_BEARING_DEBT_TOTAL].value == Decimal("500")
    assert by_metric[Metric.LEASE_LIABILITIES_CURRENT].value == Decimal("25")
    assert by_metric[Metric.LEASE_LIABILITIES_NONCURRENT].value == Decimal("75")


def test_date_currency_entity_and_statement_mismatches_block_net_debt() -> None:
    batch = _positive_batch(cash="100")
    by_metric = {fact.metric: fact for fact in batch.facts}
    debt = by_metric[Metric.INTEREST_BEARING_DEBT_TOTAL]
    cash = by_metric[Metric.CASH_AND_CASH_EQUIVALENTS]

    mutations = (
        replace(cash, period=replace(cash.period, start=date(2026, 3, 31), end=date(2026, 3, 31))),
        replace(cash, currency="KRW", unit="KRW"),
        replace(cash, entity_scope="parent_only"),
        replace(cash, statement_basis="separate"),
    )
    expected = (
        "point_in_time_mismatch",
        "currency_mismatch",
        "entity_scope_mismatch",
        "statement_basis_mismatch",
    )
    for changed, reason in zip(mutations, expected, strict=True):
        derived, reasons = derive_net_debt(debt, changed)
        assert derived is None
        assert reason in reasons


def test_holding_company_caution_and_idempotent_identity_are_preserved() -> None:
    first = build_debt_liquidity_batch(
        _positive_occurrences(),
        as_of_date=AS_OF,
        analysis_framework="holding_company",
        statement_inventory_complete=True,
        holding_company=True,
    )
    second = build_debt_liquidity_batch(
        _positive_occurrences(),
        as_of_date=AS_OF,
        analysis_framework="holding_company",
        statement_inventory_complete=True,
        holding_company=True,
    )

    assert first == second
    assert len({fact.fact_id for fact in first.facts}) == len(first.facts)
    assert all(
        "holding_company_parent_subsidiary_funding_separation_not_resolved"
        in fact.cautions
        for fact in first.direct_facts
    )


def test_sec_companyfacts_exact_semantics_build_complete_lineage() -> None:
    def rows(value: int) -> dict[str, list[dict[str, object]]]:
        return {
            "USD": [
                {
                    "val": value,
                    "end": "2026-06-30",
                    "fy": 2026,
                    "fp": "Q2",
                    "form": "10-Q",
                    "filed": "2026-08-01",
                    "accn": "0000000000-26-000001",
                    "frame": "CY2026Q2I",
                }
            ]
        }

    payload = {
        "cik": 1,
        "facts": {
            "us-gaap": {
                "CashAndCashEquivalentsAtCarryingValue": {"units": rows(200)},
                "ShortTermBorrowings": {"units": rows(100)},
                "LongTermDebtNoncurrent": {"units": rows(400)},
            }
        },
    }

    batch = build_sec_debt_liquidity_batch(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
    )

    assert batch.source_candidates == 3
    assert batch.completeness.status == DebtCompletenessStatus.COMPLETE
    assert {fact.metric for fact in batch.facts}.issuperset(
        {Metric.CASH_AND_CASH_EQUIVALENTS, Metric.INTEREST_BEARING_DEBT_TOTAL, Metric.NET_DEBT}
    )


def _opendart_filing() -> Filing:
    return Filing(
        ticker="GENERIC",
        corp_code="00123456",
        company_name="Generic",
        receipt_no="20260814000001",
        report_name="preserved formal filing",
        receipt_date=date(2026, 8, 14),
        business_year=2026,
        report_code="11012",
        correction=False,
    )


def _opendart_row(account_id: str, value: str, ordinal: str) -> dict[str, object]:
    return {
        "corp_code": "00123456",
        "rcept_no": "20260814000001",
        "reprt_code": "11012",
        "bsns_year": "2026",
        "fs_div": "CFS",
        "sj_div": "BS",
        "account_id": account_id,
        "account_nm": "exact balance-sheet fixture",
        "account_detail": "-",
        "thstrm_amount": value,
        "currency": "KRW",
        "ord": ordinal,
    }


def test_opendart_exact_instant_maps_cash_borrowings_and_bonds() -> None:
    values = (
        ("CashAndCashEquivalents", "200"),
        ("ShorttermBorrowings", "100"),
        ("LongtermBorrowings", "300"),
        ("NoncurrentPortionOfNoncurrentBondsIssued", "100"),
    )
    facts_xml = "".join(
        f'<ifrs:{tag} contextRef="instant-cfs" unitRef="KRW">{value}</ifrs:{tag}>'
        for tag, value in values
    )
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance"
 xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
 xmlns:ifrs="http://xbrl.ifrs.org/taxonomy/2024-03-27/ifrs-full">
 <context id="instant-cfs"><entity><identifier scheme="corp">00123456</identifier>
 <segment><xbrldi:explicitMember dimension="ifrs:ConsolidatedAndSeparateFinancialStatementsAxis">ifrs:ConsolidatedMember</xbrldi:explicitMember></segment>
 </entity><period><instant>2026-06-30</instant></period></context>
 {facts_xml}
</xbrl>'''.encode()
    _contexts, xbrl_facts = parse_xbrl_document(xml)
    rows = {
        "CFS": [
            _opendart_row(f"ifrs-full_{tag}", value, str(index))
            for index, (tag, value) in enumerate(values, 1)
        ]
    }

    batch = promote_opendart_debt_liquidity_facts(
        _opendart_filing(),
        rows,
        xbrl_facts,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
    )
    by_metric = {fact.metric: fact for fact in batch.facts}

    assert batch.denials == ()
    assert batch.source_candidates == 4
    assert by_metric[Metric.INTEREST_BEARING_DEBT_TOTAL].value == Decimal("500")
    assert by_metric[Metric.NET_DEBT].value == Decimal("300")
    assert all(fact.statement_basis == "consolidated" for fact in batch.facts)


def test_financial_context_adapter_revalidates_lineage_and_does_not_leak_to_ai() -> None:
    batch = _positive_batch(cash="200")
    rows = project_financial_fact_catalog(batch.facts, context_id="m9-fixture")
    contexts = {
        row["fact_type"]: adapt_fact_catalog_financial_context(row, rows)
        for row in rows
    }

    assert all(result.denial_reasons == () for result in contexts.values())
    assert contexts["balance_sheet_interest_bearing_debt_total"].context is not None
    assert contexts["balance_sheet_net_debt"].context is not None
    assert contexts["balance_sheet_net_debt"].context["derivation"] == {
        "formula": "net_debt",
        "input_source_refs": [
            "stock.fact_catalog."
            + next(
                fact.fact_id
                for fact in batch.facts
                if fact.metric == Metric.INTEREST_BEARING_DEBT_TOTAL
            ),
            "stock.fact_catalog."
            + next(
                fact.fact_id
                for fact in batch.facts
                if fact.metric == Metric.CASH_AND_CASH_EQUIVALENTS
            ),
        ],
        "version": CONTRACT_VERSION,
    }
    packet = build_decision_evidence_packet(
        packet={
            "packet_id": "m9-debt-liquidity",
            "market": "us",
            "assessment_date": "2026-09-08",
        },
        stock={"ticker": "M9FIXTURE", "fact_catalog": rows},
    )
    legacy = packet.model_copy(
        update={
            "evidence": tuple(
                ref.model_copy(update={"financial_context": None})
                for ref in packet.evidence
            )
        }
    )

    assert compact_ai_context(packet) == compact_ai_context(legacy)
    assert hashlib.sha256(
        json.dumps(compact_ai_context(packet), sort_keys=True, default=str).encode()
    ).hexdigest() == hashlib.sha256(
        json.dumps(compact_ai_context(legacy), sort_keys=True, default=str).encode()
    ).hexdigest()


def test_adapter_rejects_component_overlap_and_restricted_cash_netting() -> None:
    direct = canonicalize_debt_liquidity_occurrences(
        (
            _occurrence("us-gaap:CashAndCashEquivalentsAtCarryingValue", "100"),
            _occurrence("us-gaap:DebtCurrent", "150"),
            _occurrence("us-gaap:ShortTermBorrowings", "100"),
            _occurrence("us-gaap:LongTermDebtCurrent", "50"),
            _occurrence("us-gaap:LongTermDebtNoncurrent", "400"),
        ),
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
    )
    debt_inputs = tuple(
        fact for fact in direct.facts if fact.metric != Metric.CASH_AND_CASH_EQUIVALENTS
    )
    forged_completeness = DebtCompletenessAssessment(
        DebtCompletenessStatus.COMPLETE,
        selected_fact_ids=tuple(fact.fact_id for fact in debt_inputs),
    )
    unsafe_total, source_reasons = derive_interest_bearing_debt_total(
        debt_inputs,
        forged_completeness,
    )
    assert unsafe_total is None
    assert source_reasons == ("component_overlap",)

    first = debt_inputs[0]
    forged_total = replace(
        first,
        fact_id="forged-overlap-total",
        metric=Metric.INTEREST_BEARING_DEBT_TOTAL,
        value=sum((fact.value for fact in debt_inputs), Decimal(0)),
        reported_or_derived="derived",
        source_provider="canonical_derivation",
        source_document_type="derived_metric",
        source_occurrence_id="forged-overlap-occurrence",
        raw_payload_sha256=hashlib.sha256(b"forged-overlap").hexdigest(),
        semantic_mapping="forged_overlap_fixture",
        fact_type=FactType.DERIVED_METRIC,
        source_semantic=None,
        source_reported_value=None,
        source_reported_unit=None,
        source_sign=None,
        normalization_transform=None,
        derivation_formula="interest_bearing_debt_total",
        derivation_version=CONTRACT_VERSION,
        input_fact_ids=tuple(fact.fact_id for fact in debt_inputs),
        balance_scope=DEBT_SCOPE,
        net_gross_scope="gross",
    )
    overlap_rows = project_financial_fact_catalog(
        [*direct.facts, forged_total],
        context_id="m9-overlap-negative",
    )
    overlap_row = next(
        row for row in overlap_rows if row["fact_id"] == forged_total.fact_id
    )
    overlap_result = adapt_fact_catalog_financial_context(
        overlap_row,
        overlap_rows,
    )

    batch = _positive_batch(cash="100")
    rows = project_financial_fact_catalog(batch.facts, context_id="m9-negative")
    net_row = next(row for row in rows if row["fact_type"] == "balance_sheet_net_debt")
    cash_row = next(
        row for row in rows if row["fact_type"] == "balance_sheet_cash_and_cash_equivalents"
    )

    cash_fields = dict(cash_row["fields"])
    cash_fields["balance_scope"] = "cash_and_restricted_cash_combined"
    ambiguous_cash = {**cash_row, "fields": cash_fields}
    restricted_result = adapt_fact_catalog_financial_context(
        net_row,
        [row if row is not cash_row else ambiguous_cash for row in rows],
    )

    assert overlap_result.context is None
    assert "component_overlap" in overlap_result.denial_reasons
    assert restricted_result.context is None
    assert restricted_result.denial_reasons


def test_direct_fact_shape_is_reported_point_in_time_and_eligible() -> None:
    direct = canonicalize_debt_liquidity_occurrences(
        _positive_occurrences(),
        as_of_date=AS_OF,
        analysis_framework="standard_operating_company",
    )

    assert all(fact.fact_type == FactType.REPORTED for fact in direct.facts)
    assert all(fact.eligibility == EligibilityStatus.ELIGIBLE for fact in direct.facts)
    assert all(not fact.input_fact_ids for fact in direct.facts)
