from __future__ import annotations

from datetime import date
import json

import httpx
import pytest

from app.models.financial import FinancialSnapshot
from app.providers.filings import OpenDARTProvider
from app.schemas.thesis import ValuationSnapshot
from app.services.financial_amount_period_service import (
    comparison_periods_compatible,
    financial_amount_period_lineage,
)
from app.services.kr_financial_lineage_service import (
    FINANCIAL_LINEAGE_VERSION,
    opendart_field_lineage,
    opendart_lineage_records,
    select_field_source,
)
from app.services.valuation_snapshot_service import (
    EarningsTtmResult,
    PerShareBasisContext,
    ValuationSnapshotService,
)


def _item(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "rcept_no": "20260814000001",
        "reprt_code": "11012",
        "bsns_year": "2026",
        "fs_div": "CFS",
        "sj_div": "CIS",
        "sj_nm": "연결포괄손익계산서",
        "account_id": "ifrs-full_Revenue",
        "account_nm": "매출액",
        "account_detail": "-",
        "thstrm_nm": "제58기 반기",
        "thstrm_amount": "171000000000000",
        "thstrm_add_amount": "305000000000000",
        "frmtrm_nm": "제57기 반기",
        "frmtrm_q_nm": "제57기 반기 3개월",
        "frmtrm_q_amount": "79000000000000",
        "frmtrm_add_amount": "150000000000000",
        "currency": "KRW",
    }
    value.update(overrides)
    return value


def _row(
    lineage: list[dict[str, object]],
    *,
    filing_date: date = date(2026, 8, 14),
    snapshot_type: str = "full_statement",
) -> FinancialSnapshot:
    return FinancialSnapshot(
        ticker="FIXTURE",
        period="2026-06-30",
        snapshot_type=snapshot_type,
        source_filing_id="20260814000001",
        period_type="Q2",
        fiscal_year=2026,
        period_scope="half-year",
        normalization_method="cumulative_less_prior_cumulative",
        financial_period_end=date(2026, 6, 30),
        filing_date=filing_date,
        provider="opendart",
        currency="KRW",
        revenue=171_000_000_000_000,
        cumulative_revenue=305_000_000_000_000,
        raw_financial_fields=json.dumps(lineage, ensure_ascii=False),
    )


@pytest.mark.parametrize(
    ("fs_div", "state", "basis"),
    [
        ("CFS", "verified_consolidated", "consolidated"),
        ("OFS", "verified_separate", "separate"),
        ("", "unknown", None),
    ],
)
def test_opendart_field_lineage_preserves_exact_statement_basis(
    fs_div: str, state: str, basis: str | None
) -> None:
    lineage = opendart_field_lineage(
        _item(fs_div=fs_div),
        logical_field="revenue",
        report_code="11012",
        source_column="thstrm_amount",
        selected=True,
    )

    assert lineage["statement_basis_state"] == state
    assert lineage["statement_basis"] == basis
    assert lineage["lineage_verified"] is (basis is not None)


def test_non_krw_source_cannot_be_promoted_as_krw_financial_fact() -> None:
    lineage = opendart_field_lineage(
        _item(currency="USD"),
        logical_field="revenue",
        report_code="11012",
        source_column="thstrm_amount",
        selected=True,
    )

    assert lineage["lineage_verified"] is False
    assert lineage["denial_reason"] == "unsupported_financial_currency"


def test_filing_period_keeps_quarter_and_cumulative_amounts_distinct() -> None:
    records = opendart_lineage_records(
        _item(), logical_field="revenue", report_code="11012", selected=True
    )
    current = next(item for item in records if item["source_column"] == "thstrm_amount")
    cumulative = next(
        item for item in records if item["source_column"] == "thstrm_add_amount"
    )

    assert current["amount_period_type"] == "single_quarter"
    assert current["amount_period_start"] == "2026-04-01"
    assert cumulative["amount_period_type"] == "year_to_date_cumulative"
    assert cumulative["amount_period_start"] == "2026-01-01"


