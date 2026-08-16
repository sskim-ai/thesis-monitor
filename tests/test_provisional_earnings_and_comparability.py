import json
from datetime import date

import pytest

from app.models.financial import FinancialSnapshot
from app.models.security import SecurityMaster
from app.providers.dart_text_fallback import extract_preliminary_earnings_facts_from_text
from app.schemas.thesis import ValuationSnapshot
from app.services.historical_valuation_service import point_in_time_denominators
from app.services.financial_quality_service import sanitize_financial_snapshot_for_prose
from app.services.notification_service import _data_cautions, _valuation_formula_lines
from app.services.security_identity_service import (
    IDENTITY_CONFLICT,
    VERIFIED_DEPOSITARY,
    VERIFIED_NON_DEPOSITARY,
)
from app.services.valuation_snapshot_service import (
    MultipleBasis,
    PerShareBasisContext,
    ValuationSnapshotService,
    _earnings_quarters,
    _normalize_per_share_value,
    _resolve_per_share_basis_context,
    _ttm_earnings,
    determine_basis_comparability,
)


def _verified_common_basis(currency: str) -> PerShareBasisContext:
    return PerShareBasisContext(
        issuer_type="krx" if currency == "KRW" else "domestic_us",
        security_type="common_stock",
        security_identity_state=VERIFIED_NON_DEPOSITARY,
        price_currency=currency,
        financial_currency=currency,
    )


def _full(
    period_end: date,
    eps: float,
    *,
    revenue: float = 100,
    income: float | None = 10,
    shares: float = 100,
) -> FinancialSnapshot:
    quarter = (period_end.month - 1) // 3 + 1
    return FinancialSnapshot(
        ticker="FIXTURE",
        period=f"{period_end.year}-Q{quarter}",
        snapshot_type="full_statement",
        period_type={2: "H1", 4: "FY"}.get(quarter, f"Q{quarter}"),
        fiscal_year=period_end.year,
        financial_period_end=period_end,
        filing_date=date(period_end.year, period_end.month, min(28, period_end.day)),
        reported_date=date(period_end.year, period_end.month, min(28, period_end.day)),
        revenue=revenue,
        operating_income=income,
        common_net_income=income,
        owners_parent_net_income=income,
        diluted_eps=eps,
        common_shares_outstanding=shares,
        diluted_shares=shares,
        common_equity=1000,
        owners_parent_equity=1000,
        currency="KRW",
        provider="opendart",
    )


def _preliminary(
    *,
    owners_income: float | None = 400,
    total_income: float | None = 450,
    diluted_eps: float | None = None,
    hard_errors: list[str] | None = None,
) -> FinancialSnapshot:
    return FinancialSnapshot(
        ticker="FIXTURE",
        period="2026-Q2",
        snapshot_type="preliminary_earnings",
        source_filing_id="20260729000001",
        period_type="Q2",
        fiscal_year=2026,
        period_scope="single-quarter",
        financial_period_end=date(2026, 6, 30),
        filing_date=date(2026, 7, 29),
        reported_date=date(2026, 7, 29),
        reporting_period_source="current_header_date_range",
        reporting_period_confidence="high",
        revenue=800,
        operating_income=600,
        net_income=total_income,
        common_net_income=owners_income,
        owners_parent_net_income=owners_income,
        diluted_eps=diluted_eps,
        operating_margin=75,
        currency="KRW",
        unit_scale=1,
        provider="opendart",
        raw_financial_fields=json.dumps(
            [
                {
                    "raw_label": "매출액",
                    "raw_value": "800",
                    "raw_unit": "백만원",
                    "raw_period": "single_quarter",
                    "raw_column_header": "당해실적 2026.04.01~2026.06.30",
                    "parse_method": "html_semantic_table",
                },
                {
                    "raw_label": "영업이익",
                    "raw_value": "600",
                    "raw_unit": "백만원",
                    "raw_period": "single_quarter",
                    "raw_column_header": "당해실적 2026.04.01~2026.06.30",
                    "parse_method": "html_semantic_table",
                },
            ],
            ensure_ascii=False,
        ),
        financial_hard_errors=json.dumps(hard_errors or []),
        financial_soft_outliers=json.dumps(["unusually_high_or_low_operating_margin"]),
    )


def _foreign_preliminary(
    *,
    diluted_eps: float | None = None,
    eps_currency: str | None = None,
    eps_security_basis: str = "unknown",
) -> FinancialSnapshot:
    fields: list[dict[str, object]] = [
        {
            "field": "revenue",
            "value": 1_000,
            "currency": "TWD",
            "source": "sec_foreign_filing",
            "parse_method": "sec_foreign_release",
        },
        {
            "field": "operating_income",
            "value": 500,
            "currency": "TWD",
            "source": "sec_foreign_filing",
            "parse_method": "sec_foreign_release",
        },
    ]
    if diluted_eps is not None:
        fields.append(
            {
                "field": "diluted_eps",
                "value": diluted_eps,
                "currency": eps_currency,
                "security_basis": eps_security_basis,
                "representation_type": "security_equivalent",
                "selected_for_valuation": True,
                "source": "sec_foreign_filing",
                "parse_method": "sec_foreign_release",
            }
        )
    return FinancialSnapshot(
        ticker="FOREIGN",
        period="2026-Q2",
        snapshot_type="preliminary_earnings",
        source_filing_id="0000000000-26-000001",
        period_type="Q2",
        fiscal_year=2026,
        period_scope="single-quarter",
        financial_period_end=date(2026, 6, 30),
        filing_date=date(2026, 7, 10),
        reported_date=date(2026, 7, 10),
        reporting_period_source="foreign_release_explicit_period",
        reporting_period_confidence="high",
        revenue=1_000,
        operating_income=500,
        operating_margin=50,
        net_income=400,
        diluted_eps=diluted_eps,
        currency="TWD",
        unit_scale=1,
        provider="sec_foreign_filing",
        raw_financial_fields=json.dumps(fields),
    )


