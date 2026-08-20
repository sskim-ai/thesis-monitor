from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FactType,
    Metric,
    PeriodType,
)
from app.services.cash_flow_shadow_service import (
    blocked_cash_flow_core,
    build_sec_cash_flow_core,
    snapshot_to_dict,
)


AS_OF = date(2026, 8, 20)
RAW_SHA = "b" * 64


def _row(
    value: int,
    *,
    start: str,
    end: str,
    filed: str,
    accession: str,
    form: str,
    fiscal_year: int,
    fiscal_period: str,
) -> dict[str, object]:
    return {
        "val": value,
        "start": start,
        "end": end,
        "filed": filed,
        "accn": accession,
        "form": form,
        "fy": fiscal_year,
        "fp": fiscal_period,
    }


def _payload(
    ocf: list[dict[str, object]],
    capex: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "cik": 42,
        "entityName": "Cash Flow Fixture",
        "facts": {
            "us-gaap": {
                "NetCashProvidedByUsedInOperatingActivities": {
                    "units": {"USD": ocf}
                },
                "PaymentsToAcquirePropertyPlantAndEquipment": {
                    "units": {"USD": capex}
                },
            }
        },
    }


def _period_rows(
    prior_fy: int,
    prior_q1: int,
    prior_q2: int,
    current_q1: int,
    current_q2: int,
) -> list[dict[str, object]]:
    return [
        _row(
            prior_fy,
            start="2025-01-01",
            end="2025-12-31",
            filed="2026-02-15",
            accession="2025-fy",
            form="10-K",
            fiscal_year=2025,
            fiscal_period="FY",
        ),
        _row(
            prior_q1,
            start="2025-01-01",
            end="2025-03-31",
            filed="2025-04-20",
            accession="2025-q1",
            form="10-Q",
            fiscal_year=2025,
            fiscal_period="Q1",
        ),
        _row(
            prior_q2,
            start="2025-01-01",
            end="2025-06-30",
            filed="2025-07-20",
            accession="2025-q2",
            form="10-Q",
            fiscal_year=2025,
            fiscal_period="Q2",
        ),
        _row(
            current_q1,
            start="2026-01-01",
            end="2026-03-31",
            filed="2026-04-20",
            accession="2026-q1",
            form="10-Q",
            fiscal_year=2026,
            fiscal_period="Q1",
        ),
        _row(
            current_q2,
            start="2026-01-01",
            end="2026-06-30",
            filed="2026-07-20",
            accession="2026-q2",
            form="10-Q",
            fiscal_year=2026,
            fiscal_period="Q2",
        ),
    ]


def test_shadow_core_builds_reported_qtd_ttm_and_fcf_lineage() -> None:
    payload = _payload(
        _period_rows(500, 100, 220, 130, 300),
        _period_rows(200, 40, 90, 50, 120),
    )

    snapshot = build_sec_cash_flow_core(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
        financial_type="non_financial",
    )

    assert snapshot.status == EligibilityStatus.ELIGIBLE
    assert snapshot.latest_fcf is not None
    assert snapshot.latest_fcf.value == Decimal("180")
    assert snapshot.latest_fcf.period.period_type == PeriodType.YTD
    assert snapshot.latest_qtd_fcf is not None
    assert snapshot.latest_qtd_fcf.value == Decimal("100")
    assert snapshot.latest_ttm_fcf is not None
    assert snapshot.latest_ttm_fcf.value == Decimal("350")
    assert all(
        item.fact_type == FactType.DERIVED_METRIC
        for item in snapshot.facts
        if item.metric == Metric.FCF
    )
    facts = {item.fact_id: item for item in snapshot.facts}
    for fcf in (item for item in snapshot.facts if item.metric == Metric.FCF):
        assert len(fcf.input_fact_ids) == 2
        ocf = facts[fcf.input_fact_ids[0]]
        capex = facts[fcf.input_fact_ids[1]]
        assert fcf.value == ocf.value - capex.value
        assert fcf.derivation_version == "cash-flow-capital-efficiency-v1"


def test_missing_capex_is_partial_and_never_substituted_with_zero() -> None:
    payload = _payload(_period_rows(500, 100, 220, 130, 300), [])

    snapshot = build_sec_cash_flow_core(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
        financial_type="non_financial",
    )

    assert snapshot.status == EligibilityStatus.PARTIAL
    assert snapshot.latest_fcf is None
    assert "missing_ppe_capex" in snapshot.denial_reasons
    assert not any(item.metric == Metric.CAPEX for item in snapshot.facts)


def test_insurance_is_not_applicable_before_source_arithmetic() -> None:
    snapshot = build_sec_cash_flow_core(
        _payload(_period_rows(500, 100, 220, 130, 300), _period_rows(200, 40, 90, 50, 120)),
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
        financial_type="financial",
    )

    assert snapshot.status == EligibilityStatus.NOT_APPLICABLE
    assert snapshot.facts == ()
    assert snapshot.denial_reasons == ("financial_industry_not_applicable",)


def test_issuer_level_foreign_cash_flow_does_not_require_security_basis() -> None:
    payload = _payload(
        [
            _row(
                1000,
                start="2025-01-01",
                end="2025-12-31",
                filed="2026-04-01",
                accession="foreign-fy",
                form="20-F",
                fiscal_year=2025,
                fiscal_period="FY",
            )
        ],
        [
            _row(
                400,
                start="2025-01-01",
                end="2025-12-31",
                filed="2026-04-01",
                accession="foreign-fy",
                form="20-F",
                fiscal_year=2025,
                fiscal_period="FY",
            )
        ],
    )

    snapshot = build_sec_cash_flow_core(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
        financial_type="non_financial",
    )

    assert snapshot.status == EligibilityStatus.ELIGIBLE
    assert snapshot.latest_fcf is not None
    assert snapshot.latest_fcf.value == Decimal("600")
    serialized = snapshot_to_dict(snapshot)
    assert "security" not in serialized
    assert "market_cap" not in serialized


def test_blocked_kr_period_context_has_no_facts() -> None:
    snapshot = blocked_cash_flow_core(
        "period_context_unresolved",
        partial=True,
        source_audit={"provider": "opendart_stored"},
    )

    assert snapshot.status == EligibilityStatus.PARTIAL
    assert snapshot.facts == ()
    assert snapshot.denial_reasons == ("period_context_unresolved",)


def test_snapshot_serialization_preserves_decimal_as_exact_string() -> None:
    payload = _payload(
        [
            _row(
                -7,
                start="2025-01-01",
                end="2025-12-31",
                filed="2026-02-01",
                accession="negative-fy",
                form="10-K",
                fiscal_year=2025,
                fiscal_period="FY",
            )
        ],
        [
            _row(
                11,
                start="2025-01-01",
                end="2025-12-31",
                filed="2026-02-01",
                accession="negative-fy",
                form="10-K",
                fiscal_year=2025,
                fiscal_period="FY",
            )
        ],
    )

    snapshot = build_sec_cash_flow_core(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
        financial_type="non_financial",
    )
    serialized = snapshot_to_dict(snapshot)
    fcf = next(item for item in serialized["facts"] if item["metric"] == Metric.FCF)

    assert fcf["value"] == "-18"
