from __future__ import annotations

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
from app.services.official_cash_flow_service import (
    OfficialFilingOccurrence,
    canonicalize_official_occurrence,
    canonicalize_sec_companyfacts,
    extract_sec_companyfacts_occurrences,
)


RAW_SHA = "a" * 64
AS_OF = date(2026, 8, 20)


def _occurrence(
    semantic: str,
    value: str,
    *,
    start: date = date(2026, 1, 1),
    end: date = date(2026, 6, 30),
    fiscal_year: int = 2026,
    fiscal_period: str = "Q2",
    accession: str = "0000000001-26-000001",
    form: str = "10-Q",
    filed: date = date(2026, 8, 1),
    unit: str | None = "USD",
) -> OfficialFilingOccurrence:
    namespace, tag = semantic.split(":", maxsplit=1)
    return OfficialFilingOccurrence(
        issuer_id="sec:0000000001",
        value=Decimal(value),
        currency=unit,
        unit=unit,
        period_start=start,
        period_end=end,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        source_provider="sec_edgar_companyfacts",
        source_document_id=accession,
        source_document_type=form,
        filing_date=filed,
        namespace=namespace,
        tag=tag,
        raw_payload_sha256=RAW_SHA,
        entity_scope="issuer_level",
        statement_basis="official_filing_cash_flow_statement",
    )


def _concept(tag: str, rows: list[dict[str, object]]) -> dict[str, object]:
    return {tag: {"units": {"USD": rows}}}


def _row(
    value: int,
    *,
    start: str = "2026-01-01",
    end: str = "2026-06-30",
    filed: str = "2026-08-01",
    accession: str = "0000000001-26-000001",
    form: str = "10-Q",
    fiscal_year: int = 2026,
    fiscal_period: str = "Q2",
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
    ocf_rows: list[dict[str, object]],
    capex_rows: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "cik": 1,
        "entityName": "Fixture Issuer",
        "facts": {
            "us-gaap": {
                **_concept("NetCashProvidedByUsedInOperatingActivities", ocf_rows),
                **_concept("PaymentsToAcquirePropertyPlantAndEquipment", capex_rows),
            }
        },
    }


def test_reported_ocf_is_occurrence_bound_and_deterministic() -> None:
    occurrence = _occurrence(
        "us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "250",
    )

    first = canonicalize_official_occurrence(occurrence, as_of_date=AS_OF)
    second = canonicalize_official_occurrence(occurrence, as_of_date=AS_OF)

    assert first.status == EligibilityStatus.ELIGIBLE
    assert first.fact is not None
    assert first.fact == second.fact
    assert first.fact.metric == Metric.OCF
    assert first.fact.fact_type == FactType.REPORTED
    assert first.fact.value == Decimal("250")
    assert first.fact.period.period_type == PeriodType.YTD
    assert first.fact.source_occurrence_id.startswith("sec-occurrence:")
    assert first.fact.raw_payload_sha256 == RAW_SHA


def test_ppe_capex_normalizes_negative_source_to_positive_outflow() -> None:
    decision = canonicalize_official_occurrence(
        _occurrence(
            "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
            "-40",
        ),
        as_of_date=AS_OF,
    )

    assert decision.status == EligibilityStatus.ELIGIBLE
    assert decision.fact is not None
    assert decision.fact.metric == Metric.CAPEX
    assert decision.fact.value == Decimal("40")
    assert decision.fact.source_reported_value == Decimal("-40")
    assert decision.fact.normalization_transform == (
        "absolute_value_of_negative_cash_outflow"
    )