def _base_rows() -> list[FinancialSnapshot]:
    return [
        _full(date(2025, 9, 30), 1),
        _full(date(2025, 12, 31), 2),
        _full(date(2026, 3, 31), 3),
    ]


def _basis(
    *,
    metric: str = "pe",
    horizon: str = "TTM",
    accounting: str = "GAAP",
    security: str = "current_security",
) -> MultipleBasis:
    return MultipleBasis(
        metric=metric,
        horizon=horizon,
        accounting_basis=accounting,
        earnings_attribution=(
            "owners_parent_common" if metric == "pe" else "owners_parent_common_equity"
        ),
        share_basis="diluted" if metric == "pe" else "common_outstanding",
        security_basis=security,
        currency="KRW",
    )


def test_preliminary_quarter_is_included_in_ttm_with_point_in_time_shares() -> None:
    result = _ttm_earnings([*_base_rows(), _preliminary()])

    assert result.eps == pytest.approx(10)
    assert result.contains_preliminary is True
    assert result.quarters[-1].snapshot_type == "preliminary_earnings"
    assert result.share_basis[-1] == "latest_official_diluted_shares"


def test_full_statement_supersedes_same_quarter_preliminary_without_double_count() -> None:
    q2_full = _full(date(2026, 6, 30), 5, revenue=900, income=500)
    rows = [*_base_rows(), _preliminary(), q2_full]

    selected = _earnings_quarters(rows)
    result = _ttm_earnings(rows)

    assert len(selected[-4:]) == 4
    assert selected[-1] is q2_full
    assert result.eps == pytest.approx(11)
    assert result.contains_preliminary is False


def test_non_calendar_fiscal_quarters_use_actual_period_end_identity() -> None:
    rows = [
        _full(date(2025, 4, 4), 1),
        _full(date(2025, 7, 4), 2),
        _full(date(2025, 10, 3), 3),
        _full(date(2026, 1, 2), 4),
    ]

    result = _ttm_earnings(rows)

    assert result.eps == pytest.approx(10)
    assert [row.financial_period_end for row in result.quarters] == [
        date(2025, 4, 4),
        date(2025, 7, 4),
        date(2025, 10, 3),
        date(2026, 1, 2),
    ]


def test_hard_invalid_preliminary_is_excluded_but_soft_outlier_is_usable() -> None:
    invalid = _ttm_earnings(
        [*_base_rows(), _preliminary(hard_errors=["raw_metric_mapping_mismatch"])]
    )
    soft_only = _ttm_earnings([*_base_rows(), _preliminary()])

    assert invalid.eps is None
    assert soft_only.eps == pytest.approx(10)


def test_total_net_income_without_owner_attribution_does_not_create_eps() -> None:
    result = _ttm_earnings([*_base_rows(), _preliminary(owners_income=None, total_income=450)])

    assert result.eps is None
    assert result.quarters[-1].revenue == 800
    assert result.quarters[-1].operating_income == 600


def test_foreign_preliminary_updates_context_without_unsafe_eps() -> None:
    rows = [*_base_rows(), _foreign_preliminary()]
    snapshot = ValuationSnapshot(current_price=100, currency="USD")
    basis = PerShareBasisContext(
        issuer_type="foreign_private_issuer",
        security_type="ADR",
        is_depositary_security=True,
        security_identity_state=VERIFIED_DEPOSITARY,
        price_currency="USD",
        financial_currency="TWD",
        adr_ratio=5,
    )

    derived_pe, _derived_pb = ValuationSnapshotService()._apply_derived_trailing(
        snapshot, rows, basis
    )

    assert derived_pe is None
    assert snapshot.latest_earnings_period == "2026-06-30"
    assert snapshot.earnings_context_source == "preliminary_earnings"
    assert snapshot.earnings_context_usable is True
    assert snapshot.latest_eps_usable is False
    assert snapshot.ttm_eps_usable is False
    assert snapshot.eps_per_usable is False
    assert snapshot.latest_revenue == 1_000
    assert snapshot.latest_operating_income == 500
    assert snapshot.latest_operating_margin == 50
    assert snapshot.ttm_eps is None


def test_valuation_snapshot_persists_exact_lineage_for_fallback() -> None:
    rows = [*_base_rows(), _full(date(2026, 6, 30), 4)]
    rows[1].financial_soft_outliers = json.dumps(["net_income_exceeds_revenue"])
    service = ValuationSnapshotService()
    snapshot = ValuationSnapshot(current_price=100, currency="KRW")

    service._apply_derived_trailing(snapshot, rows, _verified_common_basis("KRW"))
    source_metadata = service._financial_quality_source_metadata(snapshot, rows)
    source_metadata["security_identity"] = {
        "identity_state": VERIFIED_NON_DEPOSITARY,
        "decision_version": "security-identity-v1",
        "verification_status": "verified",
    }
    snapshot.financial_quality_source_metadata = source_metadata
    restored = json.loads(snapshot.model_dump_json())
    sanitized = sanitize_financial_snapshot_for_prose(restored)

    sources = restored["financial_quality_source_metadata"]["ttm_sources"]
    assert [item["period"] for item in sources] == [
        "2025-09-30",
        "2025-12-31",
        "2026-03-31",
        "2026-06-30",
    ]
    assert sources[1]["soft_outliers"] == ["net_income_exceeds_revenue"]
    assert sanitized["ttm_eps"] is None
    assert sanitized["trailing_pe"] is None
    assert sanitized["price_to_book"] is not None


