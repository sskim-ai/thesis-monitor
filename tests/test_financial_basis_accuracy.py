import json
from datetime import date

from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.providers.dart_text_fallback import extract_preliminary_earnings_facts_from_text
from app.schemas.thesis import ValuationSnapshot
from app.services.financial_validation import (
    validate_event_financials,
    validate_snapshot_period_chronology,
)
from app.services.valuation_snapshot_service import MultipleBasis, ValuationSnapshotService


def _same_pe_basis() -> MultipleBasis:
    return MultipleBasis(
        metric="pe",
        horizon="TTM",
        accounting_basis="GAAP",
        earnings_attribution="owners_parent_common",
        share_basis="diluted",
        security_basis="current_security",
        currency="USD",
    )


def _same_pb_basis() -> MultipleBasis:
    return MultipleBasis(
        metric="pb",
        horizon="latest_reported",
        accounting_basis="GAAP",
        earnings_attribution="owners_parent_common_equity",
        share_basis="common_outstanding",
        security_basis="current_security",
        currency="USD",
    )


def _fact(label: str, value: float, *, unit: str = "KRW") -> str:
    return (
        f"OpenDART financial fact: {label} = {value} {unit} "
        "(fs_div=CFS; sj_div=IS; thstrm_nm=당기; "
        "period_scope=single-quarter)"
    )


def _official_event(**overrides: object) -> Event:
    values: dict[str, object] = {
        "ticker": "FIXTURE",
        "date": date(2026, 7, 29),
        "source": "OpenDART",
        "provider": "opendart",
        "title": "연결재무제표기준영업(잠정)실적",
        "url": "https://example.com/filing",
        "event_type": "financial_report",
        "document_type": "preliminary_earnings",
        "reporting_period_end": date(2026, 6, 30),
        "raw_financial_fields": json.dumps(
            [
                {
                    "raw_label": label,
                    "raw_value": value,
                    "raw_unit": "백만원",
                    "raw_period": "single_quarter",
                    "raw_column_header": "당해실적",
                    "parse_method": "html_semantic_table",
                }
                for label, value in (
                    ("매출액", "100"),
                    ("영업이익", "75"),
                    ("당기순이익", "120"),
                )
            ],
            ensure_ascii=False,
        ),
        "confirmed_facts": json.dumps(
            [_fact("매출액", 100), _fact("영업이익", 75), _fact("당기순이익", 120)]
        ),
        "revenue": 100,
        "operating_income": 75,
        "net_income": 120,
        "operating_margin": 75,
    }
    values.update(overrides)
    return Event(**values)


def test_unit_mismatch_remains_a_hard_error() -> None:
    event = _official_event(
        confirmed_facts=json.dumps([_fact("매출액", 100, unit="UNKNOWN")])
    )

    result = validate_event_financials(event)

    assert result.valid is False
    assert "unsupported_financial_amount_unit" in result.hard_errors
    assert event.revenue is None


def test_high_margin_and_net_income_above_revenue_are_soft_outliers() -> None:
    event = _official_event()

    result = validate_event_financials(event, operating_margin_upper_bound=60)

    assert result.valid is True
    assert result.hard_errors == []
    assert "unusually_high_or_low_operating_margin" in result.soft_outliers
    assert "net_income_exceeds_revenue" in result.soft_outliers
    assert event.revenue == 100
    assert event.operating_income == 75
    assert event.net_income == 120


def test_financial_company_structure_keeps_existing_industry_aware_exception() -> None:
    event = _official_event(company_name="검증보험", title="보험사 잠정실적")

    result = validate_event_financials(event, operating_margin_upper_bound=60)

    assert result.valid is True
    assert "unusually_high_or_low_operating_margin" not in result.soft_outliers
    assert "net_income_exceeds_revenue" not in result.soft_outliers


def test_reported_margin_arithmetic_mismatch_is_a_hard_error() -> None:
    event = _official_event(operating_margin=25)

    result = validate_event_financials(event)

    assert result.valid is False
    assert "reported_and_derived_margin_mismatch" in result.hard_errors
    assert event.operating_income is None


def test_positive_provider_pe_with_negative_internal_eps_is_basis_conflict() -> None:
    snapshot = ValuationSnapshot(
        current_price=100,
        trailing_pe=20,
        trailing_pe_status="value",
        ttm_eps=-2,
        trailing_valuation_confidence=0.75,
    )

    ValuationSnapshotService()._cross_check(
        snapshot,
        20,
        None,
        None,
        None,
        provider_pe_basis=_same_pe_basis(),
        derived_pe_basis=_same_pe_basis(),
    )

    assert snapshot.trailing_pe_basis_conflict is True
    assert snapshot.trailing_pe is None
    assert snapshot.trailing_pe_status == "not_meaningful"
    assert snapshot.trailing_valuation_confidence <= 0.35


