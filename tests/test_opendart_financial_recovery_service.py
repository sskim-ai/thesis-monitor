from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx

from app.services.opendart_financial_recovery_service import (
    FIELD_SPECS,
    Filing,
    LIST_ENDPOINT,
    OpenDartRecoveryClient,
    STATEMENT_ENDPOINT,
    XBRL_ENDPOINT,
    authoritative_filings,
    promote_recovered_fields,
    select_basis_occurrence,
    select_field_occurrence,
)
from app.services.opendart_xbrl_service import parse_xbrl_document
from scripts.recover_opendart_financials import _withheld_growth_labels


def _filing() -> Filing:
    return Filing(
        ticker="GENERIC",
        corp_code="00123456",
        company_name="Generic",
        receipt_no="20260814000001",
        report_name="반기보고서 (2026.06)",
        receipt_date=date(2026, 8, 14),
        business_year=2026,
        report_code="11012",
        correction=False,
    )


def _row(
    account_id: str,
    account_name: str,
    value: str,
    *,
    basis: str = "CFS",
    statement: str = "IS",
    receipt: str = "20260814000001",
    current_column: str = "thstrm_amount",
    currency: str = "KRW",
    ordinal: str = "1",
) -> dict[str, str]:
    return {
        "rcept_no": receipt,
        "reprt_code": "11012",
        "bsns_year": "2026",
        "fs_div": basis,
        "sj_div": statement,
        "sj_nm": "연결 손익계산서" if basis == "CFS" else "별도 손익계산서",
        "account_id": account_id,
        "account_nm": account_name,
        "account_detail": "-",
        current_column: value,
        "frmtrm_q_amount": "100",
        "currency": currency,
        "ord": ordinal,
    }


def _rows() -> dict[str, list[dict[str, object]]]:
    return {
        "CFS": [
            _row("ifrs-full_Revenue", "매출액", "200"),
            _row("dart_OperatingIncomeLoss", "영업이익", "40", ordinal="2"),
            _row("ifrs-full_ProfitLoss", "반기순이익", "30", ordinal="3"),
            _row(
                "ifrs-full_Assets",
                "자산총계",
                "1000",
                statement="BS",
                ordinal="4",
            ),
            _row(
                "ifrs-full_Equity",
                "자본총계",
                "600",
                statement="BS",
                ordinal="5",
            ),
            _row(
                "ifrs-full_Inventories",
                "재고자산",
                "80",
                statement="BS",
                ordinal="6",
            ),
        ],
        "OFS": [
            _row("ifrs-full_Revenue", "매출액", "150", basis="OFS"),
            _row(
                "dart_OperatingIncomeLoss",
                "영업이익",
                "20",
                basis="OFS",
                ordinal="2",
            ),
        ],
    }


def test_authoritative_filing_discovery_prefers_latest_correction() -> None:
    rows = [
        {
            "corp_name": "Generic",
            "report_nm": "반기보고서 (2026.06)",
            "rcept_no": "20260814000001",
            "rcept_dt": "20260814",
        },
        {
            "corp_name": "Generic",
            "report_nm": "[기재정정]반기보고서 (2026.06)",
            "rcept_no": "20260820000002",
            "rcept_dt": "20260820",
        },
        {
            "corp_name": "Generic",
            "report_nm": "분기보고서 (2026.03)",
            "rcept_no": "20260515000001",
            "rcept_dt": "20260515",
        },
    ]

    selected, history = authoritative_filings(
        rows, ticker="GENERIC", corp_code="00123456", limit=1
    )

    assert selected[0].receipt_no == "20260820000002"
    assert selected[0].correction is True
    assert len(history) == 3


def test_exact_cfs_selection_and_missing_cfs_ofs_fallback() -> None:
    selected = select_field_occurrence(_rows(), FIELD_SPECS["revenue"])
    fallback = select_field_occurrence(
        {"CFS": [], "OFS": _rows()["OFS"]}, FIELD_SPECS["revenue"]
    )

    assert selected.status == "selected"
    assert selected.basis == "CFS"
    assert selected.row["thstrm_amount"] == "200"
    assert fallback.status == "selected"
    assert fallback.basis == "OFS"


def test_duplicate_currency_and_cfs_conflict_fail_closed() -> None:
    duplicate = [
        _row("ifrs-full_Revenue", "매출액", "200", ordinal="1"),
        _row("ifrs-full_Revenue", "매출액", "201", ordinal="2"),
    ]
    ambiguous = select_basis_occurrence(
        duplicate, FIELD_SPECS["revenue"], basis="CFS"
    )
    no_ofs_escape = select_field_occurrence(
        {"CFS": duplicate, "OFS": _rows()["OFS"]}, FIELD_SPECS["revenue"]
    )
    foreign_currency = promote_recovered_fields(
        _filing(),
        {"CFS": [_row("ifrs-full_Revenue", "매출액", "200", currency="USD")], "OFS": []},
    )

    assert ambiguous.status == "ambiguous"
    assert no_ofs_escape.status == "ambiguous"
    assert foreign_currency["fields"]["revenue"]["status"] == "unknown"


def test_standalone_margin_and_growth_have_independent_dependencies() -> None:
    recovered = promote_recovered_fields(_filing(), _rows())

    assert recovered["fields"]["revenue"]["value"] == 200.0
    assert recovered["fields"]["operating_income"]["value"] == 40.0
    assert recovered["fields"]["operating_margin"]["value"] == 20.0
    assert recovered["fields"]["revenue"]["yoy"]["value"] == 100.0

    mismatch = _rows()
    mismatch["CFS"][0]["frmtrm_q_amount"] = None
    result = promote_recovered_fields(_filing(), mismatch)
    assert result["fields"]["revenue"]["status"] == "verified_usable"
    assert result["fields"]["revenue"]["yoy"]["status"] == "unknown"