def test_earnings_context_keeps_reported_operating_margin_with_exact_income() -> None:
    latest = _foreign_preliminary()
    latest.revenue = 1_270_380
    latest.operating_income = 766_603
    latest.operating_margin = 60.3
    snapshot = ValuationSnapshot(current_price=100, currency="USD")

    ValuationSnapshotService()._apply_derived_trailing(
        snapshot, [latest], _verified_common_basis("KRW")
    )

    assert snapshot.latest_operating_income == 766_603
    assert snapshot.latest_operating_margin == 60.3


def test_foreign_preliminary_direct_adr_eps_remains_separately_eligible() -> None:
    rows = []
    for period_end, eps in (
        (date(2025, 9, 30), 1.0),
        (date(2025, 12, 31), 2.0),
        (date(2026, 3, 31), 3.0),
    ):
        row = _full(period_end, eps)
        row.currency = "USD"
        row.raw_financial_fields = json.dumps(
            [
                {
                    "field": "diluted_eps",
                    "currency": "USD",
                    "security_basis": "depositary_security",
                }
            ]
        )
        rows.append(row)
    rows.append(
        _foreign_preliminary(
            diluted_eps=4.0,
            eps_currency="USD",
            eps_security_basis="depositary_security",
        )
    )
    snapshot = ValuationSnapshot(current_price=100, currency="USD")
    basis = PerShareBasisContext(
        issuer_type="foreign_private_issuer",
        security_type="ADR",
        is_depositary_security=True,
        security_identity_state=VERIFIED_DEPOSITARY,
        price_currency="USD",
        financial_currency="TWD",
        adr_ratio=5,
    )

    derived_pe, _derived_pb = ValuationSnapshotService()._apply_derived_trailing(
        snapshot, rows, basis
    )

    assert snapshot.earnings_context_usable is True
    assert snapshot.latest_eps_usable is True
    assert snapshot.ttm_eps_usable is True
    assert snapshot.eps_per_usable is True
    assert snapshot.ttm_contains_preliminary is True
    assert snapshot.ttm_eps == pytest.approx(10)
    assert derived_pe == pytest.approx(10)
    latest_lineage = snapshot.earnings_quarter_series[-1]
    assert latest_lineage["reported_diluted_eps"] == 4
    assert latest_lineage["reported_eps_currency"] == "USD"
    assert latest_lineage["reported_eps_security_basis"] == "depositary_security"
    assert latest_lineage["eps_representation"] == "security_equivalent"
    assert latest_lineage["normalized_eps_usable"] is True


def test_latest_direct_adr_eps_can_be_usable_when_ttm_is_not() -> None:
    older_rows = []
    for period_end in (date(2022, 12, 31), date(2023, 12, 31), date(2024, 12, 31)):
        row = _full(period_end, 1)
        row.currency = "USD"
        row.raw_financial_fields = json.dumps(
            [
                {
                    "field": "diluted_eps",
                    "currency": "USD",
                    "security_basis": "unknown",
                }
            ]
        )
        older_rows.append(row)
    latest = _foreign_preliminary(
        diluted_eps=4.31,
        eps_currency="USD",
        eps_security_basis="depositary_security",
    )
    snapshot = ValuationSnapshot(current_price=100, currency="USD")
    basis = PerShareBasisContext(
        issuer_type="foreign_private_issuer",
        security_type="ADR",
        is_depositary_security=True,
        security_identity_state=VERIFIED_DEPOSITARY,
        price_currency="USD",
        financial_currency="TWD",
        adr_ratio=5,
    )

    derived_pe, _derived_pb = ValuationSnapshotService()._apply_derived_trailing(
        snapshot, [*older_rows, latest], basis
    )

    assert derived_pe is None
    assert snapshot.latest_eps_usable is True
    assert snapshot.ttm_eps_usable is False
    assert snapshot.eps_per_usable is False
    assert snapshot.ttm_eps is None
    assert snapshot.trailing_pe_denominator_period_end is None
    assert snapshot.earnings_quarter_series[-1]["normalized_eps_usable"] is True


def test_negative_normalized_ttm_eps_is_usable_and_keeps_denominator_date() -> None:
    rows = []
    for period_end, eps in (
        (date(2025, 9, 30), -2.0),
        (date(2025, 12, 31), -1.0),
        (date(2026, 3, 31), 0.5),
        (date(2026, 6, 30), 0.5),
    ):
        row = _full(period_end, eps)
        row.currency = "USD"
        row.raw_financial_fields = json.dumps(
            [
                {
                    "field": "diluted_eps",
                    "currency": "USD",
                    "security_basis": "current_security",
                }
            ]
        )
        rows.append(row)
    snapshot = ValuationSnapshot(current_price=100, currency="USD")
    basis = PerShareBasisContext(
        security_type="common_stock",
        security_identity_state=VERIFIED_NON_DEPOSITARY,
        price_currency="USD",
        financial_currency="USD",
    )

    derived_pe, _derived_pb = ValuationSnapshotService()._apply_derived_trailing(
        snapshot, rows, basis
    )

    assert derived_pe is None
    assert snapshot.latest_eps_usable is True
    assert snapshot.ttm_eps_usable is True
    assert snapshot.eps_per_usable is True
    assert snapshot.ttm_eps == pytest.approx(-2)
    assert snapshot.trailing_pe_status == "not_meaningful"
    assert snapshot.trailing_pe_denominator_period_end == "2026-06-30"