def test_large_provider_derived_pe_difference_is_excluded() -> None:
    snapshot = ValuationSnapshot(
        current_price=100,
        trailing_pe=50,
        trailing_pe_status="value",
        ttm_eps=5,
        trailing_valuation_confidence=0.75,
    )

    ValuationSnapshotService()._cross_check(
        snapshot,
        50,
        None,
        20,
        None,
        provider_pe_basis=_same_pe_basis(),
        derived_pe_basis=_same_pe_basis(),
    )

    assert snapshot.trailing_pe_basis_conflict is True
    assert snapshot.valuation_discrepancy_warning is True
    assert snapshot.trailing_pe_status == "conflict"
    assert snapshot.trailing_pe is None


def test_small_provider_derived_pe_difference_is_accepted() -> None:
    snapshot = ValuationSnapshot(
        current_price=100,
        trailing_pe=21,
        trailing_pe_status="value",
        ttm_eps=5,
        trailing_valuation_confidence=0.75,
    )

    ValuationSnapshotService()._cross_check(
        snapshot,
        21,
        None,
        20,
        None,
        provider_pe_basis=_same_pe_basis(),
        derived_pe_basis=_same_pe_basis(),
    )

    assert snapshot.trailing_pe_basis_conflict is False
    assert snapshot.valuation_discrepancy_warning is False
    assert snapshot.trailing_pe == 20
    assert snapshot.trailing_pe_source == "derived_trailing"


def test_provider_pbr_and_forward_multiple_conflicts_are_detected() -> None:
    service = ValuationSnapshotService()
    snapshot = ValuationSnapshot(
        current_price=100,
        price_to_book=4,
        price_to_book_status="value",
        bvps=100,
        trailing_valuation_confidence=0.75,
        forward_pe=25,
        forward_pe_status="value",
        forward_eps=10,
        forward_valuation_confidence=0.7,
    )

    service._cross_check(
        snapshot,
        None,
        4,
        None,
        1,
        provider_pb_basis=_same_pb_basis(),
        derived_pb_basis=_same_pb_basis(),
    )
    forward_basis = MultipleBasis(
        metric="pe",
        horizon="FY1",
        accounting_basis="GAAP",
        earnings_attribution="common_eps",
        share_basis="diluted",
        security_basis="current_security",
        currency="USD",
    )
    service._cross_check_forward(
        snapshot,
        provider_pe=25,
        derived_pe=10,
        provider_pe_basis=forward_basis,
        derived_pe_basis=forward_basis,
    )

    assert snapshot.price_to_book_basis_conflict is True
    assert snapshot.price_to_book is None
    assert snapshot.forward_pe_basis_conflict is True
    assert snapshot.forward_pe is None
    assert set(snapshot.multiple_basis_conflicts) == {"price_to_book", "forward_pe"}


def test_impossible_preliminary_period_remains_quarantined() -> None:
    snapshot = FinancialSnapshot(
        ticker="005490",
        period="2026-Q2",
        snapshot_type="preliminary_earnings",
        financial_period_end=date(2026, 6, 30),
        filing_date=date(2026, 4, 30),
        reporting_period_source="table_header",
        reporting_period_confidence="high",
    )

    assert validate_snapshot_period_chronology(snapshot) is False
    assert snapshot.period_mapping_validation_failed is True
    assert "financial_period_after_filing_date" in json.loads(
        snapshot.financial_hard_errors
    )


def test_unclear_preliminary_period_is_not_accepted_as_current() -> None:
    event = _official_event(reporting_period_end=None)

    result = validate_event_financials(event)

    assert result.valid is False
    assert "reporting_period_unavailable" in result.hard_errors


def test_preliminary_period_uses_current_table_header_not_comparison_date() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        <table id="posco-q1">
          <tr><td colspan="5">단위 : 백만원, %</td></tr>
          <tr><th colspan="2">구분</th><th>당해실적</th><th>전기실적</th><th>전년동기실적</th></tr>
          <tr><th colspan="2">구분</th><th>2026년 1분기</th><th>2025년 4분기</th><th>2025년 1분기</th></tr>
          <tr><td>매출액</td><td>당해실적</td><td>100</td><td>95</td><td>90</td></tr>
          <tr><td>영업이익</td><td>당해실적</td><td>10</td><td>9</td><td>8</td></tr>
        </table>
        """
    )

    assert parsed.period_end == date(2026, 3, 31)
    assert parsed.reporting_period_source == "current_header_quarter"
    assert parsed.reporting_period_confidence == "high"