@pytest.mark.parametrize(
    ("semantic", "reason"),
    [
        (
            "us-gaap:NetCashProvidedByUsedInInvestingActivities",
            "generic_investing_cash_flow_not_ppe_capex",
        ),
        (
            "us-gaap:PaymentsToAcquireBusinessesNetOfCashAcquired",
            "business_acquisition_excluded",
        ),
        (
            "us-gaap:PaymentsToAcquireShorttermInvestments",
            "securities_purchase_excluded",
        ),
        (
            "us-gaap:PaymentsToAcquireIntangibleAssets",
            "intangible_purchase_excluded",
        ),
    ],
)
def test_rejected_investing_semantics_never_become_ppe_capex(
    semantic: str,
    reason: str,
) -> None:
    decision = canonicalize_official_occurrence(
        _occurrence(semantic, "100"),
        as_of_date=AS_OF,
    )

    assert decision.status == EligibilityStatus.BLOCKED
    assert decision.fact is None
    assert decision.reasons == (reason,)


def test_missing_unit_and_future_filing_fail_closed() -> None:
    base = _occurrence(
        "us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "100",
    )

    missing = canonicalize_official_occurrence(
        replace(base, currency=None, unit=None),
        as_of_date=AS_OF,
    )
    future = canonicalize_official_occurrence(
        replace(base, filing_date=date(2026, 8, 21)),
        as_of_date=AS_OF,
    )

    assert missing.reasons == ("currency_or_unit_missing",)
    assert future.reasons == ("filing_date_unavailable_or_after_as_of",)


def test_q2_cash_flow_occurrence_remains_ytd() -> None:
    decision = canonicalize_official_occurrence(
        _occurrence(
            "us-gaap:NetCashProvidedByUsedInOperatingActivities",
            "100",
        ),
        as_of_date=AS_OF,
    )

    assert decision.fact is not None
    assert decision.fact.period.period_type == PeriodType.YTD
    assert decision.fact.period.duration_days == 181


def test_latest_amendment_is_selected_without_blind_overwrite() -> None:
    original = _row(
        100,
        start="2025-01-01",
        end="2025-12-31",
        filed="2026-02-01",
        accession="annual-original",
        form="10-K",
        fiscal_year=2025,
        fiscal_period="FY",
    )
    amended = {
        **original,
        "val": 110,
        "filed": "2026-03-01",
        "accn": "annual-amended",
        "form": "10-K/A",
    }
    payload = _payload([original, amended], [])

    batch = canonicalize_sec_companyfacts(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
    )

    assert len(batch.facts) == 1
    assert batch.facts[0].value == Decimal("110")
    assert batch.facts[0].source_document_id == "annual-amended"
    assert batch.facts[0].source_document_type == "10-K/A"


def test_comparative_occurrence_keeps_original_economic_fiscal_context() -> None:
    original = _row(
        100,
        start="2025-01-01",
        end="2025-06-30",
        filed="2025-07-20",
        accession="2025-q2",
        fiscal_year=2025,
    )
    comparative = {
        **original,
        "val": 105,
        "filed": "2026-07-20",
        "accn": "2026-q2",
        "fy": 2026,
    }
    payload = _payload([original, comparative], [])

    batch = canonicalize_sec_companyfacts(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
    )

    assert len(batch.facts) == 1
    assert batch.facts[0].value == Decimal("105")
    assert batch.facts[0].period.fiscal_year == 2025
    assert batch.facts[0].source_document_id == "2026-q2"


def test_exact_duplicate_is_idempotently_suppressed() -> None:
    row = _row(100)
    payload = _payload([row, dict(row)], [])

    batch = canonicalize_sec_companyfacts(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
    )

    assert len(batch.facts) == 1
    assert batch.exact_duplicates_suppressed == 1
    assert batch.conflicts == 0


def test_same_occurrence_different_values_is_conflict() -> None:
    payload = _payload([_row(100), _row(101)], [])

    batch = canonicalize_sec_companyfacts(
        payload,
        raw_payload_sha256=RAW_SHA,
        as_of_date=AS_OF,
    )

    assert batch.facts == ()
    assert batch.conflicts == 1
    assert batch.denials[0]["reason"] == "source_occurrence_conflict"


def test_extraction_uses_only_verified_registry_semantics() -> None:
    payload = _payload([_row(100)], [_row(40)])

    occurrences = extract_sec_companyfacts_occurrences(
        payload,
        raw_payload_sha256=RAW_SHA,
    )

    assert {item.semantic for item in occurrences} == {
        "us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
    }