def test_provider_only_pe_does_not_keep_stale_derived_denominator_date() -> None:
    snapshot = ValuationSnapshot(
        current_price=100,
        currency="USD",
        trailing_pe=18,
        trailing_pe_status="value",
        trailing_pe_source="provider",
        trailing_pe_denominator_period_end="2025-12-31",
        trailing_pe_denominator_filing_date="2026-02-15",
    )

    derived_pe, _derived_pb = ValuationSnapshotService()._apply_derived_trailing(
        snapshot, [], _verified_common_basis("KRW")
    )

    assert derived_pe is None
    assert snapshot.trailing_pe == 18
    assert snapshot.ttm_eps_usable is False
    assert snapshot.trailing_pe_denominator_period_end is None
    assert snapshot.trailing_pe_denominator_filing_date is None


def test_foreign_preliminary_and_adr_basis_caution_is_compact() -> None:
    cautions = _data_cautions(
        {
            "earnings_context_is_preliminary": True,
            "earnings_context_usable": True,
            "eps_per_usable": False,
            "trailing_pe_status": "value",
            "trailing_pe_basis_status": "currency_mismatch",
        },
        {"reason_codes": ["per_share_basis_insufficient"]},
    )

    assert cautions == [
        "최근 공식 잠정실적의 매출·영업이익은 반영했지만 주당 기준을 확인하지 못해 자체 PER 계산은 보류했습니다."
    ]


def test_preliminary_caution_distinguishes_latest_eps_from_ttm_basis() -> None:
    cautions = _data_cautions(
        {
            "earnings_context_is_preliminary": True,
            "earnings_context_usable": True,
            "latest_eps_usable": True,
            "ttm_eps_usable": False,
            "eps_per_usable": False,
            "trailing_pe_status": "value",
        },
        {"reason_codes": ["per_share_basis_insufficient"]},
    )

    assert cautions == [
        "최근 분기 주당 실적은 확인했지만 이전 분기들의 주당 기준을 확인하지 못해 TTM EPS/PER 자체 계산을 보류했습니다."
    ]


def test_preliminary_caution_distinguishes_incomplete_ttm_coverage() -> None:
    cautions = _data_cautions(
        {
            "earnings_context_is_preliminary": True,
            "earnings_context_usable": True,
            "latest_eps_usable": True,
            "ttm_eps_usable": False,
            "eps_per_usable": False,
        },
        {"reason_codes": []},
    )

    assert cautions == [
        "최근 분기 주당 실적은 확인했지만 최근 4개 분기 자료가 충분하지 않아 TTM EPS/PER 자체 계산을 보류했습니다."
    ]


def test_eps_less_preliminary_updates_earnings_context_without_recalculating_per() -> None:
    rows = [*_base_rows(), _preliminary(owners_income=None, total_income=450)]
    snapshot = ValuationSnapshot(
        current_price=100,
        currency="KRW",
        trailing_pe=20,
        trailing_pe_status="value",
    )

    derived_pe, _derived_pb = ValuationSnapshotService()._apply_derived_trailing(
        snapshot, rows, _verified_common_basis("KRW")
    )

    assert derived_pe is None
    assert snapshot.trailing_pe == 20
    assert snapshot.latest_earnings_period == "2026-06-30"
    assert snapshot.financial_currency == "KRW"
    assert snapshot.earnings_context_is_preliminary is True
    assert snapshot.earnings_context_usable is True
    assert snapshot.eps_per_usable is False
    assert snapshot.latest_revenue == 800
    assert snapshot.latest_operating_income == 600
    assert snapshot.latest_operating_margin == pytest.approx(75)
    assert snapshot.ttm_contains_preliminary is False


@pytest.mark.parametrize("financial_currency", ["TWD", None])
def test_earnings_context_uses_selected_financial_snapshot_currency(
    financial_currency: str | None,
) -> None:
    latest = _preliminary(owners_income=None, total_income=450)
    latest.currency = financial_currency
    rows = _base_rows()
    for row in rows:
        row.currency = financial_currency
    snapshot = ValuationSnapshot(current_price=100, currency="USD")

    ValuationSnapshotService()._apply_derived_trailing(
        snapshot, [*rows, latest], _verified_common_basis("KRW")
    )

    assert snapshot.currency == "USD"
    assert snapshot.financial_currency == financial_currency


def test_preliminary_reported_diluted_eps_takes_priority() -> None:
    result = _ttm_earnings([*_base_rows(), _preliminary(owners_income=400, diluted_eps=7)])

    assert result.eps == pytest.approx(13)
    assert result.share_basis[-1] == "reported_diluted_eps"


def test_preliminary_updates_per_and_margin_but_not_full_balance_pbr() -> None:
    rows = [*_base_rows(), _preliminary()]
    snapshot = ValuationSnapshot(current_price=100, currency="KRW")

    derived_pe, derived_pb = ValuationSnapshotService()._apply_derived_trailing(
        snapshot, rows, _verified_common_basis("KRW")
    )

    assert derived_pe == pytest.approx(10)
    assert snapshot.ttm_contains_preliminary is True
    assert snapshot.latest_operating_margin == pytest.approx(75)
    assert snapshot.bvps == pytest.approx(10)
    assert derived_pb == pytest.approx(10)
    assert snapshot.pbr_denominator_period_end == "2026-03-31"


