from __future__ import annotations

import pytest

from app.services.report_subject_identity_service import (
    MARKET_EXPECTATION_EVIDENCE_VIEW_CONTRACT,
    ReportSubjectIdentityError,
    audit_subject_set_identity,
    report_subject_identity,
)


def _report(tickers: list[str], *, count: int | None = None):
    return {
        "contract": MARKET_EXPECTATION_EVIDENCE_VIEW_CONTRACT,
        "subject_count": len(tickers) if count is None else count,
        "rows": [{"ticker": ticker} for ticker in tickers],
    }


def test_subject_count_and_exact_22_ticker_set_pass() -> None:
    tickers = [f"T{index:02d}" for index in range(22)]
    identity = report_subject_identity(_report(tickers))
    audit = audit_subject_set_identity(
        tickers,
        {"expectation_view": identity.tickers, "packets": tickers},
    )

    assert identity.count_field == "subject_count"
    assert identity.reported_count == 22
    assert audit["status"] == "PASS"


def test_non22_exact_active_universe_passes_without_fixed_count() -> None:
    tickers = [f"N{index:02d}" for index in range(21)]
    identity = report_subject_identity(_report(tickers))

    assert audit_subject_set_identity(
        tickers,
        {"expectation_view": identity.tickers, "packets": tickers},
    )["status"] == "PASS"


def test_subject_count_row_count_mismatch_fails_closed() -> None:
    with pytest.raises(
        ReportSubjectIdentityError,
        match="SUBJECT_COUNT_ROW_COUNT_MISMATCH",
    ):
        report_subject_identity(_report([f"T{index:02d}" for index in range(21)], count=22))


def test_duplicate_ticker_fails_closed() -> None:
    tickers = [f"T{index:02d}" for index in range(21)] + ["T00"]

    with pytest.raises(ReportSubjectIdentityError, match="DUPLICATE_TICKERS"):
        report_subject_identity(_report(tickers))


def test_same_count_different_ticker_set_fails_identity_audit() -> None:
    active = [f"T{index:02d}" for index in range(22)]
    observed = [*active[:-1], "OTHER"]

    audit = audit_subject_set_identity(active, {"expectation_view": observed})

    assert audit["status"] == "FAIL"
    assert audit["ticker_set_mismatch_count"] == 1


def test_unknown_contract_does_not_guess_a_count_field() -> None:
    with pytest.raises(ReportSubjectIdentityError, match="UNKNOWN_REPORT_CONTRACT"):
        report_subject_identity(
            {
                "contract": "unknown-v1",
                "active_count": 2,
                "subject_count": 2,
                "rows": [{"ticker": "A"}, {"ticker": "B"}],
            }
        )


def test_missing_subject_count_fails_closed() -> None:
    with pytest.raises(
        ReportSubjectIdentityError,
        match="MISSING_AUTHORITATIVE_COUNT",
    ):
        report_subject_identity(
            {
                "contract": MARKET_EXPECTATION_EVIDENCE_VIEW_CONTRACT,
                "rows": [{"ticker": "A"}],
            }
        )
