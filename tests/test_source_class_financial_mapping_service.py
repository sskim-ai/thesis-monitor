from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.services.cash_flow_capital_efficiency_service import (
    FactType,
    Metric,
    PeriodType,
    derive_fcf,
)
from app.services.financial_context_adapter_service import (
    adapt_fact_catalog_financial_context,
)
from app.services.financial_lineage_projection_service import (
    project_financial_fact_catalog,
)
from app.services.official_cash_flow_service import canonicalize_sec_companyfacts
from app.services.opendart_financial_recovery_service import Filing
from app.services.opendart_xbrl_service import parse_xbrl_document
from app.services.source_class_financial_mapping_service import (
    promote_opendart_cash_flow_facts,
)


RAW_SHA = "a" * 64
AS_OF = date(2026, 9, 8)


def _filing() -> Filing:
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


def _row(
    account_id: str,
    value: str,
    *,
    basis: str = "CFS",
    currency: str = "KRW",
    ordinal: str = "1",
) -> dict[str, object]:
    return {
        "corp_code": "00123456",
        "rcept_no": "20260814000001",
        "reprt_code": "11012",
        "bsns_year": "2026",
        "fs_div": basis,
        "sj_div": "CF",
        "account_id": account_id,
        "account_nm": "source-class fixture",
        "account_detail": "-",
        "thstrm_amount": value,
        "currency": currency,
        "ord": ordinal,
    }


def _rows() -> dict[str, list[dict[str, object]]]:
    return {
        "CFS": [
            _row(
                "ifrs-full_CashFlowsFromUsedInOperatingActivities",
                "50",
            ),
            _row(
                "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
                "25",
                ordinal="2",
            ),
        ],
        "OFS": [
            _row(
                "ifrs-full_CashFlowsFromUsedInOperatingActivities",
                "40",
                basis="OFS",
            ),
            _row(
                "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
                "20",
                basis="OFS",
                ordinal="2",
            ),
        ],
    }