def test_adr_ordinary_eps_is_normalized_only_with_same_currency_and_ratio() -> None:
    context = PerShareBasisContext(
        issuer_type="adr",
        security_type="Depositary Receipt",
        is_depositary_security=True,
        security_identity_state=VERIFIED_DEPOSITARY,
        price_currency="USD",
        financial_currency="USD",
        adr_ratio=5,
        adr_ratio_source="SEC filing",
    )

    result = _normalize_per_share_value(
        4,
        value_currency="USD",
        security_basis="ordinary_share",
        context=context,
    )

    assert result.value == pytest.approx(20)
    assert result.status == "normalized_to_current_security"
    assert result.ratio_used == 5


def test_adr_per_share_value_rejects_currency_mismatch_or_unknown_basis() -> None:
    context = PerShareBasisContext(
        issuer_type="adr",
        security_type="adr",
        is_depositary_security=True,
        security_identity_state=VERIFIED_DEPOSITARY,
        price_currency="USD",
        financial_currency="TWD",
        adr_ratio=5,
        adr_ratio_source="SEC filing",
    )

    currency_mismatch = _normalize_per_share_value(
        20,
        value_currency="TWD",
        security_basis="ordinary_share",
        context=context,
    )
    unknown_basis = _normalize_per_share_value(
        10,
        value_currency="USD",
        security_basis="unknown",
        context=context,
    )

    assert currency_mismatch.value is None
    assert currency_mismatch.status == "currency_mismatch"
    assert unknown_basis.value is None
    assert unknown_basis.status == "security_basis_mismatch"


def test_adr_direct_eps_does_not_apply_ratio_twice() -> None:
    context = PerShareBasisContext(
        issuer_type="adr",
        security_type="ads",
        is_depositary_security=True,
        security_identity_state=VERIFIED_DEPOSITARY,
        price_currency="USD",
        financial_currency="TWD",
        adr_ratio=5,
        adr_ratio_source="SEC filing",
    )

    result = _normalize_per_share_value(
        10,
        value_currency="USD",
        security_basis="depositary_security",
        context=context,
    )

    assert result.value == 10
    assert result.status == "directly_comparable"
    assert result.ratio_used is None


def test_unmonitored_security_master_adr_activates_basis_gate() -> None:
    security = SecurityMaster(
        canonical_company_id="company:fixture",
        canonical_security_id="security:fixture:adr",
        ticker="FIXADR",
        company_name="Fixture ADR",
        issuer_type="adr",
        security_type="adr",
        adr_ratio=5,
    )

    context = _resolve_per_share_basis_context(
        None,
        security,
        price_currency="USD",
        financial_currency="TWD",
    )

    assert context.is_depositary_security is True
    assert context.issuer_type == "adr"
    assert context.adr_ratio == 5
    assert context.adr_ratio_direction is None


def test_domestic_common_issuer_and_depositary_type_are_a_conflict() -> None:
    security = SecurityMaster(
        canonical_company_id="company:domestic-common",
        canonical_security_id="security:domestic-common",
        ticker="COMMON",
        company_name="Domestic Common",
        issuer_type="domestic_us",
        security_type="Depositary Receipt",
    )

    context = _resolve_per_share_basis_context(
        None,
        security,
        price_currency="USD",
        financial_currency="USD",
    )

    assert context.is_depositary_security is False
    assert context.security_identity_state == IDENTITY_CONFLICT


def _with_per_share_metadata(
    row: FinancialSnapshot,
    *,
    currency: str,
    eps_security_basis: str,
    share_security_basis: str = "ordinary_share",
) -> FinancialSnapshot:
    row.currency = currency
    row.raw_financial_fields = json.dumps(
        [
            {
                "field": "diluted_eps",
                "currency": currency,
                "security_basis": eps_security_basis,
            },
            {
                "field": "common_shares_outstanding",
                "security_basis": share_security_basis,
            },
        ]
    )
    return row


def test_adr_derived_pe_and_pb_use_ordinary_shares_per_adr_direction() -> None:
    rows = [
        _with_per_share_metadata(
            row,
            currency="USD",
            eps_security_basis="ordinary_share",
        )
        for row in [*_base_rows(), _full(date(2026, 6, 30), 4)]
    ]
    context = PerShareBasisContext(
        issuer_type="adr",
        security_type="adr",
        is_depositary_security=True,
        security_identity_state=VERIFIED_DEPOSITARY,
        price_currency="USD",
        financial_currency="USD",
        adr_ratio=5,
    )
    snapshot = ValuationSnapshot(current_price=100, currency="USD")

    derived_pe, derived_pb = ValuationSnapshotService()._apply_derived_trailing(
        snapshot, rows, context
    )

    assert snapshot.raw_ttm_eps == pytest.approx(10)
    assert snapshot.ttm_eps == pytest.approx(50)
    assert derived_pe == pytest.approx(2)
    assert snapshot.raw_bvps == pytest.approx(10)
    assert snapshot.bvps == pytest.approx(50)
    assert derived_pb == pytest.approx(2)
    assert snapshot.trailing_pe_basis_status == "normalized_to_current_security"
    assert snapshot.price_to_book_basis_status == "normalized_to_current_security"


