from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


CONTRACT_VERSION = "ohlcv-provider-integrity-v1"
BAR_FIELDS = ("date", "open", "high", "low", "close", "volume", "value")
PRICE_FIELDS = ("open", "high", "low", "close")


class OhlcvViolation(StrEnum):
    INVALID_BAR_DATE = "INVALID_BAR_DATE"
    FUTURE_BAR = "FUTURE_BAR"
    MISSING_OHLC_FIELD = "MISSING_OHLC_FIELD"
    NONFINITE_VALUE = "NONFINITE_VALUE"
    NONPOSITIVE_PRICE = "NONPOSITIVE_PRICE"
    HIGH_LT_OPEN = "HIGH_LT_OPEN"
    HIGH_LT_CLOSE = "HIGH_LT_CLOSE"
    LOW_GT_OPEN = "LOW_GT_OPEN"
    LOW_GT_CLOSE = "LOW_GT_CLOSE"
    LOW_GT_HIGH = "LOW_GT_HIGH"
    NEGATIVE_VOLUME = "NEGATIVE_VOLUME"
    DUPLICATE_TIMESTAMP = "DUPLICATE_TIMESTAMP"
    DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"
    BAR_TIMESTAMP_ORDERING = "BAR_TIMESTAMP_ORDERING"


class MalformedRefetchOutcome(StrEnum):
    FIRST_RESPONSE_INVALID = "FIRST_RESPONSE_INVALID"
    PROVIDER_REFETCH_RECOVERED = "PROVIDER_REFETCH_RECOVERED"
    STABLE_BAD_SOURCE = "STABLE_BAD_SOURCE"
    INTERMITTENT_BAD_SOURCE = "INTERMITTENT_BAD_SOURCE"
    REFRESH_TRANSPORT_FAILED_RETAIN_INVALID = "REFRESH_TRANSPORT_FAILED_RETAIN_INVALID"


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class OhlcvIntegrityIssue(FrozenModel):
    timeframe: str
    bar_date: str | None
    violation: OhlcvViolation
    field_values: dict[str, str | None]
    row_fingerprint: str


class OhlcvIntegrityInspection(FrozenModel):
    contract: str = CONTRACT_VERSION
    valid: bool
    bar_count: int
    invalid_row_count: int
    payload_fingerprint: str
    issues: tuple[OhlcvIntegrityIssue, ...] = ()


class OhlcvIntegrityEvent(FrozenModel):
    provider: str
    ticker: str
    timeframe: str
    adjustment_mode: str
    first_bad_stage: str
    outcome: MalformedRefetchOutcome
    first_payload_fingerprint: str
    second_payload_fingerprint: str | None = None
    issues: tuple[OhlcvIntegrityIssue, ...] = ()


class UniformAdjustmentAudit(FrozenModel):
    compatible: bool
    price_factor: str | None
    volume_factor: str | None
    reason: str | None = None