def test_interim_annual_or_point_column_remains_unverified() -> None:
    lineage = opendart_field_lineage(
        _item(frmtrm_amount="150000000000000"),
        logical_field="revenue",
        report_code="11012",
        source_column="frmtrm_amount",
        selected=False,
    )

    assert lineage["amount_period_type"] is None
    assert lineage["lineage_verified"] is False


def test_balance_sheet_comparison_occurrences_use_prior_years() -> None:
    comparison = opendart_field_lineage(
        _item(sj_div="BS", frmtrm_amount="100"),
        logical_field="equity",
        report_code="11011",
        source_column="frmtrm_amount",
        selected=False,
    )
    older = opendart_field_lineage(
        _item(sj_div="BS", bfefrmtrm_amount="90"),
        logical_field="equity",
        report_code="11011",
        source_column="bfefrmtrm_amount",
        selected=False,
    )

    assert comparison["amount_period_end"] == "2025-12-31"
    assert older["amount_period_end"] == "2024-12-31"


def test_snapshot_field_lineage_uses_exact_stored_source_occurrence() -> None:
    records = opendart_lineage_records(
        _item(), logical_field="revenue", report_code="11012", selected=True
    )

    lineage = financial_amount_period_lineage(_row(records), "latest_revenue")

    assert lineage["financial_lineage_contract"] == FINANCIAL_LINEAGE_VERSION
    assert lineage["lineage_verified"] is True
    assert lineage["consolidated_separate_basis"] == "consolidated"
    assert lineage["amount_period_start"] == "2026-04-01"


def test_growth_rejects_mixed_basis_scope_currency_and_account() -> None:
    current = financial_amount_period_lineage(
        _row(
            opendart_lineage_records(
                _item(), logical_field="revenue", report_code="11012", selected=True
            )
        ),
        "latest_revenue_yoy",
    )

    def previous(**overrides: object) -> dict[str, object]:
        return {
            **current,
            "amount_period_start": "2025-04-01",
            "amount_period_end": "2025-06-30",
            **overrides,
        }

    assert comparison_periods_compatible([current, previous()], comparison="yoy")
    assert not comparison_periods_compatible(
        [current, previous(statement_basis_state="verified_separate")],
        comparison="yoy",
    )
    assert not comparison_periods_compatible(
        [current, previous(amount_period_type="year_to_date_cumulative")],
        comparison="yoy",
    )
    assert not comparison_periods_compatible(
        [current, previous(currency="USD")], comparison="yoy"
    )
    assert not comparison_periods_compatible(
        [current, previous(account_identifier="different")], comparison="yoy"
    )


def test_latest_formal_correction_wins_without_deleting_prior_provenance() -> None:
    lineage = opendart_lineage_records(
        _item(), logical_field="revenue", report_code="11012", selected=True
    )
    original = _row(lineage, filing_date=date(2026, 8, 14))
    correction = _row(lineage, filing_date=date(2026, 8, 28))
    original.id = 1
    correction.id = 2

    selected = select_field_source([original, correction], "latest_revenue")

    assert selected is not None
    assert selected[0] is correction
    assert original.raw_financial_fields == correction.raw_financial_fields