@pytest.mark.parametrize(
    ("currency", "security_basis", "expected_status"),
    [
        ("TWD", "ordinary_share", "currency_mismatch"),
        ("USD", "unknown", "security_basis_mismatch"),
    ],
)
def test_adr_unsafe_eps_is_not_exposed_as_current_security_ttm_eps(
    currency: str,
    security_basis: str,
    expected_status: str,
) -> None:
    rows = [
        _with_per_share_metadata(
            row,
            currency=currency,
            eps_security_basis=security_basis,
        )
        for row in [*_base_rows(), _full(date(2026, 6, 30), 4)]
    ]
    context = PerShareBasisContext(
        issuer_type="adr",
        security_type="adr",
        is_depositary_security=True,
        security_identity_state=VERIFIED_DEPOSITARY,
        price_currency="USD",
        financial_currency=currency,
        adr_ratio=5,
    )
    snapshot = ValuationSnapshot(
        current_price=100,
        currency="USD",
        trailing_pe=18,
        trailing_pe_status="value",
        trailing_pe_source="provider",
    )

    derived_pe, _derived_pb = ValuationSnapshotService()._apply_derived_trailing(
        snapshot, rows, context
    )

    assert derived_pe is None
    assert snapshot.raw_ttm_eps == pytest.approx(10)
    assert snapshot.ttm_eps is None
    assert snapshot.trailing_pe == 18
    assert snapshot.trailing_pe_basis_status == expected_status
    assert snapshot.latest_eps_usable is False
    assert snapshot.ttm_eps_usable is False
    assert snapshot.trailing_pe_denominator_period_end is None


def test_foreign_private_issuer_common_stock_does_not_require_adr_ratio() -> None:
    context = PerShareBasisContext(
        issuer_type="foreign_private_issuer",
        security_type="common_stock",
        is_depositary_security=False,
        security_identity_state=VERIFIED_NON_DEPOSITARY,
        price_currency="USD",
        financial_currency="USD",
    )

    result = _normalize_per_share_value(
        8,
        value_currency="USD",
        security_basis="unknown",
        context=context,
    )

    assert result.value == 8
    assert result.status == "directly_comparable"


def test_user_caution_hides_internal_adr_basis_status() -> None:
    snapshot = ValuationSnapshot(
        trailing_pe_basis_status="currency_mismatch",
        price_to_book_basis_status="security_basis_mismatch",
        valuation_calculation_warning=True,
    )

    cautions = _data_cautions(
        snapshot.model_dump(),
        {"reason_codes": ["per_share_basis_insufficient"]},
    )

    assert cautions == ["가격 통화와 주당 실적 기준 통화가 달라 자체 PER/PBR 계산을 보류했습니다."]
    assert "currency_mismatch" not in cautions[0]


def test_unknown_security_basis_caution_stays_identity_neutral() -> None:
    snapshot = ValuationSnapshot(
        trailing_pe_basis_status="security_basis_mismatch",
        price_to_book_basis_status="insufficient_metadata",
        valuation_calculation_warning=True,
    )

    cautions = _data_cautions(
        snapshot.model_dump(),
        {"reason_codes": ["per_share_basis_insufficient"]},
    )

    assert cautions == [
        "현재 거래 증권의 주당 기준을 확인하지 못해 자체 PER/PBR 계산을 보류했습니다."
    ]
    assert "ADR" not in cautions[0]


def test_adr_unknown_share_count_basis_blocks_pbr_independently_of_pe() -> None:
    rows = [
        _with_per_share_metadata(
            row,
            currency="USD",
            eps_security_basis="depositary_security",
            share_security_basis="unknown",
        )
        for row in [*_base_rows(), _full(date(2026, 6, 30), 4)]
    ]
    context = PerShareBasisContext(
        issuer_type="adr",
        security_type="adr",
        is_depositary_security=True,
        security_identity_state=VERIFIED_DEPOSITARY,
        price_currency="USD",
        financial_currency="USD",
        adr_ratio=5,
    )
    snapshot = ValuationSnapshot(current_price=100, currency="USD")

    derived_pe, derived_pb = ValuationSnapshotService()._apply_derived_trailing(
        snapshot, rows, context
    )

    assert derived_pe == pytest.approx(10)
    assert snapshot.ttm_eps == pytest.approx(10)
    assert derived_pb is None
    assert snapshot.bvps is None
    assert snapshot.price_to_book_basis_status == "security_basis_mismatch"


def test_internal_forward_eps_uses_same_verified_adr_normalization() -> None:
    period_ends = [
        date(2024, 9, 30),
        date(2024, 12, 31),
        date(2025, 3, 31),
        date(2025, 6, 30),
        date(2025, 9, 30),
        date(2025, 12, 31),
        date(2026, 3, 31),
        date(2026, 6, 30),
    ]
    rows = [
        _with_per_share_metadata(
            _full(
                period_end,
                index + 1,
                revenue=100 + index * 10,
                income=10 + index,
            ),
            currency="USD",
            eps_security_basis="ordinary_share",
        )
        for index, period_end in enumerate(period_ends)
    ]
    context = PerShareBasisContext(
        issuer_type="adr",
        security_type="adr",
        is_depositary_security=True,
        security_identity_state=VERIFIED_DEPOSITARY,
        price_currency="USD",
        financial_currency="USD",
        adr_ratio=5,
    )
    snapshot = ValuationSnapshot(current_price=100, currency="USD")

    ValuationSnapshotService()._apply_forward_model(
        snapshot, rows, "FIXTURE", {}, basis_context=context
    )

    assert snapshot.forward_eps is not None
    assert snapshot.forward_pe == pytest.approx(100 / snapshot.forward_eps)
    assert snapshot.forward_pe_basis_status == "normalized_to_current_security"


def test_historical_point_in_time_series_remains_full_statement_only() -> None:
    rows = [*_base_rows(), _preliminary()]

    eps, _bvps, quarters, _balance = point_in_time_denominators(rows, date(2026, 8, 1))

    assert eps is None
    assert all(row.snapshot_type == "full_statement" for row in quarters)