def _xbrl(*, duplicate_ocf: bool = False, entity: str = "00123456") -> bytes:
    duplicate = (
        '<ifrs:CashFlowsFromUsedInOperatingActivities contextRef="duration-cfs-2" '
        'unitRef="KRW">50</ifrs:CashFlowsFromUsedInOperatingActivities>'
        if duplicate_ocf
        else ""
    )
    duplicate_context = (
        f'<context id="duration-cfs-2"><entity><identifier scheme="corp">{entity}</identifier>'
        '<segment><xbrldi:explicitMember '
        'dimension="ifrs:ConsolidatedAndSeparateFinancialStatementsAxis">'
        'ifrs:ConsolidatedMember</xbrldi:explicitMember></segment></entity>'
        '<period><startDate>2026-01-01</startDate><endDate>2026-06-30</endDate>'
        '</period></context>'
        if duplicate_ocf
        else ""
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance"
      xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
      xmlns:ifrs="http://xbrl.ifrs.org/taxonomy/2024-03-27/ifrs-full">
  <context id="duration-cfs"><entity><identifier scheme="corp">{entity}</identifier>
    <segment><xbrldi:explicitMember dimension="ifrs:ConsolidatedAndSeparateFinancialStatementsAxis">ifrs:ConsolidatedMember</xbrldi:explicitMember></segment>
  </entity><period><startDate>2026-01-01</startDate><endDate>2026-06-30</endDate></period></context>
  <context id="duration-ofs"><entity><identifier scheme="corp">{entity}</identifier>
    <segment><xbrldi:explicitMember dimension="ifrs:ConsolidatedAndSeparateFinancialStatementsAxis">ifrs:SeparateMember</xbrldi:explicitMember></segment>
  </entity><period><startDate>2026-01-01</startDate><endDate>2026-06-30</endDate></period></context>
  {duplicate_context}
  <ifrs:CashFlowsFromUsedInOperatingActivities contextRef="duration-cfs" unitRef="KRW">50</ifrs:CashFlowsFromUsedInOperatingActivities>
  <ifrs:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities contextRef="duration-cfs" unitRef="KRW">25</ifrs:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities>
  <ifrs:CashFlowsFromUsedInOperatingActivities contextRef="duration-ofs" unitRef="KRW">40</ifrs:CashFlowsFromUsedInOperatingActivities>
  <ifrs:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities contextRef="duration-ofs" unitRef="KRW">20</ifrs:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities>
  {duplicate}
</xbrl>'''.encode()


def _promote(
    *,
    rows: dict[str, list[dict[str, object]]] | None = None,
    xbrl: bytes | None = None,
):
    _contexts, facts = parse_xbrl_document(xbrl or _xbrl())
    return promote_opendart_cash_flow_facts(
        _filing(),
        rows or _rows(),
        facts,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
    )


def test_exact_opendart_context_promotes_direct_ocf_and_ppe() -> None:
    batch = _promote()
    by_metric = {fact.metric: fact for fact in batch.facts}

    assert batch.denials == ()
    assert batch.source_candidates == 2
    assert set(by_metric) == {Metric.OCF, Metric.CAPEX}
    assert all(fact.fact_type == FactType.REPORTED for fact in batch.facts)
    assert all(fact.period.period_type == PeriodType.YTD for fact in batch.facts)
    assert all(fact.period.start == date(2026, 1, 1) for fact in batch.facts)
    assert all(fact.period.end == date(2026, 6, 30) for fact in batch.facts)
    assert all(fact.statement_basis == "consolidated" for fact in batch.facts)
    assert all(fact.entity_scope == "issuer_level" for fact in batch.facts)
    assert all(fact.source_provider == "opendart_xbrl" for fact in batch.facts)
    assert all(
        fact.source_occurrence_id.startswith("opendart-occurrence:")
        for fact in batch.facts
    )
    assert by_metric[Metric.OCF].value == Decimal("50")
    assert by_metric[Metric.CAPEX].value == Decimal("25")


def test_opendart_promotion_is_idempotent_and_flows_through_m6_m7() -> None:
    first = _promote()
    second = _promote()
    assert first == second

    by_metric = {fact.metric: fact for fact in first.facts}
    fcf = derive_fcf(by_metric[Metric.OCF], by_metric[Metric.CAPEX]).fact
    assert fcf is not None
    rows = project_financial_fact_catalog(
        [*first.facts, fcf],
        context_id="m8-exact-context",
    )
    contexts = [
        adapt_fact_catalog_financial_context(row, rows).context for row in rows
    ]

    assert all(context is not None for context in contexts)
    assert {context["evidence_status"] for context in contexts if context} == {
        "DIRECT_REPORTED",
        "DERIVED_SAFE",
    }


def test_opendart_source_precedence_selects_cfs_over_ofs() -> None:
    batch = _promote()

    assert {fact.statement_basis for fact in batch.facts} == {"consolidated"}
    assert {fact.value for fact in batch.facts} == {Decimal("50"), Decimal("25")}


def test_ambiguous_amount_entity_basis_and_currency_fail_closed() -> None:
    duplicate = _promote(xbrl=_xbrl(duplicate_ocf=True))
    wrong_entity = _promote(xbrl=_xbrl(entity="00999999"))
    rows = _rows()
    rows["CFS"][0]["currency"] = "USD"
    wrong_currency = _promote(rows=rows)
    amount_rows = _rows()
    amount_rows["CFS"][0]["thstrm_amount"] = "51"
    wrong_amount = _promote(rows=amount_rows)

    assert {fact.metric for fact in duplicate.facts} == {Metric.CAPEX}
    assert duplicate.denials[0]["reason"] == "exact_xbrl_context_unresolved"
    assert wrong_entity.facts == ()
    assert {item["reason"] for item in wrong_entity.denials} == {
        "exact_xbrl_context_unresolved"
    }
    assert {fact.metric for fact in wrong_currency.facts} == {Metric.CAPEX}
    assert wrong_currency.denials[0]["reason"] == "unsupported_financial_currency"
    assert {fact.metric for fact in wrong_amount.facts} == {Metric.CAPEX}
    assert wrong_amount.denials[0]["reason"] == "exact_xbrl_context_unresolved"


def test_non_ppe_investing_semantics_are_not_promoted() -> None:
    rows = _rows()
    rows["CFS"][1] = _row(
        "ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities",
        "25",
        ordinal="2",
    )
    rows["OFS"][1] = _row(
        "ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities",
        "20",
        basis="OFS",
        ordinal="2",
    )

    batch = _promote(rows=rows)

    assert {fact.metric for fact in batch.facts} == {Metric.OCF}
    assert batch.denials[0]["reason"] == "source_row_missing"


def test_generic_ifrs_foreign_issuer_class_is_already_supported() -> None:
    row = {
        "val": 50,
        "start": "2025-01-01",
        "end": "2025-12-31",
        "filed": "2026-03-01",
        "accn": "0000000001-26-000001",
        "form": "20-F",
        "fy": 2025,
        "fp": "FY",
    }
    payload = {
        "cik": 1,
        "facts": {
            "ifrs-full": {
                "CashFlowsFromUsedInOperatingActivities": {
                    "units": {"TWD": [row]}
                },
                "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": {
                    "units": {"TWD": [{**row, "val": 25}]}
                },
            }
        },
    }

    batch = canonicalize_sec_companyfacts(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
    )

    assert {fact.metric for fact in batch.facts} == {Metric.OCF, Metric.CAPEX}
    assert {fact.issuer_id for fact in batch.facts} == {"sec:0000000001"}
    assert {fact.currency for fact in batch.facts} == {"TWD"}
    assert {fact.entity_scope for fact in batch.facts} == {"issuer_level"}
    assert all("share" not in fact.metric.value for fact in batch.facts)


def test_wrong_statement_basis_cannot_be_repaired_by_security_identity() -> None:
    batch = _promote()
    ocf = next(fact for fact in batch.facts if fact.metric == Metric.OCF)
    capex = next(fact for fact in batch.facts if fact.metric == Metric.CAPEX)

    decision = derive_fcf(ocf, replace(capex, statement_basis="separate"))

    assert decision.fact is None
    assert "statement_basis_mismatch" in decision.reasons


def test_filing_identity_mismatch_blocks_canonical_promotion() -> None:
    rows = _rows()
    rows["CFS"][0]["rcept_no"] = "20260814000002"

    batch = _promote(rows=rows)

    assert {fact.metric for fact in batch.facts} == {Metric.CAPEX}
    assert batch.denials[0]["reason"] == "filing_identity_mismatch"