def test_valuation_keeps_safe_current_amount_and_blocks_mixed_basis_growth() -> None:
    current = _row(
        [
            *opendart_lineage_records(
                _item(), logical_field="revenue", report_code="11012", selected=True
            ),
            *opendart_lineage_records(
                _item(
                    account_id="dart_OperatingIncomeLoss",
                    account_nm="영업이익",
                    thstrm_amount="495100000000",
                    thstrm_add_amount="900000000000",
                    frmtrm_q_amount="510000000000",
                    frmtrm_add_amount="1000000000000",
                ),
                logical_field="operating_income",
                report_code="11012",
                selected=True,
            ),
        ]
    )
    current.operating_income = 495_100_000_000
    previous = _row(
        [
            *opendart_lineage_records(
                _item(bsns_year="2025", fs_div="OFS"),
                logical_field="revenue",
                report_code="11012",
                selected=True,
            ),
            *opendart_lineage_records(
                _item(
                    bsns_year="2025",
                    fs_div="OFS",
                    account_id="dart_OperatingIncomeLoss",
                    account_nm="영업이익",
                    thstrm_amount="510000000000",
                ),
                logical_field="operating_income",
                report_code="11012",
                selected=True,
            ),
        ],
        filing_date=date(2025, 8, 14),
    )
    previous.period = "2025-06-30"
    previous.fiscal_year = 2025
    previous.financial_period_end = date(2025, 6, 30)
    previous.operating_income = 510_000_000_000
    snapshot = ValuationSnapshot(current_price=100, currency="KRW")
    result = EarningsTtmResult(
        eps=None,
        common_income=None,
        method=None,
        quarters=(current,),
        quarter_eps=(None,),
        share_basis=(None,),
    )

    ValuationSnapshotService()._apply_earnings_context(
        snapshot,
        [previous, current],
        result,
        PerShareBasisContext(price_currency="KRW", financial_currency="KRW"),
    )

    assert snapshot.latest_operating_income == 495_100_000_000
    assert snapshot.latest_operating_income_yoy is None


@pytest.mark.anyio
async def test_full_statement_api_is_primary_and_preserves_raw_lineage() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested = request.url.params["fs_div"]
        calls.append(requested)
        rows = [_item()] if requested == "CFS" else []
        return httpx.Response(200, json={"status": "000", "list": rows})

    provider = OpenDARTProvider()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        facts, warnings, lineage = await provider._fetch_financial_facts(
            client,
            "test-key",
            "00126380",
            "반기보고서 (2026.06)",
            date(2026, 8, 14),
            "20260814000001",
        )

    assert calls == ["CFS", "OFS"]
    assert warnings == []
    assert any("financial fact: 매출액" in fact for fact in facts)
    assert any(item["contract"] == FINANCIAL_LINEAGE_VERSION for item in lineage)
    assert all(item["statement_basis"] == "consolidated" for item in lineage)


@pytest.mark.anyio
async def test_full_statement_api_uses_verified_ofs_only_when_cfs_unavailable() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested = request.url.params["fs_div"]
        calls.append(requested)
        if requested == "CFS":
            return httpx.Response(200, json={"status": "013", "message": "no data"})
        return httpx.Response(
            200,
            json={"status": "000", "list": [_item(fs_div="OFS")]},
        )

    provider = OpenDARTProvider()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        facts, warnings, lineage = await provider._fetch_financial_facts(
            client,
            "test-key",
            "00126380",
            "반기보고서 (2026.06)",
            date(2026, 8, 14),
            "20260814000001",
        )

    assert calls == ["CFS", "OFS"]
    assert facts
    assert "OpenDART full financial statement CFS status: 013" in warnings
    assert all(item["statement_basis"] == "separate" for item in lineage)


@pytest.mark.anyio
async def test_full_statement_api_selects_cfs_per_field_then_ofs_fallback() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        requested = request.url.params["fs_div"]
        if requested == "CFS":
            rows = [_item()]
        else:
            rows = [
                _item(
                    fs_div="OFS",
                    account_id="dart_OperatingIncomeLoss",
                    account_nm="영업이익",
                    thstrm_amount="495100000000",
                )
            ]
        return httpx.Response(200, json={"status": "000", "list": rows})

    provider = OpenDARTProvider()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        facts, warnings, lineage = await provider._fetch_financial_facts(
            client,
            "test-key",
            "00126380",
            "반기보고서 (2026.06)",
            date(2026, 8, 14),
            "20260814000001",
        )

    assert warnings == []
    assert any("different fs_div basis" in warning for warning in facts)
    assert any("financial fact: 매출액" in fact for fact in facts)
    assert any("financial fact: 영업이익" in fact for fact in facts)
    selected = {
        item["logical_field"]: item["statement_basis"]
        for item in lineage
        if item["selected_for_canonical"] is True
    }
    assert selected == {"revenue": "consolidated", "operating_income": "separate"}