def test_internal_forward_model_uses_latest_valid_preliminary_earnings() -> None:
    period_ends = [
        date(2024, 9, 30),
        date(2024, 12, 31),
        date(2025, 3, 31),
        date(2025, 6, 30),
        date(2025, 9, 30),
        date(2025, 12, 31),
        date(2026, 3, 31),
    ]
    rows = [
        _full(period_end, index + 1, revenue=100 + index * 10, income=10 + index)
        for index, period_end in enumerate(period_ends)
    ]
    rows.append(_preliminary(owners_income=60, total_income=65))
    snapshot = ValuationSnapshot(current_price=100, currency="KRW")

    ValuationSnapshotService()._apply_forward_model(
        snapshot,
        rows,
        "FIXTURE",
        {},
        basis_context=_verified_common_basis("KRW"),
    )

    assert snapshot.forward_pe_status == "value"
    assert snapshot.forward_eps is not None
    assert snapshot.forecast_method == "normalized_net_margin"


def test_period_parser_uses_current_range_and_ignores_comparison_ranges() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        <table id="posco-q1">
          <tr><td colspan="5">단위 : 백만원, %</td></tr>
          <tr><th>구분</th><th>당해실적</th><th>전기실적</th><th>전년동기실적</th></tr>
          <tr><th>구분</th><th>2026.01.01 ~ 2026.03.31</th><th>2025.10.01 ~ 2025.12.31</th><th>2025.01.01 ~ 2025.03.31</th></tr>
          <tr><td>매출액</td><td>당해실적</td><td>100</td><td>95</td><td>90</td></tr>
          <tr><td>영업이익</td><td>당해실적</td><td>10</td><td>9</td><td>8</td></tr>
        </table>
        """
    )

    assert parsed.period_end == date(2026, 3, 31)
    assert parsed.reporting_period_source == "current_header_date_range"
    assert parsed.reporting_period_confidence == "high"
    assert parsed.diagnostics["current_period_date_candidates"] == [
        "2026-01-01",
        "2026-03-31",
    ]
    assert "2025-12-31" in parsed.diagnostics["ignored_comparison_period_dates"]


def test_posco_short_year_current_quarter_header_is_parsed_without_comparison_pollution() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        <table id="posco-q1-short-year">
          <tr><td colspan="7">단위 : 조원, %</td></tr>
          <tr><th>구분</th><th>구분</th><th>당기실적</th><th>전기실적</th><th>전기대비</th><th>전년동기실적</th><th>전년동기대비</th></tr>
          <tr><th>구분</th><th>구분</th><th>('26.1Q)</th><th>('25.4Q)</th><th>증감율(%)</th><th>('25.1Q)</th><th>증감율(%)</th></tr>
          <tr><td>매출액</td><td>당해실적</td><td>17.88</td><td>17.20</td><td>4.0</td><td>17.44</td><td>2.5</td></tr>
          <tr><td>영업이익</td><td>당해실적</td><td>0.71</td><td>0.50</td><td>42.0</td><td>0.58</td><td>22.4</td></tr>
        </table>
        """
    )

    assert parsed.period_end == date(2026, 3, 31)
    assert parsed.reporting_period_source == "current_header_quarter"
    assert parsed.reporting_period_confidence == "high"
    assert parsed.diagnostics["current_result_header"] == "당기실적 ('26.1Q)"
    assert "2025-12-31" in parsed.diagnostics["ignored_comparison_period_dates"]
    assert "2026-03-31" not in parsed.diagnostics["ignored_comparison_period_dates"]


def test_posco_style_separate_period_table_and_trillion_unit_are_normalized() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        <table>
          <tr><td>당기실적</td><td>2026-01-01</td><td>~</td><td>2026-03-31</td></tr>
          <tr><td>전기실적</td><td>2025-10-01</td><td>~</td><td>2025-12-31</td></tr>
          <tr><td>전년동기실적</td><td>2025-01-01</td><td>~</td><td>2025-03-31</td></tr>
        </table>
        <table id="posco-results">
          <tr><td colspan="5">단위 : 조원, %</td></tr>
          <tr><th>구분</th><th>구분</th><th>당기실적</th><th>전기실적</th><th>전기대비 증감율(%)</th></tr>
          <tr><th>구분</th><th>구분</th><th>( )</th><th>( )</th><th>증감율(%)</th></tr>
          <tr><td>매출액</td><td>당해실적</td><td>17.88</td><td>16.84</td><td>6.1</td></tr>
          <tr><td>영업이익</td><td>당해실적</td><td>0.71</td><td>0.01</td><td>7,000</td></tr>
          <tr><td>지배주주순이익</td><td>당해실적</td><td>0.47</td><td>-0.23</td><td>-</td></tr>
        </table>
        """
    )

    assert parsed.period_end == date(2026, 3, 31)
    assert parsed.reporting_period_source == "document_explicit_date_range"
    assert parsed.revenue == pytest.approx(17.88e12)
    assert parsed.operating_income == pytest.approx(0.71e12)
    assert parsed.owners_parent_net_income == pytest.approx(0.47e12)
    assert parsed.raw_fields[0]["raw_unit"] == "조원"


def test_ambiguous_semantic_period_remains_null() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        <table>
          <tr><td>단위 : 백만원</td></tr>
          <tr><th>구분</th><th>당해실적</th><th>전기실적</th></tr>
          <tr><td>매출액</td><td>당해실적</td><td>100</td></tr>
          <tr><td>영업이익</td><td>당해실적</td><td>10</td></tr>
        </table>
        """
    )

    assert parsed.period_end is None
    assert parsed.reporting_period_confidence == "unavailable"