def canonical_fingerprint(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _decimal(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def _row_identity(row: Mapping[str, object]) -> dict[str, object]:
    return {field: row.get(field) for field in BAR_FIELDS}


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def inspect_normalized_ohlcv_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    timeframe: str,
    cutoff: date | None = None,
) -> OhlcvIntegrityInspection:
    identities = [_row_identity(row) for row in rows]
    payload_fingerprint = canonical_fingerprint(identities)
    issues: list[OhlcvIntegrityIssue] = []
    dates: list[str] = []
    seen: dict[str, str] = {}
    invalid_rows: set[str] = set()

    def add_issue(
        *,
        row: Mapping[str, object],
        bar_date: str | None,
        violation: OhlcvViolation,
    ) -> None:
        identity = _row_identity(row)
        row_fingerprint = canonical_fingerprint(identity)
        invalid_rows.add(row_fingerprint)
        issues.append(
            OhlcvIntegrityIssue(
                timeframe=timeframe,
                bar_date=bar_date,
                violation=violation,
                field_values={
                    field: None if identity[field] is None else str(identity[field])
                    for field in BAR_FIELDS
                },
                row_fingerprint=row_fingerprint,
            )
        )

    for row in rows:
        raw_date = str(row.get("date") or "")[:10]
        try:
            bar_date = date.fromisoformat(raw_date)
        except ValueError:
            add_issue(
                row=row,
                bar_date=raw_date or None,
                violation=OhlcvViolation.INVALID_BAR_DATE,
            )
            continue
        dates.append(bar_date.isoformat())
        if cutoff is not None and bar_date > cutoff:
            add_issue(
                row=row,
                bar_date=bar_date.isoformat(),
                violation=OhlcvViolation.FUTURE_BAR,
            )

        missing = [field for field in PRICE_FIELDS if field not in row or row.get(field) is None]
        if missing:
            add_issue(
                row=row,
                bar_date=bar_date.isoformat(),
                violation=OhlcvViolation.MISSING_OHLC_FIELD,
            )
            continue
        values = {field: _decimal(row.get(field)) for field in PRICE_FIELDS}
        if any(value is None for value in values.values()):
            add_issue(
                row=row,
                bar_date=bar_date.isoformat(),
                violation=OhlcvViolation.NONFINITE_VALUE,
            )
            continue
        open_price = values["open"]
        high = values["high"]
        low = values["low"]
        close = values["close"]
        assert open_price is not None and high is not None and low is not None and close is not None
        if min(open_price, high, low, close) <= 0:
            add_issue(
                row=row,
                bar_date=bar_date.isoformat(),
                violation=OhlcvViolation.NONPOSITIVE_PRICE,
            )
        for condition, violation in (
            (high < open_price, OhlcvViolation.HIGH_LT_OPEN),
            (high < close, OhlcvViolation.HIGH_LT_CLOSE),
            (low > open_price, OhlcvViolation.LOW_GT_OPEN),
            (low > close, OhlcvViolation.LOW_GT_CLOSE),
            (low > high, OhlcvViolation.LOW_GT_HIGH),
        ):
            if condition:
                add_issue(row=row, bar_date=bar_date.isoformat(), violation=violation)
        volume = _decimal(row.get("volume"))
        if volume is not None and volume < 0:
            add_issue(
                row=row,
                bar_date=bar_date.isoformat(),
                violation=OhlcvViolation.NEGATIVE_VOLUME,
            )

        row_fingerprint = canonical_fingerprint(_row_identity(row))
        previous = seen.get(bar_date.isoformat())
        if previous is not None:
            add_issue(
                row=row,
                bar_date=bar_date.isoformat(),
                violation=(
                    OhlcvViolation.DUPLICATE_TIMESTAMP
                    if previous == row_fingerprint
                    else OhlcvViolation.DUPLICATE_CONFLICT
                ),
            )
        else:
            seen[bar_date.isoformat()] = row_fingerprint

    if dates != sorted(dates) and rows:
        add_issue(
            row=rows[-1],
            bar_date=dates[-1] if dates else None,
            violation=OhlcvViolation.BAR_TIMESTAMP_ORDERING,
        )
    unique_issues = tuple(
        {
            (issue.row_fingerprint, issue.violation): issue for issue in issues
        }.values()
    )
    return OhlcvIntegrityInspection(
        valid=not unique_issues,
        bar_count=len(rows),
        invalid_row_count=len(invalid_rows),
        payload_fingerprint=payload_fingerprint,
        issues=unique_issues,
    )


def audit_uniform_adjustment(
    raw: Mapping[str, object],
    adjusted: Mapping[str, object],
) -> UniformAdjustmentAudit:
    raw_prices = [_decimal(raw.get(field)) for field in PRICE_FIELDS]
    adjusted_prices = [_decimal(adjusted.get(field)) for field in PRICE_FIELDS]
    if any(value in {None, Decimal(0)} for value in raw_prices) or any(
        value is None for value in adjusted_prices
    ):
        return UniformAdjustmentAudit(
            compatible=False,
            price_factor=None,
            volume_factor=None,
            reason="missing_or_zero_adjustment_input",
        )
    factors = {
        adjusted_value / raw_value
        for raw_value, adjusted_value in zip(raw_prices, adjusted_prices, strict=True)
        if raw_value is not None and adjusted_value is not None
    }
    if len(factors) != 1:
        return UniformAdjustmentAudit(
            compatible=False,
            price_factor=None,
            volume_factor=None,
            reason="mixed_field_adjustment",
        )
    factor = next(iter(factors))
    raw_volume = _decimal(raw.get("volume"))
    adjusted_volume = _decimal(adjusted.get("volume"))
    volume_factor = (
        adjusted_volume / raw_volume
        if raw_volume not in {None, Decimal(0)} and adjusted_volume is not None
        else None
    )
    return UniformAdjustmentAudit(
        compatible=True,
        price_factor=_decimal_text(factor),
        volume_factor=_decimal_text(volume_factor) if volume_factor is not None else None,
    )
