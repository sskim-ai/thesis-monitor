"""Strict subject identity extraction for versioned audit report contracts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json


CONTRACT_VERSION = "report-subject-identity-v1"
MARKET_EXPECTATION_EVIDENCE_VIEW_CONTRACT = (
    "market-expectation-evidence-view-v1"
)


class ReportSubjectIdentityError(ValueError):
    """Raised when a report cannot prove its subject identity safely."""


@dataclass(frozen=True)
class ReportSubjectIdentity:
    contract: str
    count_field: str
    reported_count: int
    actual_row_count: int
    tickers: tuple[str, ...]
    ticker_set_sha256: str


def _ticker_set_sha256(tickers: Sequence[str]) -> str:
    payload = json.dumps(
        sorted(tickers),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _strict_tickers(rows: object, *, subject: str) -> tuple[str, ...]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ReportSubjectIdentityError(f"{subject}:ROWS_SEQUENCE_REQUIRED")
    tickers: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ReportSubjectIdentityError(
                f"{subject}:ROW_MAPPING_REQUIRED:{index}"
            )
        ticker = row.get("ticker")
        if not isinstance(ticker, str) or not ticker.strip():
            raise ReportSubjectIdentityError(
                f"{subject}:NONEMPTY_TICKER_REQUIRED:{index}"
            )
        tickers.append(ticker.strip())
    duplicates = sorted(
        ticker for ticker, count in Counter(tickers).items() if count > 1
    )
    if duplicates:
        raise ReportSubjectIdentityError(
            f"{subject}:DUPLICATE_TICKERS:{','.join(duplicates)}"
        )
    return tuple(tickers)


def report_subject_identity(
    report: Mapping[str, object],
) -> ReportSubjectIdentity:
    """Read only the count field authorized by the report's versioned contract."""

    contract = report.get("contract")
    if contract != MARKET_EXPECTATION_EVIDENCE_VIEW_CONTRACT:
        raise ReportSubjectIdentityError(
            f"UNKNOWN_REPORT_CONTRACT:{contract!s}"
        )
    if "subject_count" not in report:
        raise ReportSubjectIdentityError(
            f"{contract}:MISSING_AUTHORITATIVE_COUNT:subject_count"
        )
    reported_count = report["subject_count"]
    if isinstance(reported_count, bool) or not isinstance(reported_count, int):
        raise ReportSubjectIdentityError(
            f"{contract}:INTEGER_SUBJECT_COUNT_REQUIRED"
        )
    if reported_count < 0:
        raise ReportSubjectIdentityError(
            f"{contract}:NONNEGATIVE_SUBJECT_COUNT_REQUIRED"
        )
    rows = report.get("rows")
    tickers = _strict_tickers(rows, subject=contract)
    if reported_count != len(tickers):
        raise ReportSubjectIdentityError(
            f"{contract}:SUBJECT_COUNT_ROW_COUNT_MISMATCH:"
            f"{reported_count}!={len(tickers)}"
        )
    return ReportSubjectIdentity(
        contract=contract,
        count_field="subject_count",
        reported_count=reported_count,
        actual_row_count=len(tickers),
        tickers=tickers,
        ticker_set_sha256=_ticker_set_sha256(tickers),
    )


def audit_subject_set_identity(
    active_tickers: Sequence[str],
    inventories: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    """Compare exact ticker sets while rejecting missing or duplicate identities."""

    active_rows = tuple({"ticker": ticker} for ticker in active_tickers)
    active = _strict_tickers(active_rows, subject="active_universe")
    active_set = set(active)
    rows: list[dict[str, object]] = []
    total_duplicates = 0
    mismatch_count = 0
    for artifact, raw_tickers in inventories.items():
        raw = tuple(str(ticker).strip() for ticker in raw_tickers)
        duplicate_count = len(raw) - len(set(raw))
        total_duplicates += duplicate_count
        empty_count = sum(not ticker for ticker in raw)
        observed_set = set(raw)
        missing = sorted(active_set - observed_set)
        extra = sorted(observed_set - active_set)
        matches = (
            duplicate_count == 0
            and empty_count == 0
            and len(raw) == len(active)
            and observed_set == active_set
        )
        mismatch_count += not matches
        rows.append(
            {
                "artifact": artifact,
                "reported_count": len(raw),
                "ticker_set_sha256": _ticker_set_sha256(raw),
                "matches_active_universe": matches,
                "duplicate_count": duplicate_count,
                "empty_ticker_count": empty_count,
                "missing_tickers": missing,
                "extra_tickers": extra,
                "status": "PASS" if matches else "FAIL",
            }
        )
    return {
        "status": (
            "PASS"
            if active and mismatch_count == 0 and total_duplicates == 0
            else "FAIL"
        ),
        "contract": CONTRACT_VERSION,
        "active_count": len(active),
        "active_ticker_set_sha256": _ticker_set_sha256(active),
        "ticker_set_mismatch_count": mismatch_count,
        "duplicate_ticker_count": total_duplicates,
        "rows": rows,
    }