def test_adjusted_and_gaap_multiples_are_not_comparable() -> None:
    result = determine_basis_comparability(_basis(accounting="adjusted"), _basis(accounting="GAAP"))

    assert result.status == "not_comparable"
    assert result.reason == "accounting_basis_mismatch"


def test_unknown_provider_basis_preserves_official_derived_per() -> None:
    snapshot = ValuationSnapshot(
        current_price=100,
        currency="KRW",
        trailing_pe=20,
        trailing_pe_status="value",
        ttm_eps=5,
        trailing_valuation_confidence=0.85,
    )

    ValuationSnapshotService()._cross_check(
        snapshot,
        50,
        None,
        20,
        None,
        provider_pe_basis=MultipleBasis(
            metric="pe", horizon="TTM", currency="KRW", source="provider"
        ),
        derived_pe_basis=_basis(),
    )

    assert snapshot.trailing_pe == 20
    assert snapshot.trailing_pe_source == "derived_trailing"
    assert snapshot.trailing_pe_basis_conflict is False
    assert snapshot.trailing_pe_comparability == "insufficient_metadata"


def test_same_basis_discrepancy_and_structural_conflict_are_strong() -> None:
    service = ValuationSnapshotService()
    discrepancy = ValuationSnapshot(
        current_price=100,
        currency="KRW",
        trailing_pe=50,
        trailing_pe_status="value",
        ttm_eps=5,
        trailing_valuation_confidence=0.85,
    )
    service._cross_check(
        discrepancy,
        50,
        None,
        20,
        None,
        provider_pe_basis=_basis(),
        derived_pe_basis=_basis(),
    )
    structural = ValuationSnapshot(
        current_price=100,
        currency="KRW",
        trailing_pe=20,
        trailing_pe_status="value",
        ttm_eps=-2,
        trailing_valuation_confidence=0.85,
    )
    service._cross_check(
        structural,
        20,
        None,
        None,
        None,
        provider_pe_basis=_basis(),
        derived_pe_basis=_basis(),
    )

    assert discrepancy.trailing_pe_basis_conflict is True
    assert discrepancy.trailing_pe_status == "conflict"
    assert structural.trailing_pe_comparability == "structural_conflict"
    assert structural.trailing_pe_status == "not_meaningful"


def test_forward_different_horizon_does_not_create_consensus_conflict() -> None:
    snapshot = ValuationSnapshot(
        current_price=100,
        currency="KRW",
        forward_pe=25,
        forward_pe_status="value",
        forward_eps=10,
        forward_valuation_confidence=0.7,
    )

    ValuationSnapshotService()._cross_check_forward(
        snapshot,
        provider_pe=25,
        derived_pe=10,
        provider_pe_basis=_basis(horizon="provider_defined"),
        derived_pe_basis=_basis(horizon="FY1"),
    )

    assert snapshot.forward_pe == 25
    assert snapshot.forward_pe_basis_conflict is False
    assert snapshot.forward_pe_comparability == "insufficient_metadata"
    assert snapshot.forward_pe_reference_caution is True
    assert snapshot.consensus_disagreement is False
    cautions = _data_cautions(snapshot.model_dump(), {})
    assert "fPER는 산출 기간이 명확하지 않아 참고 수준입니다." in cautions


def test_single_forward_source_does_not_create_reference_caution() -> None:
    snapshot = ValuationSnapshot(
        current_price=100,
        currency="KRW",
        forward_pe=25,
        forward_pe_status="value",
    )

    ValuationSnapshotService()._cross_check_forward(
        snapshot,
        provider_pe=25,
        provider_pe_basis=_basis(horizon="provider_defined"),
    )

    assert snapshot.forward_pe_reference_caution is False
    assert not any("fPER" in caution for caution in _data_cautions(snapshot.model_dump(), {}))


def test_comparable_forward_estimates_keep_existing_conflict_policy() -> None:
    snapshot = ValuationSnapshot(
        current_price=100,
        currency="KRW",
        forward_pe=25,
        forward_pe_status="value",
        forward_eps=10,
        forward_valuation_confidence=0.7,
    )

    ValuationSnapshotService()._cross_check_forward(
        snapshot,
        provider_pe=25,
        derived_pe=10,
        provider_pe_basis=_basis(horizon="FY1"),
        derived_pe_basis=_basis(horizon="FY1"),
    )

    assert snapshot.forward_pe_basis_conflict is True
    assert snapshot.forward_pe_status == "conflict"
    assert snapshot.forward_pe_reference_caution is False


def test_adr_and_ordinary_share_multiples_are_not_comparable() -> None:
    result = determine_basis_comparability(_basis(security="ADR"), _basis(security="ordinary"))

    assert result.status == "not_comparable"
    assert result.reason == "security_basis_mismatch"


def test_preliminary_per_formula_uses_recent_four_quarter_label() -> None:
    snapshot = {
        "current_price": 100,
        "currency": "KRW",
        "trailing_pe": 10,
        "trailing_pe_status": "value",
        "ttm_eps": 10,
        "ttm_contains_preliminary": True,
    }

    lines = _valuation_formula_lines(
        snapshot,
        label="PER",
        multiple_field="trailing_pe",
        denominator_field="ttm_eps",
        denominator_label="최근 4개 분기 EPS",
    )

    assert "최근 4개 분기 EPS" in lines[0]
    assert "provisional" not in lines[0]