def test_prior_quality_conflict_blocks_only_named_direct_fields() -> None:
    recovered = promote_recovered_fields(
        _filing(),
        _rows(),
        blocked_fields={"revenue", "operating_income", "net_income"},
    )

    assert recovered["fields"]["revenue"]["status"] == "denied"
    assert recovered["fields"]["operating_income"]["status"] == "denied"
    assert recovered["fields"]["operating_margin"]["status"] == "unknown"
    assert recovered["fields"]["inventory"]["status"] == "verified_usable"


def test_preview_growth_caution_names_only_safe_standalone_amounts() -> None:
    rows = _rows()
    rows["CFS"][0]["frmtrm_q_amount"] = None
    comparison_unknown = promote_recovered_fields(_filing(), rows)
    blocked = promote_recovered_fields(
        _filing(),
        _rows(),
        blocked_fields={"revenue", "operating_income", "net_income"},
    )

    assert _withheld_growth_labels(comparison_unknown) == ["매출"]
    assert _withheld_growth_labels(blocked) == []


XBRL = b"""<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance"
      xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
      xmlns:ifrs="http://xbrl.ifrs.org/taxonomy/2024-03-27/ifrs-full"
      xmlns:dart="http://dart.fss.or.kr/taxonomy">
  <context id="duration-cfs"><entity><identifier scheme="corp">00123456</identifier>
    <segment><xbrldi:explicitMember dimension="dart:StatementBasisAxis">dart:ConsolidatedMember</xbrldi:explicitMember></segment>
  </entity><period><startDate>2026-01-01</startDate><endDate>2026-06-30</endDate></period></context>
  <ifrs:CashFlowsFromUsedInOperatingActivities contextRef="duration-cfs" unitRef="KRW">50</ifrs:CashFlowsFromUsedInOperatingActivities>
</xbrl>"""


def test_cash_flow_uses_unique_xbrl_duration_and_rejects_multiple_match() -> None:
    _contexts, facts = parse_xbrl_document(XBRL)
    rows = _rows()
    rows["CFS"].append(
        _row(
            "ifrs-full_CashFlowsFromUsedInOperatingActivities",
            "영업활동현금흐름",
            "50",
            statement="CF",
            ordinal="7",
        )
    )

    resolved = promote_recovered_fields(_filing(), rows, xbrl_facts=facts)
    ambiguous = promote_recovered_fields(_filing(), rows, xbrl_facts=[*facts, *facts])

    assert resolved["fields"]["operating_cash_flow"]["status"] == "verified_usable"
    assert resolved["fields"]["operating_cash_flow"]["lineage"]["amount_period_type"] == "year_to_date_cumulative"
    assert ambiguous["fields"]["operating_cash_flow"]["status"] == "unknown"


def test_capex_components_are_audit_only_until_cash_flow_period_is_verified() -> None:
    rows = _rows()
    rows["CFS"].append(
        _row(
            "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
            "유형자산의 취득",
            "25",
            statement="CF",
            ordinal="8",
        )
    )

    recovered = promote_recovered_fields(_filing(), rows)

    assert recovered["capex_components"] == [
        {
            "classification": "property_plant_and_equipment",
            "classification_confidence": "taxonomy_exact",
            "basis": "CFS",
            "account_id": "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
            "account_name": "유형자산의 취득",
            "amount": 25.0,
            "currency": "KRW",
            "lineage": recovered["capex_components"][0]["lineage"],
            "aggregation_eligible": False,
            "reason": "cash_flow_period_requires_unique_xbrl_context",
        }
    ]
    assert recovered["capex_components"][0]["lineage"]["lineage_verified"] is False


def _zip_xbrl() -> bytes:
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("instance.xbrl", XBRL)
    return output.getvalue()


def test_client_persists_raw_rows_and_reuses_xbrl_cache(tmp_path: Path) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if str(request.url).startswith(LIST_ENDPOINT):
            return httpx.Response(
                200,
                json={
                    "status": "000",
                    "total_page": 1,
                    "list": [
                        {
                            "corp_name": "Generic",
                            "report_nm": "반기보고서 (2026.06)",
                            "rcept_no": "20260814000001",
                            "rcept_dt": "20260814",
                        }
                    ],
                },
            )
        if str(request.url).startswith(STATEMENT_ENDPOINT):
            basis = request.url.params["fs_div"]
            return httpx.Response(
                200,
                json={
                    "status": "000",
                    "list": [_row("ifrs-full_Revenue", "매출액", "200", basis=basis)],
                },
            )
        if str(request.url).startswith(XBRL_ENDPOINT):
            return httpx.Response(200, content=_zip_xbrl())
        raise AssertionError(request.url)

    client = OpenDartRecoveryClient(
        "secret", tmp_path, transport=httpx.MockTransport(handler)
    )

    async def exercise() -> None:
        selected, _history = await client.discover(
            ticker="GENERIC",
            corp_code="00123456",
            begin=date(2026, 1, 1),
            end=date(2026, 8, 17),
        )
        rows = await client.statements(selected[0])
        assert rows["CFS"] and rows["OFS"]
        await client.xbrl_facts(selected[0])
        await client.xbrl_facts(selected[0])

    import asyncio

    asyncio.run(exercise())

    raw = tmp_path / "GENERIC" / "20260814000001" / "CFS.json"
    assert raw.exists()
    assert "secret" not in raw.read_text(encoding="utf-8")
    assert sum(url.startswith(XBRL_ENDPOINT) for url in calls) == 1
